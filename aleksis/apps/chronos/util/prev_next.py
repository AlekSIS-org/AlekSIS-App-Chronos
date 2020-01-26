from datetime import timedelta, date, time
from typing import Optional, Tuple

from calendarweek import CalendarWeek
from django.urls import reverse
from django.utils import timezone

from ..models import TimePeriod


def get_next_relevant_day(day: Optional[date] = None, time: Optional[time] = None, prev: bool = False) -> date:
    """ Returns next (previous) day with lessons depending on date and time """

    if day is None:
        day = timezone.now().date()

    if time is not None and not prev:
        if time > TimePeriod.time_max:
            day += timedelta(days=1)

    cw = CalendarWeek.from_date(day)

    if day.weekday() > TimePeriod.weekday_max:
        if prev:
            day = cw[TimePeriod.weekday_max]
        else:
            cw += 1
            day = cw[TimePeriod.weekday_min]
    elif day.weekday() < TimePeriod.weekday_min:
        if prev:
            cw -= 1
            day = cw[TimePeriod.weekday_max]
        else:
            day = cw[TimePeriod.weekday_min]

    return day


def get_prev_next_by_day(day: date, url: str) -> Tuple[str, str]:
    """ Build URLs for previous/next day """

    day_prev = get_next_relevant_day(day - timedelta(days=1), prev=True)
    day_next = get_next_relevant_day(day + timedelta(days=1))

    url_prev = reverse(url, args=[day_prev.year, day_prev.month, day_prev.day])
    url_next = reverse(url, args=[day_next.year, day_next.month, day_next.day])

    return url_prev, url_next
