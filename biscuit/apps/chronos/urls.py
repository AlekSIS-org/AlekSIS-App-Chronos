from django.urls import path
from . import views

urlpatterns = [
    path('admin/all/', views.admin_all, name='timetable_admin_all'),
    path('plan/<str:plan_type>/<int:plan_id>', views.plan, name='timetable_plan')
]
