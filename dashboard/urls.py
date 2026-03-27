from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dashboard_index'),
    path('explore/', views.explore, name='explore'),
]

