"""
Streak calculation engine for the 75-Day Vibe Habit Tracker.

Dynamically derives current streak and best streak from completion history
without storing mutable counters in the database.
"""

from datetime import date, timedelta
from typing import Iterable, Union, Set


def parse_date(d: Union[str, date]) -> date:
    """Helper to convert string ISO date (YYYY-MM-DD) or date object to date."""
    if isinstance(d, str):
        return date.fromisoformat(d)
    return d


def is_scheduled_day(d: date, frequency: str) -> bool:
    """
    Day validation rule:
    - 'weekdays': Monday(0)..Friday(4) are scheduled; Saturday(5) and Sunday(6) are skipped.
    - 'daily': Every calendar day is scheduled.
    """
    if frequency == 'weekdays':
        return d.weekday() < 5  # 0 = Monday, ..., 4 = Friday
    return True


def get_previous_scheduled_day(d: date, frequency: str) -> date:
    """Returns the previous valid scheduled day prior to d."""
    prev = d - timedelta(days=1)
    while not is_scheduled_day(prev, frequency):
        prev -= timedelta(days=1)
    return prev


def get_next_scheduled_day(d: date, frequency: str) -> date:
    """Returns the next valid scheduled day after d."""
    nxt = d + timedelta(days=1)
    while not is_scheduled_day(nxt, frequency):
        nxt += timedelta(days=1)
    return nxt


def calculate_current_streak(frequency: str, completion_dates: Iterable[Union[str, date]], today: date = None) -> int:
    """
    Calculates the current streak count walking backward from today.

    Algorithm:
    1. Start a pointer at today's date.
    2. If today is a non-scheduled day for this habit (weekend on a weekdays-only habit),
       shift pointer back to the most recent valid scheduled day.
    3. If the pointer's date has no completion logged, do not treat this as a broken streak —
       just move the pointer back to the previous scheduled day and check again.
    4. Continue walking backward while each scheduled day has a matching completion;
       increment the streak count each time.
    5. Stop at the first scheduled day with no completion — that's the streak boundary.
    """
    if today is None:
        today = date.today()

    completed_set: Set[date] = {parse_date(d) for d in completion_dates}

    curr = today
    # Step 2: Shift to most recent valid scheduled day if currently on a non-scheduled day
    while not is_scheduled_day(curr, frequency):
        curr -= timedelta(days=1)

    streak = 0

    # Step 3: Check if anchor scheduled day is completed
    if curr in completed_set:
        streak += 1
        curr = get_previous_scheduled_day(curr, frequency)
    else:
        # Move back to previous scheduled day without breaking
        curr = get_previous_scheduled_day(curr, frequency)

    # Step 4: Continue walking backward as long as scheduled days are completed
    while curr in completed_set:
        streak += 1
        curr = get_previous_scheduled_day(curr, frequency)

    return streak


def calculate_best_streak(frequency: str, completion_dates: Iterable[Union[str, date]]) -> int:
    """
    Calculates the longest contiguous run of scheduled days completed across all time.

    Algorithm:
    1. Pull all completion dates for the habit, sorted ascending.
    2. Walk through them as contiguous scheduled-day blocks — a weekend gap does not
       break the chain for weekday-only habits.
    3. Track the longest such run across all time.
    """
    if not completion_dates:
        return 0

    # Filter & sort unique scheduled completion dates
    sorted_dates = sorted(list({
        parse_date(d) for d in completion_dates if is_scheduled_day(parse_date(d), frequency)
    }))

    if not sorted_dates:
        return 0

    best_streak = 0
    current_run = 0
    last_date = None

    for d in sorted_dates:
        if last_date is None:
            current_run = 1
        else:
            expected_next = get_next_scheduled_day(last_date, frequency)
            if d == expected_next:
                current_run += 1
            else:
                current_run = 1

        last_date = d
        if current_run > best_streak:
            best_streak = current_run

    return best_streak
