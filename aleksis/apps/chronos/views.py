from collections import OrderedDict
from datetime import date, datetime, timedelta
from typing import Optional, Tuple

from constance import config
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext as _
from django_tables2 import RequestConfig

from aleksis.core.decorators import admin_required
from aleksis.core.models import Person, Group, Announcement
from aleksis.core.util import messages
from .forms import LessonSubstitutionForm
from .models import LessonPeriod, LessonSubstitution, TimePeriod, Room
from .tables import LessonsTable
from .util.js import date_unix
from .util.date import CalendarWeek, get_weeks_for_year
from aleksis.core.util.core_helpers import has_person


@login_required
def all_timetables(request: HttpRequest) -> HttpResponse:
    context = {}

    teachers = Person.objects.annotate(
        lessons_count=Count("lessons_as_teacher")
    ).filter(lessons_count__gt=0)
    classes = Group.objects.annotate(lessons_count=Count("lessons")).filter(
        lessons_count__gt=0, parent_groups=None
    )
    rooms = Room.objects.annotate(lessons_count=Count("lesson_periods")).filter(
        lessons_count__gt=0
    )

    context["teachers"] = teachers
    context["classes"] = classes
    context["rooms"] = rooms

    return render(request, "chronos/all.html", context)


@login_required
def my_timetable(
    request: HttpRequest,
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
) -> HttpResponse:
    context = {}

    if day:
        wanted_day = timezone.datetime(year=year, month=month, day=day).date()
        wanted_day = TimePeriod.get_next_relevant_day(wanted_day)
    else:
        wanted_day = TimePeriod.get_next_relevant_day(timezone.now().date(), datetime.now().time())

    if has_person(request.user):
        person = request.user.person

        lesson_periods = LessonPeriod.objects.daily_lessons_for_person(person, wanted_day)

        if lesson_periods is None:
            # If no student or teacher, redirect to all timetables
            return redirect("all_timetables")

        type_ = person.timetable_type
        super_el = person.timetable_object

        context["lesson_periods"] = lesson_periods.per_period_one_day()
        context["super"] = {"type": type_, "el": super_el}
        context["type"] = type_
        context["day"] = wanted_day
        context["periods"] = TimePeriod.get_times_dict()
        context["smart"] = True
        context["announcements"] = Announcement.for_timetables().on_date(wanted_day).for_person(person)

        context["url_prev"], context["url_next"] = TimePeriod.get_prev_next_by_day(
            wanted_day, "my_timetable_by_date"
        )

        return render(request, "chronos/my_timetable.html", context)
    else:
        return redirect("all_timetables")


@login_required
def timetable(
    request: HttpRequest,
    type_: str,
    pk: int,
    year: Optional[int] = None,
    week: Optional[int] = None,
    regular: Optional[str] = None,
) -> HttpResponse:
    context = {}

    is_smart = regular != "regular"

    if type_ == "group":
        el = get_object_or_404(Group, pk=pk)
    elif type_ == "teacher":
        el = get_object_or_404(Person, pk=pk)
    elif type_ == "room":
        el = get_object_or_404(Room, pk=pk)
    else:
        return HttpResponseNotFound()

    if year and week:
        wanted_week = CalendarWeek(year=year, week=week)
    else:
        # TODO: On not used days show next week
        wanted_week = CalendarWeek()

    lesson_periods = LessonPeriod.objects.in_week(wanted_week)
    lesson_periods = lesson_periods.filter_from_type(type_, pk)

    # Regroup lesson periods per weekday
    per_period = {}
    for lesson_period in lesson_periods:
        added = False
        if lesson_period.period.period in per_period:
            if lesson_period.period.weekday in per_period[lesson_period.period.period]:
                per_period[lesson_period.period.period][
                    lesson_period.period.weekday
                ].append(lesson_period)
                added = True

        if not added:
            per_period.setdefault(lesson_period.period.period, {})[
                lesson_period.period.weekday
            ] = [lesson_period]

    # Fill in empty lessons
    for period_num in range(TimePeriod.period_min, TimePeriod.period_max + 1):
        # Fill in empty weekdays
        if period_num not in per_period.keys():
            per_period[period_num] = {}

        # Fill in empty lessons on this workday
        for weekday_num in range(TimePeriod.weekday_min, TimePeriod.weekday_max + 1):
            if weekday_num not in per_period[period_num].keys():
                per_period[period_num][weekday_num] = []

        # Order this weekday by periods
        per_period[period_num] = OrderedDict(sorted(per_period[period_num].items()))

    context["lesson_periods"] = OrderedDict(sorted(per_period.items()))
    context["periods"] = TimePeriod.get_times_dict()

    # Build lists with weekdays and corresponding dates (long and short variant)
    context["weekdays"] = [
        (key, weekday, wanted_week[key])
        for key, weekday in TimePeriod.WEEKDAY_CHOICES[
            TimePeriod.weekday_min : TimePeriod.weekday_max + 1
        ]
    ]
    context["weekdays_short"] = [
        (key, weekday, wanted_week[key])
        for key, weekday in TimePeriod.WEEKDAY_CHOICES_SHORT[
            TimePeriod.weekday_min : TimePeriod.weekday_max + 1
        ]
    ]

    context["weeks"] = get_weeks_for_year(year=wanted_week.year)
    context["week"] = wanted_week
    context["type"] = type_
    context["pk"] = pk
    context["el"] = el
    context["smart"] = is_smart
    context["week_select"] = {
        "year": wanted_week.year,
        "dest": reverse("timetable", args=[type_, pk])
    }

    if is_smart:
        start = wanted_week[TimePeriod.weekday_min]
        stop = wanted_week[TimePeriod.weekday_max]
        context["announcements"] = Announcement.for_timetables().relevant_for(el).within_days(start, stop)

    week_prev = wanted_week - 1
    week_next = wanted_week + 1

    context["url_prev"] = reverse(
        "timetable_by_week", args=[type_, pk, week_prev.year, week_prev.week]
    )
    context["url_next"] = reverse(
        "timetable_by_week", args=[type_, pk, week_next.year, week_next.week]
    )

    return render(request, "chronos/timetable.html", context)


