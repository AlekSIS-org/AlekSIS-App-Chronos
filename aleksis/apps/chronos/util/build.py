from collections import OrderedDict

from calendarweek import CalendarWeek

from aleksis.apps.chronos.models import LessonPeriod, TimePeriod, Break


def build_timetable(type_: str, pk: int, week: CalendarWeek):
    needed_breaks = []

    # Get matching lesson periods
    lesson_periods = LessonPeriod.objects.in_week(week).filter_from_type(type_, pk)

    # Sort lesson periods in a dict
    lesson_periods_per_period = {}
    for lesson_period in lesson_periods:
        period = lesson_period.period.period
        weekday = lesson_period.period.weekday

        if period not in lesson_periods_per_period:
            lesson_periods_per_period[period] = {}

        if weekday not in lesson_periods_per_period[period]:
            lesson_periods_per_period[period][weekday] = []

        lesson_periods_per_period[period][weekday].append(lesson_period)

    # Get ordered breaks
    breaks = OrderedDict(sorted(Break.get_breaks_dict().items()))

    rows = []
    for period, break_ in breaks.items():  # period is period after break
        # Break
        if period in needed_breaks:
            row = {
                "type": "break",
                "after_period": break_.after_period_number,
                "before_period": break_.before_period_number,
                "time_start": break_.time_start,
                "time_end": break_.time_end,
            }

            cols = []

            # ...

            row["cols"] = cols
            rows.append(row)

        # Lesson
        if period <= TimePeriod.period_max:
            row = {
                "type": "period",
                "period": period,
                "time_start": break_.before_period.time_start,
                "time_end": break_.before_period.time_end,
            }
            cols = []
            for weekday in range(TimePeriod.weekday_min, TimePeriod.weekday_max + 1):
                col = []
                if row["type"] == "period":

                    # Add lesson periods
                    if period in lesson_periods_per_period:
                        if weekday in lesson_periods_per_period[period]:
                            col += lesson_periods_per_period[period][weekday]

                cols.append(col)

            row["cols"] = cols
            rows.append(row)

    return rows
