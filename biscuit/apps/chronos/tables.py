from django.utils.translation import ugettext_lazy as _
import django_tables2 as tables
from django_tables2.utils import A


def _css_class_from_lesson_state(record: Optional[LessonPeriod] = None, table: Optional[LessonTable] = None) -> str:
    if record.get_substitution(table._week):
        return 'table-warning'
    else:
        return ''


class LessonsTable(tables.Table):
    class Meta:
        attrs = {'class': 'table table-striped table-bordered table-hover table-responsive-xl'}

    period__period = tables.Column(accessor='period.period')
    lesson__groups = tables.Column(accessor='lesson.group_names')
    lesson__teachers = tables.Column(accessor='lesson.teacher_names')
    lesson__subject = tables.Column(accessor='lesson.subject')
    room = tables.Column(accessor='room')

    def __init__(self, week, *args, **kwargs):
        self._week = week
        super().__init__(*args, **kwargs)

    class Meta:
        row_attrs = {'class': _css_class_from_lesson_state}
