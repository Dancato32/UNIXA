from django.db import models
from django.conf import settings


class Assignment(models.Model):
    """Model for storing assignment uploads and instructions."""
    
    TASK_TYPE_CHOICES = [
        ('essay', 'Write an Essay'),
        ('summarize', 'Summarize'),
        ('answer', 'Answer Questions'),
        ('slides', 'Generate Slides'),
        ('structured', 'Provide Structured Answers'),
    ]
    
    OUTPUT_FORMAT_CHOICES = [
        ('word', 'Microsoft Word (.docx)'),
        ('powerpoint', 'PowerPoint (.pptx)'),
        ('pdf', 'PDF Document (.pdf)'),
        ('text', 'Plain Text'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255, help_text="Assignment title")
    file = models.FileField(upload_to='assignments/', blank=True, null=True, help_text="Uploaded assignment file (PDF, Word, PowerPoint)")
    text_content = models.TextField(blank=True, default='', help_text="Manual assignment instructions/text")
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='essay')
    instructions = models.TextField(blank=True, default='', help_text="Additional instructions for the AI")
    output_format = models.CharField(max_length=20, choices=OUTPUT_FORMAT_CHOICES, default='word')
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Assignment'
        verbose_name_plural = 'Assignments'
    
    def __str__(self):
        return f"{self.user.username} - {self.title[:50]}"


class AssignmentResult(models.Model):
    """Model for storing generated assignment results."""
    
    assignment = models.OneToOneField(Assignment, on_delete=models.CASCADE, related_name='result')
    content = models.TextField(help_text="Generated content from AI")
    result_file = models.FileField(upload_to='assignment_results/', blank=True, null=True, help_text="Generated file in selected format")
    used_materials = models.TextField(blank=True, default='', help_text="Study materials used for RAG")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Assignment Result'
        verbose_name_plural = 'Assignment Results'
    
    def __str__(self):
        return f"Result for: {self.assignment.title[:50]}"
