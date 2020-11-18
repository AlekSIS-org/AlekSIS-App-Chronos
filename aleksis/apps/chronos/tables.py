from __future__ import annotations

from typing import Optional

from django.utils.translation import gettext_lazy as _

import django_tables2 as tables
from django_tables2.utils import A

from .models import LessonPeriod


def _css_class_from_lesson_state(
    record: Optional[LessonPeriod] = None, table: Optional[LessonsTable] = None
) -> str:
    """Return CSS class depending on lesson state."""
    if record.get_substitution():
        if record.get_substitution().cancelled:
            return "success"
        else:
            return "warning"
    else:
        return ""


class LessonsTable(tables.Table):
    """Table for daily lessons and management of substitutions."""

    class Meta:
        attrs = {"class": "highlight"}
        row_attrs = {"class": _css_class_from_lesson_state}

    period__period = tables.Column(accessor="period__period")
    lesson__groups = tables.Column(accessor="lesson__group_names", verbose_name=_("Groups"))
    lesson__teachers = tables.Column(accessor="lesson__teacher_names", verbose_name=_("Teachers"))
    lesson__subject = tables.Column(accessor="lesson__subject")
    room = tables.Column(accessor="room")
    edit_substitution = tables.LinkColumn(
        "edit_substitution",
        args=[A("id"), A("_week")],
        text=_("Substitution"),
        attrs={"a": {"class": "btn-flat waves-effect waves-orange"}},
        verbose_name=_("Manage substitution"),
    )
