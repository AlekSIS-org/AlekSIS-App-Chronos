from datetime import date

from django.utils.formats import date_format


def format_m2m(f, attr: str = "short_name") -> str:
    """Join a attribute of all elements of a ManyToManyField."""
    return ", ".join([getattr(x, attr) for x in f.all()])


def format_date_period(day: date, period: "TimePeriod") -> str:
    """Format date and time period."""
    return f"{date_format(day)}, {period.period}."
