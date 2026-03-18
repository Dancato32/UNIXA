from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, FileResponse, StreamingHttpResponse, HttpResponse
from django.conf import settings
from .models import StudyMaterial
from .forms import StudyMaterialForm
from ai_tutor.ai_utils import ask_ai
import os
import json
import uuid


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


def extract_text_from_memory(uploaded_file, file_extension):
    """Extract text from an in-memory uploaded file (used with cloud storage)."""
    import tempfile, shutil
    text = ""
    try:
        uploaded_file.seek(0)
        suffix = file_extension or '.tmp'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(uploaded_file, tmp)
            tmp_path = tmp.name
        text = extract_text_from_file(tmp_path, file_extension)
        os.remove(tmp_path)
    except Exception as e:
        text = f"[Error extracting text: {str(e)}]"
    return text


@login_required
def upload_material(request):
    """Allow logged-in students to upload study materials."""
    if request.method == 'POST':
        form = StudyMaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.owner = request.user
            material.save()
            uploaded_file = request.FILES.get('file')
            file_extension = os.path.splitext(uploaded_file.name)[1].lower() if uploaded_file else ''
            try:
                file_path = material.file.path
                extracted_text = extract_text_from_file(file_path, file_extension)
            except (NotImplementedError, ValueError, AttributeError):
                extracted_text = extract_text_from_memory(uploaded_file, file_extension)
            material.extracted_text = extracted_text
            material.save(update_fields=['extracted_text'])
            if extracted_text.startswith('[') and 'requires' in extracted_text:
                messages.warning(request, f'Material uploaded, but {extracted_text}')
            else:
                messages.success(request, 'Material uploaded successfully!')
            return redirect('list_materials')
    else:
        form = StudyMaterialForm()
    return render(request, 'materials/upload.html', {'form': form, 'title': 'Upload Study Material'})


