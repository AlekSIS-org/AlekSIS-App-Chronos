from typing import Optional

from django.http import HttpRequest, HttpResponseNotFound
from django.shortcuts import get_object_or_404

from aleksis.core.models import Person, Group
from ..managers import TimetableType
from ..models import LessonPeriod, LessonSubstitution, Room


def get_el_by_pk(
    request: HttpRequest,
    type_: str,
    pk: int,
    year: Optional[int] = None,
    week: Optional[int] = None,
    regular: Optional[str] = None,
):
    if type_ == TimetableType.GROUP.value:
        return get_object_or_404(Group, pk=pk)
    elif type_ == TimetableType.TEACHER.value:
        return get_object_or_404(Person, pk=pk)
    elif type_ == TimetableType.ROOM.value:
        return get_object_or_404(Room, pk=pk)
    else:
        return HttpResponseNotFound()


def get_substitution_by_id(request: HttpRequest, id_: int, week: int):
    lesson_period = get_object_or_404(LessonPeriod, pk=id_)
    wanted_week = lesson_period.lesson.get_calendar_week(week)

    return LessonSubstitution.objects.filter(
        week=wanted_week.week, lesson_period=lesson_period
    ).first()
