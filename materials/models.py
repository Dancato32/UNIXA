from django.db import models
from django.conf import settings


class StudyMaterial(models.Model):
    """Model for storing study materials uploaded by students."""
    
    MATERIAL_TYPE_CHOICES = [
        ('PDF', 'PDF'),
        ('PowerPoint', 'PowerPoint'),
        ('Word', 'Word'),
        ('Slides', 'Slides'),
    ]
    
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='study_materials/')
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPE_CHOICES)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_materials')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=255, blank=True, default='')
    extracted_text = models.TextField(blank=True, default='', help_text='Extracted text from the file for AI/RAG integration')
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Study Material'
        verbose_name_plural = 'Study Materials'
    
    def __str__(self):
        return self.title

