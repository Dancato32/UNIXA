from django.shortcuts import render, redirect, get_object_or_404, reverse
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
from django.http import JsonResponse, StreamingHttpResponse

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
            default_headers={"HTTP-Referer": "https://unixa.onrender.com", "X-Title": "Nexa AI Assignment"}
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
    """Create a new assignment with AJAX support and Deep Research capability."""
    if request.method == 'POST':
        try:
            # 1. Handle Photo/OCR logic
            photo_data = request.POST.get('photo_data', '')
            image_text = ""
            
            if photo_data and photo_data.startswith('data:image'):
                from .ai_utils import extract_text_from_photo
                import base64
                try:
                    header, encoded = photo_data.split(',', 1)
                    image_bytes = base64.b64decode(encoded)
                    image_text = extract_text_from_photo(image_bytes) or ""
                except Exception as pe:
                    logger.error(f"Photo processing error: {pe}")

            # 2. Process Form
            form = AssignmentForm(request.POST, request.FILES)
            if form.is_valid():
                assignment = form.save(commit=False)
                assignment.user = request.user
                
                # Append OCR text if found
                if image_text:
                    existing = assignment.text_content or ""
                    assignment.text_content = (existing + "\n\n" + image_text).strip()

                # Validate content availability
                if not assignment.file and not assignment.text_content:
                    msg = "Please upload a file, take a photo, or enter assignment content."
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == 'true':
                        return JsonResponse({'ok': False, 'errors': msg}, status=400)
                    form.add_error(None, msg)
                    user_materials = StudyMaterial.objects.filter(owner=request.user).order_by('-uploaded_at')
                    return render(request, 'assignment/create.html', {'form': form, 'title': 'New Assignment', 'user_materials': user_materials})

                assignment.save()

                # 3. Handle M2M & Session
                selected_ids = request.POST.getlist('selected_materials')
                if selected_ids:
                    materials = StudyMaterial.objects.filter(pk__in=selected_ids, owner=request.user)
                    assignment.selected_materials.set(materials)

                request.session[f'display_opts_{assignment.id}'] = {
                    'font_style': request.POST.get('font_style', 'inter'),
                    'font_size': request.POST.get('font_size', '14'),
                    'line_spacing': request.POST.get('line_spacing', '1.6'),
                    'text_align': request.POST.get('text_align', 'left'),
                }

                # 4. Respond
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == 'true':
                    return JsonResponse({
                        'ok': True,
                        'assignment_id': assignment.id,
                        'is_research': request.POST.get('deep_research') == 'true',
                        'title': assignment.title
                    })

                messages.success(request, 'Assignment created! Synthesis starting...')
                return redirect(reverse('assignment_result', args=[assignment.id]) + '?stream=true')
            
            # Handle invalid form
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == 'true':
                return JsonResponse({'ok': False, 'errors': form.errors.as_text()}, status=400)

        except Exception as e:
            logger.error(f"Critical error in assignment_create: {e}")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == 'true':
                return JsonResponse({'ok': False, 'errors': f"Critical Server Error: {str(e)}"}, status=500)
            raise e
    else:
        form = AssignmentForm()

    user_materials = StudyMaterial.objects.filter(owner=request.user).order_by('-uploaded_at')
    recent_assignments = Assignment.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    return render(request, 'assignment/create.html', {
        'form': form,
        'title': 'Build Your Assignment',
        'user_materials': user_materials,
        'recent_assignments': recent_assignments
    })


