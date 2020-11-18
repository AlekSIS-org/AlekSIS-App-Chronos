from datetime import date
from typing import Union

from django.db import models
from django.utils.translation import gettext as _

from calendarweek import CalendarWeek

from aleksis.apps.chronos.util.date import week_weekday_to_date
from aleksis.core.managers import CurrentSiteManagerWithoutMigrations
from aleksis.core.mixins import ExtensibleModel

from .managers import ValidityRangeRelatedQuerySet


class ValidityRangeRelatedExtensibleModel(ExtensibleModel):
    """Add relation to validity range."""

    objects = CurrentSiteManagerWithoutMigrations.from_queryset(ValidityRangeRelatedQuerySet)()

    validity = models.ForeignKey(
        "chronos.ValidityRange",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("Linked validity range"),
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class WeekRelatedMixin:
    @property
    def date(self) -> date:
        return week_weekday_to_date(self.calendar_week, self.lesson_period.period.weekday)

    @property
    def calendar_week(self) -> CalendarWeek:
        return CalendarWeek(week=self.week, year=self.year)


class WeekAnnotationMixin:
    @property
    def week(self) -> Union[CalendarWeek, None]:
        """Get annotated week as `CalendarWeek`.

        Defaults to `None` if no week is annotated.
        """
        if hasattr(self, "_week"):
            return CalendarWeek(week=self._week, year=self._year)
        else:
            return None
