from collections import OrderedDict
from datetime import date
from typing import List, Tuple, Union

from django.apps import apps

from calendarweek import CalendarWeek

from aleksis.apps.chronos.managers import TimetableType
from aleksis.core.models import Person

LessonPeriod = apps.get_model("chronos", "LessonPeriod")
TimePeriod = apps.get_model("chronos", "TimePeriod")
Break = apps.get_model("chronos", "Break")
Supervision = apps.get_model("chronos", "Supervision")
LessonSubstitution = apps.get_model("chronos", "LessonSubstitution")
SupervisionSubstitution = apps.get_model("chronos", "SupervisionSubstitution")
Event = apps.get_model("chronos", "Event")
Holiday = apps.get_model("chronos", "Holiday")
ExtraLesson = apps.get_model("chronos", "ExtraLesson")


def build_timetable(
    type_: Union[TimetableType, str], obj: Union[int, Person], date_ref: Union[CalendarWeek, date],
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

    if type_ is None:
        return None

    # Get matching holidays
    if is_person:
        holiday = Holiday.on_day(date_ref)
    else:
        holidays_per_weekday = Holiday.in_week(date_ref)

    # Get matching lesson periods
    if is_person:
        lesson_periods = LessonPeriod.objects.daily_lessons_for_person(obj, date_ref)
    else:
        lesson_periods = LessonPeriod.objects.in_week(date_ref).filter_from_type(type_, obj)

    # Sort lesson periods in a dict
    lesson_periods_per_period = lesson_periods.group_by_periods(is_person=is_person)

    # Get events
    if is_person:
        extra_lessons = ExtraLesson.objects.on_day(date_ref).filter_from_person(obj)
    else:
        extra_lessons = ExtraLesson.objects.filter(week=date_ref.week).filter_from_type(type_, obj)

    # Sort lesson periods in a dict
    extra_lessons_per_period = extra_lessons.group_by_periods(is_person=is_person)

    # Get events
    if is_person:
        events = Event.objects.on_day(date_ref).filter_from_person(obj)
    else:
        events = Event.objects.in_week(date_ref).filter_from_type(type_, obj)

    # Sort events in a dict
    events_per_period = {}
    for event in events:
        if not is_person and event.date_start < date_ref[TimePeriod.weekday_min]:
            # If start date not in current week, set weekday and period to min
            weekday_from = TimePeriod.weekday_min
            period_from_first_weekday = TimePeriod.period_min
        else:
            weekday_from = event.date_start.weekday()
            period_from_first_weekday = event.period_from.period

        if not is_person and event.date_end > date_ref[TimePeriod.weekday_max]:
            # If end date not in current week, set weekday and period to max
            weekday_to = TimePeriod.weekday_max
            period_to_last_weekday = TimePeriod.period_max
        else:
            weekday_to = event.date_end.weekday()
            period_to_last_weekday = event.period_to.period

        for weekday in range(weekday_from, weekday_to + 1):
            if is_person and weekday != date_ref.weekday():
                # If daily timetable for person, skip other weekdays
                continue

            if weekday == weekday_from:
                # If start day, use start period
                period_from = period_from_first_weekday
            else:
                # If not start day, use min period
                period_from = TimePeriod.period_min

            if weekday == weekday_to:
                # If end day, use end period
                period_to = period_to_last_weekday
            else:
                # If not end day, use max period
                period_to = TimePeriod.period_max

            for period in range(period_from, period_to + 1):
                if period not in events_per_period:
                    events_per_period[period] = [] if is_person else {}

                if not is_person and weekday not in events_per_period[period]:
                    events_per_period[period][weekday] = []

                if is_person:
                    events_per_period[period].append(event)
                else:
                    events_per_period[period][weekday].append(event)

    if type_ == TimetableType.TEACHER:
        # Get matching supervisions
        if is_person:
            week = CalendarWeek.from_date(date_ref)
        else:
            week = date_ref
        supervisions = Supervision.objects.all().annotate_week(week).filter_by_teacher(obj)

        if is_person:
            supervisions.filter_by_weekday(date_ref.weekday())

        supervisions_per_period_after = {}
        for supervision in supervisions:
            weekday = supervision.break_item.weekday
            period_after_break = supervision.break_item.before_period_number
            print(supervision, weekday, period_after_break)

            if period_after_break not in needed_breaks:
                needed_breaks.append(period_after_break)

            if not is_person and period_after_break not in supervisions_per_period_after:
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
        if type_ == TimetableType.TEACHER and period in needed_breaks:
            row = {
                "type": "break",
                "after_period": break_.after_period_number,
                "before_period": break_.before_period_number,
                "time_start": break_.time_start,
                "time_end": break_.time_end,
            }

            if not is_person:
                cols = []

                for weekday in range(TimePeriod.weekday_min, TimePeriod.weekday_max + 1):
                    col = None
                    if (
                        period in supervisions_per_period_after
                        and weekday not in holidays_per_weekday
                    ):
                        if weekday in supervisions_per_period_after[period]:
                            col = supervisions_per_period_after[period][weekday]
                    cols.append(col)

                row["cols"] = cols
            else:
                col = None
                if period in supervisions_per_period_after and not holiday:
                    col = supervisions_per_period_after[period]
                row["col"] = col
            rows.append(row)

        # Period
        if period <= TimePeriod.period_max:
            row = {
                "type": "period",
                "period": period,
                "time_start": break_.before_period.time_start,
                "time_end": break_.before_period.time_end,
            }

            if not is_person:
                cols = []
                for weekday in range(TimePeriod.weekday_min, TimePeriod.weekday_max + 1):
                    col = []

                    # Add lesson periods
                    if period in lesson_periods_per_period and weekday not in holidays_per_weekday:
                        if weekday in lesson_periods_per_period[period]:
                            col += lesson_periods_per_period[period][weekday]

                    # Add extra lessons
                    if period in extra_lessons_per_period and weekday not in holidays_per_weekday:
                        if weekday in extra_lessons_per_period[period]:
                            col += extra_lessons_per_period[period][weekday]

                    # Add events
                    if period in events_per_period and weekday not in holidays_per_weekday:
                        if weekday in events_per_period[period]:
                            col += events_per_period[period][weekday]

                    cols.append(col)

                row["cols"] = cols
            else:
                col = []

                # Add lesson periods
                if period in lesson_periods_per_period and not holiday:
                    col += lesson_periods_per_period[period]

                # Add events
                if period in events_per_period and not holiday:
                    col += events_per_period[period]

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
            sort_a = f"Z.{sub.lesson_period.lesson.teacher_names}"

        row = {
            "type": "substitution",
            "sort_a": sort_a,
            "sort_b": str(sub.lesson_period.period.period),
            "el": sub,
        }

        rows.append(row)

    # Get supervision substitutions
    super_subs = SupervisionSubstitution.objects.filter(date=wanted_day)

    for super_sub in super_subs:
        row = {
            "type": "supervision_substitution",
            "sort_a": f"Z.{super_sub.teacher}",
            "sort_b": str(super_sub.supervision.break_item.after_period_number),
            "el": super_sub,
        }
        rows.append(row)

    # Get extra lessons
    extra_lessons = ExtraLesson.objects.on_day(wanted_day)

    for extra_lesson in extra_lessons:
        row = {
            "type": "extra_lesson",
            "sort_a": str(extra_lesson.group_names),
            "sort_b": str(extra_lesson.period.period),
            "el": extra_lesson,
        }
        rows.append(row)

    # Get events
    events = Event.objects.on_day(wanted_day).annotate_day(wanted_day)

    for event in events:
        if event.groups.all():
            sort_a = event.group_names
        else:
            sort_a = f"Z.{event.teacher_names}"

        row = {
            "type": "event",
            "sort_a": sort_a,
            "sort_b": str(event.period_from_on_day),
            "el": event,
        }
        rows.append(row)

    # Sort all items
    def sorter(row: dict):
        return row["sort_a"] + row["sort_b"]

    rows.sort(key=sorter)

    return rows


def build_weekdays(base: List[Tuple[int, str]], wanted_week: CalendarWeek) -> List[dict]:
    holidays_per_weekday = Holiday.in_week(wanted_week)

    weekdays = []
    for key, name in base[TimePeriod.weekday_min : TimePeriod.weekday_max + 1]:

        weekday = {
            "key": key,
            "name": name,
            "date": wanted_week[key],
            "holiday": holidays_per_weekday[key] if key in holidays_per_weekday else None,
        }
        weekdays.append(weekday)

    return weekdays
