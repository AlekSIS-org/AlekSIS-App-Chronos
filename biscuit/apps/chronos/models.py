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
