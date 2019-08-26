from django.utils.translation import ugettext_lazy as _

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
                    'validators': ['menu_generator.validators.is_authenticated']
                }
            ]
        }
    ]
}
