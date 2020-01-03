import datetime

from timetable.models import Hint


def get_all_hints_by_date(date):
    hints = filter_date(date)
    return hints


def get_all_hints_by_class_and_time_period(_class, from_date, to_date):
    hints_tmp = get_all_hints_by_time_period(from_date, to_date)
    hints_match = []
    for hint in hints_tmp:
        if _class.id in [x.class_id for x in hint.classes.all()]:
            hints_match.append(hint)
    return hints_match


def get_all_hints_for_teachers_by_time_period(from_date, to_date):
    hints_tmp = get_all_hints_by_time_period(from_date, to_date)
    hints_match = []
    for hint in hints_tmp:
        if hint.teachers:
            hints_match.append(hint)
    return hints_match


def get_all_hints_not_for_teachers_by_time_period(from_date, to_date):
    hints_tmp = get_all_hints_by_time_period(from_date, to_date)
    hints_match = []
    for hint in hints_tmp:
        if not hint.teachers:
            hints_match.append(hint)
    return hints_match


def get_all_hints_by_time_period(from_date, to_date):
    print(from_date, to_date)
    delta = to_date - from_date
    print(delta.days + 1)
    week_days = [from_date + datetime.timedelta(days=i) for i in range(delta.days + 1)]

    hints = []
    for week_day in week_days:
        hints_tmp = get_all_hints_by_date(week_day)
        for hint in hints_tmp:
            if hint not in hints:
                hints.append(hint)
    print(hints)
    return hints


def filter_date(date):
    hints = Hint.objects.filter(from_date__lte=date, to_date__gte=date).order_by("from_date", "classes")
    return hints
