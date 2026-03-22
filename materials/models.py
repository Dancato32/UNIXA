from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os

# Store study material files locally — bypasses Cloudinary's 10 MB limit
_materials_storage = FileSystemStorage(
    location=os.path.join(settings.MEDIA_ROOT, 'study_materials'),
    base_url=settings.MEDIA_URL + 'study_materials/',
)


class StudyMaterial(models.Model):
    """Model for storing study materials uploaded by students."""
    
    MATERIAL_TYPE_CHOICES = [
        ('PDF', 'PDF'),
        ('PowerPoint', 'PowerPoint'),
        ('Word', 'Word'),
        ('Slides', 'Slides'),
    ]
    
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='', storage=_materials_storage)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPE_CHOICES)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_materials')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=255, blank=True, default='')
    extracted_text = models.TextField(blank=True, default='', help_text='Extracted text from the file for AI/RAG integration')
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Study Material'
        verbose_name_plural = 'Study Materials'
    
    @property
    def file_size(self):
        """Return file size safely — works with both local and Cloudinary storage."""
        try:
            return self.file.size
        except Exception:
            return None

    def __str__(self):
        return self.title


class SavedFlashcardDeck(models.Model):
    """Saved set of AI-generated flashcards for a study material."""
    material = models.ForeignKey(StudyMaterial, on_delete=models.CASCADE, related_name='flashcard_decks')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='flashcard_decks')
    name = models.CharField(max_length=200)
    cards = models.JSONField()  # list of {front, back}
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.material.title})"

