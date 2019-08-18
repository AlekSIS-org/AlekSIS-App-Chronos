MENUS = {
    'NAV_MENU_CORE': [
        {
            'name': 'Timetables',
            'url': '#',
            'root': True,
            'submenu': [
                {
                    'name': 'Timetable',
                    'url': 'timetable',
                    'validators': ['menu_generator.validators.is_authenticated', 'menu_generator.validators.is_superuser']
                }
            ]
        }
    ]
}
