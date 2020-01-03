from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, Optional, Tuple, Union

from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.http.request import QueryDict
from django.utils.translation import ugettext_lazy as _

from aleksis.core.mixins import ExtensibleModel
from aleksis.core.models import Group, Person

from .util import CalendarWeek, week_weekday_from_date


class LessonPeriodManager(models.Manager):
    """ Manager adding specific methods to lesson periods. """

    def get_queryset(self):
        """ Ensures all related lesson data is loaded as well. """

        return (
            super()
            .get_queryset()
            .select_related("lesson", "lesson__subject", "period", "room")
            .prefetch_related("lesson__groups", "lesson__teachers", "substitutions")
        )


class LessonPeriodQuerySet(models.QuerySet):
    """ Overrides default QuerySet to add specific methods for lesson data. """

    def within_dates(self, start: date, end: date):
        """ Filter for all lessons within a date range. """

        return self.filter(lesson__date_start__lte=start, lesson__date_end__gte=end)

    def in_week(self, wanted_week: CalendarWeek):
        """ Filter for all lessons within a calendar week. """

        return self.within_dates(
            wanted_week[0] + timedelta(days=1) * (models.F("period__weekday") - 1),
            wanted_week[0] + timedelta(days=1) * (models.F("period__weekday") - 1),
        ).annotate_week(wanted_week)

    def on_day(self, day: date):
        """ Filter for all lessons on a certain day. """

        week, weekday = week_weekday_from_date(day)

        return self.within_dates(day, day).filter(period__weekday=weekday).annotate_week(week)

    def at_time(self, when: Optional[datetime] = None):
        """ Filter for the lessons taking place at a certain point in time. """

        now = when or datetime.now()
        week, weekday = week_weekday_from_date(now.date())

        return self.filter(
            lesson__date_start__lte=now.date(),
            lesson__date_end__gte=now.date(),
            period__weekday=now.isoweekday(),
            period__time_start__lte=now.time(),
            period__time_end__gte=now.time(),
        ).annotate_week(week)

    def filter_participant(self, person: Union[Person, int]):
        """ Filter for all lessons a participant (student) attends. """

        return self.filter(
            Q(lesson__groups__members=person) | Q(lesson__groups__parent_groups__members=person)
        )

    def filter_group(self, group: Union[Group, int]):
        """ Filter for all lessons a group (class) regularly attends. """

        return self.filter(Q(lesson__groups=group) | Q(lesson__groups__parent_groups=group))

    def filter_teacher(self, teacher: Union[Person, int]):
        """ Filter for all lessons given by a certain teacher. """

        return self.filter(
            Q(substitutions__teachers=teacher, substitutions__week=models.F("_week"))
            | Q(lesson__teachers=teacher)
        )

    def filter_room(self, room: Union[Room, int]):
        """ Filter for all lessons taking part in a certain room. """

        return self.filter(
            Q(substitutions__room=room, substitutions__week=models.F("_week")) | Q(room=room)
        )

    def annotate_week(self, week: Union[CalendarWeek, int]):
        """ Annotate all lessons in the QuerySet with the number of the provided calendar week. """

        if isinstance(week, CalendarWeek):
            week_num = week.week
        else:
            week_num = week

        return self.annotate(_week=models.Value(week_num, models.IntegerField()))

    def next(self, reference: LessonPeriod, offset: Optional[int] = 1) -> LessonPeriod:
        """ Get another lesson in an ordered set of lessons.

        By default, it returns the next lesson in the set. By passing the offset argument,
        the n-th next lesson can be selected. By passing a negative number, the n-th
        previous lesson can be selected.
        """

        index = list(self.values_list("id", flat=True)).index(reference.id)

        next_index = index + offset
        if next_index > self.count() - 1:
            next_index %= self.count()
            week = reference._week + 1
        else:
            week = reference._week

        return self.annotate_week(week).all()[next_index]

    def filter_from_query(self, query_data: QueryDict):
        """ Apply all filters from a GET or POST query.

        This method expects a QueryDict, like the GET or POST attribute of a Request
        object, that contains one or more of the keys group, teacher or room.

        All three fields are filtered, in order.
        """

        if query_data.get("group", None):
            return self.filter_group(int(query_data["group"]))
        if query_data.get("teacher", None):
            return self.filter_teacher(int(query_data["teacher"]))
        if query_data.get("room", None):
            return self.filter_room(int(query_data["room"]))


