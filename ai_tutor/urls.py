from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.chat_ai, name='ai_chat'),
    path('chat/ajax/', views.chat_ajax, name='ai_chat_ajax'),
    path('chat/stream/', views.chat_stream, name='ai_chat_stream'),
    path('chat/tts/', views.text_to_speech_view, name='ai_tts'),
    path('chat/clear/', views.clear_conversations, name='clear_conversations'),
    path('chat/image/', views.chat_with_image, name='ai_chat_image'),
    path('chat/websearch/', views.web_search_ajax, name='ai_web_search'),
    path('material/ai/', views.ai_material_action, name='ai_material_action'),
    # Essay — static paths MUST come before <int:essay_id> patterns
    path('essay/', views.essay_request, name='essay_request'),
    path('essay/generate/', views.essay_generate_ajax, name='essay_generate_ajax'),
    path('essay/edit-chat/', views.essay_edit_chat, name='essay_edit_chat'),
    path('essay/web-search/', views.essay_web_search, name='essay_web_search'),
    path('essay/guidance/', views.essay_guidance, name='essay_guidance'),
    path('essay/improve/', views.essay_improve, name='essay_improve'),
    path('essay/export/', views.export_essay, name='export_essay'),
    path('essay/autocomplete/', views.essay_autocomplete, name='essay_autocomplete'),
    path('essay/copilot/', views.essay_copilot, name='essay_copilot'),
    # Essay — dynamic <int:essay_id> paths
    path('essay/<int:essay_id>/', views.essay_detail, name='essay_detail'),
    path('essay/<int:essay_id>/delete/', views.delete_essay, name='delete_essay'),
    path('essay/<int:essay_id>/save-edits/', views.essay_save_edits, name='essay_save_edits'),
    path('essay/<int:essay_id>/restyle/', views.essay_restyle, name='essay_restyle'),
]

