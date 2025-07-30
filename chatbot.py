"""
Command‑line chatbot for forming and maintaining healthy habits.

This script orchestrates the main flow of the habit‑motivation
application. Users are greeted, invited to select or define habits
they wish to cultivate, and then prompted to log daily progress. The
bot celebrates milestones and provides tailored encouragement using
OpenAI's language models when available.

Usage:
    python chatbot.py

Before running, set the ``OPENAI_API_KEY`` environment variable with
your OpenAI API key. The program gracefully falls back to built‑in
motivational quotes if the key is missing or the API fails.
"""

import logging
import os
import sys
from dotenv import load_dotenv
load_dotenv()
from datetime import date
from typing import Optional

from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

import database
from utils import get_random_quote, get_milestone_message, format_date


# Configure basic logging. In a larger application you might expose a
# command line flag or environment variable to control the logging level.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def get_motivational_message(user_name: str, habit_name: str, streak: int) -> str:
    """Generate a motivational message using OpenAI or fallback to a quote.

    The message acknowledges the user's current streak and encourages
    continued effort. If the OpenAI API key is unavailable or an error
    occurs during the call, a random quote is returned instead.

    Args:
        user_name: The name of the person being encouraged.
        habit_name: The habit the user is tracking.
        streak: The current number of consecutive days completed.

    Returns:
        A short, positive motivational message.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.warning("OPENAI_API_KEY not set; using a canned quote for motivation.")
        return get_random_quote()

    try:
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
        system_prompt = (
            "You are a friendly and supportive assistant. Your job is to encourage "
            "recent graduates who are forming healthy habits."
        )
        human_prompt = (
            f"User {user_name} is working on the habit of '{habit_name}'. "
            f"They currently have a streak of {streak} days. "
            "Provide a concise, upbeat motivational message to keep them going."
        )
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
        response = llm(messages)
        # Extract and clean the assistant's reply
        content = response.content.strip()
        logging.debug("Generated motivational message via OpenAI: %s", content)
        return content
    except Exception as exc:  # broad catch to fall back gracefully
        logging.exception("Failed to generate message via OpenAI; using a canned quote. Exception: %s", exc)
        return get_random_quote()


def celebrate_milestone(streak: int) -> str:
    """Return a celebratory message for certain streak milestones."""
    return get_milestone_message(streak)


def select_habit(user_id: int) -> int:
    """Present existing habits to the user or allow adding a new one.

    The function lists the user's current habits. The user can select
    one by entering its number or choose to create a new habit.

    Returns:
        The ID of the selected or newly created habit.
    """
    while True:
        habits = database.get_habits(user_id)
        if habits:
            print("\nYour current habits:")
            for idx, habit in enumerate(habits, start=1):
                print(f"  {idx}. {habit['name']} (started on {habit['start_date']})")
            print(f"  {len(habits) + 1}. Add a new habit")
            choice = input("Select a habit by number: ").strip()
            if choice.isdigit():
                selection = int(choice)
                if 1 <= selection <= len(habits):
                    selected = habits[selection - 1]
                    logging.info("User selected existing habit: %s", selected['name'])
                    return selected["id"]
                elif selection == len(habits) + 1:
                    # Add new habit
                    return _create_new_habit(user_id)
        else:
            print("\nYou don't have any habits yet. Let's create one!")
            return _create_new_habit(user_id)
        print("Invalid selection. Please try again.")


def _create_new_habit(user_id: int) -> int:
    """Prompt the user for a new habit name and add it to the database."""
    while True:
        habit_name = input("Enter the name of the habit you want to track: ").strip()
        if habit_name:
            habit_id = database.add_habit(user_id, habit_name)
            print(f"Added habit '{habit_name}'.")
            return habit_id
        print("Habit name cannot be empty. Please try again.")


def daily_checkin(habit_id: int, habit_name: str, user_name: str) -> None:
    """Prompt the user to log today's progress on a habit.

    The function asks the user whether they've completed the habit
    today. It records the result, calculates the new streak, and
    outputs motivational and milestone messages.
    """
    print(f"\nDid you complete '{habit_name}' today? (yes/no)")
    while True:
        answer = input("Enter yes or no: ").strip().lower()
        if answer in {"yes", "y", "no", "n"}:
            completed = answer.startswith("y")
            break
        print("Please type 'yes' or 'no'.")

    # Record the check‑in
    database.log_checkin(habit_id, completed)
    # Calculate streak only if completed; otherwise streak resets to zero
    streak = database.get_streak(habit_id) if completed else 0
    if completed:
        print(f"Great job! You're on a {streak}-day streak.")
        milestone_msg = celebrate_milestone(streak)
        if milestone_msg:
            print(milestone_msg)
    else:
        print("No worries, tomorrow is a new opportunity to get back on track!")
        streak = 0
    # Provide motivational message
    message = get_motivational_message(user_name, habit_name, streak)
    print(f"\nMotivation: {message}\n")


def start_bot() -> None:
    """Entry point for the command‑line chatbot.

    This function greets the user, ensures the database is ready,
    handles user registration, and enters a loop where the user can
    perform daily check‑ins or manage their habits.
    """
    # Initialize DB
    database.load_user_data()
    print("Welcome to the Habit Formation & Motivation Bot!")
    # Ask for user name
    name = input("What's your name? ").strip()
    while not name:
        name = input("Please enter a non‑empty name: ").strip()
    user_id = database.get_user_id(name)
    if user_id is None:
        user_id = database.add_user(name)
        print(f"Nice to meet you, {name}! Let's get started.")
    else:
        print(f"Welcome back, {name}!")
    # Main loop
    while True:
        print("\nWhat would you like to do?")
        print("  1. Select a habit to work on")
        print("  2. Log today's progress")
        print("  3. Show current streaks")
        print("  4. Exit")
        choice = input("Enter your choice: ").strip()
        if choice == "1":
            # Choose or add a habit; store selected habit_id in user session
            habit_id = select_habit(user_id)
            # Persist selection for session
            _current_habit[0] = habit_id
        elif choice == "2":
            habit_id = _current_habit[0]
            if habit_id is None:
                print("You haven't selected a habit yet. Please choose one first.")
                continue
            # Get habit name for display
            habits = database.get_habits(user_id)
            habit_name = next((h["name"] for h in habits if h["id"] == habit_id), None)
            if habit_name is None:
                print("Selected habit no longer exists. Please choose again.")
                _current_habit[0] = None
                continue
            daily_checkin(habit_id, habit_name, name)
        elif choice == "3":
            # Display current streaks for all habits
            habits = database.get_habits(user_id)
            if not habits:
                print("You haven't added any habits yet.")
                continue
            print("\nYour current streaks:")
            for habit in habits:
                streak = database.get_streak(habit["id"])
                print(f"  {habit['name']}: {streak} day(s)")
        elif choice == "4":
            print("Goodbye! Keep up the good work!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")


# A simple container to hold the selected habit across function calls.
# Using a list allows us to mutate the reference within nested scopes
# without using global variables extensively.
_current_habit = [None]  # type: ignore


if __name__ == "__main__":
    try:
        start_bot()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")