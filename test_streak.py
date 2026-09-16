"""
Unit tests for streak.py engine.
"""

from datetime import date
import pytest
from streak import (
    calculate_current_streak,
    calculate_best_streak,
    is_scheduled_day,
    get_previous_scheduled_day,
    get_next_scheduled_day,
)


def test_no_completions():
    """Test habits with no completion history."""
    today = date(2026, 9, 16)  # Wednesday
    assert calculate_current_streak("daily", [], today=today) == 0
    assert calculate_best_streak("daily", []) == 0
    assert calculate_current_streak("weekdays", [], today=today) == 0
    assert calculate_best_streak("weekdays", []) == 0


def test_daily_habit_with_gaps():
    """Test daily habit streak math with gaps."""
    today = date(2026, 9, 16)  # Wednesday

    # Completed Mon (14), Tue (15). Wed (16) not completed yet today.
    # Current streak should be 2 (Tue, Mon).
    completions = ["2026-09-14", "2026-09-15"]
    assert calculate_current_streak("daily", completions, today=today) == 2
    assert calculate_best_streak("daily", completions) == 2

    # If Wed is also completed today: streak becomes 3.
    completions_with_today = ["2026-09-14", "2026-09-15", "2026-09-16"]
    assert calculate_current_streak("daily", completions_with_today, today=today) == 3
    assert calculate_best_streak("daily", completions_with_today) == 3

    # Completed Sun (13), Mon (14), Tue (15) -> gap on Sat (12)
    # Total run: Sun, Mon, Tue = 3. Best streak = 3.
    completions_gap = ["2026-09-10", "2026-09-13", "2026-09-14", "2026-09-15"]
    assert calculate_current_streak("daily", completions_gap, today=today) == 3
    assert calculate_best_streak("daily", completions_gap) == 3


def test_weekday_habit_spanning_weekend():
    """Test weekday habit spanning across a weekend (Fri -> Mon)."""
    # 2026-09-11 is Friday, 2026-09-12 is Sat, 2026-09-13 is Sun, 2026-09-14 is Monday
    # Test 1: Today is Monday 2026-09-14, Fri 09-11 was completed. Mon not done yet.
    today_mon = date(2026, 9, 14)
    completions = ["2026-09-11"]  # Friday
    assert calculate_current_streak("weekdays", completions, today=today_mon) == 1
    assert calculate_best_streak("weekdays", completions) == 1

    # Test 2: Mon completed as well -> streak should be 2.
    completions_mon = ["2026-09-11", "2026-09-14"]
    assert calculate_current_streak("weekdays", completions_mon, today=today_mon) == 2
    assert calculate_best_streak("weekdays", completions_mon) == 2

    # Test 3: Span multiple weeks over weekends: Thu(09-10), Fri(09-11), Mon(09-14), Tue(09-15), Wed(09-16)
    full_span = ["2026-09-10", "2026-09-11", "2026-09-14", "2026-09-15", "2026-09-16"]
    today_wed = date(2026, 9, 16)
    assert calculate_current_streak("weekdays", full_span, today=today_wed) == 5
    assert calculate_best_streak("weekdays", full_span) == 5


def test_weekday_habit_on_weekend():
    """Test weekday habit evaluated on a Saturday or Sunday."""
    # 2026-09-13 is Sunday. Previous scheduled day is Friday 2026-09-11.
    today_sun = date(2026, 9, 13)
    completions = ["2026-09-10", "2026-09-11"]  # Thu, Fri
    assert calculate_current_streak("weekdays", completions, today=today_sun) == 2
    assert calculate_best_streak("weekdays", completions) == 2


def test_day_validation_and_helpers():
    """Test helper functions for day validation."""
    mon = date(2026, 9, 14)
    fri = date(2026, 9, 11)
    sat = date(2026, 9, 12)
    sun = date(2026, 9, 13)

    assert is_scheduled_day(mon, "weekdays") is True
    assert is_scheduled_day(sat, "weekdays") is False
    assert is_scheduled_day(sun, "weekdays") is False
    assert is_scheduled_day(sat, "daily") is True

    assert get_previous_scheduled_day(mon, "weekdays") == fri
    assert get_next_scheduled_day(fri, "weekdays") == mon
