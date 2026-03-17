from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from django.core.paginator import Paginator
from django.conf import settings
from django.core.files.base import ContentFile
import io
import base64
import logging

from .models import Assignment, AssignmentResult
from .forms import AssignmentForm
from .ai_utils import process_assignment_with_ai
from .doc_generator import generate_word_document, generate_powerpoint_slides, generate_pdf_document
from materials.models import StudyMaterial

logger = logging.getLogger(__name__)


def extract_text_from_photo(image_bytes):
    """Use OpenRouter vision model to OCR a photo and extract assignment text."""
    import os
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={"HTTP-Referer": "http://localhost", "X-Title": "Nexa AI System"}
        )
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract and transcribe all text from this assignment/document image. Return only the raw text content, no commentary."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }],
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Vision OCR error: {e}")
        return None


@login_required
def assignment_list(request):
    """List all assignments for the current user."""
    assignments = Assignment.objects.filter(user=request.user)
    paginator = Paginator(assignments, 10)
    page_number = request.GET.get('page')
    assignments_page = paginator.get_page(page_number)
    
    return render(request, 'assignment/list.html', {
        'assignments': assignments_page,
        'title': 'AI Assignment Assistant'
    })


@login_required
def assignment_create(request):
    """Create a new assignment with file upload or text input."""
    if request.method == 'POST':
        # Handle photo_data before form validation
        photo_data = request.POST.get('photo_data', '')
        photo_text = None
        photo_file = None

        if photo_data and photo_data.startswith('data:image'):
            try:
                # Strip the data URI prefix
                header, encoded = photo_data.split(',', 1)
                image_bytes = base64.b64decode(encoded)
                # Try vision OCR first
                photo_text = extract_text_from_photo(image_bytes)
                if not photo_text:
                    # Fall back to saving as file
                    photo_file = ContentFile(image_bytes, name='assignment_photo.jpg')
            except Exception as e:
                logger.error(f"Photo processing error: {e}")

        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.user = request.user
            assignment.use_rag = request.POST.get('use_rag') == 'on'

            # Inject photo content
            if photo_text:
                existing = assignment.text_content or ''
                assignment.text_content = (existing + '\n\n' + photo_text).strip()
            elif photo_file and not assignment.file:
                assignment.file = photo_file

            # Validate we have some content
            if not assignment.file and not assignment.text_content:
                form.add_error(None, "Please upload a file, take a photo, or enter assignment content.")
                user_materials = StudyMaterial.objects.filter(owner=request.user).order_by('-uploaded_at')
                return render(request, 'assignment/create.html', {'form': form, 'title': 'New Assignment', 'user_materials': user_materials})

            assignment.save()

            # Save selected materials (M2M — must be after save())
            selected_ids = request.POST.getlist('selected_materials')
            if selected_ids:
                materials = StudyMaterial.objects.filter(
                    pk__in=selected_ids, owner=request.user
                )
                assignment.selected_materials.set(materials)

            # Store display options in session
            request.session[f'display_opts_{assignment.id}'] = {
                'font_style': request.POST.get('font_style', 'inter'),
                'font_size': request.POST.get('font_size', '14'),
                'line_spacing': request.POST.get('line_spacing', '1.6'),
                'text_align': request.POST.get('text_align', 'left'),
            }

            messages.success(request, 'Assignment created! Processing now...')
            return redirect('process_assignment', assignment_id=assignment.id)
    else:
        form = AssignmentForm()

    user_materials = StudyMaterial.objects.filter(owner=request.user).order_by('-uploaded_at')

    return render(request, 'assignment/create.html', {
        'form': form,
        'title': 'New Assignment',
        'user_materials': user_materials,
    })


@login_required
def process_assignment(request, assignment_id):
    """Process an assignment using AI with RAG."""
    assignment = get_object_or_404(Assignment, id=assignment_id, user=request.user)
    
    if assignment.status == 'completed':
        return redirect('assignment_result', assignment_id=assignment.id)
    
    if assignment.status == 'processing':
        messages.info(request, 'Assignment is being processed...')
        return redirect('assignment_list')
    
    assignment.status = 'processing'
    assignment.save()
    
    try:
        # Pass use_rag flag to AI processing
        content, used_materials = process_assignment_with_ai(assignment, request.user, use_rag=assignment.use_rag)
        
        result = AssignmentResult.objects.create(
            assignment=assignment,
            content=content,
            used_materials=used_materials
        )
        
        output_format = assignment.output_format
        
        if output_format == 'word':
            doc = generate_word_document(content, assignment.title)
            buffer = io.BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            filename = f"{assignment.title}.docx"
            result.result_file.save(filename, io.BytesIO(buffer.getvalue()))
            
        elif output_format == 'powerpoint':
            prs = generate_powerpoint_slides(content, assignment.title)
            buffer = io.BytesIO()
            prs.save(buffer)
            buffer.seek(0)
            filename = f"{assignment.title}.pptx"
            result.result_file.save(filename, io.BytesIO(buffer.getvalue()))
            
        elif output_format == 'pdf':
            buffer = generate_pdf_document(content, assignment.title)
            buffer.seek(0)
            filename = f"{assignment.title}.pdf"
            result.result_file.save(filename, buffer)
            
        else:
            pass
        
        result.save()
        
        assignment.status = 'completed'
        assignment.save()
        
        messages.success(request, 'Assignment completed!')
        return redirect('assignment_result', assignment_id=assignment.id)
        
    except Exception as e:
        logger.error(f"Error processing assignment: {e}")
        assignment.status = 'failed'
        assignment.error_message = str(e)
        assignment.save()
        
        messages.error(request, f'Processing failed: {str(e)}')
        return redirect('assignment_list')


