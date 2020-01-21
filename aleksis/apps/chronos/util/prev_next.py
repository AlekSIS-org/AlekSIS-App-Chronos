from datetime import timedelta, date, time
from typing import Optional

from calendarweek import CalendarWeek
from django.utils import timezone

from aleksis.apps.chronos.util.min_max import weekday_min_, weekday_max, time_max


def get_next_relevant_day(day: Optional[date] = None, time: Optional[time] = None) -> date:
    """ Returns next day with lessons depending on date and time """

    if day is None:
        day = timezone.now().date()

    if time is not None:
        if time > time_max:
            day += timedelta(days=1)

    cw = CalendarWeek.from_date(day)

    if day.weekday() > weekday_max:
        cw += 1
        day = cw[weekday_min_]
    elif day.weekday() < weekday_min_:
        day = cw[weekday_min_]

    return day


def get_prev_relevant_day(day: Optional[date] = None) -> date:
    """ Returns previous day with lessons depending on date """

    if day is None:
        day = timezone.now().date()

    cw = CalendarWeek.from_date(day)

    if day.weekday() > weekday_max:
        day = cw[weekday_max]
    elif day.weekday() < weekday_min_:
        cw -= 1
        day = cw[weekday_max]

    return day
