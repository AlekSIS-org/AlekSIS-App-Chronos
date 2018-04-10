from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_all, name='timetable_admin_all'),
    path('<str:plan_type>/<int:plan_id>', views.plan, name='timetable_plan')
]
