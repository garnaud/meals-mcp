import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from mcp.types import TextContent
from meals_mcp.server import call_tool, list_tools
from meals_mcp.models import Meal

@pytest.mark.asyncio
async def test_list_tools():
    tools = await list_tools()
    assert len(tools) == 2
    tool_names = [tool.name for tool in tools]
    assert "get_recent_meals" in tool_names
    assert "update_meal" in tool_names

@pytest.mark.asyncio
async def test_call_tool():
    with patch("meals_mcp.server.NotionClient") as MockNotionClient:
        # Mock NotionClient behavior
        mock_instance = MockNotionClient.return_value
        
        # Mock synchronous get_meals called via asyncio.to_thread
        mock_instance.get_meals.return_value = [
            Meal(
                name="Test Meal",
                date="2023-10-27",
                ingredients=["Chicken", "Rice"],
                heure="soir",
                recipe="http://recipe.com"
            )
        ]

        # Call the tool
        result = await call_tool("get_recent_meals", {"limit": 10})
        
        # Assertions
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        
        text = result[0].text
        assert "**Test Meal** (2023-10-27, soir)" in text
        assert "Ingredients: Chicken, Rice (Recipe: http://recipe.com)" in text
        
        # Verify limit was passed correctly
        mock_instance.get_meals.assert_called_with(limit=10, start_date=None, end_date=None, search_query=None)

@pytest.mark.asyncio
async def test_call_tool_search():
    with patch("meals_mcp.server.NotionClient") as MockNotionClient:
        mock_instance = MockNotionClient.return_value
        mock_instance.get_meals.return_value = [
            Meal(
                name="Pasta",
                date="2023-10-27",
                ingredients=["Pasta", "Tomato"],
                heure="soir",
                recipe=None
            )
        ]

        # Call the tool
        result = await call_tool("get_recent_meals", {"search_query": "Pasta"})
        
        # Assertions
        assert len(result) == 1
        text = result[0].text
        assert "Here are the meals matching 'Pasta':" in text
        assert "**Pasta**" in text
        
        # Verify search_query was passed correctly
        mock_instance.get_meals.assert_called_with(limit=30, start_date=None, end_date=None, search_query="Pasta")

@pytest.mark.asyncio
async def test_call_tool_empty():
    with patch("meals_mcp.server.NotionClient") as MockNotionClient:
        mock_instance = MockNotionClient.return_value
        mock_instance.get_meals.return_value = []

        result = await call_tool("get_recent_meals", {})
        
        assert "No meals found" in result[0].text
