from django.urls import path
from untisconnect.models import Terms

try:
    from . import views

    urlpatterns = [
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
        path('class.pdf', views.sub_pdf, name="timetable_substitutions_pdf")
    ]

except Terms.DoesNotExist:
    from . import failback_view

    urlpatterns = [
        path('', failback_view.failback, name='timetable_admin_all'),
        path('my', failback_view.failback, name='timetable_my_plan'),
        path('my/<int:year>/<int:month>/<int:day>/', failback_view.failback, name='timetable_my_plan'),
        path('quick/', failback_view.failback, name='timetable_quicklaunch'),
        path('<str:plan_type>/<int:plan_id>', failback_view.failback, name='timetable_smart_plan'),
        path('<str:plan_type>/<int:plan_id>/<str:regular>', failback_view.failback, name='timetable_regular_plan'),
        path('<str:plan_type>/<int:plan_id>/<int:year>/<int:calendar_week>', failback_view.failback,
             name='timetable_smart_plan_week'),
        path('substitutions/', failback_view.failback, name='timetable_substitutions'),
        path('substitutions/<int:year>/<int:month>/<int:day>/', failback_view.failback,
             name='timetable_substitutions_date'),
        path('class.pdf', failback_view.failback, name="timetable_substitutions_pdf")
    ]
    
urlpatterns += [
    path('hints', views.hints, name="timetable_hints"),
    path('hints/add', views.add_hint, name="timetable_add_hint"),
    path('hints/<int:id>/edit', views.edit_hint, name="timetable_edit_hint"),
    path('hints/<int:id>/delete', views.delete_hint, name="timetable_delete_hint"),
]
