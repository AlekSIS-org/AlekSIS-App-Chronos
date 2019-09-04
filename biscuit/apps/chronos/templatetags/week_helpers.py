from datetime import date
from typing import Optional

from django import template
from django.db.query import QuerySet

from ..util import current_week, week_days, week_weekday_to_date


register = template.Library()


@register.filter
def week_start(week: int) -> date:
    return week_days(week)[0]


@register.filter
def week_end(week: int) -> date:
    return week_days(week)[-1]


@register.filter
def only_week(qs: QuerySet, week: Optional[int]) -> QuerySet:
   wanted_week = week or current_week()
   return qs.filter(week=wanted_week)


@register.simple_tag
def weekday_to_date(week: int, weekday: int) -> date:
    return week_weekday_to_date(week, weekday)


@register.simple_tag
def today() -> date:
    return date.today()
