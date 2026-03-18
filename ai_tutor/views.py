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
            learning_mode = data.get('learning_mode', 'explain')  # Get learning mode from request
            
            if not message:
                return JsonResponse({'error': 'Message cannot be empty'}, status=400)
            
            # Fetch last 10 conversations for memory context
            recent = Conversation.objects.filter(user=request.user).order_by('-created_at')[:10]
            history = [{'message': c.message, 'response': c.response} for c in reversed(recent)]

            # Get AI response with learning mode and history
            response = ask_ai(message, user=request.user, use_rag=use_rag, learning_mode=learning_mode, history=history)
            
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
                # No TTS available — tell frontend to use browser TTS
                return JsonResponse({'error': 'tts_unavailable', 'use_browser_tts': True}, status=200)
                
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
    try:
        essay = EssayRequest.objects.get(id=essay_id, user=request.user)
    except EssayRequest.DoesNotExist:
        messages.error(request, 'Essay not found or already deleted.')
        return redirect('essay_request')
    
    if request.method == 'POST':
        essay.delete()
        messages.success(request, 'Essay deleted successfully.')
        return redirect('essay_request')
    
    return render(request, 'ai_tutor/essay_delete.html', {
        'essay': essay,
        'title': 'Delete Essay'
    })


@login_required
def chat_with_image(request):
    """AJAX endpoint: send a message + image to the AI (vision model)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    message = request.POST.get('message', '').strip() or 'What is in this image? Explain it as a tutor.'
    learning_mode = request.POST.get('learning_mode', 'explain')
    image_file = request.FILES.get('image')

    if not image_file:
        return JsonResponse({'error': 'No image provided'}, status=400)

    try:
        import base64
        from .ai_utils import get_openai_client

        image_data = base64.b64encode(image_file.read()).decode('utf-8')
        mime = image_file.content_type or 'image/jpeg'

        client = get_openai_client()
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": message},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_data}"}}
                    ]
                }
            ],
            max_tokens=1000,
        )
        ai_response = response.choices[0].message.content

        conversation = Conversation.objects.create(
            user=request.user,
            message=f"[Image] {message}",
            response=ai_response
        )

        return JsonResponse({
            'success': True,
            'response': ai_response,
            'timestamp': conversation.created_at.strftime('%H:%M')
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def web_search_ajax(request):
    """AJAX endpoint: perform a web search then answer with context."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        query = data.get('message', '').strip()
        learning_mode = data.get('learning_mode', 'explain')

        if not query:
            return JsonResponse({'error': 'Query cannot be empty'}, status=400)

        # Fetch search results via DuckDuckGo (no API key needed)
        import urllib.request
        import urllib.parse
        import re

        search_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            ddg = json.loads(resp.read().decode())

        snippets = []
        if ddg.get('AbstractText'):
            snippets.append(ddg['AbstractText'])
        for r in ddg.get('RelatedTopics', [])[:4]:
            if isinstance(r, dict) and r.get('Text'):
                snippets.append(r['Text'])

        web_context = '\n'.join(snippets[:5]) if snippets else ''

        from .ai_utils import get_openai_client
        client = get_openai_client()

        system = """You are Nexa, an AI tutor. The user asked a question and web search results are provided below.
Use the search results to give an accurate, up-to-date answer. Cite facts from the results naturally.
Format your answer in clear steps or paragraphs as appropriate. Use LaTeX for any math."""

        user_content = f"Question: {query}"
        if web_context:
            user_content += f"\n\nWeb search results:\n{web_context}"

        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        ai_response = response.choices[0].message.content

        conversation = Conversation.objects.create(
            user=request.user,
            message=f"[Web Search] {query}",
            response=ai_response
        )

        return JsonResponse({
            'success': True,
            'response': ai_response,
            'timestamp': conversation.created_at.strftime('%H:%M'),
            'web_used': bool(web_context)
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def chat_stream(request):
    """SSE streaming endpoint — streams AI response token by token."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        use_rag = data.get('use_rag', True)
        learning_mode = data.get('learning_mode', 'explain')

        if not message:
            return JsonResponse({'error': 'Empty message'}, status=400)

        from .ai_utils import get_openai_client, get_study_materials_for_rag, build_system_prompt
        from django.http import StreamingHttpResponse

        recent = Conversation.objects.filter(user=request.user).order_by('-created_at')[:10]
        history = [{'message': c.message, 'response': c.response} for c in reversed(recent)]

        client = get_openai_client()
        system_message = build_system_prompt(learning_mode, use_rag, request.user)

        messages_list = [{"role": "system", "content": system_message}]
        for h in history:
            messages_list.append({"role": "user", "content": h['message']})
            messages_list.append({"role": "assistant", "content": h['response']})
        messages_list.append({"role": "user", "content": message})

        def event_stream():
            full_response = []
            try:
                stream = client.chat.completions.create(
                    model="openai/gpt-4o-mini",
                    messages=messages_list,
                    max_tokens=1000,
                    temperature=0.7,
                    stream=True,
                )
                for chunk in stream:
                    token = chunk.choices[0].delta.content or ''
                    if token:
                        full_response.append(token)
                        # SSE format: data: <token>\n\n
                        yield f"data: {json.dumps({'token': token})}\n\n"

                # Save full response to DB
                complete = ''.join(full_response)
                Conversation.objects.create(
                    user=request.user,
                    message=message,
                    response=complete,
                )
                yield f"data: {json.dumps({'done': True})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def clear_conversations(request):
    """Clear all chat conversations for the user."""
    if request.method == 'POST':
        Conversation.objects.filter(user=request.user).delete()
        messages.success(request, 'All conversations cleared.')
        return redirect('ai_chat')
    return redirect('ai_chat')


@login_required
def essay_save_edits(request, essay_id):
    """Save user edits to essay text."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    essay = get_object_or_404(EssayRequest, id=essay_id, user=request.user)
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        if content:
            essay.essay_text = content
            essay.save()
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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


@login_required
def ai_material_action(request):
    """AJAX endpoint for AI actions on study materials (summarize, quiz, flashcards, explain)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        action = data.get('action', '')
        material_title = data.get('material_title', 'Material')
        extracted_text = data.get('extracted_text', '')
        
        if not extracted_text:
            return JsonResponse({'success': False, 'error': 'No text content available to analyze.'})
        
        prompt = build_material_prompt(action, material_title, extracted_text, data)
        response = ask_ai(prompt, user=request.user, use_rag=False)
        
        return JsonResponse({'success': True, 'response': response})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def build_material_prompt(action, material_title, extracted_text, data=None):
    """Build the appropriate prompt based on the action."""
    
    text_preview = extracted_text[:3000]
    
    prompts = {
        'summarize': f"""You are an expert study assistant. Please provide a clear and comprehensive summary of the following content from "{material_title}". 

Focus on:
- Main ideas and key concepts
- Important details and supporting points
- Any definitions or formulas mentioned

Write in clear paragraphs, not bullet points. Make it suitable for study review.

Content:
{text_preview}

Summary:""",

        'quiz': f"""You are an expert study assistant. Create a quiz with 5 multiple choice questions based on the following content from "{material_title}".

For each question:
1. Make it test understanding, not just memorization
2. Provide 4 options (A, B, C, D)
3. Indicate the correct answer

Format your response like this:
Q1: [Your question here]
A. [Option A]
B. [Option B]
C. [Option C]
D. [Option D]
Answer: [Letter]

Content:
{text_preview}

Quiz:""",

        'flashcards': f"""You are an expert study assistant. Create 10 flashcards based on the following content from "{material_title}".

For each flashcard:
- Front: Key term or concept (brief, 1-3 words)
- Back: Definition or explanation (clear, concise)

Format your response as:
Term: Definition

Example:
Photosynthesis: The process by which plants convert light energy into chemical energy

Create at least 10 useful flashcards:

Content:
{text_preview}

Flashcards:""",

        'explain': f"""You are an expert teacher. Explain the key concepts from "{material_title}" in simple, easy-to-understand terms.

Your explanation should:
- Break down complex ideas into simpler parts
- Use analogies where helpful
- Be suitable for a student learning the topic for the first time
- Include examples where relevant

Write in clear paragraphs:

Content:
{text_preview}

Explanation:"""
    }
    
    if action == 'ask':
        user_message = data.get('message', '') if data else ''
        return f"""You are an expert study assistant helping with "{material_title}".

The student asks: {user_message}

Based on the following content, provide a helpful answer:

Content:
{text_preview}

Answer:"""
    
    return prompts.get(action, prompts['explain'])

