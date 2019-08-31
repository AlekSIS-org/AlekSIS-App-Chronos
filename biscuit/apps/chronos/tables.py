from django.utils.translation import ugettext_lazy as _
import django_tables2 as tables
from django_tables2.utils import A

class LessonsTable(tables.Table):
    class Meta:
        attrs = {'class': 'table table-striped table-bordered table-hover table-responsive-xl'}

    period__period = tables.Column()
    lesson__groups = tables.Column()
    lesson_teachers = tables.Column()
    lesson_subject = tables.Column()
    room = tables.Column()
