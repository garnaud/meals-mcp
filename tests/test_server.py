import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from mcp.types import TextContent
from meals_mcp.server import call_tool, list_tools
from meals_mcp.models import Meal

@pytest.mark.asyncio
async def test_list_tools():
    tools = await list_tools()
    assert len(tools) == 1
    assert tools[0].name == "get_recent_meals"

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
                tags=["Chicken", "Rice"],
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
        assert "Tags: Chicken, Rice (Recipe: http://recipe.com)" in text
        
        # Verify limit was passed correctly
        mock_instance.get_meals.assert_called_with(limit=10)

@pytest.mark.asyncio
async def test_call_tool_empty():
    with patch("meals_mcp.server.NotionClient") as MockNotionClient:
        mock_instance = MockNotionClient.return_value
        mock_instance.get_meals.return_value = []

        result = await call_tool("get_recent_meals", {})
        
        assert "No meals found" in result[0].text
