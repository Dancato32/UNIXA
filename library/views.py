from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
import io

from .models import SubjectBook, Resource, SUBJECTS, SUBJECT_TOPICS, SUBJECT_LEVELS
from .ai import ai_teach_topic, book_teach_topic, generate_quiz, grade_quiz, generate_podcast_script

SUBJECT_META = {
    'mathematics':  {'icon': '∑',   'color': '#3b82f6', 'desc': 'Algebra, Calculus, Statistics & more'},
    'physics':      {'icon': '⚛',   'color': '#8b5cf6', 'desc': 'Mechanics, Waves, Electricity & more'},
    'chemistry':    {'icon': '⚗',   'color': '#10b981', 'desc': 'Organic, Inorganic, Physical Chemistry'},
    'biology':      {'icon': '🧬',  'color': '#f59e0b', 'desc': 'Cells, Genetics, Ecology & more'},
    'economics':    {'icon': '📈',  'color': '#ef4444', 'desc': 'Micro, Macro, Trade & Finance'},
    'world_history':{'icon': '🌍',  'color': '#f97316', 'desc': 'Ancient, Modern & Contemporary History'},
    'english':      {'icon': '✍',   'color': '#06b6d4', 'desc': 'Comprehension, Grammar, Essay Writing'},
    'literature':   {'icon': '📖',  'color': '#ec4899', 'desc': 'Poetry, Prose, Drama & Analysis'},
    'art_design':   {'icon': '🎨',  'color': '#a855f7', 'desc': 'Visual Arts, Design Principles'},
    'music_theory': {'icon': '🎵',  'color': '#14b8a6', 'desc': 'Notation, Harmony, Composition'},
    'programming':  {'icon': '</>',  'color': '#22c55e', 'desc': 'Python, Web, Algorithms & more'},
    'geography':    {'icon': '🗺',  'color': '#f59e0b', 'desc': 'Physical, Human & Regional Geography'},
}


def _extract_pdf_text(file_field):
    """Extract text from a PDF FileField. Returns empty string on failure."""
    try:
        import PyPDF2
        file_field.seek(0)
        reader = PyPDF2.PdfReader(io.BytesIO(file_field.read()))
        pages = []
        for page in reader.pages[:30]:  # cap at 30 pages
            text = page.extract_text()
            if text:
                pages.append(text)
        return '\n'.join(pages)
    except Exception:
        return ''


@login_required
def library_home(request):
    subjects = []
    for key, label in SUBJECTS:
        meta = SUBJECT_META.get(key, {})
        book_count = SubjectBook.objects.filter(subject=key).count()
        topic_count = len(SUBJECT_TOPICS.get(key, []))
        subjects.append({
            'key': key,
            'label': label,
            'icon': meta.get('icon', '📚'),
            'color': meta.get('color', '#888'),
            'desc': meta.get('desc', ''),
            'book_count': book_count,
            'topic_count': topic_count,
        })
    return render(request, 'library/home.html', {'subjects': subjects})


@login_required
def subject_page(request, subject_key):
    subject_dict = dict(SUBJECTS)
    if subject_key not in subject_dict:
        from django.http import Http404
        raise Http404
    subject_label = subject_dict[subject_key]
    levels = SUBJECT_LEVELS.get(subject_key, {})
    books = SubjectBook.objects.filter(subject=subject_key)
    meta = SUBJECT_META.get(subject_key, {})
    # Build level summary for display
    level_list = []
    for level_name, topics in levels.items():
        level_list.append({
            'name': level_name,
            'slug': level_name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('/', '-'),
            'topic_count': len(topics),
        })
    return render(request, 'library/subject.html', {
        'subject_key': subject_key,
        'subject_label': subject_label,
        'level_list': level_list,
        'books': books,
        'meta': meta,
    })


@login_required
def level_page(request, subject_key, level_slug):
    subject_dict = dict(SUBJECTS)
    if subject_key not in subject_dict:
        from django.http import Http404
        raise Http404
    subject_label = subject_dict[subject_key]
    levels = SUBJECT_LEVELS.get(subject_key, {})
    # Match level by slug
    level_name = None
    topics = []
    for name, topic_list in levels.items():
        slug = name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('/', '-')
        if slug == level_slug:
            level_name = name
            topics = topic_list
            break
    if level_name is None:
        from django.http import Http404
        raise Http404
    books = SubjectBook.objects.filter(subject=subject_key)
    meta = SUBJECT_META.get(subject_key, {})
    # Build topic list with pre-computed slugs
    topic_list_with_slugs = []
    for t in topics:
        slug = t.lower().replace(' ', '-').replace("'", '').replace('&', 'and').replace('(', '').replace(')', '').replace('/', '-')
        topic_list_with_slugs.append({'name': t, 'slug': slug})
    return render(request, 'library/level.html', {
        'subject_key': subject_key,
        'subject_label': subject_label,
        'level_name': level_name,
        'level_slug': level_slug,
        'topics': topics,
        'topic_list': topic_list_with_slugs,
        'books': books,
        'meta': meta,
    })


