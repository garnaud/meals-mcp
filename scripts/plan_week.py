import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meals_mcp.agents.core import PlannerAgent, DieticalCoachAgent, CookerAgent

def get_date_input(prompt: str, default: str) -> str:
    user_input = input(f"{prompt} (YYYY-MM-DD, default: {default}): ").strip()
    return user_input if user_input else default

def run_orchestrator():
    # 1. Interactive Date Setup
    today = datetime.now()
    # Default: Next Monday
    days_ahead = 0 - today.weekday() if today.weekday() < 0 else 7 - today.weekday()
    next_monday = today + timedelta(days=days_ahead)
    next_sunday = next_monday + timedelta(days=6)
    
    default_start = next_monday.strftime("%Y-%m-%d")
    default_end = next_sunday.strftime("%Y-%m-%d")

    print("\n📅 --- Meal Plan Setup ---")
    start_date = get_date_input("Start Date", default_start)
    end_date = get_date_input("End Date", default_end)

    print(f"\n--- 🍱 Starting Meal Planning for {start_date} to {end_date} ---\n")

    planner = PlannerAgent()
    coach = DieticalCoachAgent()
    cooker = CookerAgent()

    max_agent_retries = 3
    user_satisfied = False
    feedback = None
    
    # Outer loop: User Feedback
    while not user_satisfied:
        
        # Inner loop: Agent Refinement (Planner <-> Coach)
        current_plan = None
        shopping_list = None
        
        for attempt in range(1, max_agent_retries + 2):
            print(f"--- 🔄 Generating Plan (Internal Iteration {attempt}) ---")
            
            print("🤖 Planner is thinking...")
            generated_plans, generated_shopping_list = planner.create_plan(start_date, end_date, feedback)
            
            if not generated_plans:
                print("❌ Planner failed to generate a valid plan. Retrying...")
                continue
            
            # Coach Evaluation
            print("🥗 Coach is evaluating...")
            evaluation = coach.evaluate_plan(generated_plans)
            status = evaluation.get("status")
            critique = evaluation.get("critique", "No feedback.")
            print(f"   Coach Status: {status}")
            print(f"   Critique: {critique}\n")

            if status == "APPROVED":
                current_plan = generated_plans
                shopping_list = generated_shopping_list
                break
            
            if attempt < max_agent_retries:
                # Automatic feedback loop
                feedback = critique 
            else:
                print("⚠️ Agent max retries reached. Presenting best effort.")
                current_plan = generated_plans
                shopping_list = generated_shopping_list
                break
        
        # Present to User
        if not current_plan:
            print("❌ Failed to generate a plan after all attempts.")
            return

        print("\n--- 📋 Proposed Meal Plan ---")
        for day in current_plan:
            midi_str = f"Midi: {day.midi} | " if day.midi else ""
            print(f"📅 {day.date}: {midi_str}Soir: {day.soir}")
        
        # User Confirmation
        print("\n------------------------------------------------")
        user_choice = input("Do you approve this plan? (yes/no/change specific meal): ").strip().lower()

        if user_choice in ["yes", "y", "ok"]:
            user_satisfied = True
            print("🎉 Plan Confirmed!")
        else:
            print("\n📝 What would you like to change?")
            feedback = input("Your feedback for the Planner: ").strip()
            print("🔄 Regenerating plan based on your feedback...\n")


    # Final Output: Shopping List & Recipes
    if shopping_list:
        print("\n--- 🛒 Shopping List (Approx for 5) ---")
        for category, items in shopping_list.items():
            print(f"\n**{category}**")
            for item in items:
                print(f"- {item['item']} ({item['quantity']})")

    print("\n--- 👨‍🍳 Chef's Recipe Cards ---")
    tips = cooker.get_tips(current_plan)
    print(tips)

if __name__ == "__main__":
    run_orchestrator()
