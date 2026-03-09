from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat_ai, name='ai_chat'),
    path('chat/ajax/', views.chat_ajax, name='ai_chat_ajax'),
    path('chat/tts/', views.text_to_speech_view, name='ai_tts'),
    path('chat/clear/', views.clear_conversations, name='clear_conversations'),
    path('material/ai/', views.ai_material_action, name='ai_material_action'),
    path('essay/', views.essay_request, name='essay_request'),
    path('essay/<int:essay_id>/', views.essay_detail, name='essay_detail'),
    path('essay/<int:essay_id>/delete/', views.delete_essay, name='delete_essay'),
    path('essay/export/', views.export_essay, name='export_essay'),
]

