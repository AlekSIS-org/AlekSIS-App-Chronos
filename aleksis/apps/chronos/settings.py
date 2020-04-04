from django.utils.translation import gettext_lazy as _

CONSTANCE_CONFIG = {
    "CHRONOS_USE_PARENT_GROUPS": (
        False,
        _(
            "If an lesson or substitution has only one group"
            " and this group has parent groups,"
            " show the parent groups instead of the original group."
        ),
    ),
    "CHRONOS_SHORTEN_GROUPS": (
        False,
        _(
            "If there are more groups than the limit set in CHRONOS_SHORTEN_GROUPS_LIMIT, add text collapsible."
        ),
    ),
    "CHRONOS_SHORTEN_GROUPS_LIMIT": (
        4,
        _(
            "If there are more groups than this limit and CHRONOS_SHORTEN_GROUPS is enabled, add text collapsible."
        ),
    ),
    "CHRONOS_SUBSTITUTIONS_PRINT_DAY_NUMBER": (
        2,
        _("Number of days shown on substitutions print view"),
    ),
    "CHRONOS_SUBSTITUTIONS_SHOW_HEADER_BOX": (
        True,
        _("The header box shows affected teachers/groups."),
    ),
}
CONSTANCE_CONFIG_FIELDSETS = {
    "Chronos settings": (
        "CHRONOS_USE_PARENT_GROUPS",
        "CHRONOS_SHORTEN_GROUPS",
        "CHRONOS_SHORTEN_GROUPS_LIMIT",
        "CHRONOS_SUBSTITUTIONS_PRINT_DAY_NUMBER",
        "CHRONOS_SUBSTITUTIONS_SHOW_HEADER_BOX",
    ),
}
