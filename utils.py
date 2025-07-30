"""
Utility functions for the habit‑motivation chatbot.

This module contains helper routines that aren't directly related to
business logic, such as retrieving motivational quotes and formatting
dates. Keeping these helpers separate makes the core code easier to
read and maintain.
"""

import random
from datetime import date
from typing import List

# A small selection of uplifting quotes. These can be expanded or
# replaced with calls to an external API if desired.
QUOTES: List[str] = [
    "Every journey begins with a single step.",
    "Success is the sum of small efforts, repeated day in and day out.",
    "Don't watch the clock; do what it does. Keep going.",
    "The secret of getting ahead is getting started.",
    "Keep pushing forward – your hard work will pay off.",
    "Discipline is choosing between what you want now and what you want most.",
    "Little by little, a little becomes a lot.",
]


def get_random_quote() -> str:
    """Return a random motivational quote from the list."""
    return random.choice(QUOTES)


def format_date(d: date) -> str:
    """Format a date object as a human friendly string (e.g. 'Jul 29, 2025')."""
    return d.strftime("%b %d, %Y")


def get_milestone_message(streak: int) -> str:
    """Return a celebration message for specific streak milestones.

    Args:
        streak: The current consecutive days streak.

    Returns:
        A celebratory string if the streak hits a milestone; otherwise
        an empty string.
    """
    if streak in (3, 7, 10):
        return f"🎉 You've hit a {streak}-day streak! Amazing discipline!"
    return ""