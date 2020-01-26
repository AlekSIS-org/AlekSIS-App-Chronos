from datetime import datetime, time, date


def date_unix(value: date) -> int:
    """ Converts a date object to an UNIX timestamp """

    value = datetime.combine(value, time(hour=0, minute=0))
    return int(value.timestamp()) * 1000
