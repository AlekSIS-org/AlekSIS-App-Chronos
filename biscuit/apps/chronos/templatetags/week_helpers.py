from datetime import date

from django import template

from ..util import week_days, week_weekday_to_date


register = template.Library()


@register.filter
def week_start(week: int) -> date:
    return week_days(week)[0]


@register.filter
def week_end(week: int) -> date:
    return week_days(week)[-1]


@register.simple_tag
def weekday_to_date(week: int, weekday: int) -> date:
    return week_weekday_to_date(week, weekday)


@register.simple_tag
def today() -> date:
    return date.today()
