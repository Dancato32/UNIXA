from django.contrib import admin
from .models import SubjectBook, Resource


@admin.register(SubjectBook)
class SubjectBookAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'author', 'uploaded_at')
    list_filter = ('subject',)
    search_fields = ('title', 'author')


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'topic', 'source', 'created_at')
    list_filter = ('subject',)
    search_fields = ('title', 'topic', 'content')
