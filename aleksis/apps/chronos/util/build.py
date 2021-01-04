from collections import OrderedDict
from datetime import date
from typing import List, Tuple, Union

from django.apps import apps

from calendarweek import CalendarWeek

from aleksis.apps.chronos.managers import TimetableType
from aleksis.apps.chronos.models import Room
from aleksis.core.models import Group, Person

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
    type_: Union[TimetableType, str],
    obj: Union[Group, Room, Person],
    date_ref: Union[CalendarWeek, date],
):
    needed_breaks = []

    is_person = False
    if type_ == "person":
        is_person = True
        type_ = obj.timetable_type

    is_week = False
    if type(date_ref) == CalendarWeek:
        is_week = True

    if type_ is None:
        return None

    # Get matching holidays
    if is_week:
        holidays_per_weekday = Holiday.in_week(date_ref)
    else:
        holiday = Holiday.on_day(date_ref)

    # Get matching lesson periods
    lesson_periods = LessonPeriod.objects
    if is_week:
        lesson_periods = lesson_periods.in_week(date_ref)
    else:
        lesson_periods = lesson_periods.on_day(date_ref)

    if is_person:
        lesson_periods = lesson_periods.filter_from_person(obj)
    else:
        lesson_periods = lesson_periods.filter_from_type(type_, obj)

    # Sort lesson periods in a dict
    lesson_periods_per_period = lesson_periods.group_by_periods(is_week=is_week)

    # Get events
    extra_lessons = ExtraLesson.objects
    if is_week:
        extra_lessons = extra_lessons.filter(week=date_ref.week, year=date_ref.year)
    else:
        extra_lessons = extra_lessons.on_day(date_ref)
    if is_person:
        extra_lessons = extra_lessons.filter_from_person(obj)
    else:
        extra_lessons = extra_lessons.filter_from_type(type_, obj)

    # Sort lesson periods in a dict
    extra_lessons_per_period = extra_lessons.group_by_periods(is_week=is_week)

    # Get events
    events = Event.objects
    if is_week:
        events = events.in_week(date_ref)
    else:
        events = events.on_day(date_ref)

    if is_person:
        events = events.filter_from_person(obj)
    else:
        events = events.filter_from_type(type_, obj)

    # Sort events in a dict
    events_per_period = {}
    for event in events:
        if is_week and event.date_start < date_ref[TimePeriod.weekday_min]:
            # If start date not in current week, set weekday and period to min
            weekday_from = TimePeriod.weekday_min
            period_from_first_weekday = TimePeriod.period_min
        else:
            weekday_from = event.date_start.weekday()
            period_from_first_weekday = event.period_from.period

        if is_week and event.date_end > date_ref[TimePeriod.weekday_max]:
            # If end date not in current week, set weekday and period to max
            weekday_to = TimePeriod.weekday_max
            period_to_last_weekday = TimePeriod.period_max
        else:
            weekday_to = event.date_end.weekday()
            period_to_last_weekday = event.period_to.period

        for weekday in range(weekday_from, weekday_to + 1):
            if not is_week and weekday != date_ref.weekday():
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

                if is_week and weekday not in events_per_period[period]:
                    events_per_period[period][weekday] = []

                if not is_week:
                    events_per_period[period].append(event)
                else:
                    events_per_period[period][weekday].append(event)

    if type_ == TimetableType.TEACHER:
        # Get matching supervisions
        if not is_week:
            week = CalendarWeek.from_date(date_ref)
        else:
            week = date_ref
        supervisions = (
            Supervision.objects.in_week(week).all().annotate_week(week).filter_by_teacher(obj)
        )

        if not is_week:
            supervisions = supervisions.filter_by_weekday(date_ref.weekday())

        supervisions_per_period_after = {}
        for supervision in supervisions:
            weekday = supervision.break_item.weekday
            period_after_break = supervision.break_item.before_period_number

            if period_after_break not in needed_breaks:
                needed_breaks.append(period_after_break)

            if is_week and period_after_break not in supervisions_per_period_after:
                supervisions_per_period_after[period_after_break] = {}

            if not is_week:
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

            if is_week:
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

            if is_week:
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

                # Add extra lessons
                if period in extra_lessons_per_period and not holiday:
                    col += extra_lessons_per_period[period]

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

    start_period = None
    for i, sub in enumerate(subs):
        if not sub.cancelled_for_teachers:
            sort_a = sub.lesson_period.lesson.groups_to_show_names
        else:
            sort_a = f"Z.{sub.lesson_period.lesson.teacher_names}"

        # Get next substitution
        next_sub = subs[i + 1] if i + 1 < len(subs) else None

        # Check if next substitution is equal with this substitution
        if (
            next_sub
            and sub.comment == next_sub.comment
            and sub.cancelled == next_sub.cancelled
            and sub.subject == next_sub.subject
            and sub.room == next_sub.room
            and sub.lesson_period.lesson == next_sub.lesson_period.lesson
            and set(sub.teachers.all()) == set(next_sub.teachers.all())
        ):
            if not start_period:
                start_period = sub.lesson_period.period.period
            continue

        row = {
            "type": "substitution",
            "sort_a": sort_a,
            "sort_b": str(sub.lesson_period.period.period),
            "el": sub,
            "start_period": start_period if start_period else sub.lesson_period.period.period,
            "end_period": sub.lesson_period.period.period,
        }

        if start_period:
            start_period = None

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
