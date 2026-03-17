from django.contrib import admin
from .models import Assignment, AssignmentResult


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'task_type', 'output_format', 'status', 'created_at']
    list_filter = ['status', 'task_type', 'output_format', 'created_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AssignmentResult)
class AssignmentResultAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'created_at']
    search_fields = ['assignment__title', 'assignment__user__username']
    readonly_fields = ['created_at']
