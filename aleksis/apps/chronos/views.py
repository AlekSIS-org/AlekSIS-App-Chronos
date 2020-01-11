from collections import OrderedDict
from datetime import date, datetime, timedelta
from typing import Optional

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Min
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
from .models import LessonPeriod, LessonSubstitution, TimePeriod, Room
from .tables import LessonsTable, SubstitutionsTable
from .util import CalendarWeek


@login_required
def all(request: HttpRequest) -> HttpResponse:
    context = {}

    teachers = Person.objects.annotate(lessons_count=Count("lessons_as_teacher")).filter(lessons_count__gt=0)
    classes = Group.objects.annotate(lessons_count=Count("lessons")).filter(lessons_count__gt=0, parent_groups=None)
    rooms = Room.objects.annotate(lessons_count=Count("lesson_periods")).filter(lessons_count__gt=0)

    context['teachers'] = teachers
    context['classes'] = classes
    context['rooms'] = rooms

    return render(request, 'chronos/quicklaunch.html', context)


@login_required
def timetable(
    request: HttpRequest, _type: str, pk: int, year: Optional[int] = None, week: Optional[int] = None
) -> HttpResponse:
    context = {}

    if _type == "group":
        el = get_object_or_404(Group, pk=pk)
    elif _type == "teacher":
        el = get_object_or_404(Person, pk=pk)
    elif _type == "room":
        el = get_object_or_404(Room, pk=pk)
    else:
        return HttpResponseNotFound()

    if year and week:
        wanted_week = CalendarWeek(year=year, week=week)
    else:
        wanted_week = CalendarWeek()

    lesson_periods = LessonPeriod.objects.in_week(wanted_week)


    lesson_periods = lesson_periods.filter_from_type(_type, pk)
    # else:
    #     # Redirect to a selected view if no filter provided
    #     if request.user.person:
    #         if request.user.person.primary_group:
    #             return redirect(
    #                 reverse("timetable") + "?group=%d" % request.user.person.primary_group.pk
    #             )
    #         elif lesson_periods.filter(lesson__teachers=request.user.person).exists():
    #             return redirect(reverse("timetable") + "?teacher=%d" % request.user.person.pk)

    # Regroup lesson periods per weekday
    per_period = {}
    for lesson_period in lesson_periods:
        print(lesson_period.period)
        added = False
        if lesson_period.period.period in per_period :
            if lesson_period.period.weekday in per_period[lesson_period.period.period]:
                print("HEY HEY")
                print(per_period[lesson_period.period.period][lesson_period.period.weekday])
                per_period[lesson_period.period.period][lesson_period.period.weekday].append(lesson_period)
                added =True

        if not added:
            per_period.setdefault(lesson_period.period.period, {})[
                lesson_period.period.weekday
            ] = [lesson_period]

    print(per_period)
    # Determine overall first and last day and period
    min_max = TimePeriod.objects.aggregate(
        Min("period"), Max("period"), Min("weekday"), Max("weekday")
    )

    period_min = min_max.get("period__min", 1)
    period_max = min_max.get("period__max", 7)

    weekday_min = min_max.get("weekday__min", 0)
    weekday_max = min_max.get("weekday__max", 6)

    # Fill in empty lessons
    for period_num in range(period_min, period_max + 1):
        print(period_num)
        # Fill in empty weekdays
        if period_num not in per_period.keys():
            per_period[period_num] = {}

        # Fill in empty lessons on this workday
        for weekday_num in range(weekday_min, weekday_max + 1):
            if weekday_num not in per_period[period_num].keys():
                per_period[period_num][weekday_num] = []

        # Order this weekday by periods
        per_period[period_num] = OrderedDict(sorted(per_period[period_num].items()))

    print(lesson_periods)
    context["lesson_periods"] = OrderedDict(sorted(per_period.items()))
    context["periods"] = TimePeriod.get_times_dict()
    context["weekdays"] = dict(TimePeriod.WEEKDAY_CHOICES[weekday_min:weekday_max + 1])
    context["weekdays_short"] = dict(TimePeriod.WEEKDAY_CHOICES_SHORT[weekday_min:weekday_max + 1])
    context["week"] = wanted_week
    context["type"] = _type
    context["pk"] = pk
    context["el"] = el

    week_prev = wanted_week - 1
    week_next = wanted_week + 1
    context["url_prev"] = "%s?%s" % (
        reverse("timetable_by_week", args=[_type, pk, week_prev.year, week_prev.week]),
        request.GET.urlencode(),
    )
    context["url_next"] = "%s?%s" % (
        reverse("timetable_by_week", args=[_type, pk, week_next.year, week_next.week]),
        request.GET.urlencode(),
    )

    return render(request, "chronos/plan.html", context)


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
    context["url_prev"] = reverse("lessons_day_by_date", args=[day_prev.strftime("%Y-%m-%d")])
    context["url_next"] = reverse("lessons_day_by_date", args=[day_next.strftime("%Y-%m-%d")])

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
    context = {}

    lesson_period = get_object_or_404(LessonPeriod, pk=id_)
    wanted_week = lesson_period.lesson.get_calendar_week(week)

    LessonSubstitution.objects.filter(week=wanted_week.week, lesson_period=lesson_period).delete()

    messages.success(request, _("The substitution has been deleted."))
    return redirect(
        "lessons_day_by_date",
        when=wanted_week[lesson_period.period.weekday - 1].strftime("%Y-%m-%d"),
    )


def substitutions(
    request: HttpRequest, year: Optional[int] = None, month: Optional[int] = None, day: Optional[int] = None
) -> HttpResponse:
    context = {}

    if day:
        wanted_day = timezone.datetime(year=year, month=month, day=day).date()
    else:
        wanted_day = timezone.now().date()

    substitutions = LessonSubstitution.objects.on_day(wanted_day)

    # Prepare table
    substitutions_table = SubstitutionsTable(substitutions)
    RequestConfig(request).configure(substitutions_table)

    context["current_head"] = str(wanted_day)
    context["substitutions_table"] = substitutions_table
    context["substitutions"] = substitutions
    context["day"] = wanted_day

    day_prev = wanted_day - timedelta(days=1)
    day_next = wanted_day + timedelta(days=1)
    context["url_prev"] = "%s" % (
        reverse("substitutions_by_day", args=[day_prev.year, day_prev.month, day_prev.day])
    )
    context["url_next"] = "%s" % (
        reverse("substitutions_by_day", args=[day_next.year, day_next.month, day_next.day])
    )

    return render(request, "chronos/substitution.html", context)
