from django import forms
from .models import Assignment


class AssignmentForm(forms.ModelForm):
    """Form for creating and updating assignments."""
    
    class Meta:
        model = Assignment
        fields = ['title', 'file', 'text_content', 'task_type', 'instructions', 'output_format']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter assignment title'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': '.pdf,.docx,.pptx,.ppt'
            }),
            'text_content': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Enter assignment instructions or paste content here...',
                'rows': 6
            }),
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'instructions': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Additional instructions for the AI (optional)...',
                'rows': 4
            }),
            'output_format': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        text_content = cleaned_data.get('text_content')
        # photo_data is handled in the view (not a model field), so we skip validation here
        # if the view will populate text_content from the photo
        return cleaned_data


class AssignmentProcessForm(forms.ModelForm):
    """Form for selecting task type and output format."""
    
    class Meta:
        model = Assignment
        fields = ['task_type', 'instructions', 'output_format']
        widgets = {
            'task_type': forms.Select(attrs={'class': 'form-select'}),
            'instructions': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Additional instructions for the AI...',
                'rows': 4
            }),
            'output_format': forms.Select(attrs={'class': 'form-select'}),
        }