@login_required
def upload_material_ajax(request):
    """AJAX upload endpoint — returns JSON so the frontend can show a progress bar."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    form = StudyMaterialForm(request.POST, request.FILES)
    if form.is_valid():
        material = form.save(commit=False)
        material.owner = request.user
        material.save()

        # Extract text — works with both local disk and Cloudinary storage
        uploaded_file = request.FILES.get('file')
        file_extension = os.path.splitext(uploaded_file.name)[1].lower() if uploaded_file else ''

        try:
            # Try local path first (local dev)
            file_path = material.file.path
            extracted_text = extract_text_from_file(file_path, file_extension)
        except (NotImplementedError, ValueError, AttributeError):
            # Cloudinary storage — read from the uploaded file in memory
            extracted_text = extract_text_from_memory(uploaded_file, file_extension)

        material.extracted_text = extracted_text
        material.save(update_fields=['extracted_text'])
        return JsonResponse({'success': True, 'redirect': '/materials/list/'})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


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
        material.delete()
        messages.success(request, 'Material deleted successfully.')
        return redirect('list_materials')
    
    return render(request, 'materials/delete.html', {
        'material': material,
        'title': 'Delete Material'
    })


@login_required
def podcast_view(request, pk):
    """View for the Podcast Learning Mode."""
    material = get_object_or_404(StudyMaterial, pk=pk, owner=request.user)
    
    return render(request, 'materials/podcast.html', {
        'material': material,
        'title': f'Podcast: {material.title}'
    })


@login_required
def generate_podcast_ajax(request):
    """AJAX endpoint to generate podcast script — TTS handled client-side."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=405)

    try:
        data = json.loads(request.body)
        material_id = data.get('material_id')

        material = get_object_or_404(StudyMaterial, pk=material_id, owner=request.user)

        if not material.extracted_text:
            return JsonResponse({'error': 'No text content available for this material'}, status=400)

        text_content = material.extracted_text[:4000]
        prompt = build_podcast_prompt(text_content, material.title)
        podcast_script = ask_ai(prompt, user=request.user, use_rag=False, learning_mode='explain')

        word_count = len(podcast_script.split())
        duration_mins = round(word_count / 130)

        return JsonResponse({
            'success': True,
            'raw_content': podcast_script,
            'material_title': material.title,
            'word_count': word_count,
            'duration_estimate': f'~{duration_mins} minutes',
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def generate_podcast_audio(script_text, material_id):
    """Generate podcast audio - now directly uses OpenAI TTS."""
    # OpenRouter doesn't support TTS, so we go straight to OpenAI
    return generate_podcast_audio_direct(script_text, material_id)


def generate_podcast_audio_direct(script_text, material_id):
    """Generate podcast audio using direct OpenAI TTS API."""
    try:
        from openai import OpenAI
        import os
        
        # Get direct OpenAI API key only
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("No direct OpenAI API key for TTS")
            return None
        
        # Create OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Prepare full text for audio (combine all segments)
        full_text = script_text
        if isinstance(script_text, dict):
            full_text = " ".join([seg['content'] for seg in script_text.get('segments', [])])
        
        # Limit text length for TTS
        full_text = full_text[:2500]
        
        if not full_text:
            return None
        
        # Create audio directory if not exists
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'podcasts')
        os.makedirs(audio_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"podcast_{material_id}_{uuid.uuid4().hex[:8]}.mp3"
        filepath = os.path.join(audio_dir, filename)
        
        # Generate speech using OpenAI's TTS
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=full_text,
            response_format="mp3"
        )
        
        # Save audio file
        response.stream_to_file(filepath)
        
        return filename
        
    except Exception as e:
        print(f"Direct TTS Error: {e}")
        return None


def generate_podcast_audio_elevenlabs(script_text, material_id):
    """Generate podcast audio using ElevenLabs TTS API for higher quality."""
    try:
        import os
        import requests
        
        # Get ElevenLabs API key
        api_key = os.environ.get("ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("No ElevenLabs API key found in environment")
            # Try to get from Django settings
            api_key = getattr(settings, 'ELEVENLABS_API_KEY', None)
            if not api_key:
                print("No ElevenLabs API key found in settings either")
                return None
        
        # Prepare full text for audio
        full_text = script_text
        if isinstance(script_text, dict):
            full_text = " ".join([seg['content'] for seg in script_text.get('segments', [])])
        
        full_text = full_text[:2500]
        
        if not full_text:
            print("No text content for TTS")
            return None
        
        # Create audio directory
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'podcasts')
        os.makedirs(audio_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"podcast_{material_id}_{uuid.uuid4().hex[:8]}.mp3"
        filepath = os.path.join(audio_dir, filename)
        
        # ElevenLabs TTS API call - using a popular voice
        # "Rachel" voice - most popular
        voice_id = "21m00Tcm4TlvDq8ikWAM"
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        data = {
            "text": full_text,
            "model_id": "eleven_multilingual_v2"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=120)
        
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"ElevenLabs audio generated successfully: {filename}")
            return filename
        else:
            print(f"ElevenLabs API Error {response.status_code}: {response.text[:200]}")
            return None
        
    except Exception as e:
        print(f"ElevenLabs TTS Exception: {e}")
        return None


def generate_podcast_audio_streaming(request, script_text, material_id):
    """Generate podcast audio using streaming TTS for immediate playback."""
    try:
        from openai import OpenAI
        import os
        
        # Get API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            return None, None
        
        client = OpenAI(api_key=api_key)
        
        # Prepare full text
        full_text = script_text
        if isinstance(script_text, dict):
            full_text = " ".join([seg['content'] for seg in script_text.get('segments', [])])
        
        full_text = full_text[:2500]
        
        if not full_text:
            return None, None
        
        # Create audio directory
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'podcasts')
        os.makedirs(audio_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"podcast_{material_id}_{uuid.uuid4().hex[:8]}.mp3"
        filepath = os.path.join(audio_dir, filename)
        
        # Generate with streaming for immediate playback
        response = client.audio.speech.create(
            model="tts-1-hd",  # Higher quality TTS
            voice="nova",
            input=full_text,
            response_format="mp3"
        )
        
        # Save while generating (streams to file)
        response.stream_to_file(filepath)
        
        return filename, filepath
        
    except Exception as e:
        print(f"Streaming TTS Error: {e}")
        return None, None


@login_required
def serve_podcast_audio(request, material_id, filename=None):
    """Serve the generated podcast audio file with HTTP Range support for browser <audio>."""
    try:
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'podcasts')

        if not os.path.exists(audio_dir):
            return HttpResponse('Audio not found', status=404)

        # Resolve filepath
        filepath = None
        if filename:
            candidate = os.path.join(audio_dir, filename)
            if os.path.exists(candidate):
                filepath = candidate
            else:
                matches = [f for f in os.listdir(audio_dir)
                           if f.startswith(f'podcast_{material_id}_') and filename in f]
                if matches:
                    filepath = os.path.join(audio_dir, matches[0])

        if not filepath:
            files = [f for f in os.listdir(audio_dir) if f.startswith(f'podcast_{material_id}_')]
            if not files:
                return HttpResponse('Audio not found', status=404)
            latest = max(files, key=lambda f: os.path.getctime(os.path.join(audio_dir, f)))
            filepath = os.path.join(audio_dir, latest)

        file_size = os.path.getsize(filepath)
        content_type = 'audio/mpeg'

        # Handle HTTP Range requests (required for browser audio seeking/streaming)
        range_header = request.META.get('HTTP_RANGE', '').strip()
        if range_header:
            range_match = range_header.replace('bytes=', '').split('-')
            first_byte = int(range_match[0]) if range_match[0] else 0
            last_byte = int(range_match[1]) if range_match[1] else file_size - 1
            last_byte = min(last_byte, file_size - 1)
            length = last_byte - first_byte + 1

            with open(filepath, 'rb') as f:
                f.seek(first_byte)
                data = f.read(length)

            response = HttpResponse(data, status=206, content_type=content_type)
            response['Content-Range'] = f'bytes {first_byte}-{last_byte}/{file_size}'
            response['Accept-Ranges'] = 'bytes'
            response['Content-Length'] = str(length)
            return response

        # Full file response
        response = FileResponse(open(filepath, 'rb'), content_type=content_type)
        response['Content-Length'] = str(file_size)
        response['Accept-Ranges'] = 'bytes'
        return response

    except Exception as e:
        return HttpResponse(str(e), status=500)


