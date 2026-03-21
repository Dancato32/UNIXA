from django.contrib import admin
from .models import ResearchWorkspace, WorkspaceDocument, WorkspaceChat

@admin.register(ResearchWorkspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'subject', 'created_at']
    list_filter = ['subject']

@admin.register(WorkspaceDocument)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'workspace', 'file_type', 'status', 'uploaded_at']

@admin.register(WorkspaceChat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['workspace', 'role', 'created_at']
