from django.utils.translation import gettext_lazy as _

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
                    "url": "my_timetable",
                    "icon": "person",
                    "validators": [
                        (
                            "aleksis.core.util.predicates.permission_validator",
                            "chronos.view_my_timetable",
                        ),
                    ],
                },
                {
                    "name": _("All timetables"),
                    "url": "all_timetables",
                    "icon": "grid_on",
                    "validators": [
                        (
                            "aleksis.core.util.predicates.permission_validator",
                            "chronos.view_timetable_overview",
                        ),
                    ],
                },
                {
                    "name": _("Daily lessons"),
                    "url": "lessons_day",
                    "icon": "calendar_today",
                    "validators": [
                        (
                            "aleksis.core.util.predicates.permission_validator",
                            "chronos.view_lessons_day",
                        ),
                    ],
                },
                {
                    "name": _("Substitutions"),
                    "url": "substitutions",
                    "icon": "update",
                    "validators": [
                        (
                            "aleksis.core.util.predicates.permission_validator",
                            "chronos.view_substitutions",
                        ),
                    ],
                },
            ],
        }
    ]
}
