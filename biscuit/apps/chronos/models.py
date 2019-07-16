from django.core import validators
from django.db import models
from django.utils.translation import ugettext_lazy as _


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

    def __str__(self):
        return '%s, %d. period (%s - %s)' % (self.weekday, self.period, self.time_start, self.time_end)


class Subject(models.Model):
    abbrev = models.CharField(verbose_name=_(
        'Abbreviation of subject in timetable'), max_length=10)
    name = models.CharField(verbose_name=_(
        'Long name of subject'), max_length=30)

    colour_fg = models.CharField(verbose_name=_('Foreground colour in timetable'), blank=True, validators=[
                                 validators.RegexValidator(r'#[0-9A-F]{6}')], max_length=7)
    colour_bg = models.CharField(verbose_name=_('Background colour in timetable'), blank=True, validators=[
                                 validators.RegexValidator(r'#[0-9A-F]{6}')], max_length=7)

    def __str__(self):
        return '%s - %s' % (self.abbrev, self.name)


class Lesson(models.Model):
    subject = models.ForeignKey(
        'Subject', on_delete=models.CASCADE, related_name='lessons')
    teachers = models.ManyToManyField('core.Person', related_name='lessons')
    periods = models.ManyToManyField('TimePeriod', related_name='lessons')
    groups = models.ManyToManyField('core.Group', related_name='lessons')

    date_start = models.DateField(verbose_name=_(
        'Effective start date of lesson'), null=True)
    date_end = models.DateField(verbose_name=_(
        'Effective end date of lesson'), null=True)
