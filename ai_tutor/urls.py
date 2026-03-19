from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat_ai, name='ai_chat'),
    path('chat/ajax/', views.chat_ajax, name='ai_chat_ajax'),
    path('chat/stream/', views.chat_stream, name='ai_chat_stream'),
    path('chat/tts/', views.text_to_speech_view, name='ai_tts'),
    path('tts/audio/<str:filename>/', views.serve_tts_audio, name='serve_tts_audio'),
    path('chat/clear/', views.clear_conversations, name='clear_conversations'),
    path('chat/image/', views.chat_with_image, name='ai_chat_image'),
    path('chat/websearch/', views.web_search_ajax, name='ai_web_search'),
    path('material/ai/', views.ai_material_action, name='ai_material_action'),
    path('essay/', views.essay_request, name='essay_request'),
    path('essay/<int:essay_id>/', views.essay_detail, name='essay_detail'),
    path('essay/<int:essay_id>/delete/', views.delete_essay, name='delete_essay'),
    path('essay/<int:essay_id>/save-edits/', views.essay_save_edits, name='essay_save_edits'),
    path('essay/<int:essay_id>/restyle/', views.essay_restyle, name='essay_restyle'),
    path('essay/guidance/', views.essay_guidance, name='essay_guidance'),
    path('essay/improve/', views.essay_improve, name='essay_improve'),
    path('essay/export/', views.export_essay, name='export_essay'),
    path('essay/editor/', views.essay_editor, name='essay_editor'),
    path('essay/<int:essay_id>/editor/', views.essay_editor, name='essay_editor_existing'),
    path('essay/<int:essay_id>/editor-save/', views.essay_editor_save, name='essay_editor_save'),
    path('essay/autocomplete/', views.essay_autocomplete, name='essay_autocomplete'),
    path('essay/copilot/', views.essay_copilot, name='essay_copilot'),
]

