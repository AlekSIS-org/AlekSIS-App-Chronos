from aleksis.core.models import Person

from .models import Lesson, LessonPeriod


@Person.property
def is_teacher(self):
    """ Check if the user has lessons as a teacher """

    return Lesson.objects.filter(teachers=self).exists()


@Person.property
def lessons_as_participant(self):
    """ Return a `QuerySet` containing all `Lesson`s this person
    participates in (as student).

    .. note:: Only available when AlekSIS-App-Chronos is installed.

    :Date: 2019-11-07
    :Authors:
        - Dominik George <dominik.george@teckids.org>
    """

    return Lesson.objects.filter(groups__members=self)


@Person.property
def lesson_periods_as_participant(self):
    """ Return a `QuerySet` containing all `LessonPeriod`s this person
    participates in (as student).

    .. note:: Only available when AlekSIS-App-Chronos is installed.

    :Date: 2019-11-07
    :Authors:
        - Dominik George <dominik.george@teckids.org>
    """

    return LessonPeriod.objects.filter(lesson__groups__members=self)


@Person.property
def lesson_periods_as_teacher(self):
    """ Return a `QuerySet` containing all `Lesson`s this person
    gives (as teacher).

    .. note:: Only available when AlekSIS-App-Chronos is installed.

    :Date: 2019-11-07
    :Authors:
        - Dominik George <dominik.george@teckids.org>
    """

    return LessonPeriod.objects.filter(lesson__teachers=self)
