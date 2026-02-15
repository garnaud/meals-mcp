import sys
import os

# Add the parent directory to sys.path so we can import meals_mcp
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meals_mcp.utils.notion import NotionClient
from meals_mcp.models import Meal

def add_meals():
    client = NotionClient()
    
    meals_to_add = [
        Meal(
            name="Wok de poulet et légumes",
            date="2026-02-14",
            heure="Soir",
            ingredients=["poulet", "légumes", "wok"],
            recipe=None
        ),
        Meal(
            name="Soupe de légumes & Tartines",
            date="2026-02-15",
            heure="Soir",
            ingredients=["légumes", "pain"],
            recipe=None
        ),
        Meal(
            name="Steak haché - Haricots verts",
            date="2026-02-16",
            heure="Soir",
            ingredients=["steak haché", "haricot vert"],
            recipe=None
        ),
        Meal(
            name="Pâtes au thon et à la tomate",
            date="2026-02-17",
            heure="Soir",
            ingredients=["pâtes", "thon", "tomate"],
            recipe=None
        ),
        Meal(
            name="Tarte aux poireaux et lardons",
            date="2026-02-18",
            heure="Soir",
            ingredients=["poireau", "lardon", "pâte brisée"],
            recipe=None
        ),
        Meal(
            name="Curry de chou-fleur et pois chiches",
            date="2026-02-19",
            heure="Soir",
            ingredients=["chou-fleur", "pois chiche", "curry"],
            recipe=None
        ),
        Meal(
            name="Fajitas / Tacos",
            date="2026-02-20",
            heure="Soir",
            ingredients=["poulet", "tortilla", "poivron", "oignon"],
            recipe=None
        ),
        Meal(
            name="Omelette aux pommes de terre",
            date="2026-02-21",
            heure="Midi",
            ingredients=["oeufs", "pomme de terre"],
            recipe=None
        ),
        Meal(
            name="Lasagnes à la bolognaise",
            date="2026-02-21",
            heure="Soir",
            ingredients=["pâtes", "viande hachée", "tomate", "béchamel"],
            recipe=None
        ),
    ]

    for meal in meals_to_add:
        try:
            client.add_meal(meal)
            print(f"Added: {meal.name} for {meal.date} ({meal.heure})")
        except Exception as e:
            print(f"Failed to add {meal.name}: {e}")

if __name__ == "__main__":
    add_meals()
