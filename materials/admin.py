from django.contrib import admin
from .models import StudyMaterial


@admin.register(StudyMaterial)
class StudyMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'material_type', 'owner', 'uploaded_at', 'subject']
    list_filter = ['material_type', 'uploaded_at', 'subject']
    search_fields = ['title', 'subject', 'owner__username']
    readonly_fields = ['uploaded_at', 'extracted_text']
    raw_id_fields = ['owner']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'file', 'material_type', 'subject', 'owner')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',)
        }),
        ('AI Integration', {
            'fields': ('extracted_text',),
            'classes': ('collapse',)
        }),
    )