@login_required
def assignment_result(request, assignment_id):
    """View the result of a processed assignment."""
    assignment = get_object_or_404(Assignment, id=assignment_id, user=request.user)

    display_opts = request.session.get(f'display_opts_{assignment_id}', {
        'font_style': 'inter',
        'font_size': '14',
        'line_spacing': '1.6',
        'text_align': 'left',
    })

    return render(request, 'assignment/result.html', {
        'assignment': assignment,
        'display_opts': display_opts,
        'title': f'Result: {assignment.title}'
    })


@login_required
def download_result(request, assignment_id):
    """Download the generated file. Accepts ?fmt=word|pdf|powerpoint to re-generate on the fly."""
    assignment = get_object_or_404(Assignment, id=assignment_id, user=request.user)

    if not hasattr(assignment, 'result'):
        messages.error(request, 'No result available for download.')
        return redirect('assignment_result', assignment_id=assignment.id)

    result = assignment.result
    fmt = request.GET.get('fmt', assignment.output_format)

    content_types = {
        'word': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'powerpoint': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'pdf': 'application/pdf',
    }
    extensions = {'word': '.docx', 'powerpoint': '.pptx', 'pdf': '.pdf'}

    content_type = content_types.get(fmt, 'application/octet-stream')
    extension = extensions.get(fmt, '.txt')
    filename = f"{assignment.title}{extension}"

    try:
        buffer = io.BytesIO()
        if fmt == 'word':
            doc = generate_word_document(result.content, assignment.title)
            doc.save(buffer)
            buffer.seek(0)
        elif fmt == 'powerpoint':
            prs = generate_powerpoint_slides(result.content, assignment.title)
            prs.save(buffer)
            buffer.seek(0)
        elif fmt == 'pdf':
            buffer = generate_pdf_document(result.content, assignment.title)
            buffer.seek(0)
        else:
            # Plain text fallback
            buffer.write(result.content.encode('utf-8'))
            buffer.seek(0)
            content_type = 'text/plain'
            filename = f"{assignment.title}.txt"

        response = HttpResponse(buffer.read(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        logger.error(f"Download generation error: {e}")
        messages.error(request, f'Download failed: {e}')
        return redirect('assignment_result', assignment_id=assignment.id)


@login_required
def assignment_delete(request, assignment_id):
    """Delete an assignment."""
    assignment = get_object_or_404(Assignment, id=assignment_id, user=request.user)
    
    if request.method == 'POST':
        assignment.delete()
        messages.success(request, 'Assignment deleted.')
        return redirect('assignment_list')
    
    return render(request, 'assignment/delete.html', {
        'assignment': assignment,
        'title': 'Delete Assignment'
    })


@login_required
def retry_assignment(request, assignment_id):
    """Retry processing a failed assignment."""
    assignment = get_object_or_404(Assignment, id=assignment_id, user=request.user)
    
    if assignment.status != 'failed':
        messages.error(request, 'Can only retry failed assignments.')
        return redirect('assignment_list')
    
    assignment.status = 'pending'
    assignment.error_message = ''
    assignment.save()
    
    return redirect('process_assignment', assignment_id=assignment.id)


@login_required
def save_assignment_edits(request, assignment_id):
    """Save user edits to the generated assignment content."""
    import json as _json
    if request.method != 'POST':
        return redirect('assignment_result', assignment_id=assignment_id)

    assignment = get_object_or_404(Assignment, id=assignment_id, user=request.user)

    try:
        data = _json.loads(request.body)
        new_content = data.get('content', '').strip()
        display_opts = data.get('display_opts', {})
    except Exception:
        new_content = request.POST.get('content', '').strip()
        display_opts = {}

    if new_content and hasattr(assignment, 'result'):
        assignment.result.content = new_content
        assignment.result.save()

    if display_opts:
        request.session[f'display_opts_{assignment_id}'] = display_opts

    from django.http import JsonResponse
    return JsonResponse({'ok': True})
