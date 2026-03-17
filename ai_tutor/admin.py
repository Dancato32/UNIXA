from django.contrib import admin
from .models import Conversation, EssayRequest


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['message', 'response', 'user__username']
    readonly_fields = ['created_at']


@admin.register(EssayRequest)
class EssayRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'output_format', 'research_done', 'created_at']
    list_filter = ['created_at', 'output_format', 'research_done', 'user']
    search_fields = ['topic', 'essay_text', 'user__username']
    readonly_fields = ['created_at']

