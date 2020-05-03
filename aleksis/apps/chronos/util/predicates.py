from django.contrib.auth.models import User
from django.db.models import Model

from rules import predicate

from aleksis.apps.chronos.models import Room
from aleksis.core.models import Group, Person


@predicate
def has_timetable_perm(user: User, obj: Model) -> bool:
    """Predicate which checks whether the user is allowed to access the requested timetable."""
    if obj.model is Group:
        return obj in user.person.member_of
    elif obj.model is Person:
        return user.person == obj
    elif obj.model is Room:
        return True
    else:
        return False
