from datetime import date

from django import template

from ..util import week_days


register = template.Library()


@register.filter
def week_start(week: int) -> date:
    return week_days(week)[0]


@register.filter
def week_end(week: int) -> date:
    return week_days(week)[-1]
