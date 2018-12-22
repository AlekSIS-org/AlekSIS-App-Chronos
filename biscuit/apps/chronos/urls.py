from django.urls import path
from . import views

urlpatterns = [
    path('', views.all, name='timetable_admin_all'),
    path('quick/', views.quicklaunch, name='timetable_quicklaunch'),
    path('<str:plan_type>/<int:plan_id>', views.plan, name='timetable_plan'),
    path('<str:plan_type>/<int:plan_id>/<str:smart>', views.plan, name='timetable_smart_plan'),
    path('<str:plan_type>/<int:plan_id>/<str:smart>/<int:year>/<int:calendar_week>', views.plan,
         name='timetable_smart_plan_week'),
    path('substitutions/', views.substitutions, name='timetable_substitutions'),
    path('substitutions/<int:year>/<int:month>/<int:day>/', views.substitutions, name='timetable_substitutions_date'),
    path('class.pdf', views.sub_pdf, name="timetable_substitutions_pdf")
]
