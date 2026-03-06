from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import StudyMaterial
from .forms import StudyMaterialForm
import os


def extract_text_from_file(file_path, file_extension):
    """
    Extract text from uploaded files.
    Supports: .docx (Word), .pptx (PowerPoint), .pdf
    """
    text = ""
    
    if file_extension == '.docx':
        # Extract text from Word documents
        try:
            import docx
            doc = docx.Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + '\n'
        except ImportError:
            text = "[Word text extraction requires 'python-docx'. Install it with: pip install python-docx]"
        except Exception as e:
            text = f"[Error extracting Word content: {str(e)}]"
            
    elif file_extension == '.pptx':
        # Extract text from PowerPoint presentations
        try:
            import pptx
            prs = pptx.Presentation(file_path)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + '\n'
        except ImportError:
            text = "[PowerPoint text extraction requires 'python-pptx'. Install it with: pip install python-pptx]"
        except Exception as e:
            text = f"[Error extracting PowerPoint content: {str(e)}]"
            
    elif file_extension == '.pdf':
        # Simple PDF text extraction using PyPDF2
        try:
            import PyPDF2
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    text += page.extract_text() or ''
        except ImportError:
            text = "[PDF text extraction requires 'PyPDF2'. Install it with: pip install PyPDF2]"
        except Exception as e:
            text = f"[Error extracting PDF content: {str(e)}]"
    
    return text


@login_required
def upload_material(request):
    """Allow logged-in students to upload study materials."""
    
    if request.method == 'POST':
        form = StudyMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the material but don't commit yet
            material = form.save(commit=False)
            # Set the owner to the current user
            material.owner = request.user
            
            # Save the material to get the file path
            material.save()
            
            # Extract text from the uploaded file
            file_path = material.file.path
            file_extension = os.path.splitext(file_path)[1].lower()
            
            extracted_text = extract_text_from_file(file_path, file_extension)
            material.extracted_text = extracted_text
            material.save(update_fields=['extracted_text'])
            
            if extracted_text.startswith('[') and 'requires' in extracted_text:
                messages.warning(request, f'Material uploaded, but {extracted_text}')
            else:
                messages.success(request, 'Material uploaded successfully! Text has been extracted.')
            
            return redirect('list_materials')
    else:
        form = StudyMaterialForm()
    
    return render(request, 'materials/upload.html', {
        'form': form,
        'title': 'Upload Study Material'
    })


@login_required
def list_materials(request):
    """List all uploaded materials by the logged-in student."""
    
    materials_list = StudyMaterial.objects.filter(owner=request.user)
    
    # Add pagination
    paginator = Paginator(materials_list, 10)  # Show 10 materials per page
    page_number = request.GET.get('page')
    materials = paginator.get_page(page_number)
    
    return render(request, 'materials/list.html', {
        'materials': materials,
        'title': 'My Study Materials'
    })


@login_required
def material_detail(request, pk):
    """View details of a specific study material."""
    
    material = get_object_or_404(StudyMaterial, pk=pk, owner=request.user)
    return render(request, 'materials/detail.html', {
        'material': material,
        'title': material.title
    })


@login_required
def delete_material(request, pk):
    """Delete a study material."""
    
    material = get_object_or_404(StudyMaterial, pk=pk, owner=request.user)
    
    if request.method == 'POST':
        # Delete the file from storage
        if material.file:
            if os.path.isfile(material.file.path):
                os.remove(material.file.path)
        material.delete()
        messages.success(request, 'Material deleted successfully.')
        return redirect('list_materials')
    
    return render(request, 'materials/delete.html', {
        'material': material,
        'title': 'Delete Material'
    })

