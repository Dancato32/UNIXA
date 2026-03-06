from django.urls import path
from . import views

urlpatterns = [
    path('', views.assignment_list, name='assignment_list'),
    path('new/', views.assignment_create, name='assignment_create'),
    path('<int:assignment_id>/process/', views.process_assignment, name='process_assignment'),
    path('<int:assignment_id>/result/', views.assignment_result, name='assignment_result'),
    path('<int:assignment_id>/download/', views.download_result, name='download_result'),
    path('<int:assignment_id>/delete/', views.assignment_delete, name='assignment_delete'),
    path('<int:assignment_id>/retry/', views.retry_assignment, name='retry_assignment'),
]
