from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from biscuit.core.decorators import admin_required

from .models import LessonPeriod


@login_required
@admin_required
def timetable(request):
    context = {}

    lesson_periods = LessonPeriod.objects.all()

    if 'group' in request.GET:
        lesson_periods = lesson_periods.filter(
            lesson__groups__pk__contains=int(request.GET('group')))
    if 'teacher' in request.GET:
        lesson_periods = lesson_periods.filter(
            lesson__teachers__pk__contains=int(request.GET('teacher')))
    if 'room' in request.GET:
        lesson_periods = lesson_periods.filter(
            room__pk=int(request.GET('room')))

    per_day = {}
    for lesson_period in lesson_periods:
        for period in lesson_period.periods.all():
            per_day.setdefault(period.weekday, []).append(lesson_period)

    context['lesson_periods'] = per_day

    return render(request, 'chronos/tt_week.html', context)
