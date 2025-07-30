"""
Scheduling utilities for the habit‑motivation chatbot.

This module wraps the ``schedule`` library to trigger reminder
callbacks at predefined intervals. In the context of a long running
application (e.g. a bot integrated into a messaging platform), the
``run_scheduler_loop`` function could be run in a background thread
to send reminders without blocking the main event loop. For a simple
command‑line interface the scheduler may not be used at all or can
be called manually to simulate reminders.
"""

import logging
import time
from typing import Callable

import schedule


def schedule_daily_reminder(callback: Callable[[], None], time_of_day: str = "09:00") -> None:
    """Schedule a callback function to run every day at the given time.

    Args:
        callback: A function with no arguments that performs the reminder.
        time_of_day: A string in HH:MM (24h) format indicating when to
            run the reminder each day. Defaults to 09:00.
    """
    logging.debug("Scheduling daily reminder at %s", time_of_day)
    schedule.every().day.at(time_of_day).do(callback)


def run_scheduler_loop(interval: int = 60) -> None:
    """Run a loop that executes pending scheduled jobs.

    This function blocks the calling thread. It polls the scheduler
    every ``interval`` seconds to execute due jobs. In a production
    bot this could be started in a separate daemon thread.

    Args:
        interval: Number of seconds between calls to
            ``schedule.run_pending()``.
    """
    logging.info("Scheduler loop started; polling every %s seconds", interval)
    try:
        while True:
            schedule.run_pending()
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("Scheduler loop stopped by user.")