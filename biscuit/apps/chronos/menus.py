from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from menu import Menu, MenuItem


menu_items = [
    MenuItem(_('Stundenplan'),
             reverse('timetable'),
             check=lambda request: request.user.is_authenticated and request.user.is_superuser),
]

app_menu = MenuItem(_('Timetables'),
                    '#',
                    children=menu_items)

Menu.add_item('main', app_menu)
