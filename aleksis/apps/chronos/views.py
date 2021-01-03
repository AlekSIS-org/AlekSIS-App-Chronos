from datetime import datetime, timedelta
from typing import Optional

from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache

from django_tables2 import RequestConfig
from rules.contrib.views import permission_required

from aleksis.core.models import Announcement, Group, Person
from aleksis.core.util import messages
from aleksis.core.util.core_helpers import get_site_preferences, has_person

from .forms import LessonSubstitutionForm
from .managers import TimetableType
from .models import Absence, Holiday, LessonPeriod, LessonSubstitution, Room, TimePeriod
from .tables import LessonsTable
from .util.build import build_substitutions_list, build_timetable, build_weekdays
from .util.chronos_helpers import get_el_by_pk, get_substitution_by_id
from .util.date import CalendarWeek, get_weeks_for_year
from .util.js import date_unix


@permission_required("chronos.view_timetable_overview")
def all_timetables(request: HttpRequest) -> HttpResponse:
    """View all timetables for persons, groups and rooms."""
    context = {}

    teachers = (
        Person.objects.annotate(lessons_count=Count("lessons_as_teacher"))
        .filter(lessons_count__gt=0)
        .order_by("short_name", "last_name")
    )
    groups = Group.objects.for_current_school_term_or_all().annotate(
        lessons_count=Count("lessons"), child_lessons_count=Count("child_groups__lessons"),
    )
    classes = groups.filter(lessons_count__gt=0, parent_groups=None) | groups.filter(
        child_lessons_count__gt=0, parent_groups=None
    ).order_by("short_name", "name")
    rooms = (
        Room.objects.annotate(lessons_count=Count("lesson_periods"))
        .filter(lessons_count__gt=0)
        .order_by("short_name", "name")
    )

    context["teachers"] = teachers
    context["classes"] = classes
    context["rooms"] = rooms

    return render(request, "chronos/all.html", context)


@permission_required("chronos.view_my_timetable")
def my_timetable(
    request: HttpRequest,
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
) -> HttpResponse:
    """View personal timetable on a specified date."""
    context = {}

    if day:
        wanted_day = timezone.datetime(year=year, month=month, day=day).date()
        wanted_day = TimePeriod.get_next_relevant_day(wanted_day)
    else:
        wanted_day = TimePeriod.get_next_relevant_day(timezone.now().date(), datetime.now().time())

    wanted_week = CalendarWeek.from_date(wanted_day)

    if has_person(request.user):
        person = request.user.person
        type_ = person.timetable_type

        # Build timetable
        timetable = build_timetable("person", person, wanted_day)
        week_timetable = build_timetable("person", person, wanted_week)

        if type_ is None:
            # If no student or teacher, redirect to all timetables
            return redirect("all_timetables")

        super_el = person.timetable_object

        context["timetable"] = timetable
        context["week_timetable"] = week_timetable
        context["holiday"] = Holiday.on_day(wanted_day)
        context["super"] = {"type": type_, "el": super_el}
        context["type"] = type_
        context["day"] = wanted_day
        context["today"] = timezone.now().date()
        context["week"] = wanted_week
        context["periods"] = TimePeriod.get_times_dict()
        context["smart"] = True
        context["announcements"] = (
            Announcement.for_timetables().on_date(wanted_day).for_person(person)
        )
        context["week_announcements"] = (
            Announcement.for_timetables()
            .within_days(wanted_week[0], wanted_week[6])
            .for_person(person)
        )
        context["weekdays"] = build_weekdays(TimePeriod.WEEKDAY_CHOICES, wanted_week)
        context["weekdays_short"] = build_weekdays(TimePeriod.WEEKDAY_CHOICES_SHORT, wanted_week)
        context["url_prev"], context["url_next"] = TimePeriod.get_prev_next_by_day(
            wanted_day, "my_timetable_by_date"
        )

        return render(request, "chronos/my_timetable.html", context)
    else:
        return redirect("all_timetables")


@permission_required("chronos.view_timetable", fn=get_el_by_pk)
def timetable(
    request: HttpRequest,
    type_: str,
    pk: int,
    year: Optional[int] = None,
    week: Optional[int] = None,
    regular: Optional[str] = None,
) -> HttpResponse:
    """View a selected timetable for a person, group or room."""
    context = {}

    is_smart = regular != "regular"

    el = get_el_by_pk(request, type_, pk, prefetch=True)

    if type(el) == HttpResponseNotFound:
        return HttpResponseNotFound()

    type_ = TimetableType.from_string(type_)

    if year and week:
        wanted_week = CalendarWeek(year=year, week=week)
    else:
        wanted_week = TimePeriod.get_relevant_week_from_datetime()

    # Build timetable
    timetable = build_timetable(type_, el, wanted_week)
    context["timetable"] = timetable

    # Add time periods
    context["periods"] = TimePeriod.get_times_dict()

    # Build lists with weekdays and corresponding dates (long and short variant)
    context["weekdays"] = build_weekdays(TimePeriod.WEEKDAY_CHOICES, wanted_week)
    context["weekdays_short"] = build_weekdays(TimePeriod.WEEKDAY_CHOICES_SHORT, wanted_week)

    context["weeks"] = get_weeks_for_year(year=wanted_week.year)
    context["week"] = wanted_week
    context["type"] = type_
    context["pk"] = pk
    context["el"] = el
    context["smart"] = is_smart
    context["week_select"] = {
        "year": wanted_week.year,
        "dest": reverse(
            "timetable_by_week", args=[type_.value, pk, wanted_week.year, wanted_week.week],
        )
        .replace(str(wanted_week.year), "year")
        .replace(str(wanted_week.week), "cw"),
    }

    if is_smart:
        start = wanted_week[TimePeriod.weekday_min]
        stop = wanted_week[TimePeriod.weekday_max]
        context["announcements"] = (
            Announcement.for_timetables().relevant_for(el).within_days(start, stop)
        )

    week_prev = wanted_week - 1
    week_next = wanted_week + 1

    context["url_prev"] = reverse(
        "timetable_by_week", args=[type_.value, pk, week_prev.year, week_prev.week]
    )
    context["url_next"] = reverse(
        "timetable_by_week", args=[type_.value, pk, week_next.year, week_next.week]
    )

    return render(request, "chronos/timetable.html", context)


