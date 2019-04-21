from timetable.models import Hint


def get_all_hints_by_date(date):
    hints = filter_date(date)
    return hints


def get_all_hints_by_time_period(from_date, to_date):
    print(from_date, to_date)
    hints = Hint.objects.filter(from_date__gte=from_date, to_date__lte=to_date).order_by("from_date", "classes")
    print(hints)
    return hints


def filter_date(date):
    hints = Hint.objects.filter(from_date__lte=date, to_date__gte=date).order_by("from_date", "classes")
    return hints
