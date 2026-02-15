from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class Meal(BaseModel):
    id: Optional[str] = Field(None, description="The Notion ID of the meal page")
    name: str = Field(..., description="The name of the meal")
    date: str = Field(..., description="The date the meal was cooked or planned")
    tags: List[str] = Field(default_factory=list, description="List of ingredients or tags associated with the meal")
    heure: str = Field(..., description="Whether the meal is for 'midi' (noon) or 'soir' (evening)")
    recipe: Optional[str] = Field(None, description="Link to the recipe")

    model_config = ConfigDict(populate_by_name=True)
