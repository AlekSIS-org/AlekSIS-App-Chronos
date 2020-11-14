from datetime import date
from typing import List, Tuple

from django.utils import timezone

from calendarweek import CalendarWeek


def week_weekday_from_date(when: date) -> Tuple[CalendarWeek, int]:
    """Return a tuple of week and weekday from a given date."""
    return (CalendarWeek.from_date(when), when.weekday())


def week_weekday_to_date(week: CalendarWeek, weekday: int) -> date:
    """Return a date object for one day in a calendar week."""
    return week[weekday]


def week_period_to_date(week: CalendarWeek, period) -> date:
    """Return the date of a lesson period in a given week."""
    return period.get_date(week)


def get_weeks_for_year(year: int) -> List[CalendarWeek]:
    """Generate all weeks for one year."""
    weeks = []

    # Go for all weeks in year and create week list
    current_week = CalendarWeek(year=year, week=1)

    while current_week.year == year:
        weeks.append(current_week)
        current_week += 1

    return weeks


def get_current_year() -> int:
    """Get current year."""
    return timezone.now().year
