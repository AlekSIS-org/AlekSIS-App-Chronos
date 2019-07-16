from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ChronosConfig(AppConfig):
    name = 'biscuit.apps.chronos'
    verbose_name = _('BiscuIT - Chronos (Timetables)')
