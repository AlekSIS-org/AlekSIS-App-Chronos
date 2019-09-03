from django.utils.translation import ugettext_lazy as _

MENUS = {
    'NAV_MENU_CORE': [
        {
            'name': _('Timetables'),
            'url': '#',
            'root': True,
            'validators': ['menu_generator.validators.is_authenticated', 'biscuit.core.util.core_helpers.has_person'],
            'submenu': [
                {
                    'name': _('Timetable'),
                    'url': 'timetable',
                    'validators': ['menu_generator.validators.is_authenticated']
                },
                {
                    'name': _('Daily lessons'),
                    'url': 'lessons_day',
                    'validators': ['menu_generator.validators.is_authenticated']
                }
            ]
        }
    ]
}
