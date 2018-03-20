from django.urls import path
from . import views

urlpatterns = [
    path('teachers/', views.admin_teachers, name='timetable_admin_teachers')
]
