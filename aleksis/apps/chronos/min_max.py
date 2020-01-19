from datetime import date, time, timedelta
from typing import Optional

from calendarweek import CalendarWeek
from django.db.models import Min, Max
from django.utils import timezone

from .models import TimePeriod

# Determine overall first and last day and period
min_max = TimePeriod.objects.aggregate(
    Min("period"), Max("period"), Min("weekday"), Max("weekday"), Min("time_start"), Max("time_end")
)

period_min = min_max.get("period__min", 1)
period_max = min_max.get("period__max", 7)

time_min = min_max.get("time_start__min", None)
time_max = min_max.get("time_end__max", None)

weekday_min_ = min_max.get("weekday__min", 0)
weekday_max = min_max.get("weekday__max", 6)


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
