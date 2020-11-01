from datetime import date
from typing import Optional, Union

from django.utils.translation import gettext_lazy as _

from jsonstore import BooleanField

from aleksis.core.models import Announcement, Group, Person

from .managers import TimetableType
from .models import Lesson, LessonPeriod, Subject


@Person.property_
def is_teacher(self):
    """Check if the user has lessons as a teacher."""
    return self.lesson_periods_as_teacher.exists()


@Person.property_
def timetable_type(self) -> Optional[TimetableType]:
    """Return which type of timetable this user has."""
    if self.is_teacher:
        return TimetableType.TEACHER
    elif self.primary_group:
        return TimetableType.GROUP
    else:
        return None


@Person.property_
def timetable_object(self) -> Optional[Union[Group, Person]]:
    """Return the object which has the user's timetable."""
    type_ = self.timetable_type

    if type_ == TimetableType.TEACHER:
        return self
    elif type_ == TimetableType.GROUP:
        return self.primary_group
    else:
        return None


@Person.property_
def lessons_as_participant(self):
    """Return a `QuerySet` containing all `Lesson`s this person participates in (as student).

    .. note:: Only available when AlekSIS-App-Chronos is installed.

    :Date: 2019-11-07
    :Authors:
        - Dominik George <dominik.george@teckids.org>
    """
    return Lesson.objects.filter(groups__members=self)


@Person.property_
def lesson_periods_as_participant(self):
    """Return a `QuerySet` containing all `LessonPeriod`s this person participates in (as student).

    .. note:: Only available when AlekSIS-App-Chronos is installed.

    :Date: 2019-11-07
    :Authors:
        - Dominik George <dominik.george@teckids.org>
    """
    return LessonPeriod.objects.filter(lesson__groups__members=self)


@Person.property_
def lesson_periods_as_teacher(self):
    """Return a `QuerySet` containing all `Lesson`s this person gives (as teacher).

    .. note:: Only available when AlekSIS-App-Chronos is installed.

    :Date: 2019-11-07
    :Authors:
        - Dominik George <dominik.george@teckids.org>
    """
    return LessonPeriod.objects.filter(lesson__teachers=self)


@Person.method
def daily_lessons(self, day: date):
    """Get all lessons of this person on the given day."""
    return LessonPeriod.objects.on_day(day).filter_from_person(self)


@Person.method
def next_lesson(self, lesson_period: "LessonPeriod", day: date) -> Union["LessonPeriod", None]:
    """Get next lesson of the person on the same day."""
    daily_lessons = self.daily_lessons(day)
    ids = list(daily_lessons.values_list("id", flat=True))
    index = ids.index(lesson_period.pk)

    if index + 1 < len(ids):
        return daily_lessons[index + 1]
    else:
        return None


@Person.method
def previous_lesson(self, lesson_period: "LessonPeriod", day: date) -> Union["LessonPeriod", None]:
    """Get previous lesson of the person on the same day."""
    daily_lessons = self.daily_lessons(day)
    ids = list(daily_lessons.values_list("id", flat=True))
    index = ids.index(lesson_period.pk)

    if index > 0:
        return daily_lessons[index - 1]
    else:
        return None


def for_timetables(cls):
    """Return all announcements that should be shown in timetable views."""
    return cls.objects.filter(show_in_timetables=True)


Announcement.class_method(for_timetables)
Announcement.field(
    show_in_timetables=BooleanField(
        verbose_name=_("Show announcement in timetable views?")
    )
)

Group.foreign_key("subject", Subject, related_name="groups")
