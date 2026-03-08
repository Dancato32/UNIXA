from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_material, name='upload_material'),
    path('list/', views.list_materials, name='list_materials'),
    path('detail/<int:pk>/', views.material_detail, name='material_detail'),
    path('delete/<int:pk>/', views.delete_material, name='delete_material'),
    path('api/count/', views.materials_count_api, name='materials_count_api'),
]

