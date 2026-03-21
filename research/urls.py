from django.urls import path
from . import views

app_name = 'research'

urlpatterns = [
    path('', views.research_home, name='home'),
    path('quick-ask/', views.quick_ask, name='quick_ask'),
    path('workspace/create/', views.workspace_create, name='workspace_create'),
    path('workspace/<uuid:ws_id>/', views.workspace_detail, name='workspace_detail'),
    path('workspace/<uuid:ws_id>/delete/', views.workspace_delete, name='workspace_delete'),
    path('workspace/<uuid:ws_id>/upload/', views.upload_document, name='upload_document'),
    path('workspace/<uuid:ws_id>/doc/<uuid:doc_id>/delete/', views.delete_document, name='delete_document'),
    path('workspace/<uuid:ws_id>/doc/<uuid:doc_id>/summarize/', views.summarize_doc, name='summarize_doc'),
    path('workspace/<uuid:ws_id>/chat/', views.chat_message, name='chat_message'),
    path('workspace/<uuid:ws_id>/chat/clear/', views.clear_chat, name='clear_chat'),
    path('workspace/<uuid:ws_id>/tts/', views.tts_view, name='tts'),
    path('workspace/<uuid:ws_id>/simplify/', views.simplify_view, name='simplify'),
    path('workspace/<uuid:ws_id>/search/', views.search_papers_view, name='search_papers'),
]
