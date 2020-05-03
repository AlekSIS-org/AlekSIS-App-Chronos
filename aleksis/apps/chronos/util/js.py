from datetime import date, datetime, time


def date_unix(value: date) -> int:
    """Convert a date object to an UNIX timestamp."""
    value = datetime.combine(value, time(hour=0, minute=0))
    return int(value.timestamp()) * 1000
