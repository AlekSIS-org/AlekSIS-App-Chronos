from datetime import date
from typing import Optional

from django import template
from django.db.models.query import QuerySet

from ..util import CalendarWeek, week_weekday_to_date


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
   return qs.filter(week=wanted_week.week)


@register.simple_tag
def weekday_to_date(week: CalendarWeek, weekday: int) -> date:
    return week_weekday_to_date(week, weekday)


@register.simple_tag
def today() -> date:
    return date.today()
