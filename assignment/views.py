from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from django.core.paginator import Paginator
from django.conf import settings
import io
import logging

from .models import Assignment, AssignmentResult
from .forms import AssignmentForm
from .ai_utils import process_assignment_with_ai
from .doc_generator import generate_word_document, generate_powerpoint_slides, generate_pdf_document

logger = logging.getLogger(__name__)


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
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.user = request.user
            # Handle use_rag checkbox
            assignment.use_rag = request.POST.get('use_rag') == 'on'
            assignment.save()
            
            messages.success(request, 'Assignment created! Processing now...')
            return redirect('process_assignment', assignment_id=assignment.id)
    else:
        form = AssignmentForm()
    
    return render(request, 'assignment/create.html', {
        'form': form,
        'title': 'New Assignment'
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
    
    return render(request, 'assignment/result.html', {
        'assignment': assignment,
        'title': f'Result: {assignment.title}'
    })


@login_required
def download_result(request, assignment_id):
    """Download the generated file."""
    assignment = get_object_or_404(Assignment, id=assignment_id, user=request.user)
    
    if not hasattr(assignment, 'result') or not assignment.result.result_file:
        messages.error(request, 'No file available for download.')
        return redirect('assignment_result', assignment_id=assignment.id)
    
    result = assignment.result
    file_format = assignment.output_format
    
    content_types = {
        'word': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'powerpoint': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'pdf': 'application/pdf',
    }
    
    extensions = {
        'word': '.docx',
        'powerpoint': '.pptx',
        'pdf': '.pdf',
    }
    
    content_type = content_types.get(file_format, 'application/octet-stream')
    extension = extensions.get(file_format, '')
    filename = f"{assignment.title}{extension}"
    
    response = FileResponse(result.result_file, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


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
