# Meals MCP

This project is a Python-based MCP (Mission Control Plane) for interacting with Notion.

## Setup

1.  **Install uv:**

    ```bash
    pip install uv
    ```

2.  **Create a virtual environment:**

    ```bash
    uv venv
    ```

3.  **Activate the virtual environment:**

    ```bash
    source .venv/bin/activate
    ```

4.  **Install dependencies:**

    ```bash
    uv pip install -e .
    ```

5.  **Set up your Notion API key:**

    Create a `.env` file in the root of the project and add your Notion API key:

    ```
    NOTION_TOKEN="your_notion_api_key"
    ```

## Usage

To run the main application (CLI example):

```bash
meals-mcp
```

To run the MCP server:

```bash
meals-mcp-server
```

## Using MCP Locally with Gemini

To use this MCP server locally with the Gemini desktop app, you need to add it to your Gemini configuration file.

1.  **Locate the Gemini configuration file:**
    *   **macOS:** `~/Library/Application Support/Google/Gemini/gemini_config.json` (or similar path depending on exact version)
    *   *Alternatively, check the Gemini app settings for "Manage MCP Servers".*

2.  **Add the server configuration:**

    Add the following entry to the `mcpServers` object in your configuration file. Make sure to replace `/path/to/your/meals-mcp` with the actual absolute path to this project directory.

    ```json
    {
      "mcpServers": {
        "meals-mcp": {
          "command": "uv",
          "args": [
            "run",
            "meals-mcp-server"
          ],
          "cwd": "/path/to/your/meals-mcp",
          "env": {
            "NOTION_TOKEN": "your_notion_api_key"
          }
        }
      }
    }
    ```

    *Note: You can either hardcode the `NOTION_TOKEN` in the `env` section (as shown above) or ensure the `.env` file is loaded correctly by the environment.*

3.  **Restart Gemini:** Restart the Gemini application for the changes to take effect.

4.  **Verify:** Ask Gemini to "List my recent meals" to verify the connection.

## Testing

To run the tests:

```bash
uv run pytest
```
