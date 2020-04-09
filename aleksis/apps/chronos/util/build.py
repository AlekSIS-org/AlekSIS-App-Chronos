from collections import OrderedDict
from datetime import date
from typing import Union, List

from calendarweek import CalendarWeek
from django.apps import apps

from aleksis.core.models import Person

LessonPeriod = apps.get_model("chronos", "LessonPeriod")
TimePeriod = apps.get_model("chronos", "TimePeriod")
Break = apps.get_model("chronos", "Break")
Supervision = apps.get_model("chronos", "Supervision")
LessonSubstitution = apps.get_model("chronos", "LessonSubstitution")


def build_timetable(
    type_: str, obj: Union[int, Person], date_ref: Union[CalendarWeek, date]
):
    needed_breaks = []

    if not isinstance(obj, int):
        pk = obj.pk
    else:
        pk = obj

    is_person = False
    if type_ == "person":
        is_person = True
        type_ = obj.timetable_type

    # Get matching lesson periods
    if is_person:
        lesson_periods = LessonPeriod.objects.daily_lessons_for_person(obj, date_ref)
    else:
        lesson_periods = LessonPeriod.objects.in_week(date_ref).filter_from_type(
            type_, obj
        )

    # Sort lesson periods in a dict
    lesson_periods_per_period = {}
    for lesson_period in lesson_periods:
        period = lesson_period.period.period
        weekday = lesson_period.period.weekday

        if period not in lesson_periods_per_period:
            lesson_periods_per_period[period] = [] if is_person else {}

        if not is_person and weekday not in lesson_periods_per_period[period]:
            lesson_periods_per_period[period][weekday] = []

        if is_person:
            lesson_periods_per_period[period].append(lesson_period)
        else:
            lesson_periods_per_period[period][weekday].append(lesson_period)

    if type_ == "teacher":
        # Get matching supervisions
        if is_person:
            week = CalendarWeek.from_date(date_ref)
        else:
            week = date_ref
        supervisions = Supervision.objects.filter(teacher=obj).annotate_week(week)

        if is_person:
            supervisions.filter_by_weekday(date_ref.weekday())

        supervisions_per_period_after = {}
        for supervision in supervisions:
            weekday = supervision.break_item.weekday
            period_after_break = supervision.break_item.before_period_number
            print(supervision, weekday, period_after_break)

            if period_after_break not in needed_breaks:
                needed_breaks.append(period_after_break)

            if (
                not is_person
                and period_after_break not in supervisions_per_period_after
            ):
                supervisions_per_period_after[period_after_break] = {}

            if is_person:
                supervisions_per_period_after[period_after_break] = supervision
            else:
                supervisions_per_period_after[period_after_break][weekday] = supervision

    # Get ordered breaks
    breaks = OrderedDict(sorted(Break.get_breaks_dict().items()))

    rows = []
    for period, break_ in breaks.items():  # period is period after break
        # Break
        if type_ == "teacher" and period in needed_breaks:
            row = {
                "type": "break",
                "after_period": break_.after_period_number,
                "before_period": break_.before_period_number,
                "time_start": break_.time_start,
                "time_end": break_.time_end,
            }

            if not is_person:
                cols = []

                for weekday in range(
                    TimePeriod.weekday_min, TimePeriod.weekday_max + 1
                ):
                    col = None
                    if period in supervisions_per_period_after:
                        if weekday in supervisions_per_period_after[period]:
                            col = supervisions_per_period_after[period][weekday]
                    cols.append(col)

                row["cols"] = cols
            else:
                col = None
                if period in supervisions_per_period_after:
                    col = supervisions_per_period_after[period]
                row["col"] = col
            rows.append(row)

        # Lesson
        if period <= TimePeriod.period_max:
            row = {
                "type": "period",
                "period": period,
                "time_start": break_.before_period.time_start,
                "time_end": break_.before_period.time_end,
            }

            if not is_person:
                cols = []
                for weekday in range(
                    TimePeriod.weekday_min, TimePeriod.weekday_max + 1
                ):
                    col = []

                    # Add lesson periods
                    if period in lesson_periods_per_period:
                        if weekday in lesson_periods_per_period[period]:
                            col += lesson_periods_per_period[period][weekday]

                    cols.append(col)

                row["cols"] = cols
            else:
                col = []

                # Add lesson periods
                if period in lesson_periods_per_period:
                    col += lesson_periods_per_period[period]

                row["col"] = col

            rows.append(row)

    return rows


def build_substitutions_list(wanted_day: date) -> List[dict]:
    rows = []

    subs = LessonSubstitution.objects.on_day(wanted_day).order_by(
        "lesson_period__lesson__groups", "lesson_period__period"
    )

    for sub in subs:
        if not sub.cancelled_for_teachers:
            sort_a = sub.lesson_period.lesson.group_names
        else:
            sort_a = "Z.{}".format(sub.lesson_period.lesson.teacher_names)

        row = {
            "type": "substitution",
            "sort_a": sort_a,
            "sort_b": "{}".format(sub.lesson_period.period.period),
            "el": sub,
        }

        rows.append(row)

    return rows
