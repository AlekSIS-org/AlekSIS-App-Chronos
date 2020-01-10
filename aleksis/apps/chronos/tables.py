from __future__ import annotations

from typing import Optional

from django.utils.translation import ugettext_lazy as _

import django_tables2 as tables
from django_tables2.utils import A

from .models import LessonPeriod


def _css_class_from_lesson_state(
    record: Optional[LessonPeriod] = None, table: Optional[LessonsTable] = None
) -> str:
    if record.get_substitution(record._week):
        if record.get_substitution(record._week).cancelled:
            return "table-danger"
        else:
            return "table-warning"
    else:
        return ""


class LessonsTable(tables.Table):
    class Meta:
        attrs = {"class": "highlight"}
        row_attrs = {"class": _css_class_from_lesson_state}

    period__period = tables.Column(accessor="period__period")
    lesson__groups = tables.Column(accessor="lesson__group_names", verbose_name=_("Groups"))
    lesson__teachers = tables.Column(accessor="lesson__teacher_names", verbose_name=_("Teachers"))
    lesson__subject = tables.Column(accessor="lesson__subject")
    room = tables.Column(accessor="room")
    edit_substitution = tables.LinkColumn(
        "edit_substitution", args=[A("id"), A("_week")], text=_("Substitution")
    )


class SubstitutionsTable(tables.Table):
    class Meta:
        attrs = {"class": "highlight"}

    lesson_period = tables.Column(verbose_name=_("Lesson"))
    lesson__groups = tables.Column(
        accessor="lesson_period__lesson__group_names", verbose_name=_("Groups")
    )
    lesson__teachers = tables.Column(
        accessor="lesson_period__get_teacher_names", verbose_name=_("Teachers")
    )
    lesson__subject = tables.Column(accessor="subject")
    room = tables.Column(accessor="room")
    cancelled = tables.BooleanColumn(accessor="cancelled", verbose_name=_("Cancelled"))
