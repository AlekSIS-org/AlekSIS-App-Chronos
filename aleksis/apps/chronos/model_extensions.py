from biscuit.core.models import Person

from .models import Lesson, LessonPeriod


@Person.property
def lessons_as_participant(self):
    """ Return a `QuerySet` containing all `Lesson`s this person
    participates in (as student).

    .. note:: Only available when BiscuIT-App-Chronos is installed.

    :Date: 2019-11-07
    :Authors:
        - Dominik George <dominik.george@teckids.org>
    """

    return Lesson.objects.filter(groups__members=self)


@Person.property
def lesson_periods_as_participant(self):
    """ Return a `QuerySet` containing all `LessonPeriod`s this person
    participates in (as student).

    .. note:: Only available when BiscuIT-App-Chronos is installed.

    :Date: 2019-11-07
    :Authors:
        - Dominik George <dominik.george@teckids.org>
    """

    return LessonPeriod.objects.filter(lesson__groups__members=self)


@Person.property
def lesson_periods_as_teacher(self):
    """ Return a `QuerySet` containing all `Lesson`s this person
    gives (as teacher).

    .. note:: Only available when BiscuIT-App-Chronos is installed.

    :Date: 2019-11-07
    :Authors:
        - Dominik George <dominik.george@teckids.org>
    """

    return LessonPeriod.objects.filter(lesson__teachers=self)
