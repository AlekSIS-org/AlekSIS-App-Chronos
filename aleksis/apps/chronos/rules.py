from rules import add_perm

from aleksis.core.util.predicates import (
    has_any_object,
    has_global_perm,
    has_object_perm,
    has_person,
)

from .models import LessonSubstitution
from .util.predicates import has_timetable_perm

# View timetable overview
view_timetable_overview_predicate = has_person & has_global_perm("chronos.view_timetable_overview")
add_perm("chronos.view_timetable_overview", view_timetable_overview_predicate)

# View my timetable
add_perm("chronos.view_my_timetable", has_person)

# View timetable
view_timetable_predicate = has_person & (
    has_global_perm("chronos.view_all_timetables") | has_timetable_perm
)
add_perm("chronos.view_timetable", view_timetable_predicate)

# View all lessons per day
view_lessons_day_predicate = has_person & has_global_perm("chronos.view_lessons_day")
add_perm("chronos.view_lessons_day", view_lessons_day_predicate)

# Edit substition
edit_substitution_predicate = has_person & (
    has_global_perm("chronos.change_lessonsubstitution")
    | has_object_perm("chronos.change_lessonsubstitution")
)
add_perm("chronos.edit_substitution", edit_substitution_predicate)

# Delete substitution
delete_substitution_predicate = has_person & (
    has_global_perm("chronos.delete_lessonsubstitution")
    | has_object_perm("chronos.delete_lessonsubstitution")
)
add_perm("chronos.delete_substitution", delete_substitution_predicate)

# View substitutions
view_substitutions_predicate = has_person & (
    has_global_perm("chronos.view_lessonsubstitution")
    | has_any_object("chronos.view_lessonsubstitution", LessonSubstitution)
)
add_perm("chronos.view_substitutions", view_substitutions_predicate)
