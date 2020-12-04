from django.utils.translation import gettext as _

from dynamic_preferences.preferences import Section
from dynamic_preferences.types import BooleanPreference, IntegerPreference

from aleksis.core.registries import person_preferences_registry, site_preferences_registry

chronos = Section("chronos", verbose_name=_("Chronos"))


@site_preferences_registry.register
class UseParentGroups(BooleanPreference):
    section = chronos
    name = "use_parent_groups"
    default = False
    verbose_name = _("Use parent groups in timetable views")
    help_text = _(
        "If an lesson or substitution has only one group"
        " and this group has parent groups,"
        " show the parent groups instead of the original group."
    )


@person_preferences_registry.register
class ShortenGroups(BooleanPreference):
    section = chronos
    name = "shorten_groups"
    default = True
    verbose_name = _("Shorten groups in timetable views")
    help_text = _("If there are more groups than the set limit, they will be collapsed.")


@site_preferences_registry.register
class ShortenGroupsLimit(IntegerPreference):
    section = chronos
    name = "shorten_groups_limit"
    default = 4
    verbose_name = _("Limit of groups for shortening of groups")
    help_text = _(
        "If an user activates shortening of groups,"
        "they will be collapsed if there are more groups than this limit."
    )


@site_preferences_registry.register
class SubstitutionsPrintNumberOfDays(IntegerPreference):
    section = chronos
    name = "substitutions_print_number_of_days"
    default = 2
    verbose_name = _("Number of days shown on substitutions print view")


@site_preferences_registry.register
class SubstitutionsShowHeaderBox(BooleanPreference):
    section = chronos
    name = "substitutions_show_header_box"
    default = True
    verbose_name = _("Show header box in substitution views")
    help_text = _("The header box shows affected teachers/groups.")


@site_preferences_registry.register
class AffectedGroupsUseParentGroups(BooleanPreference):
    section = chronos
    name = "affected_groups_parent_groups"
    default = True
    verbose_name = _(
        "Show parent groups in header box in substitution views instead of original groups"
    )
