from django.urls import path
from . import views

urlpatterns = [
    path('', views.all, name='timetable_admin_all'),
    path('quick/', views.quicklaunch, name='timetable_quicklaunch'),
    path('<str:plan_type>/<int:plan_id>/', views.plan, name='timetable_plan'),
    path('substitutions/', views.substitutions, name='timetable_substitutions'),
    path('substitutions/<int:year>/<int:month>/<int:day>/', views.substitutions, name='timetable_substitutions'),
]
