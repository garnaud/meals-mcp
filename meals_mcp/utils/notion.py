import os
import notion_client
from typing import List
from meals_mcp.models import Meal

class NotionClient:
    def __init__(self, auth_token: str = None):
        if auth_token is None:
            auth_token = os.environ.get("NOTION_TOKEN")
        if not auth_token:
            raise ValueError("Notion API token (NOTION_TOKEN) not found. Please set the environment variable or pass it to the constructor.")
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

    def get_meals(self, limit: int = 30, start_date: str = None, end_date: str = None) -> List[Meal]:
        """
        Retrieves a list of meals from the 'Repas' database.
        Optionally filters by a date range.
        """
        try:
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
                    # For data_source objects, name might be in properties or different
                    # but since query="Repas" matched, we use its ID
                    data_source_id = result.get("id")
                    break
            
            # Fallback: if no direct match found, try the previous property-based discovery
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
            
            if not data_source_id:
                raise ValueError("Could not find a database named 'Repas' or a valid Data Source with 'Date' property.")

            # 2. Build Query
            query_params = {
                "page_size": 100 if start_date or end_date else limit, # Fetch more if filtering
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
                properties = page.get("properties", {})
                
                # 3. Map properties to Meal object
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
                         continue # Skip meals without a date

                    # Filter in Python
                    if start_date and date < start_date:
                        continue
                    if end_date and date > end_date:
                        continue

                    # Tags (Multi-select)
                    tags_prop = properties.get("Tags", {}).get("multi_select", [])
                    tags = [tag.get("name") for tag in tags_prop]

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

                    meal = Meal(
                        name=name,
                        date=date,
                        tags=tags,
                        heure=heure,
                        recipe=recipe
                    )
                    meals.append(meal)
                except Exception as e:
                    print(f"Skipping malformed meal entry: {e}")
                    continue

            return meals

        except Exception as e:
            print(f"Error fetching meals from Notion API: {e}")
            raise
