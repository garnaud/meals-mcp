import os
from unittest.mock import patch
from meals_mcp.main import main
from meals_mcp.utils.notion import NotionClient

def test_main_no_token(capsys):
    """
    Test the main function when the NOTION_TOKEN is not set.
    """
    if "NOTION_TOKEN" in os.environ:
        del os.environ["NOTION_TOKEN"]
    if "NOTION_API_KEY" in os.environ:
        del os.environ["NOTION_API_KEY"]

    main()
    captured = capsys.readouterr()
    assert "Error: Notion API token (NOTION_TOKEN or NOTION_API_KEY) not found. Please set the environment variable or pass it to the constructor." in captured.out

@patch("meals_mcp.main.NotionClient")
@patch("meals_mcp.utils.notion.notion_client.Client")
def test_main_with_token(MockNotionAPIClient, MockNotionClient, capsys):
    """
    Test the main function when the NOTION_TOKEN is set.
    """
    os.environ["NOTION_TOKEN"] = "test_token"

    # Mock the NotionClient instance and its get_users method
    mock_instance = MockNotionClient.return_value
    mock_instance.get_users.return_value = [
        {
            "name": "Test User",
            "person": {
                "email": "test@example.com"
            }
        }
    ]

    main()
    captured = capsys.readouterr()
    assert "Successfully connected to Notion API." in captured.out
    assert "Users in your workspace:" in captured.out
    assert "- Test User (test@example.com)" in captured.out

    del os.environ["NOTION_TOKEN"]
