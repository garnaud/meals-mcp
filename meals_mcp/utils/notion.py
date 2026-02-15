import os
import notion_client
from typing import List, Optional
from meals_mcp.models import Meal

class NotionClient:
    def __init__(self, auth_token: str = None):
        if auth_token is None:
            auth_token = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
        if not auth_token:
            raise ValueError("Notion API token (NOTION_TOKEN or NOTION_API_KEY) not found. Please set the environment variable or pass it to the constructor.")
        self._client = notion_client.Client(auth=auth_token)

    def get_users(self):
        """
        Retrieves a list of users in the Notion workspace.
        """
        try:
            users = self._client.users.list()
            return users.get("results", [])
        except Exception as e:
            print(f"Error fetching users from Notion API: {e}")
            return []

    def _find_data_source_id(self) -> str:
        """
        Finds the ID of the 'Repas' database or data source.
        """
        # 1. Search for a database named 'Repas'
        search_results = self._client.search(query="Repas").get("results", [])
        
        data_source_id = None
        for result in search_results:
            obj_type = result.get("object")
            if obj_type == "database":
                title_list = result.get("title", [])
                if title_list and title_list[0].get("plain_text") == "Repas":
                    data_source_id = result.get("id")
                    break
            elif obj_type == "data_source":
                data_source_id = result.get("id")
                break
        
        # Fallback: if no direct match found, try property-based discovery
        if not data_source_id:
            for result in search_results:
                props = result.get("properties", {})
                if "Date" in props:
                    parent = result.get("parent", {})
                    if parent.get("type") == "data_source_id":
                        data_source_id = parent.get("data_source_id")
                        break
                    elif "database_id" in parent:
                        data_source_id = parent.get("database_id")
                        break
        
        # Final Fallback: try first result if available
        if not data_source_id and search_results:
            first_result = search_results[0]
            parent = first_result.get("parent", {})
            if parent.get("type") == "data_source_id":
                data_source_id = parent.get("data_source_id")
            elif "database_id" in parent:
                data_source_id = parent.get("database_id")
        
        if not data_source_id:
            raise ValueError("Could not find a database named 'Repas' or a valid Data Source with 'Date' property.")
            
        return data_source_id

    def _map_page_to_meal(self, page: dict) -> Optional[Meal]:
        """
        Maps a Notion page result to a Meal object.
        """
        properties = page.get("properties", {})
        try:
            # Name (Title) - Key is likely empty string ""
            name_prop = properties.get("", {}).get("title", [])
            if not name_prop:
                 # Fallback to "Name" if "" fails
                 name_prop = properties.get("Name", {}).get("title", [])
            
            name = name_prop[0].get("plain_text") if name_prop else "Unnamed Meal"

            # Date
            date_prop = properties.get("Date", {}).get("date", {})
            date = date_prop.get("start") if date_prop else None
            
            if not date:
                 return None

            # Ingredients (Multi-select)
            ingredients_prop = properties.get("Ingredients", {}).get("multi_select", [])
            ingredients = [tag.get("name") for tag in ingredients_prop]

            # Heure (Select)
            heure_prop = properties.get("Heure", {}).get("select", {})
            heure = heure_prop.get("name") if heure_prop else "Unknown"

            # Recipe (URL)
            # Check 'Lien' first (URL type)
            recipe = properties.get("Lien", {}).get("url")
            if not recipe:
                # Check 'Recipe' (Files type)
                files_prop = properties.get("Recipe", {}).get("files", [])
                if files_prop:
                    first_file = files_prop[0]
                    if "external" in first_file:
                        recipe = first_file.get("external", {}).get("url")
                    elif "file" in first_file:
                        recipe = first_file.get("file", {}).get("url")

            return Meal(
                id=page.get("id"),
                name=name,
                date=date,
                ingredients=ingredients,
                heure=heure,
                recipe=recipe
            )
        except Exception as e:
            print(f"Skipping malformed meal entry: {e}")
            return None

    def get_meals(self, limit: int = 30, start_date: str = None, end_date: str = None, search_query: str = None) -> List[Meal]:
        """
        Retrieves a list of meals from the 'Repas' database.
        Optionally filters by a date range or search query.
        """
        try:
            data_source_id = self._find_data_source_id()

            # Build Query
            query_params = {
                "page_size": 100 if start_date or end_date or search_query else limit, # Fetch more if filtering
                "sorts": [
                    {
                        "property": "Date",
                        "direction": "descending"
                    }
                ]
            }

            # Handle querying based on endpoint availability
            if hasattr(self._client, "data_sources") and hasattr(self._client.data_sources, "query"):
                query_params["data_source_id"] = data_source_id
                response = self._client.data_sources.query(**query_params)
            elif hasattr(self._client.databases, "query"):
                query_params["database_id"] = data_source_id
                response = self._client.databases.query(**query_params)
            else:
                 raise AttributeError("Neither data_sources.query nor databases.query is available on the client.")

            results = response.get("results", [])

            meals = []
            for page in results:
                meal = self._map_page_to_meal(page)
                if not meal:
                    continue

                # Filter in Python
                if start_date and meal.date < start_date:
                    continue
                if end_date and meal.date > end_date:
                    continue
                if search_query and search_query.lower() not in meal.name.lower():
                    continue

                meals.append(meal)
            
            # Respect limit if we fetched more due to filtering
            if (start_date or end_date or search_query) and len(meals) > limit:
                 meals = meals[:limit]

            return meals

        except Exception as e:
            print(f"Error fetching meals from Notion API: {e}")
            raise

    def update_meal(self, meal_id: str, updates: dict) -> Optional[Meal]:
        """
        Updates a meal in the 'Repas' database.
        
        Args:
            meal_id: The ID of the meal page to update.
            updates: A dictionary of fields to update. Supported keys:
                     - name: str (Update the title)
                     - date: str (ISO 8601 date string)
                     - heure: str ("Midi" or "Soir")
                     - tags: List[str] (List of tags)
                     - recipe: str (URL for the recipe)
        
        Returns:
            The updated Meal object, or None if the update failed.
        """
        properties = {}
        
        # Name (Title)
        if "name" in updates and updates["name"]:
            # We need to find the title property name, defaulting to "Name"
            # Since we can't easily dynamically find it here without an extra call, 
            # we'll assume "Name" or try to be smart if possible.
            # However, for updates, providing the correct property name is crucial.
            # Let's assume "Name" as per previous observations.
            properties["Name"] = {
                "title": [
                    {
                        "text": {
                            "content": updates["name"]
                        }
                    }
                ]
            }

        # Date
        if "date" in updates and updates["date"]:
            properties["Date"] = {
                "date": {
                    "start": updates["date"]
                }
            }

        # Heure (Select)
        if "heure" in updates and updates["heure"]:
             properties["Heure"] = {
                "select": {
                    "name": updates["heure"]
                }
            }

        # Ingredients (Multi-select)
        if "ingredients" in updates and updates["ingredients"] is not None:
            properties["Ingredients"] = {
                "multi_select": [{"name": ingredient} for ingredient in updates["ingredients"]]
            }

        # Recipe (URL) - Maps to 'Lien'
        if "recipe" in updates: # Allow clearing if None passed explicitly? For now just update if present.
             if updates["recipe"]:
                properties["Lien"] = {
                    "url": updates["recipe"]
                }

        if not properties:
            return None

        try:
            response = self._client.pages.update(page_id=meal_id, properties=properties)
            return self._map_page_to_meal(response)
        except Exception as e:
            print(f"Error updating meal {meal_id}: {e}")
            raise
