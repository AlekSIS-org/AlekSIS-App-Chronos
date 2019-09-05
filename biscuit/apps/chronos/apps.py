from django.apps import AppConfig
from django.utils.translation import ugettext as _


class ChronosConfig(AppConfig):
    name = 'biscuit.apps.chronos'
    verbose_name = 'BiscuIT - Chronos (' + _('Timetables') + ')'
