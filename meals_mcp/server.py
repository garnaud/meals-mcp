import asyncio
import sys
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server
from meals_mcp.utils.notion import NotionClient

# Initialize the server
app = Server("meals-mcp")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_recent_meals",
            description="Retrieves a list of meals from the Notion 'Repas' database. Can filter by date range (start_date, end_date), search by name, or just get the most recent ones.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "The number of meals to retrieve (default: 30)",
                        "default": 30
                    },
                    "start_date": {
                        "type": "string",
                        "description": "The start date for filtering meals (ISO 8601 format, e.g., '2023-10-27'). If provided, retrieves meals on or after this date."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "The end date for filtering meals (ISO 8601 format, e.g., '2023-10-31'). If provided, retrieves meals on or before this date."
                    },
                    "search_query": {
                        "type": "string",
                        "description": "A search term to filter meals by name (e.g., 'pasta')."
                    }
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution."""
    if name == "get_recent_meals":
        limit = arguments.get("limit", 30)
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        search_query = arguments.get("search_query")
        
        try:
            client = NotionClient()
            # Run the synchronous Notion client in a thread
            meals = await asyncio.to_thread(client.get_meals, limit=limit, start_date=start_date, end_date=end_date, search_query=search_query)
            
            if not meals:
                return [TextContent(type="text", text="No meals found within the specified criteria.")]

            if search_query:
                meal_list_str = f"Here are the meals matching '{search_query}':\n\n"
            elif start_date or end_date:
                meal_list_str = f"Here are the meals from {start_date or 'beginning'} to {end_date or 'now'}:\n\n"
            else:
                meal_list_str = "Here are the most recent meals:\n\n"
            
            for meal in meals:
                tags_str = ", ".join(meal.tags) if meal.tags else "No tags"
                recipe_link = f" (Recipe: {meal.recipe})" if meal.recipe else ""
                meal_list_str += f"- **{meal.name}** ({meal.date}, {meal.heure})\n"
                meal_list_str += f"  Tags: {tags_str}{recipe_link}\n"

            return [TextContent(type="text", text=meal_list_str)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error fetching meals: {str(e)}")]
    
    raise ValueError(f"Tool not found: {name}")

async def main():
    # run the server using stdio
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

def run():
    asyncio.run(main())

if __name__ == "__main__":
    run()
