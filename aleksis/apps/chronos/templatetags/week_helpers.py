from datetime import date, datetime
from typing import Optional, Union

from django import template
from django.db.models.query import QuerySet

from aleksis.apps.chronos.util.date import CalendarWeek, week_period_to_date, week_weekday_to_date

register = template.Library()


@register.filter
def week_start(week: CalendarWeek) -> date:
    return week[0]


@register.filter
def week_end(week: CalendarWeek) -> date:
    return week[-1]


@register.filter
def only_week(qs: QuerySet, week: Optional[CalendarWeek]) -> QuerySet:
    wanted_week = week or CalendarWeek()
    return qs.filter(week=wanted_week.week, year=wanted_week.year)


@register.simple_tag
def weekday_to_date(week: CalendarWeek, weekday: int) -> date:
    return week_weekday_to_date(week, weekday)


@register.simple_tag
def period_to_date(week: CalendarWeek, period) -> date:
    return week_period_to_date(week, period)


@register.simple_tag
def period_to_time_start(week: CalendarWeek, period) -> date:
    return period.get_datetime_start(week)


@register.simple_tag
def period_to_time_end(week: Union[CalendarWeek, int], period) -> date:
    return period.get_datetime_end(week)


@register.simple_tag
def today() -> date:
    return date.today()


@register.simple_tag
def now_datetime() -> datetime:
    return datetime.now()