@permission_required("chronos.view_lessons_day")
def lessons_day(
    request: HttpRequest,
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
) -> HttpResponse:
    """View all lessons taking place on a specified day."""
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
        "dest": reverse("lessons_day"),
    }

    context["url_prev"], context["url_next"] = TimePeriod.get_prev_next_by_day(
        wanted_day, "lessons_day_by_date"
    )

    return render(request, "chronos/lessons_day.html", context)


@never_cache
@permission_required("chronos.edit_substitution", fn=get_substitution_by_id)
def edit_substitution(request: HttpRequest, id_: int, week: int) -> HttpResponse:
    """View a form to edit a substitution lessen."""
    context = {}

    lesson_period = get_object_or_404(LessonPeriod, pk=id_)
    wanted_week = lesson_period.lesson.get_calendar_week(week)

    lesson_substitution = get_substitution_by_id(request, id_, week)

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
            return redirect("lessons_day_by_date", year=date.year, month=date.month, day=date.day)

    context["edit_substitution_form"] = edit_substitution_form

    return render(request, "chronos/edit_substitution.html", context)


@permission_required("chronos.delete_substitution", fn=get_substitution_by_id)
def delete_substitution(request: HttpRequest, id_: int, week: int) -> HttpResponse:
    """Delete a substitution lesson.

    Redirects back to substition list on success.
    """
    lesson_period = get_object_or_404(LessonPeriod, pk=id_)
    wanted_week = lesson_period.lesson.get_calendar_week(week)

    get_substitution_by_id(request, id_, week).delete()

    messages.success(request, _("The substitution has been deleted."))

    date = wanted_week[lesson_period.period.weekday]
    return redirect("lessons_day_by_date", year=date.year, month=date.month, day=date.day)


@permission_required("chronos.view_substitutions")
def substitutions(
    request: HttpRequest,
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    is_print: bool = False,
) -> HttpResponse:
    """View all substitutions on a spcified day."""
    context = {}

    if day:
        wanted_day = timezone.datetime(year=year, month=month, day=day).date()
        wanted_day = TimePeriod.get_next_relevant_day(wanted_day)
    else:
        wanted_day = TimePeriod.get_next_relevant_day(timezone.now().date(), datetime.now().time())

    day_number = get_site_preferences()["chronos__substitutions_print_number_of_days"]
    day_contexts = {}

    if is_print:
        next_day = wanted_day
        for i in range(day_number):
            day_contexts[next_day] = {"day": next_day}
            next_day = TimePeriod.get_next_relevant_day(next_day + timedelta(days=1))
    else:
        day_contexts = {wanted_day: {"day": wanted_day}}

    for day in day_contexts:
        subs = build_substitutions_list(day)
        day_contexts[day]["substitutions"] = subs

        day_contexts[day]["announcements"] = (
            Announcement.for_timetables().on_date(day).filter(show_in_timetables=True)
        )

        if get_site_preferences()["chronos__substitutions_show_header_box"]:
            subs = LessonSubstitution.objects.on_day(day).order_by(
                "lesson_period__lesson__groups", "lesson_period__period"
            )
            absences = Absence.objects.on_day(day)
            day_contexts[day]["absent_teachers"] = absences.absent_teachers()
            day_contexts[day]["absent_groups"] = absences.absent_groups()
            day_contexts[day]["affected_teachers"] = subs.affected_teachers()
            affected_groups = subs.affected_groups()
            if get_site_preferences()["chronos__affected_groups_parent_groups"]:
                groups_with_parent_groups = affected_groups.filter(parent_groups__isnull=False)
                groups_without_parent_groups = affected_groups.filter(parent_groups__isnull=True)
                affected_groups = Group.objects.filter(
                    Q(child_groups__pk__in=groups_with_parent_groups.values_list("pk", flat=True))
                    | Q(pk__in=groups_without_parent_groups.values_list("pk", flat=True))
                ).distinct()
            day_contexts[day]["affected_groups"] = affected_groups

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
