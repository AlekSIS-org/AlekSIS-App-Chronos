from datetime import timedelta, date, time
from typing import Optional

from calendarweek import CalendarWeek
from django.utils import timezone

from aleksis.apps.chronos.util.min_max import weekday_min_, weekday_max, time_max


def get_next_relevant_day(day: Optional[date] = None, time: Optional[time] = None, prev: bool = False) -> date:
    """ Returns next (previous) day with lessons depending on date and time """

    if day is None:
        day = timezone.now().date()

    if time is not None and not prev:
        if time > time_max:
            day += timedelta(days=1)

    cw = CalendarWeek.from_date(day)

    if day.weekday() > weekday_max:
        if prev:
            day = cw[weekday_max]
        else:
            cw += 1
            day = cw[weekday_min_]
    elif day.weekday() < weekday_min_:
        if prev:
            cw -= 1
            day = cw[weekday_max]
        else:
            day = cw[weekday_min_]

    return day

