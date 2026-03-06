from django import forms
from .models import Conversation, EssayRequest


class ChatForm(forms.Form):
    """Form for sending messages to the AI chat."""
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ask me anything...',
            'id': 'chat-input'
        }),
        help_text="Enter your message to the AI"
    )


class ConversationForm(forms.ModelForm):
    """Form for creating a new conversation."""
    class Meta:
        model = Conversation
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ask me anything...',
                'id': 'chat-input'
            })
        }


class EssayForm(forms.ModelForm):
    """Form for requesting an essay."""
    OUTPUT_FORMAT_CHOICES = [
        ('text', 'Plain Text'),
        ('pdf', 'PDF Document'),
        ('word', 'Word Document'),
        ('powerpoint', 'PowerPoint Presentation'),
    ]
    
    WORD_COUNT_CHOICES = [
        (250, '250 words (Short)'),
        (500, '500 words (Medium)'),
        (750, '750 words'),
        (1000, '1000 words (Long)'),
        (1500, '1500 words (Extended)'),
        (2000, '2000 words (Essay)'),
        (3000, '3000 words (Research Paper)'),
    ]
    
    topic = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your essay topic...',
            'id': 'essay-topic'
        }),
        help_text="Enter the topic for your essay"
    )
    
    word_count = forms.ChoiceField(
        choices=WORD_COUNT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'word-count'
        }),
        initial=500,
        required=False,
        help_text="Optional: Target word count"
    )
    
    output_format = forms.ChoiceField(
        choices=OUTPUT_FORMAT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'output-format'
        }),
        initial='text',
        help_text="Select the output format"
    )
    
    class Meta:
        model = EssayRequest
        fields = ['topic', 'word_count', 'output_format']