@login_required
def topic_page(request, subject_key, topic_slug):
    subject_dict = dict(SUBJECTS)
    if subject_key not in subject_dict:
        from django.http import Http404
        raise Http404
    subject_label = subject_dict[subject_key]
    all_topics = SUBJECT_TOPICS.get(subject_key, [])
    topic_name = topic_slug.replace('-', ' ').title()
    for t in all_topics:
        if t.lower().replace(' ', '-').replace("'", '').replace('&', 'and').replace('(', '').replace(')', '') == topic_slug:
            topic_name = t
            break
    # Find which level this topic belongs to
    levels = SUBJECT_LEVELS.get(subject_key, {})
    level_name = None
    level_slug = None
    for name, topic_list in levels.items():
        if topic_name in topic_list:
            level_name = name
            level_slug = name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('/', '-')
            break
    books = SubjectBook.objects.filter(subject=subject_key)
    meta = SUBJECT_META.get(subject_key, {})
    return render(request, 'library/topic.html', {
        'subject_key': subject_key,
        'subject_label': subject_label,
        'topic_name': topic_name,
        'topic_slug': topic_slug,
        'level_name': level_name,
        'level_slug': level_slug,
        'books': books,
        'meta': meta,
    })


# ── API endpoints ──────────────────────────────────────────────────────────────

@login_required
def api_ai_teach(request):
    """AI teaches from its own knowledge."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        subject = data.get('subject', '')
        topic = data.get('topic', '')
        question = data.get('question', 'Teach me this topic')
        answer = ai_teach_topic(subject, topic, question)
        return JsonResponse({'success': True, 'response': answer})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_book_teach(request):
    """AI teaches using an uploaded book."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        subject = data.get('subject', '')
        topic = data.get('topic', '')
        book_id = data.get('book_id')
        question = data.get('question', 'Teach me this topic')

        book = get_object_or_404(SubjectBook, pk=book_id)
        book_text = _extract_pdf_text(book.file)
        if not book_text:
            return JsonResponse({'error': 'Could not extract text from this book. Make sure it is a text-based PDF.'}, status=400)

        answer = book_teach_topic(subject, topic, book_text, question)
        return JsonResponse({'success': True, 'response': answer})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_quiz(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        subject = data.get('subject', '')
        topic = data.get('topic', '')
        book_id = data.get('book_id')
        book_text = None
        if book_id:
            book = get_object_or_404(SubjectBook, pk=book_id)
            book_text = _extract_pdf_text(book.file)
        quiz = generate_quiz(subject, topic, book_text=book_text)
        if 'error' in quiz:
            return JsonResponse({'error': quiz['error']}, status=500)
        return JsonResponse({'success': True, 'quiz': quiz})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_grade(request):
    """Grade student quiz answers and return feedback."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        subject = data.get('subject', '')
        topic = data.get('topic', '')
        mc_questions = data.get('mc_questions', [])
        mc_answers = data.get('mc_answers', [])
        theory_questions = data.get('theory_questions', [])
        theory_answers = data.get('theory_answers', [])
        result = grade_quiz(subject, topic, mc_questions, mc_answers, theory_questions, theory_answers)
        if 'error' in result:
            return JsonResponse({'error': result['error']}, status=500)
        return JsonResponse({'success': True, 'result': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_podcast(request):
    """Generate a full podcast script and Resemble.ai audio."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        import os, requests as req, base64, uuid as _uuid
        from django.conf import settings as django_settings

        data = json.loads(request.body)
        subject = data.get('subject', '')
        topic = data.get('topic', '')
        level = data.get('level', None)

        script = generate_podcast_script(subject, topic, level=level)

        word_count = len(script.split())
        duration_mins = round(word_count / 130)

        # Generate Resemble.ai audio with custom NEXA voice
        audio_url = None
        try:
            api_key = os.environ.get('RESEMBLE_API_KEY', '')
            if api_key:
                voice_uuid = 'f644f59c'  # My Custom Voice NEXA
                resp = req.post(
                    'https://f.cluster.resemble.ai/synthesize',
                    headers={'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'},
                    json={'voice_uuid': voice_uuid, 'data': script[:2000], 'output_format': 'mp3'},
                    timeout=120
                )
                if resp.status_code == 200:
                    audio_b64 = resp.json().get('audio_content')
                    if audio_b64:
                        audio_dir = os.path.join(django_settings.MEDIA_ROOT, 'podcasts')
                        os.makedirs(audio_dir, exist_ok=True)
                        filename = f'podcast_lib_{_uuid.uuid4().hex[:8]}.mp3'
                        with open(os.path.join(audio_dir, filename), 'wb') as f:
                            f.write(base64.b64decode(audio_b64))
                        audio_url = f'/materials/podcast/audio/0/{filename}'
                        print(f'[RESEMBLE] library podcast audio saved: {filename}')
                else:
                    print(f'[RESEMBLE] Error {resp.status_code}: {resp.text[:200]}')
        except Exception as e:
            print(f'[RESEMBLE] library podcast exception: {e}')

        return JsonResponse({
            'success': True,
            'script': script,
            'audio_url': audio_url,
            'duration_estimate': f'~{duration_mins} minutes',
            'word_count': word_count,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Legacy endpoints (keep old resource-based API working)
@login_required
def api_teach(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        resource = get_object_or_404(Resource, pk=data.get('resource_id'))
        question = data.get('question', 'Teach me this topic')
        from .ai import teach_resource
        answer = teach_resource(resource.get_subject_display(), resource.topic, resource.content, question)
        return JsonResponse({'success': True, 'response': answer})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
