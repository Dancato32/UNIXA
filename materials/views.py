from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, FileResponse
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
    """AJAX endpoint to generate podcast content from study material using AI."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=405)
    
    try:
        data = json.loads(request.body)
        material_id = data.get('material_id')
        
        material = get_object_or_404(StudyMaterial, pk=material_id, owner=request.user)
        
        if not material.extracted_text:
            return JsonResponse({'error': 'No text content available for this material'}, status=400)
        
        # Get the extracted text (truncated for processing)
        text_content = material.extracted_text[:4000] if material.extracted_text else ""
        
        # Build AI prompt for podcast generation
        prompt = build_podcast_prompt(text_content, material.title)
        
        # Generate podcast script using AI
        podcast_script = ask_ai(prompt, user=request.user, use_rag=False, learning_mode='explain')
        
        # Parse the AI response into structured segments
        segments = parse_podcast_response(podcast_script, material.title)
        
        # Generate audio for the podcast
        audio_filename = generate_podcast_audio(podcast_script, material.pk)
        
        return JsonResponse({
            'success': True,
            'podcast_script': segments,
            'material_title': material.title,
            'raw_content': podcast_script,
            'audio_url': f'/materials/podcast/audio/{material.pk}/'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def generate_podcast_audio(script_text, material_id):
    """Generate podcast audio using OpenAI TTS API."""
    try:
        from openai import OpenAI
        import os
        
        # Get API key - prefer direct OpenAI for TTS
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Try OpenRouter key
            api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not api_key:
            print("No API key found for TTS")
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
        # Using "nova" voice - sounds very natural and human-like
        response = client.audio.speech.create(
            model="tts-1",  # Standard TTS model
            voice="nova",   # Nova sounds very natural and friendly
            input=full_text,
            response_format="mp3"
        )
        
        # Save audio file
        response.stream_to_file(filepath)
        
        return filename
        
    except Exception as e:
        print(f"TTS Generation Error: {e}")
        return None


@login_required
def serve_podcast_audio(request, material_id):
    """Serve the generated podcast audio file."""
    try:
        # Find the latest podcast file for this material
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'podcasts')
        
        if not os.path.exists(audio_dir):
            return JsonResponse({'error': 'No audio found'}, status=404)
        
        # Get list of files for this material
        files = [f for f in os.listdir(audio_dir) if f.startswith(f'podcast_{material_id}_')]
        
        if not files:
            return JsonResponse({'error': 'No audio found'}, status=404)
        
        # Get most recent file
        latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(audio_dir, f)))
        filepath = os.path.join(audio_dir, latest_file)
        
        return FileResponse(open(filepath, 'rb'), content_type='audio/mpeg')
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
