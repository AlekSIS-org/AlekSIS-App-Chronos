from datetime import datetime
from typing import Dict, Optional, List, Tuple

from django.core import validators
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .util import current_week

from biscuit.core.models import Person


class TimePeriod(models.Model):
    WEEKDAY_CHOICES = [
        (0, _('Sunday')),
        (1, _('Monday')),
        (2, _('Tuesday')),
        (3, _('Wednesday')),
        (4, _('Thursday')),
        (5, _('Friday')),
        (6, _('Saturday'))
    ]

    weekday = models.PositiveSmallIntegerField(verbose_name=_(
        'Week day'), choices=WEEKDAY_CHOICES)
    period = models.PositiveSmallIntegerField(
        verbose_name=_('Number of period'))

    time_start = models.TimeField(verbose_name=_('Time the period starts'))
    time_end = models.TimeField(verbose_name=_('Time the period ends'))

    def __str__(self) -> str:
        return '%s, %d. period (%s - %s)' % (self.weekday, self.period, self.time_start, self.time_end)

    @classmethod
    def get_times_dict(cls) -> Dict[int, Tuple[datetime, datetime]]:
        periods = {}
        for period in cls.objects.all():
            periods[period.period] = (period.time_start, period.time_end)

        return periods

    class Meta:
        unique_together = [['weekday', 'period']]
        ordering = ['weekday', 'period']


class Subject(models.Model):
    abbrev = models.CharField(verbose_name=_(
        'Abbreviation of subject in timetable'), max_length=10, unique=True)
    name = models.CharField(verbose_name=_(
        'Long name of subject'), max_length=30, unique=True)

    colour_fg = models.CharField(verbose_name=_('Foreground colour in timetable'), blank=True, validators=[
                                 validators.RegexValidator(r'#[0-9A-F]{6}')], max_length=7)
    colour_bg = models.CharField(verbose_name=_('Background colour in timetable'), blank=True, validators=[
                                 validators.RegexValidator(r'#[0-9A-F]{6}')], max_length=7)

    def __str__(self) -> str:
        return '%s - %s' % (self.abbrev, self.name)

    class Meta:
        ordering = ['name', 'abbrev']


class Room(models.Model):
    short_name = models.CharField(verbose_name=_(
        'Short name, e.g. room number'), max_length=10, unique=True)
    name = models.CharField(verbose_name=_('Long name'),
                            max_length=30, unique=True)

    def __str__(self) -> str:
        return '%s (%s)' % (self.name, self.short_name)

    class Meta:
        ordering = ['name', 'short_name']


class Lesson(models.Model):
    subject = models.ForeignKey(
        'Subject', on_delete=models.CASCADE, related_name='lessons')
    teachers = models.ManyToManyField('core.Person', related_name='lessons')
    periods = models.ManyToManyField(
        'TimePeriod', related_name='lessons', through='LessonPeriod')
    groups = models.ManyToManyField('core.Group', related_name='lessons')

    date_start = models.DateField(verbose_name=_(
        'Effective start date of lesson'), null=True)
    date_end = models.DateField(verbose_name=_(
        'Effective end date of lesson'), null=True)

    @property
    def teacher_names(self, sep: Optional[str] = ', ') -> str:
        return sep.join([teacher.full_name for teacher in self.teachers.all()])

    @property
    def group_names(self, sep: Optional[str] = ', ') -> str:
        return sep.join([group.short_name for group in self.groups.all()])

    class Meta:
        ordering = ['date_start']


class LessonSubstitution(models.Model):
    week = models.IntegerField(verbose_name=_('Week'),
                               default=current_week)

    lesson_period = models.ForeignKey(
        'LessonPeriod', models.CASCADE, 'substitutions')

    subject = models.ForeignKey(
        'Subject', on_delete=models.CASCADE,
        related_name='lesson_substitutions', null=True)
    teachers = models.ManyToManyField('core.Person',
                                      related_name='lesson_substitutions')
    room = models.ForeignKey('Room', models.CASCADE, null=True)

    class Meta:
        ordering = ['lesson_period__lesson__date_start', 'week',
                    'lesson_period__period__weekday', 'lesson_period__period__period']


class LessonPeriod(models.Model):
    lesson = models.ForeignKey('Lesson', models.CASCADE, related_name='lesson_periods')
    period = models.ForeignKey('TimePeriod', models.CASCADE, related_name='lesson_periods')

    room = models.ForeignKey('Room', models.CASCADE, null=True, related_name='lesson_periods')

    def get_substitution(self, week: Optional[int] = None) -> LessonSubstitution:
        wanted_week = week or current_week()
        return self.substitutions.filter(week=wanted_week).first()

    def get_subject(self) -> Optional[Subject]:
        if self.get_substitution():
            return self.get_substitution().subject
        else:
            return self.lesson.subject

    def get_teachers(self) -> models.query.QuerySet:
        if self.get_substitution():
            return self.get_substitution().teachers
        else:
            return self.lesson.teachers

    def get_room(self) -> Optional[Room]:
        if self.get_substitution():
            return self.get_substitution().room
        else:
            return self.room

    def get_groups(self) -> models.query.QuerySet:
        return self.lesson.groups

    def __str__(self) -> str:
        return '%s, %d' % (self.period.get_weekday_display(), self.period.period)

    class Meta:
        ordering = ['lesson__date_start', 'period__weekday', 'period__period']
