from django import forms
from .models import StudyMaterial


class StudyMaterialForm(forms.ModelForm):
    """Form for uploading study materials."""
    
    class Meta:
        model = StudyMaterial
        fields = ['title', 'file', 'material_type', 'subject']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter material title'
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.docx,.pptx'
            }),
            'material_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter subject (optional)'
            }),
        }
    
    def clean_file(self):
        """Validate the uploaded file."""
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 50MB)
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError("File size must be less than 50MB.")
            
            # Check file extension
            allowed_extensions = ['.pdf', '.docx', '.pptx']
            import os
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError("Unsupported file type. Please upload PDF, Word, or PowerPoint files.")
        
        return file

