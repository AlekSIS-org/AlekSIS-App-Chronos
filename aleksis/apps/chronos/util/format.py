from django.utils.formats import date_format


def format_m2m(f, attr: str = "short_name"):
    return ", ".join([getattr(x, attr) for x in f.all()])


def format_date_period(date, period):
    return "{}, {}.".format(date_format(date), period.period)
