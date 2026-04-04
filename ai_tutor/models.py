from django.db import models
from django.conf import settings


class ChatThread(models.Model):
    """Group conversations into sessions (ChatGPT-style threads)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_threads')
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name_plural = 'Chat Threads'
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class Conversation(models.Model):
    """Store chat conversations between users and AI."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_conversations')
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    message = models.TextField(help_text="User's message to the AI")
    response = models.TextField(help_text="AI's response")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp of the conversation")
    
    class Meta:
        ordering = ['created_at'] # Oldest first within a thread
        verbose_name_plural = 'Conversations'
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class EssayRequest(models.Model):
    """Store essay generation requests."""
    OUTPUT_FORMAT_CHOICES = [
        ('text', 'Plain Text'),
        ('pdf', 'PDF Document'),
        ('word', 'Word Document'),
        ('powerpoint', 'PowerPoint Presentation'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='essay_requests')
    topic = models.CharField(max_length=500, help_text="Essay topic")
    word_count = models.PositiveIntegerField(default=500, help_text="Target word count for the essay")
    research_done = models.BooleanField(default=False, help_text="Whether research was performed")
    essay_text = models.TextField(help_text="Generated essay text")
    output_format = models.CharField(
        max_length=20,
        choices=OUTPUT_FORMAT_CHOICES,
        default='text',
        help_text="Desired output format"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp of the request")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Essay Requests'
    
    def __str__(self):
        return f"{self.user.username} - {self.topic[:50]}"

