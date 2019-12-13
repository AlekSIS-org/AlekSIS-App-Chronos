from django.db import ProgrammingError, OperationalError
from django.urls import path

from untisconnect.models import Terms, Schoolyear

try:
    from . import views

    urlpatterns = [
        path('hints', views.hints, name="timetable_hints"),
        path('hints/add', views.add_hint, name="timetable_add_hint"),
        path('hints/<int:id>/edit', views.edit_hint, name="timetable_edit_hint"),
        path('hints/<int:id>/delete', views.delete_hint, name="timetable_delete_hint"),
        path('', views.all, name='timetable_admin_all'),
        path('my', views.my_plan, name='timetable_my_plan'),
        path('my/<int:year>/<int:month>/<int:day>/', views.my_plan, name='timetable_my_plan'),
        path('quick/', views.quicklaunch, name='timetable_quicklaunch'),
        # plan_type = ["teacher", "class", "room"]
        path('<str:plan_type>/<int:plan_id>', views.plan, name='timetable_smart_plan'),
        path('<str:plan_type>/<int:plan_id>/<str:regular>', views.plan, name='timetable_regular_plan'),
        path('<str:plan_type>/<int:plan_id>/<int:year>/<int:calendar_week>', views.plan,
             name='timetable_smart_plan_week'),
        path('substitutions/', views.substitutions, name='timetable_substitutions'),
        path('substitutions/<int:year>/<int:month>/<int:day>/', views.substitutions,
             name='timetable_substitutions_date'),
        path('substitutions/<int:year>/<int:month>/<int:day>/print/', views.substitutions_print,
             name='timetable_substitutions_date_print'),
        path('substitutions/print/', views.substitutions_print,
             name='timetable_substitutions_print'),
        path('aktuell.pdf', views.sub_pdf, name="timetable_substitutions_pdf"),
        path('<str:plan_date>-aktuell.pdf', views.sub_pdf, name="timetable_substitutions_pdf_date")
    ]

except (Terms.DoesNotExist, Schoolyear.DoesNotExist, ProgrammingError, OperationalError):
    from . import fallback_view

    urlpatterns = [
        path('hints', fallback_view.fallback, name="timetable_hints"),
        path('hints/add', fallback_view.fallback, name="timetable_add_hint"),
        path('hints/<int:id>/edit', fallback_view.fallback, name="timetable_edit_hint"),
        path('hints/<int:id>/delete', fallback_view.fallback, name="timetable_delete_hint"),
        path('', fallback_view.fallback, name='timetable_admin_all'),
        path('my', fallback_view.fallback, name='timetable_my_plan'),
        path('my/<int:year>/<int:month>/<int:day>/', fallback_view.fallback, name='timetable_my_plan'),
        path('quick/', fallback_view.fallback, name='timetable_quicklaunch'),
        path('<str:plan_type>/<int:plan_id>', fallback_view.fallback, name='timetable_smart_plan'),
        path('<str:plan_type>/<int:plan_id>/<str:regular>', fallback_view.fallback, name='timetable_regular_plan'),
        path('<str:plan_type>/<int:plan_id>/<int:year>/<int:calendar_week>', fallback_view.fallback,
             name='timetable_smart_plan_week'),
        path('substitutions/', fallback_view.fallback, name='timetable_substitutions'),
        path('substitutions/<int:year>/<int:month>/<int:day>/', fallback_view.fallback,
             name='timetable_substitutions_date'),
        path('substitutions/<int:year>/<int:month>/<int:day>/<str:print_view>/', fallback_view.fallback,
             name='timetable_substitutions_date_print'),
        path('substitutions/<str:print_view>/', fallback_view.fallback,
             name='timetable_substitutions_print'),
        path('aktuell.pdf', fallback_view.fallback, name="timetable_substitutions_pdf"),
        path('<str:plan_date>-aktuell.pdf', fallback_view.fallback, name="timetable_substitutions_pdf_date")
    ]
