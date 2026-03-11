from django.urls import path, re_path
from . import views

urlpatterns = [
    path('upload/', views.upload_material, name='upload_material'),
    path('list/', views.list_materials, name='list_materials'),
    path('detail/<int:pk>/', views.material_detail, name='material_detail'),
    path('delete/<int:pk>/', views.delete_material, name='delete_material'),
    path('podcast/<int:pk>/', views.podcast_view, name='podcast_view'),
    path('podcast/generate/', views.generate_podcast_ajax, name='generate_podcast_ajax'),
    path('podcast/question/', views.podcast_question_ajax, name='podcast_question_ajax'),
    path('podcast/audio/<int:material_id>/', views.serve_podcast_audio, name='serve_podcast_audio'),
    path('podcast/audio/<int:material_id>/<str:filename>/', views.serve_podcast_audio, name='serve_podcast_audio_named'),
    path('podcast/answer-audio/<int:material_id>/<str:filename>/', views.serve_answer_audio, name='serve_answer_audio'),
    path('api/count/', views.materials_count_api, name='materials_count_api'),
]


