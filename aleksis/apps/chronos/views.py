from collections import OrderedDict
from datetime import date, datetime, timedelta
from typing import Optional, Tuple

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext as _

from django_tables2 import RequestConfig

from aleksis.core.decorators import admin_required
from aleksis.core.models import Person, Group
from aleksis.core.util import messages

from .forms import LessonSubstitutionForm
from .min_max import (
    period_min,
    period_max,
    weekday_min_,
    weekday_max,
    get_next_relevant_day,
)
from .models import LessonPeriod, LessonSubstitution, TimePeriod, Room
from .tables import LessonsTable, SubstitutionsTable
from .util import CalendarWeek, get_weeks_for_year


def get_prev_next_by_day(day: date, url: str) -> Tuple[str, str]:
    """ Build URLs for previous/next day """

    day_prev = day - timedelta(days=1)
    day_next = day + timedelta(days=1)

    url_prev = reverse(url, args=[day_prev.year, day_prev.month, day_prev.day])
    url_next = reverse(url, args=[day_next.year, day_next.month, day_next.day])

    return url_prev, url_next


@login_required
def all(request: HttpRequest) -> HttpResponse:
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
        wanted_day = get_next_relevant_day(wanted_day)
    else:
        wanted_day = get_next_relevant_day(timezone.now().date(), datetime.now().time())

    if request.user.person:
        person = request.user.person

        if person.primary_group:
            # Student

            type_ = "group"
            super_el = person.primary_group
            lesson_periods_person = person.lesson_periods_as_participant

        elif person.is_teacher():
            # Teacher

            type_ = "teacher"
            super_el = person
            lesson_periods_person = person.lesson_periods_as_teacher
        else:
            # If no student or teacher, redirect to all timetables
            return redirect("all_timetables")

    lesson_periods = lesson_periods_person.on_day(wanted_day)

    # Build dictionary with lessons
    per_period = {}
    for lesson_period in lesson_periods:
        if lesson_period.period.period in per_period:
            per_period[lesson_period.period.period].append(lesson_period)
        else:
            per_period[lesson_period.period.period] = [lesson_period]

    context["lesson_periods"] = OrderedDict(sorted(per_period.items()))
    context["super"] = {"type": type_, "el": super_el}
    context["type"] = type_
    context["day"] = wanted_day
    context["periods"] = TimePeriod.get_times_dict()

    context["url_prev"], context["url_next"] = get_prev_next_by_day(
        wanted_day, "substitutions_by_day"
    )

    return render(request, "chronos/my_timetable.html", context)


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
    for period_num in range(period_min, period_max + 1):
        # Fill in empty weekdays
        if period_num not in per_period.keys():
            per_period[period_num] = {}

        # Fill in empty lessons on this workday
        for weekday_num in range(weekday_min_, weekday_max + 1):
            if weekday_num not in per_period[period_num].keys():
                per_period[period_num][weekday_num] = []

        # Order this weekday by periods
        per_period[period_num] = OrderedDict(sorted(per_period[period_num].items()))

    context["lesson_periods"] = OrderedDict(sorted(per_period.items()))
    context["periods"] = TimePeriod.get_times_dict()
    context["weekdays"] = dict(
        TimePeriod.WEEKDAY_CHOICES[weekday_min_ : weekday_max + 1]
    )
    context["weekdays_short"] = dict(
        TimePeriod.WEEKDAY_CHOICES_SHORT[weekday_min_ : weekday_max + 1]
    )
    context["weeks"] = get_weeks_for_year(year=wanted_week.year)
    context["week"] = wanted_week
    context["type"] = type_
    context["pk"] = pk
    context["el"] = el
    context["smart"] = is_smart

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
def lessons_day(request: HttpRequest, when: Optional[str] = None) -> HttpResponse:
    context = {}

    if when:
        day = datetime.strptime(when, "%Y-%m-%d").date()
    else:
        day = date.today()

    # Get lessons
    lesson_periods = LessonPeriod.objects.on_day(day)

    # Build table
    lessons_table = LessonsTable(lesson_periods.all())
    RequestConfig(request).configure(lessons_table)

    context["lessons_table"] = lessons_table
    context["day"] = day
    context["lesson_periods"] = lesson_periods

    day_prev = day - timedelta(days=1)
    day_next = day + timedelta(days=1)

    context["url_prev"] = reverse(
        "lessons_day_by_date", args=[day_prev.strftime("%Y-%m-%d")]
    )
    context["url_next"] = reverse(
        "lessons_day_by_date", args=[day_next.strftime("%Y-%m-%d")]
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
            return redirect(
                "lessons_day_by_date",
                when=wanted_week[lesson_period.period.weekday - 1].strftime("%Y-%m-%d"),
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
    return redirect(
        "lessons_day_by_date",
        when=wanted_week[lesson_period.period.weekday - 1].strftime("%Y-%m-%d"),
    )


def substitutions(
    request: HttpRequest,
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
) -> HttpResponse:
    context = {}

    if day:
        wanted_day = timezone.datetime(year=year, month=month, day=day).date()
        wanted_day = get_next_relevant_day(wanted_day)
    else:
        wanted_day = get_next_relevant_day(timezone.now().date(), datetime.now().time())

    substitutions = LessonSubstitution.objects.on_day(wanted_day)

    context["substitutions"] = substitutions
    context["day"] = wanted_day

    context["url_prev"], context["url_next"] = get_prev_next_by_day(
        wanted_day, "substitutions_by_day"
    )

    return render(request, "chronos/substitutions.html", context)
