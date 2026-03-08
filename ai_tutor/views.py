from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Conversation, EssayRequest
from .forms import ChatForm, EssayForm
from .ai_utils import ask_ai, deep_web_essay, generate_essay_with_sources, text_to_speech
import json


@login_required
def chat_ai(request):
    """AI Chat interface - displays chat with past conversations and input form."""
    if request.method == 'POST':
        form = ChatForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data['message']
            
            # Get AI response
            response = ask_ai(message, user=request.user, use_rag=True)
            
            # Save conversation
            Conversation.objects.create(
                user=request.user,
                message=message,
                response=response
            )
            
            messages.success(request, 'Response received!')
            return redirect('ai_chat')
    else:
        form = ChatForm()
    
    # Get past conversations for this user
    conversations = Conversation.objects.filter(user=request.user)[:50]
    
    return render(request, 'ai_tutor/chat.html', {
        'form': form,
        'conversations': conversations,
        'title': 'AI Tutor - Chat'
    })


@login_required
def chat_ajax(request):
    """AJAX endpoint for real-time chat without page reload."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            use_rag = data.get('use_rag', True)
            
            if not message:
                return JsonResponse({'error': 'Message cannot be empty'}, status=400)
            
            # Get AI response
            response = ask_ai(message, user=request.user, use_rag=use_rag)
            
            # Save conversation
            conversation = Conversation.objects.create(
                user=request.user,
                message=message,
                response=response
            )
            
            return JsonResponse({
                'success': True,
                'message': message,
                'response': response,
                'timestamp': conversation.created_at.strftime('%H:%M')
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def text_to_speech_view(request):
    """Convert text to speech and return audio."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            voice = data.get('voice', 'alloy')
            
            if not text:
                return JsonResponse({'error': 'Text cannot be empty'}, status=400)
            
            audio_content = text_to_speech(text, voice)
            
            if audio_content:
                response = HttpResponse(audio_content, content_type='audio/mpeg')
                response['Content-Disposition'] = 'attachment; filename="speech.mp3"'
                return response
            else:
                return JsonResponse({'error': 'TTS generation failed'}, status=500)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def essay_request(request):
    """Essay request interface - form for topic and list of past essays."""
    if request.method == 'POST':
        form = EssayForm(request.POST)
        if form.is_valid():
            topic = form.cleaned_data['topic']
            output_format = form.cleaned_data.get('output_format', 'text')
            word_count = int(form.cleaned_data.get('word_count') or 500)
            
            # Generate essay with research
            essay_text, sources = generate_essay_with_sources(topic, user=request.user, word_count=word_count)
            
            # Save essay request
            essay = EssayRequest.objects.create(
                user=request.user,
                topic=topic,
                word_count=word_count,
                research_done=True,
                essay_text=essay_text,
                output_format=output_format
            )
            
            messages.success(request, f'Essay generated on "{topic}"!')
            return redirect('essay_detail', essay_id=essay.id)
    else:
        form = EssayForm()
    
    # Get user's past essays
    essays = EssayRequest.objects.filter(user=request.user)
    paginator = Paginator(essays, 10)
    page_number = request.GET.get('page')
    essays_page = paginator.get_page(page_number)
    
    return render(request, 'ai_tutor/essay_request.html', {
        'form': form,
        'essays': essays_page,
        'title': 'AI Tutor - Essay Generator'
    })


@login_required
def essay_detail(request, essay_id):
    """View essay details."""
    essay = get_object_or_404(EssayRequest, id=essay_id, user=request.user)
    
    return render(request, 'ai_tutor/essay_detail.html', {
        'essay': essay,
        'title': f'Essay: {essay.topic}'
    })


@login_required
def delete_essay(request, essay_id):
    """Delete an essay request."""
    essay = get_object_or_404(EssayRequest, id=essay_id, user=request.user)
    
    if request.method == 'POST':
        essay.delete()
        messages.success(request, 'Essay deleted successfully.')
        return redirect('essay_request')
    
    return render(request, 'ai_tutor/essay_delete.html', {
        'essay': essay,
        'title': 'Delete Essay'
    })


@login_required
def clear_conversations(request):
    """Clear all chat conversations for the user."""
    if request.method == 'POST':
        Conversation.objects.filter(user=request.user).delete()
        messages.success(request, 'All conversations cleared.')
        return redirect('ai_chat')
    return redirect('ai_chat')


@login_required
def export_essay(request):
    """Export essay in the specified format."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            essay_text = data.get('essay_text', '')
            output_format = data.get('format', 'text')
            topic = data.get('topic', 'essay')
            
            if not essay_text:
                return JsonResponse({'error': 'No essay text provided'}, status=400)
            
            from io import BytesIO
            
            if output_format == 'word':
                from docx import Document
                doc = Document()
                doc.add_heading(topic, 0)
                for paragraph in essay_text.split('\n\n'):
                    if paragraph.strip():
                        doc.add_paragraph(paragraph.strip())
                
                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                response = HttpResponse(
                    buffer.getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
                response['Content-Disposition'] = f'attachment; filename="{topic[:30]}.docx"'
                return response
            
            elif output_format == 'pdf':
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=12)
                body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, spaceAfter=12)
                
                story = []
                story.append(Paragraph(topic, title_style))
                story.append(Spacer(1, 0.2*inch))
                
                for paragraph in essay_text.split('\n\n'):
                    if paragraph.strip():
                        story.append(Paragraph(paragraph.strip(), body_style))
                        story.append(Spacer(1, 0.1*inch))
                
                doc.build(story)
                buffer.seek(0)
                
                response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{topic[:30]}.pdf"'
                return response
            
            elif output_format == 'powerpoint':
                from pptx import Presentation
                from pptx.util import Inches, Pt
                
                prs = Presentation()
                prs.slide_width = Inches(10)
                prs.slide_height = Inches(7.5)
                
                title_slide_layout = prs.slide_layouts[0]
                slide = prs.slides.add_slide(title_slide_layout)
                title = slide.shapes.title
                subtitle = slide.placeholders[1]
                title.text = topic
                subtitle.text = "Generated by Nexa AI"
                
                bullet_slide_layout = prs.slide_layouts[1]
                
                sections = essay_text.split('\n\n')
                for section in sections[:8]:
                    if section.strip():
                        slide = prs.slides.add_slide(bullet_slide_layout)
                        title = slide.shapes.title
                        body = slide.placeholders[1]
                        tf = body.text_frame
                        tf.clear()
                        
                        lines = section.strip().split('\n')
                        if lines:
                            title.text = lines[0][:50]
                            for line in lines[1:]:
                                if line.strip():
                                    p = tf.add_paragraph()
                                    p.text = line.strip()
                                    p.level = 0
                
                buffer = BytesIO()
                prs.save(buffer)
                buffer.seek(0)
                
                response = HttpResponse(
                    buffer.getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation'
                )
                response['Content-Disposition'] = f'attachment; filename="{topic[:30]}.pptx"'
                return response
            
            else:
                response = HttpResponse(essay_text, content_type='text/plain')
                response['Content-Disposition'] = f'attachment; filename="{topic[:30]}.txt"'
                return response
                
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

