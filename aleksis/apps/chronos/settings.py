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
        "CHRONOS_SUBSTITUTIONS_PRINT_DAY_NUMBER",
        "CHRONOS_SUBSTITUTIONS_SHOW_HEADER_BOX",
    ),
}