class TimePeriod(models.Model):
    WEEKDAY_CHOICES = [
        (0, _("Sunday")),
        (1, _("Monday")),
        (2, _("Tuesday")),
        (3, _("Wednesday")),
        (4, _("Thursday")),
        (5, _("Friday")),
        (6, _("Saturday")),
    ]

    weekday = models.PositiveSmallIntegerField(verbose_name=_("Week day"), choices=WEEKDAY_CHOICES)
    period = models.PositiveSmallIntegerField(verbose_name=_("Number of period"))

    time_start = models.TimeField(verbose_name=_("Time the period starts"))
    time_end = models.TimeField(verbose_name=_("Time the period ends"))

    def __str__(self) -> str:
        return "%s, %d. period (%s - %s)" % (
            self.weekday,
            self.period,
            self.time_start,
            self.time_end,
        )

    @classmethod
    def get_times_dict(cls) -> Dict[int, Tuple[datetime, datetime]]:
        periods = {}
        for period in cls.objects.all():
            periods[period.period] = (period.time_start, period.time_end)

        return periods

    def get_date(self, week: Optional[Union[CalendarWeek, int]] = None) -> date:
        if isinstance(week, CalendarWeek):
            wanted_week = week
        else:
            year = date.today().year
            week_number = week or getattr(self, "_week", None) or CalendarWeek().week

            if week_number < self.school.current_term.date_start.isocalendar()[1]:
                year += 1

            wanted_week = CalendarWeek(year=year, week=week_number)

        return wanted_week[self.weekday - 1]

    class Meta:
        unique_together = [["weekday", "period"]]
        ordering = ["weekday", "period"]
        indexes = [models.Index(fields=["time_start", "time_end"])]


class Subject(models.Model):
    abbrev = models.CharField(
        verbose_name=_("Abbreviation of subject in timetable"), max_length=10, unique=True,
    )
    name = models.CharField(verbose_name=_("Long name of subject"), max_length=30, unique=True)

    colour_fg = models.CharField(
        verbose_name=_("Foreground colour in timetable"),
        blank=True,
        validators=[validators.RegexValidator(r"#[0-9A-F]{6}")],
        max_length=7,
    )
    colour_bg = models.CharField(
        verbose_name=_("Background colour in timetable"),
        blank=True,
        validators=[validators.RegexValidator(r"#[0-9A-F]{6}")],
        max_length=7,
    )

    def __str__(self) -> str:
        return "%s - %s" % (self.abbrev, self.name)

    class Meta:
        ordering = ["name", "abbrev"]


class Room(models.Model):
    short_name = models.CharField(
        verbose_name=_("Short name, e.g. room number"), max_length=10, unique=True
    )
    name = models.CharField(verbose_name=_("Long name"), max_length=30)

    def __str__(self) -> str:
        return "%s (%s)" % (self.name, self.short_name)

    class Meta:
        ordering = ["name", "short_name"]


