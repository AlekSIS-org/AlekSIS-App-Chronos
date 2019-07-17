from collections import OrderedDict

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from biscuit.apps.cambro.models import Room
from biscuit.core.decorators import admin_required
from biscuit.core.models import Group, Person

from .models import LessonPeriod


@login_required
@admin_required
def timetable(request):
    context = {}

    lesson_periods = LessonPeriod.objects.all()
    filter_descs = []

    if 'group' in request.GET:
        lesson_periods = lesson_periods.filter(
            lesson__groups__pk__contains=int(request.GET['group']))
        filter_descs.append(_('Group: %s') % Group.objects.get(
            pk=int(request.GET['group'])).name)
    if 'teacher' in request.GET:
        lesson_periods = lesson_periods.filter(
            lesson__teachers__pk__contains=int(request.GET['teacher']))
        filter_descs.append(_('Teacher: %s') % Person.objects.get(
            pk=int(request.GET['teacher'])).name)
    if 'room' in request.GET:
        lesson_periods = lesson_periods.filter(
            room__pk=int(request.GET['room']))
        filter_descs.append(_('Room: %s') % Room.objects.get(
            pk=int(request.GET['room'])).name)

    per_day = {}
    for lesson_period in lesson_periods:
        per_day.setdefault(lesson_period.period.weekday,
                           []).append(lesson_period)

    context['lesson_periods'] = OrderedDict(sorted(per_day.items()))
    context['filter_descs'] = ', '.join(filter_descs)

    return render(request, 'chronos/tt_week.html', context)
