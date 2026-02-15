import json
import os
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.chats import Chat

from meals_mcp.agents.prompts import PLANNER_INSTRUCTION, DIETICAL_COACH_INSTRUCTION, COOKER_INSTRUCTION
from meals_mcp.utils.notion import NotionClient

class Plan(BaseModel):
    date: str
    midi: Optional[str] = None
    soir: str

class MealPlan(BaseModel):
    meals: List[Plan]

class Agent:
    def __init__(self, system_instruction: str, model_name: str = "gemini-2.0-flash"):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.chat = self.client.chats.create(
             model=self.model_name,
             config=types.GenerateContentConfig(
                 system_instruction=self.system_instruction,
                 temperature=0.7,
             )
        )

    def send_message(self, message: str) -> str:
        response = self.chat.send_message(message)
        return response.text

class PlannerAgent(Agent):
    def __init__(self):
        super().__init__(system_instruction=PLANNER_INSTRUCTION)
        self.notion_client = NotionClient()

    def get_recent_meals_context(self, limit: int = 90) -> str:
        try:
            meals = self.notion_client.get_meals(limit=limit)
            context = "Here are the meals from the last 3 months (90 days approx):\n"
            for meal in meals:
                context += f"- {meal.name} ({meal.date}, {meal.heure})\n"
            return context
        except Exception as e:
            return f"Error fetching recent meals: {e}"

    def create_plan(self, start_date: str, end_date: str, feedback: Optional[str] = None) -> tuple[List[Plan], Dict[str, Any]]:
        context = self.get_recent_meals_context()
        prompt = f"""
        Context: {context}

        Task: Create a meal plan for the week from {start_date} to {end_date}.
        
        Constraints Reminder:
        - Monday/Tuesday Evening: Simple/Quick.
        - Wednesday Noon: Quick/Easy.
        - Saturday Noon: Light.
        - Sunday Evening: Light.
        - Sat/Sun: One ambitious meal, not both.
        - Sunday: One batch cooking opportunity.

        Feedback from previous iteration (if any): {feedback or "None"}
        """
        
        response_text = self.send_message(prompt)
        # Parse JSON from response
        try:
            # Clean up markdown code blocks if present
            cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_response)
            
            schedule_data = data.get("schedule", {})
            shopping_list = data.get("shopping_list", {})

            plans = []
            for date, meals in schedule_data.items():
                plans.append(Plan(
                    date=date,
                    midi=meals.get("Midi"),
                    soir=meals.get("Soir") or meals.get("Dinner") # Fallback
                ))
            return plans, shopping_list
        except json.JSONDecodeError:
            print(f"Error parsing JSON from Planner: {response_text}")
            return [], {}

class DieticalCoachAgent(Agent):
    def __init__(self):
        super().__init__(system_instruction=DIETICAL_COACH_INSTRUCTION)

    def evaluate_plan(self, plans: List[Plan]) -> Dict[str, Any]:
        plan_str = json.dumps([p.model_dump() for p in plans], indent=2)
        prompt = f"""
        Evaluate this meal plan:
        {plan_str}
        """
        response_text = self.send_message(prompt)
        try:
            cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
             print(f"Error parsing JSON from Dietical Coach: {response_text}")
             return {"status": "REJECTED", "critique": "Failed to parse coach response."}


class CookerAgent(Agent):
    def __init__(self):
        super().__init__(system_instruction=COOKER_INSTRUCTION)

    def get_tips(self, plans: List[Plan]) -> str:
        plan_str = json.dumps([p.model_dump() for p in plans], indent=2)
        prompt = f"""
        Here is the final approved meal plan:
        {plan_str}

        Please provide your Recipe Cards in French!
        """
        return self.send_message(prompt)
