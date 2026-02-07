import os
from meals_mcp.utils.notion import NotionClient

def main():
    """
    Main function to interact with Notion.
    """
    try:
        notion_client_instance = NotionClient()
        
        # Example: list users
        users = notion_client_instance.get_users()
        print("Successfully connected to Notion API.")
        print("Users in your workspace:")
        for user in users:
            print(f"- {user.get('name')} ({user.get('person', {}).get('email')})")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error interacting with Notion API: {e}")

if __name__ == "__main__":
    main()
