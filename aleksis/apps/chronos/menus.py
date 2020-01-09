from django.utils.translation import ugettext_lazy as _

MENUS = {
    "NAV_MENU_CORE": [
        {
            "name": _("Timetables"),
            "url": "#",
            "icon": "school",
            "root": True,
            "validators": [
                "menu_generator.validators.is_authenticated",
                "aleksis.core.util.core_helpers.has_person",
            ],
            "submenu": [
                {
                    "name": _("My timetable"),
                    "url": "timetable",
                    "icon": "person",
                    "validators": ["menu_generator.validators.is_authenticated"],
                },
                {
                    "name": _("All timetables"),
                    "url": "all_timetables",
                    "icon": "grid_on",
                    "validators": ["menu_generator.validators.is_authenticated"],
                },
                {
                    "name": _("Daily lessons"),
                    "url": "lessons_day",
                    "icon": "calendar_today",
                    "validators": ["menu_generator.validators.is_authenticated"],
                },
                {
                    "name": _("Substitutions"),
                    "url": "substitutions",
                    "icon": "update",
                    "validators": ["menu_generator.validators.is_authenticated"],
                },
            ],
        }
    ]
}