class Lesson(models.Model):
    subject = models.ForeignKey("Subject", on_delete=models.CASCADE, related_name="lessons")
    teachers = models.ManyToManyField("core.Person", related_name="lessons_as_teacher")
    periods = models.ManyToManyField("TimePeriod", related_name="lessons", through="LessonPeriod")
    groups = models.ManyToManyField("core.Group", related_name="lessons")

    date_start = models.DateField(verbose_name=_("Effective start date of lesson"), null=True)
    date_end = models.DateField(verbose_name=_("Effective end date of lesson"), null=True)

    @property
    def teacher_names(self, sep: Optional[str] = ", ") -> str:
        return sep.join([teacher.full_name for teacher in self.teachers.all()])

    @property
    def group_names(self, sep: Optional[str] = ", ") -> str:
        return sep.join([group.short_name for group in self.groups.all()])

    def get_calendar_week(self, week: int):
        year = self.date_start.year
        if week < int(self.date_start.strftime("%V")):
            year += 1

        return CalendarWeek(year=year, week=week)

    class Meta:
        ordering = ["date_start"]
        indexes = [models.Index(fields=["date_start", "date_end"])]


class LessonSubstitution(models.Model):
    week = models.IntegerField(verbose_name=_("Week"), default=CalendarWeek.current_week)

    lesson_period = models.ForeignKey("LessonPeriod", models.CASCADE, "substitutions")

    subject = models.ForeignKey(
        "Subject",
        on_delete=models.CASCADE,
        related_name="lesson_substitutions",
        null=True,
        blank=True,
        verbose_name=_("Subject"),
    )
    teachers = models.ManyToManyField(
        "core.Person", related_name="lesson_substitutions", blank=True
    )
    room = models.ForeignKey("Room", models.CASCADE, null=True, blank=True, verbose_name=_("Room"))

    cancelled = models.BooleanField(default=False)

    def clean(self) -> None:
        if self.subject and self.cancelled:
            raise ValidationError(_("Lessons can only be either substituted or cancelled."))

    class Meta:
        unique_together = [["lesson_period", "week"]]
        ordering = [
            "lesson_period__lesson__date_start",
            "week",
            "lesson_period__period__weekday",
            "lesson_period__period__period",
        ]
        constraints = [
            models.CheckConstraint(
                check=~Q(cancelled=True, subject__isnull=False),
                name="either_substituted_or_cancelled",
            )
        ]


class LessonPeriod(models.Model, ExtensibleModel):
    objects = LessonPeriodManager.from_queryset(LessonPeriodQuerySet)()

    lesson = models.ForeignKey("Lesson", models.CASCADE, related_name="lesson_periods")
    period = models.ForeignKey("TimePeriod", models.CASCADE, related_name="lesson_periods")

    room = models.ForeignKey("Room", models.CASCADE, null=True, related_name="lesson_periods")

    def get_substitution(self, week: Optional[int] = None) -> LessonSubstitution:
        wanted_week = week or getattr(self, "_week", None) or CalendarWeek().week

        # We iterate over all substitutions because this can make use of
        # prefetching when this model is loaded from outside, in contrast
        # to .filter()
        for substitution in self.substitutions.all():
            if substitution.week == wanted_week:
                return substitution
        return None

    def get_subject(self) -> Optional[Subject]:
        if self.get_substitution() and self.get_substitution().subject:
            return self.get_substitution().subject
        else:
            return self.lesson.subject

    def get_teachers(self) -> models.query.QuerySet:
        if self.get_substitution():
            return self.get_substitution().teachers
        else:
            return self.lesson.teachers

    def get_room(self) -> Optional[Room]:
        if self.get_substitution() and self.get_substitution().room:
            return self.get_substitution().room
        else:
            return self.room

    def get_teacher_names(self, sep: Optional[str] = ", ") -> str:
        return sep.join([teacher.full_name for teacher in self.get_teachers().all()])

    def get_groups(self) -> models.query.QuerySet:
        return self.lesson.groups

    def __str__(self) -> str:
        return "%s, %d., %s, %s" % (
            self.period.get_weekday_display(),
            self.period.period,
            ", ".join(list(self.lesson.groups.values_list("short_name", flat=True))),
            self.lesson.subject.name,
        )

    class Meta:
        ordering = ["lesson__date_start", "period__weekday", "period__period"]
        indexes = [models.Index(fields=["lesson", "period"])]