@login_required
def assignment_stream_build(request, assignment_id):
    """
    SSE endpoint to stream assignment generation.
    """
    from django.http import StreamingHttpResponse
    import json as _json
    from .ai_utils import generate_assignment_stream
    
    assignment = get_object_or_404(Assignment, id=assignment_id, user=request.user)
    
    def event_stream():
        full_text = []
        try:
            # Update status to processing
            assignment.status = 'processing'
            assignment.save()
            
            for token in generate_assignment_stream(assignment, request.user):
                full_text.append(token)
                yield f"data: {_json.dumps({'token': token})}\n\n"
            
            # Save final result - clean up internal markers
            cleaned_text = []
            for t in full_text:
                if not t.startswith('[PROGRESS]') and t != "\n\n[PAGE_BREAK]\n\n":
                    cleaned_text.append(t)
            
            final_text = "".join(cleaned_text)
            result, created = AssignmentResult.objects.get_or_create(assignment=assignment)
            result.content = final_text
            result.save()
            
            assignment.status = 'completed'
            assignment.save()
            yield "event: done\ndata: {}\n\n"
        except Exception as e:
            assignment.status = 'failed'
            assignment.error_message = str(e)
            assignment.save()
            logger.error(f"Stream build error: {e}")
            yield f"event: error\ndata: {_json.dumps({'error': str(e)})}\n\n"
            
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache, no-transform'
    response['X-Accel-Buffering'] = 'no'
    return response


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
            content_to_use = content
            if assignment.task_type != 'presentation':
                from .ai_utils import transform_to_presentation_json
                slides_data = transform_to_presentation_json(content, num_slides=7)
                if slides_data:
                    content_to_use = slides_data

            prs = generate_powerpoint_slides(content_to_use, assignment.title)
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
            content_to_use = result.content
            if assignment.task_type != 'presentation':
                from .ai_utils import transform_to_presentation_json
                slides_data = transform_to_presentation_json(result.content, num_slides=7)
                if slides_data:
                    content_to_use = slides_data

            prs = generate_powerpoint_slides(content_to_use, assignment.title)
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
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == 'true':
            return JsonResponse({'ok': True, 'message': 'Assignment deleted'})
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


@login_required
def assignment_deep_research(request, assignment_id):
    """
    Agentic Web Research Phase (SSE).
    Generates queries, searches Tavily, and streams progress.
    """
    import json, time
    from .search_service import generate_research_queries, perform_tavily_search

    assignment = get_object_or_404(Assignment, id=assignment_id, user=request.user)

    def stream():
        yield f"data: {json.dumps({'log': 'Initializing NEXA Intelligence Agent...'})}\n\n"
        time.sleep(0.5)
        
        prompt = assignment.text_content or assignment.title
        yield f"data: {json.dumps({'log': f'Mapping research vectors for: \"{prompt[:40]}...\"'})}\n\n"
        
        queries = generate_research_queries(prompt)
        all_findings = []
        all_sources = []
        
        for q in queries:
            yield f"data: {json.dumps({'log': f'Searching global databases for: \"{q}\"...'})}\n\n"
            search_data = perform_tavily_search(q)
            
            # Stream specific findings as cards
            for res in search_data.get('results', [])[:2]:
                yield f"data: {json.dumps({
                    'finding': {
                        'title': res['title'],
                        'url': res['url'],
                        'snippet': res['content'][:150] + '...'
                    }
                })}\n\n"
                all_sources.append({'title': res['title'], 'url': res['url']})
                all_findings.append(f"Source: {res['title']} ({res['url']})\nContent: {res['content']}\n")
            
            time.sleep(1.0) # For visual pacing
            
        # Finalize Research
        assignment.research_notes = "\n\n".join(all_findings)
        assignment.research_sources = {'sources': all_sources}
        assignment.save()
        
        yield f"data: {json.dumps({'log': 'Intelligence compiled. Ready for synthesis.', 'done': True})}\n\n"

    return StreamingHttpResponse(stream(), content_type='text/event-stream')

@login_required
def assignment_json(request, assignment_id):
    """Retrieve assignment details as JSON."""
    assignment = get_object_or_404(Assignment, id=assignment_id, user=request.user)
    content = ""
    if hasattr(assignment, 'result'):
        content = assignment.result.content
    
    return JsonResponse({
        'ok': True,
        'id': assignment.id,
        'title': assignment.title,
        'content': content,
        'status': assignment.status
    })