@login_required
def lessons_day(
    request: HttpRequest,
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
) -> HttpResponse:
    context = {}

    if day:
        wanted_day = timezone.datetime(year=year, month=month, day=day).date()
        wanted_day = TimePeriod.get_next_relevant_day(wanted_day)
    else:
        wanted_day = TimePeriod.get_next_relevant_day(timezone.now().date(), datetime.now().time())

    # Get lessons
    lesson_periods = LessonPeriod.objects.on_day(wanted_day)

    # Build table
    lessons_table = LessonsTable(lesson_periods.all())
    RequestConfig(request).configure(lessons_table)

    context["lessons_table"] = lessons_table
    context["day"] = wanted_day
    context["lesson_periods"] = lesson_periods

    context["datepicker"] = {
        "date": date_unix(wanted_day),
        "dest": reverse("lessons_day")
    }

    context["url_prev"], context["url_next"] = TimePeriod.get_prev_next_by_day(
        wanted_day, "lessons_day_by_date"
    )

    return render(request, "chronos/lessons_day.html", context)


@admin_required
def edit_substitution(request: HttpRequest, id_: int, week: int) -> HttpResponse:
    context = {}

    lesson_period = get_object_or_404(LessonPeriod, pk=id_)
    wanted_week = lesson_period.lesson.get_calendar_week(week)

    lesson_substitution = LessonSubstitution.objects.filter(
        week=wanted_week.week, lesson_period=lesson_period
    ).first()
    if lesson_substitution:
        edit_substitution_form = LessonSubstitutionForm(
            request.POST or None, instance=lesson_substitution
        )
    else:
        edit_substitution_form = LessonSubstitutionForm(
            request.POST or None,
            initial={"week": wanted_week.week, "lesson_period": lesson_period},
        )

    context["substitution"] = lesson_substitution

    if request.method == "POST":
        if edit_substitution_form.is_valid():
            edit_substitution_form.save(commit=True)

            messages.success(request, _("The substitution has been saved."))

            date = wanted_week[lesson_period.period.weekday]
            return redirect(
                "lessons_day_by_date",
                year=date.year, month=date.month, day=date.day
            )

    context["edit_substitution_form"] = edit_substitution_form

    return render(request, "chronos/edit_substitution.html", context)


@admin_required
def delete_substitution(request: HttpRequest, id_: int, week: int) -> HttpResponse:
    lesson_period = get_object_or_404(LessonPeriod, pk=id_)
    wanted_week = lesson_period.lesson.get_calendar_week(week)

    LessonSubstitution.objects.filter(
        week=wanted_week.week, lesson_period=lesson_period
    ).delete()

    messages.success(request, _("The substitution has been deleted."))

    date = wanted_week[lesson_period.period.weekday]
    return redirect(
        "lessons_day_by_date",
        year=date.year, month=date.month, day=date.day
    )


@login_required
def substitutions(
    request: HttpRequest,
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    is_print: bool = False,
) -> HttpResponse:
    context = {}

    if day:
        wanted_day = timezone.datetime(year=year, month=month, day=day).date()
        wanted_day = TimePeriod.get_next_relevant_day(wanted_day)
    else:
        wanted_day = TimePeriod.get_next_relevant_day(timezone.now().date(), datetime.now().time())

    day_number = config.CHRONOS_SUBSTITUTIONS_PRINT_DAY_NUMBER
    day_contexts = {}

    if is_print:
        next_day = wanted_day
        for i in range(day_number):
            day_contexts[next_day] = {"day": next_day}
            next_day = TimePeriod.get_next_relevant_day(next_day + timedelta(days=1))
    else:
        day_contexts = {wanted_day: {"day": wanted_day}}

    for day in day_contexts:
        subs = LessonSubstitution.objects.on_day(day).order_by("lesson_period__lesson__groups", "lesson_period__period")
        day_contexts[day]["substitutions"] = subs

        day_contexts[day]["announcements"] = Announcement.for_timetables().on_date(day).filter(show_in_timetables=True)

        if config.CHRONOS_SUBSTITUTIONS_SHOW_HEADER_BOX:
            day_contexts[day]["affected_teachers"] = subs.affected_teachers()
            day_contexts[day]["affected_groups"] = subs.affected_groups()

    if not is_print:
        context = day_contexts[wanted_day]
        context["datepicker"] = {
            "date": date_unix(wanted_day),
            "dest": reverse("substitutions"),
        }

        context["url_prev"], context["url_next"] = TimePeriod.get_prev_next_by_day(
            wanted_day, "substitutions_by_date"
        )

        template_name = "chronos/substitutions.html"
    else:
        context["days"] = day_contexts
        template_name = "chronos/substitutions_print.html"

    return render(request, template_name, context)
