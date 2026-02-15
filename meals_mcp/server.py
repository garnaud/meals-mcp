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
        ),
        Tool(
            name="update_meal",
            description="Updates a meal in the database. Can search by name first to confirm ID, or update directly by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "meal_id": {
                        "type": "string",
                        "description": "The Notion Page ID of the meal to update. Required for the actual update."
                    },
                    "name_search": {
                        "type": "string",
                        "description": "Name of the meal to search for if ID is unknown. Will return a list of matches with IDs."
                    },
                    "new_name": {
                        "type": "string",
                        "description": "New name for the meal."
                    },
                    "date": {
                        "type": "string",
                        "description": "New date for the meal (ISO 8601, YYYY-MM-DD)."
                    },
                    "heure": {
                        "type": "string",
                        "description": "New time ('Midi' or 'Soir')."
                    },
                    "ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of new ingredients."
                    },
                    "recipe": {
                        "type": "string",
                        "description": "New recipe URL."
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
                ingredients_str = ", ".join(meal.ingredients) if meal.ingredients else "No ingredients"
                recipe_link = f" (Recipe: {meal.recipe})" if meal.recipe else ""
                # Include ID for reference
                meal_list_str += f"- **{meal.name}** ({meal.date}, {meal.heure})\n"
                meal_list_str += f"  Ingredients: {ingredients_str}{recipe_link}\n"
                meal_list_str += f"  ID: {meal.id}\n"

            return [TextContent(type="text", text=meal_list_str)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error fetching meals: {str(e)}")]

    elif name == "update_meal":
        meal_id = arguments.get("meal_id")
        name_search = arguments.get("name_search")
        
        # Updates
        new_name = arguments.get("new_name")
        date = arguments.get("date")
        heure = arguments.get("heure")
        ingredients = arguments.get("ingredients")
        recipe = arguments.get("recipe")
        
        client = NotionClient()

        if meal_id:
            try:
                updates = {}
                if new_name: updates["name"] = new_name
                if date: updates["date"] = date
                if heure: updates["heure"] = heure
                if ingredients is not None: updates["ingredients"] = ingredients
                if recipe: updates["recipe"] = recipe
                
                updated_meal = await asyncio.to_thread(client.update_meal, meal_id=meal_id, updates=updates)
                
                if updated_meal:
                    return [TextContent(type="text", text=f"Successfully updated meal:\n- **{updated_meal.name}** ({updated_meal.date}, {updated_meal.heure})\n  ID: {updated_meal.id}")]
                else:
                    return [TextContent(type="text", text=f"Failed to update meal with ID {meal_id}.")]
            except Exception as e:
                return [TextContent(type="text", text=f"Error updating meal: {str(e)}")]

        elif name_search:
            try:
                meals = await asyncio.to_thread(client.get_meals, search_query=name_search)
                
                if not meals:
                    return [TextContent(type="text", text=f"No meal found with name '{name_search}'.")]
                
                if len(meals) == 1:
                    meal = meals[0]
                    return [TextContent(type="text", text=f"Found 1 meal matching '{name_search}':\n\n- **{meal.name}** ({meal.date}, {meal.heure})\n  ID: {meal.id}\n\nTo update this meal, please call `update_meal` again with `meal_id='{meal.id}'` and the desired changes.")]
                
                # Multiple matches
                meal_list_str = f"Multiple meals found matching '{name_search}'. Please call `update_meal` with the specific `meal_id` from the list below:\n\n"
                for i, meal in enumerate(meals, 1):
                    meal_list_str += f"{i}. **{meal.name}** ({meal.date}, {meal.heure}) - ID: {meal.id}\n"
                
                return [TextContent(type="text", text=meal_list_str)]

            except Exception as e:
                return [TextContent(type="text", text=f"Error searching for meal: {str(e)}")]
        
        else:
             return [TextContent(type="text", text="Please provide either `meal_id` (to update) or `name_search` (to find the meal first).")]

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
