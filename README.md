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

## Meal Planning Agent System

This project includes an advanced multi-agent system to plan your weekly meals based on your Notion history and specific family constraints.

### How it works

The system uses three specialized agents:
*   **Planner:** Retrieves the last 3 months of meals from Notion and creates a draft plan respecting constraints (simple meals on Mon/Tue, light Saturday noon, etc.).
*   **Dietical Coach:** Ensures the plan is balanced and healthy, providing feedback to the Planner if iterations are needed.
*   **Cooker:** Once the plan is approved, this French Chef persona provides concise recipe cards, tips, and estimated durations for each meal.

### Usage

1.  **Set your Google API Key:**
    The agents require access to Gemini. Export your API key:
    ```bash
    export GOOGLE_API_KEY="your_google_api_key"
    ```

2.  **Run the interactive script:**
    ```bash
    uv run python scripts/plan_week.py
    ```

3.  **Follow the prompts:**
    - Enter the date range for the week.
    - Review the proposed plan.
    - Provide feedback (e.g., "Change Wednesday lunch to something without chicken") or confirm the plan.
    - Receive your final shopping list (for 5 people) and Chef's recipe cards!

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