def build_podcast_prompt(text_content, title):
    """Build the AI prompt for generating a podcast-style lesson."""
    return f"""You are Nexa, an expert AI tutor creating a podcast-style audio lesson. Create an engaging, conversational podcast lesson from the following study material.

Title: {title}

Instructions:
1. Write as if you're a friendly, knowledgeable teacher giving an audio lesson
2. Use a conversational tone - like talking to a student
3. Break concepts into clear, digestible segments
4. Include real-world examples where appropriate
5. Use simple language that's easy to understand

Structure your response with these markers:
- INTRO: [Welcome message and topic introduction]
- CONCEPT_1: [First main concept explained conversationally]
- CONCEPT_2: [Second main concept]
- CONCEPT_3: [Third main concept] 
- EXAMPLE: [Real-world example or application]
- SUMMARY: [Key takeaways and review]
- OUTRO: [Closing message and encouragement]

Make it engaging and educational! Write complete sentences as if speaking.

Content to convert:
{text_content}

Now create your podcast lesson:"""


def parse_podcast_response(ai_response, title):
    """Parse the AI response into structured podcast segments."""
    import re
    
    segments = []
    
    # Default structure
    default_segments = [
        {'type': 'intro', 'title': 'Welcome to Your Learning Podcast', 'content': f"Hello learner! Welcome to this podcast on {title}. I'm excited to help you understand this topic today. Let's dive in!", 'visual': 'intro'},
        {'type': 'concept', 'title': 'Getting Started', 'content': 'Loading your personalized learning content...', 'visual': 'loading'},
    ]
    
    # Try to parse the AI response
    try:
        # Split by segment markers
        segment_pattern = r'-(INTRO|CONCEPT_\d+|EXAMPLE|SUMMARY|OUTRO):\s*'
        parts = re.split(segment_pattern, ai_response)
        
        if len(parts) > 1:
            # We have segmented content
            i = 1
            while i < len(parts):
                marker = parts[i].strip() if i < len(parts) else ''
                content = parts[i+1].strip() if i+1 < len(parts) else ''
                
                if content:
                    segment_type = 'intro' if 'INTRO' in marker.upper() else 'concept'
                    if 'EXAMPLE' in marker.upper():
                        segment_type = 'example'
                    elif 'SUMMARY' in marker.upper():
                        segment_type = 'summary'
                    elif 'OUTRO' in marker.upper():
                        segment_type = 'outro'
                    
                    # Extract title from first line if possible
                    lines = content.split('\n')
                    segment_title = lines[0].strip() if lines else marker.replace('_', ' ').title()
                    segment_content = ' '.join(lines[1:]) if len(lines) > 1 else content
                    
                    segments.append({
                        'type': segment_type,
                        'title': segment_title[:50],
                        'content': segment_content[:500],
                        'visual': segment_type
                    })
                
                i += 2
        
        # If no segments parsed, create from raw content
        if not segments:
            # Split by paragraphs
            paragraphs = ai_response.split('\n\n')
            for i, para in enumerate(paragraphs[:8]):
                if para.strip() and len(para.strip()) > 20:
                    seg_type = 'intro' if i == 0 else 'summary' if i >= len(paragraphs) - 2 else 'concept'
                    segments.append({
                        'type': seg_type,
                        'title': f"Part {i+1}" if seg_type == 'concept' else ('Introduction' if seg_type == 'intro' else 'Summary'),
                        'content': para.strip()[:500],
                        'visual': seg_type
                    })
    except Exception as e:
        # Fallback to default
        pass
    
    # Ensure we have at least some content
    if not segments:
        # Create basic segments from raw response
        content_lines = ai_response.split('\n')
        meaningful_lines = [l.strip() for l in content_lines if len(l.strip()) > 30][:10]
        
        for i, line in enumerate(meaningful_lines):
            seg_type = 'intro' if i == 0 else 'summary' if i >= len(meaningful_lines) - 1 else 'concept'
            segments.append({
                'type': seg_type,
                'title': f'Section {i+1}',
                'content': line,
                'visual': seg_type
            })
    
    # Ensure minimum segments
    if len(segments) < 3:
        segments = default_segments + segments
    
    return {
        'title': f"Learning: {title}",
        'segments': segments[:10]  # Limit to 10 segments max
    }


