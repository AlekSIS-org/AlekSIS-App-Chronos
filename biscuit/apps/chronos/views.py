from datetime import date, datetime, timedelta
from collections import OrderedDict
from typing import Optional

from django.contrib.auth.decorators import login_required
from django.db.models import Max, Min
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext as _

from django_tables2 import RequestConfig

from biscuit.core.decorators import admin_required
from biscuit.core.util import messages

from .forms import SelectForm, LessonSubstitutionForm
from .models import LessonPeriod, TimePeriod, LessonSubstitution
from .util import CalendarWeek
from .tables import LessonsTable


@login_required
def timetable(request: HttpRequest, year: Optional[int] = None, week: Optional[int] = None) -> HttpResponse:
    context = {}

    if year and week:
        wanted_week = CalendarWeek(year=year, week=week)
    else:
        wanted_week = CalendarWeek()

    lesson_periods = LessonPeriod.objects.in_week(wanted_week)

    # Incrementally filter lesson periods by GET parameters
    if request.GET.get('group', None) or request.GET.get('teacher', None) or request.GET.get('room', None):
        lesson_periods = lesson_periods.filter_from_query(request.GET)
    else:
        # Redirect to a selected view if no filter provided
        if request.user.person:
            if request.user.person.primary_group:
                return redirect(reverse('timetable') + '?group=%d' % request.user.person.primary_group.pk)
            elif lesson_periods.filter(lesson__teachers=request.user.person).exists():
                return redirect(reverse('timetable') + '?teacher=%d' % request.user.person.pk)

    # Regroup lesson periods per weekday
    per_day = {}
    for lesson_period in lesson_periods:
        per_day.setdefault(lesson_period.period.weekday,
                           {})[lesson_period.period.period] = lesson_period

    # Determine overall first and last day and period
    min_max = TimePeriod.objects.aggregate(
        Min('period'), Max('period'),
        Min('weekday'), Max('weekday'))

    # Fill in empty lessons
    for weekday_num in range(min_max.get('weekday__min', 0),
                             min_max.get('weekday__max', 6) + 1):
        # Fill in empty weekdays
        if weekday_num not in per_day.keys():
            per_day[weekday_num] = {}

        # Fill in empty lessons on this workday
        for period_num in range(min_max.get('period__min', 1),
                                min_max.get('period__max', 7) + 1):
            if period_num not in per_day[weekday_num].keys():
                per_day[weekday_num][period_num] = None

        # Order this weekday by periods
        per_day[weekday_num] = OrderedDict(
            sorted(per_day[weekday_num].items()))

    # Add a form to filter the view
    select_form = SelectForm(request.GET or None)

    context['current_head'] = _('Timetable')
    context['lesson_periods'] = OrderedDict(sorted(per_day.items()))
    context['periods'] = TimePeriod.get_times_dict()
    context['weekdays'] = dict(TimePeriod.WEEKDAY_CHOICES)
    context['week'] = wanted_week
    context['select_form'] = select_form

    week_prev = wanted_week - 1
    week_next = wanted_week + 1
    context['url_prev'] = '%s?%s' % (reverse('timetable_by_week', args=[week_prev.year, week_prev.week]), request.GET.urlencode())
    context['url_next'] = '%s?%s' % (reverse('timetable_by_week', args=[week_next.year, week_next.week]), request.GET.urlencode())

    return render(request, 'chronos/tt_week.html', context)


@login_required
def lessons_day(request: HttpRequest, when: Optional[str] = None) -> HttpResponse:
    context = {}

    if when:
        day = datetime.strptime(when, '%Y-%m-%d').date()
    else:
        day = date.today()

    # Get lessons
    lesson_periods = LessonPeriod.objects.on_day(day)

    # Build table
    lessons_table = LessonsTable(lesson_periods.all())
    RequestConfig(request).configure(lessons_table)

    context['current_head'] = _('Lessons %s') % (day)
    context['lessons_table'] = lessons_table
    context['day'] = day
    context['lesson_periods'] = lesson_periods

    day_prev = day - timedelta(days=1)
    day_next = day + timedelta(days=1)
    context['url_prev'] = reverse('lessons_day_by_date', args=[day_prev.strftime('%Y-%m-%d')])
    context['url_next'] = reverse('lessons_day_by_date', args=[day_next.strftime('%Y-%m-%d')])

    return render(request, 'chronos/lessons_day.html', context)


@admin_required
def edit_substitution(request: HttpRequest, id_: int, week: int) -> HttpResponse:
    context = {}

    lesson_period = get_object_or_404(LessonPeriod, pk=id_)
    wanted_week = lesson_period.lesson.get_calendar_week(week)

    lesson_substitution = LessonSubstitution.objects.filter(
        week=wanted_week.week, lesson_period=lesson_period).first()
    if lesson_substitution:
        edit_substitution_form = LessonSubstitutionForm(
            request.POST or None, instance=lesson_substitution)
    else:
        edit_substitution_form = LessonSubstitutionForm(
            request.POST or None, initial={'week': wanted_week.week, 'lesson_period': lesson_period})

    context['substitution'] = lesson_substitution

    if request.method == 'POST':
        if edit_substitution_form.is_valid():
            edit_substitution_form.save(commit=True)

            messages.success(request, _('The substitution has been saved.'))
            return redirect('lessons_day_by_date', when=wanted_week[lesson_period.period.weekday - 1].strftime('%Y-%m-%d'))

    context['edit_substitution_form'] = edit_substitution_form

    return render(request, 'chronos/edit_substitution.html', context)


@admin_required
def delete_substitution(request: HttpRequest, id_: int, week: int) -> HttpResponse:
    context = {}

    lesson_period = get_object_or_404(LessonPeriod, pk=id_)
    wanted_week = lesson_period.lesson.get_calendar_week(week)

    LessonSubstitution.objects.filter(
        week=wanted_week.week, lesson_period=lesson_period
    ).delete()

    messages.success(request, _('The substitution has been deleted.'))
    return redirect('lessons_day_by_date', when=wanted_week[lesson_period.period.weekday - 1].strftime('%Y-%m-%d'))
