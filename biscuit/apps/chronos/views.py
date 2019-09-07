from datetime import date, datetime, timedelta
from collections import OrderedDict
from typing import Optional

from django.contrib.auth.decorators import login_required
from django.db.models import Max, Min, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.urls import reverse
from django.utils.translation import ugettext as _

from django_tables2 import RequestConfig

from biscuit.core.decorators import admin_required
from biscuit.core.util import messages

from .forms import SelectForm, LessonSubstitutionForm
from .models import LessonPeriod, TimePeriod, LessonSubstitution
from .util import current_week, week_weekday_from_date, week_days
from .tables import LessonsTable


@login_required
@cache_page(60 * 60 * 12)
def timetable(request: HttpRequest, week: Optional[int] = None) -> HttpResponse:
    context = {}

    wanted_week = week or current_week()

    lesson_periods = LessonPeriod.objects.filter(
        lesson__date_start__lte=week_days(wanted_week)[0],
        lesson__date_end__gte=week_days(wanted_week)[-1]
    ).select_related(
        'lesson', 'lesson__subject', 'period', 'room'
    ).prefetch_related(
        'lesson__groups', 'lesson__teachers', 'substitutions'
    ).extra(
        select={'_week': wanted_week}
    )

    if request.GET.get('group', None) or request.GET.get('teacher', None) or request.GET.get('room', None):
        # Incrementally filter lesson periods by GET parameters
        if 'group' in request.GET and request.GET['group']:
            lesson_periods = lesson_periods.filter(
                Q(lesson__groups__pk=int(request.GET['group'])) | Q(lesson__groups__parent_groups__pk=int(request.GET['group'])))
        if 'teacher' in request.GET and request.GET['teacher']:
            lesson_periods = lesson_periods.filter(
                Q(substitutions__teachers__pk=int(request.GET['teacher']), substitutions__week=wanted_week) | Q(lesson__teachers__pk=int(request.GET['teacher'])))
        if 'room' in request.GET and request.GET['room']:
            lesson_periods = lesson_periods.filter(
                room__pk=int(request.GET['room']))
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

    context['lesson_periods'] = OrderedDict(sorted(per_day.items()))
    context['periods'] = TimePeriod.get_times_dict()
    context['weekdays'] = dict(TimePeriod.WEEKDAY_CHOICES)
    context['week'] = wanted_week
    context['week_prev'] = wanted_week - 1
    context['week_next'] = wanted_week + 1
    context['select_form'] = select_form

    return render(request, 'chronos/tt_week.html', context)


@login_required
def lessons_day(request: HttpRequest, when: Optional[str] = None) -> HttpResponse:
    context = {}

    if when:
        day = datetime.strptime(when, '%Y-%m-%d').date()
    else:
        day = date.today()

    week, weekday = week_weekday_from_date(day)

    # Get lessons
    lesson_periods = LessonPeriod.objects.filter(
        lesson__date_start__lte=day, lesson__date_end__gte=day,
        period__weekday=weekday
    )

    # Build table
    lessons_table = LessonsTable(lesson_periods.extra(select={'_week': week}).all())
    RequestConfig(request).configure(lessons_table)

    context['lessons_table'] = lessons_table
    context['day'] = day
    context['day_prev'] = day + timedelta(days=-1)
    context['day_next'] = day + timedelta(days=1)
    context['week'] = week
    context['lesson_periods'] = lesson_periods

    return render(request, 'chronos/lessons_day.html', context)


@admin_required
def edit_substitution(request: HttpRequest, id_: int, week: int) -> HttpResponse:
    context = {}

    lesson_period = get_object_or_404(LessonPeriod, pk=id_)

    lesson_substitution = LessonSubstitution.objects.filter(
        week=week, lesson_period=lesson_period).first()
    if lesson_substitution:
        edit_substitution_form = LessonSubstitutionForm(
            request.POST or None, instance=lesson_substitution)
    else:
        edit_substitution_form = LessonSubstitutionForm(
            request.POST or None, initial={'week': week, 'lesson_period': lesson_period})

    context['substitution'] = lesson_substitution

    if request.method == 'POST':
        if edit_substitution_form.is_valid():
            edit_substitution_form.save(commit=True)

            messages.success(request, _('The substitution has been saved.'))
            return redirect('lessons_day_by_date', when=week_days(week)[lesson_period.period.weekday - 1].strftime('%Y-%m-%d'))

    context['edit_substitution_form'] = edit_substitution_form

    return render(request, 'chronos/edit_substitution.html', context)


@admin_required
def delete_substitution(request: HttpRequest, id_: int, week: int) -> HttpResponse:
    context = {}

    LessonSubstitution.objects.filter(
        week=week, lesson_period__id=id_
    ).delete()

    messages.success(request, _('The substitution has been deleted.'))
    return redirect('lessons_day_by_date', when=week_days(week)[lesson_period.period.weekday - 1].strftime('%Y-%m-%d'))