@login_required
def materials_count_api(request):
    """API endpoint to get count of user's study materials."""
    count = StudyMaterial.objects.filter(owner=request.user).count()
    return JsonResponse({'count': count})


@login_required
def podcast_question_ajax(request):
    """AJAX endpoint to answer questions about podcast content."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=405)
    
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        podcast_context = data.get('podcast_context', '')
        material_id = data.get('material_id')
        
        if not question:
            return JsonResponse({'error': 'Question is required'}, status=400)
        
        # Build AI prompt with podcast context
        prompt = f"""You are Nexa, an AI tutor helping a student understand their study material. 

The student is listening to a podcast about their study material and has paused to ask a question.

Podcast Content:
{podcast_context[:2000]}

Student's Question: {question}

Provide a clear, concise answer (2-3 sentences) that directly addresses their question. Be friendly and encouraging."""
        
        # Get AI answer
        answer = ask_ai(prompt, user=request.user, use_rag=False, learning_mode='explain')
        
        # Generate audio for the answer using the same TTS system
        audio_filename = None
        
        # Try ElevenLabs first
        try:
            audio_filename = generate_answer_audio_elevenlabs(answer, material_id)
        except Exception as e:
            print(f"ElevenLabs TTS failed: {e}")
        
        # Fall back to OpenAI TTS
        if not audio_filename:
            try:
                audio_filename = generate_answer_audio_openai(answer, material_id)
            except Exception as e:
                print(f"OpenAI TTS failed: {e}")
        
        # Build audio URL
        audio_url = None
        if audio_filename:
            audio_url = f'/materials/podcast/answer-audio/{material_id}/{audio_filename}'
        
        return JsonResponse({
            'success': True,
            'answer': answer,
            'audio_url': audio_url
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def generate_answer_audio_elevenlabs(answer_text, material_id):
    """Generate answer audio using ElevenLabs TTS."""
    try:
        import os
        import requests
        
        api_key = os.environ.get("ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            api_key = getattr(settings, 'ELEVENLABS_API_KEY', None)
            if not api_key:
                return None
        
        # Limit text length
        text = answer_text[:1000]
        
        if not text:
            return None
        
        # Create audio directory
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'podcast_answers')
        os.makedirs(audio_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"answer_{material_id}_{uuid.uuid4().hex[:8]}.mp3"
        filepath = os.path.join(audio_dir, filename)
        
        # ElevenLabs API call - using Rachel voice
        voice_id = "21m00Tcm4TlvDq8ikWAM"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2"
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=60)
        
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filename
        else:
            print(f"ElevenLabs API Error {response.status_code}: {response.text[:200]}")
            return None
        
    except Exception as e:
        print(f"ElevenLabs answer TTS Exception: {e}")
        return None


def generate_answer_audio_openai(answer_text, material_id):
    """Generate answer audio using OpenAI TTS."""
    try:
        from openai import OpenAI
        import os
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        
        client = OpenAI(api_key=api_key)
        
        # Limit text length
        text = answer_text[:1000]
        
        if not text:
            return None
        
        # Create audio directory
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'podcast_answers')
        os.makedirs(audio_dir, exist_ok=True)
        
        # Generate unique filename
        filename = f"answer_{material_id}_{uuid.uuid4().hex[:8]}.mp3"
        filepath = os.path.join(audio_dir, filename)
        
        # Generate speech
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            response_format="mp3"
        )
        
        response.stream_to_file(filepath)
        
        return filename
        
    except Exception as e:
        print(f"OpenAI answer TTS Exception: {e}")
        return None


@login_required
def serve_answer_audio(request, material_id, filename):
    """Serve the generated answer audio file."""
    try:
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'podcast_answers')
        filepath = os.path.join(audio_dir, filename)
        
        if os.path.exists(filepath):
            return FileResponse(open(filepath, 'rb'), content_type='audio/mpeg')
        
        return JsonResponse({'error': 'Audio file not found'}, status=404)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def summarize_view(request, pk):
    """Dedicated page: AI summary of a study material."""
    material = get_object_or_404(StudyMaterial, pk=pk, owner=request.user)
    return render(request, 'materials/summarize.html', {
        'material': material, 'title': f'Summary: {material.title}'
    })


@login_required
def summarize_ajax(request, pk):
    """AJAX: generate summary."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    material = get_object_or_404(StudyMaterial, pk=pk, owner=request.user)
    if not material.extracted_text:
        return JsonResponse({'error': 'No text could be extracted from this material. Try re-uploading it.'}, status=400)
    prompt = f"""Summarize the following study material titled "{material.title}" in clear, structured paragraphs.
Cover all main ideas, key concepts, and important details. Write for a student reviewing for an exam.
Do not use markdown bold (**). Use plain text only.

Content:
{material.extracted_text[:4000]}

Summary:"""
    try:
        result = ask_ai(prompt, user=request.user, use_rag=False, learning_mode='explain')
        return JsonResponse({'success': True, 'result': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def quiz_view(request, pk):
    """Dedicated page: AI-generated quiz from a study material."""
    material = get_object_or_404(StudyMaterial, pk=pk, owner=request.user)
    return render(request, 'materials/quiz.html', {
        'material': material, 'title': f'Quiz: {material.title}'
    })


@login_required
def quiz_ajax(request, pk):
    """AJAX: generate quiz."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    material = get_object_or_404(StudyMaterial, pk=pk, owner=request.user)
    if not material.extracted_text:
        return JsonResponse({'error': 'No text could be extracted from this material.'}, status=400)
    prompt = f"""Create a 5-question multiple choice quiz from this study material. Be concise.

Format EXACTLY (no extra text):

Q1: [question]
A. [option]
B. [option]
C. [option]
D. [option]
Answer: [A/B/C/D]
Explanation: [one sentence why the answer is correct]

Q2: ...

Material ({material.title}):
{material.extracted_text[:2000]}"""
    try:
        raw = ask_ai(prompt, user=request.user, use_rag=False, learning_mode='explain')
        import re
        questions = []
        blocks = re.split(r'\n(?=Q\d+:)', raw.strip())
        for block in blocks:
            q_match = re.search(r'Q\d+:\s*(.+?)(?=\nA\.)', block, re.DOTALL)
            opts = {}
            for letter in ['A', 'B', 'C', 'D']:
                m = re.search(rf'{letter}\.\s*(.+?)(?=\n[A-D]\.|Answer:|$)', block, re.DOTALL)
                if m:
                    opts[letter] = m.group(1).strip()
            ans_match = re.search(r'Answer:\s*([A-D])', block, re.IGNORECASE)
            exp_match = re.search(r'Explanation:\s*(.+?)$', block, re.DOTALL | re.IGNORECASE)
            if q_match and ans_match and len(opts) >= 2:
                questions.append({
                    'q': q_match.group(1).strip(),
                    'opts': opts,
                    'ans': ans_match.group(1).upper(),
                    'explanation': exp_match.group(1).strip() if exp_match else ''
                })
        return JsonResponse({'success': True, 'questions': questions})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def flashcards_view(request, pk):
    """Dedicated page: AI-generated flashcards from a study material."""
    material = get_object_or_404(StudyMaterial, pk=pk, owner=request.user)
    return render(request, 'materials/flashcards.html', {
        'material': material, 'title': f'Flashcards: {material.title}'
    })


@login_required
def flashcards_ajax(request, pk):
    """AJAX: generate flashcards."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    material = get_object_or_404(StudyMaterial, pk=pk, owner=request.user)
    if not material.extracted_text:
        return JsonResponse({'error': 'No text could be extracted from this material.'}, status=400)
    prompt = f"""Create 15 flashcards from the study material titled "{material.title}".

Format each flashcard EXACTLY like this, separated by a blank line:
FRONT: [term or concept — keep it short]
BACK: [clear definition or explanation]

FRONT: [next term]
BACK: [definition]

Content:
{material.extracted_text[:4000]}

Flashcards:"""
    try:
        raw = ask_ai(prompt, user=request.user, use_rag=False, learning_mode='explain')
        import re
        pairs = re.findall(r'FRONT:\s*(.+?)\nBACK:\s*(.+?)(?=\nFRONT:|\Z)', raw, re.DOTALL)
        cards = [{'front': f.strip(), 'back': b.strip()} for f, b in pairs]
        if not cards:
            blocks = [b.strip() for b in raw.split('\n\n') if b.strip()]
            for block in blocks:
                lines = [l.strip() for l in block.split('\n') if l.strip()]
                if len(lines) >= 2:
                    cards.append({'front': lines[0], 'back': ' '.join(lines[1:])})
        return JsonResponse({'success': True, 'cards': cards})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def select_material_for_action(request, action):
    """Page to select a material before performing an action (summarize/quiz/flashcards/podcast)."""
    materials = StudyMaterial.objects.filter(owner=request.user)
    return render(request, 'materials/select_material.html', {
        'materials': materials, 'action': action, 'title': f'Select Material — {action.title()}'
    })


@login_required
def wiki_image_ajax(request):
    """Search Wikipedia for an image relevant to a query keyword. No API key needed."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        import urllib.request
        import urllib.parse
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        if not query:
            return JsonResponse({'image_url': None})

        # Step 1: search Wikipedia for the best matching article
        search_url = (
            'https://en.wikipedia.org/w/api.php?action=query&list=search'
            '&srsearch=' + urllib.parse.quote(query) +
            '&srlimit=1&format=json&origin=*'
        )
        req = urllib.request.Request(search_url, headers={'User-Agent': 'NexaApp/1.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            search_data = json.loads(r.read())

        results = search_data.get('query', {}).get('search', [])
        if not results:
            return JsonResponse({'image_url': None})

        title = results[0]['title']

        # Step 2: get the page's main image
        image_url_api = (
            'https://en.wikipedia.org/w/api.php?action=query&titles='
            + urllib.parse.quote(title) +
            '&prop=pageimages&pithumbsize=600&format=json&origin=*'
        )
        req2 = urllib.request.Request(image_url_api, headers={'User-Agent': 'NexaApp/1.0'})
        with urllib.request.urlopen(req2, timeout=5) as r2:
            img_data = json.loads(r2.read())

        pages = img_data.get('query', {}).get('pages', {})
        image_url = None
        for page in pages.values():
            thumb = page.get('thumbnail', {})
            if thumb.get('source'):
                image_url = thumb['source']
                break

        return JsonResponse({'image_url': image_url, 'title': title})

    except Exception as e:
        # Silently fail — image is optional
        return JsonResponse({'image_url': None})
