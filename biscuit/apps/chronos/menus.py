from django.utils.translation import gettext as _

MENUS = {
    'NAV_MENU_CORE': [
        {
            'name': _('Timetables'),
            'url': '#',
            'root': True,
            'submenu': [
                {
                    'name': _('Timetable'),
                    'url': 'timetable',
                    'validators': ['menu_generator.validators.is_authenticated', 'menu_generator.validators.is_superuser']
                }
            ]
        }
    ]
}
