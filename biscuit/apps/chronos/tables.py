from typing import Optional

from django.utils.translation import ugettext_lazy as _
import django_tables2 as tables
from django_tables2.utils import A

from .models import LessonPeriod


def _css_class_from_lesson_state(record: Optional[LessonPeriod] = None, table: Optional[LessonTable] = None) -> str:
    if record.get_substitution(table._week):
        return 'table-warning'
    else:
        return ''


class LessonsTable(tables.Table):
    class Meta:
        attrs = {'class': 'table table-striped table-bordered table-hover table-responsive-xl'}
        row_attrs = {'class': _css_class_from_lesson_state}

    period__period = tables.LinkColumn('edit_substitution_by_id', args=[A('id')], accessor='period.period')
    lesson__groups = tables.LinkColumn('edit_substitution_by_id', args=[A('id')], accessor='lesson.group_names')
    lesson__teachers = tables.LinkColumn('edit_substitution_by_id', args=[A('id')], accessor='lesson.teacher_names')
    lesson__subject = tables.LinkColumn('edit_substitution_by_id', args=[A('id')], accessor='lesson.subject')
    room = tables.LinkColumn('edit_substitution_by_id', args=[A('id')], accessor='room')

    def __init__(self, week, *args, **kwargs):
        self._week = week
        super().__init__(*args, **kwargs)
