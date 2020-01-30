from django.utils.translation import gettext_lazy as _

CONSTANCE_CONFIG = {
    "CHRONOS_SUBSTITUTIONS_PRINT_DAY_NUMBER": (2, _("Number of days shown on substitutions print view")),
}
CONSTANCE_CONFIG_FIELDSETS = {
    "Chronos settings": ("CHRONOS_SUBSTITUTIONS_PRINT_DAY_NUMBER",),
}
