from datetime import datetime, time

from django import template


register = template.Library()


@register.filter
def date_unix(value: datetime):
    value = datetime.combine(value, time(hour=0, minute=0))
    return int(value.timestamp()) * 1000
