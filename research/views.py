import json
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import ResearchWorkspace, WorkspaceDocument, WorkspaceChat
from .rag import (
    extract_text_from_file, ask_research_ai,
    summarize_document, simplify_text, search_papers
)


@login_required
def research_home(request):
    """Research hub — SciSpace-style landing with all workspaces."""
    workspaces = ResearchWorkspace.objects.filter(user=request.user)
    return render(request, 'research/home.html', {'workspaces': workspaces})


@login_required
def workspace_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        subject = request.POST.get('subject', 'general')
        description = request.POST.get('description', '').strip()
        if not name:
            return JsonResponse({'error': 'Name required'}, status=400)
        ws = ResearchWorkspace.objects.create(
            user=request.user, name=name,
            subject=subject, description=description
        )
        return JsonResponse({'id': str(ws.id), 'name': ws.name})
    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
def workspace_delete(request, ws_id):
    ws = get_object_or_404(ResearchWorkspace, id=ws_id, user=request.user)
    if request.method == 'POST':
        ws.delete()
        return JsonResponse({'ok': True})
    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
def workspace_detail(request, ws_id):
    """Main workspace view — chat + documents."""
    ws = get_object_or_404(ResearchWorkspace, id=ws_id, user=request.user)
    docs = ws.documents.all()
    chats = ws.chats.all()
    return render(request, 'research/workspace.html', {
        'ws': ws,
        'docs': docs,
        'chats': chats,
    })


@login_required
@require_POST
def upload_document(request, ws_id):
    """Upload and process a document into the workspace."""
    ws = get_object_or_404(ResearchWorkspace, id=ws_id, user=request.user)
    f = request.FILES.get('file')
    if not f:
        return JsonResponse({'error': 'No file provided'}, status=400)

    ext = f.name.rsplit('.', 1)[-1].lower()
    if ext not in ('pdf', 'docx', 'txt'):
        return JsonResponse({'error': 'Only PDF, DOCX, TXT supported'}, status=400)

    doc = WorkspaceDocument.objects.create(
        workspace=ws, name=f.name, file=f, file_type=ext, status='processing'
    )

    # Extract text synchronously (fast enough for MVP)
    try:
        doc.file.open('rb')
        text = extract_text_from_file(doc.file, ext)
        doc.file.close()
        doc.extracted_text = text
        doc.status = 'ready' if text.strip() else 'error'
    except Exception as e:
        doc.status = 'error'
    doc.save()

    return JsonResponse({
        'id': str(doc.id),
        'name': doc.name,
        'status': doc.status,
        'file_type': doc.file_type,
    })


@login_required
@require_POST
def delete_document(request, ws_id, doc_id):
    ws = get_object_or_404(ResearchWorkspace, id=ws_id, user=request.user)
    doc = get_object_or_404(WorkspaceDocument, id=doc_id, workspace=ws)
    doc.delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def chat_message(request, ws_id):
    """Send a message and get an AI response using RAG."""
    ws = get_object_or_404(ResearchWorkspace, id=ws_id, user=request.user)
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        if not message:
            return JsonResponse({'error': 'Empty message'}, status=400)

        # Build history from recent chats
        recent = ws.chats.order_by('-created_at')[:16]
        history = [{'role': c.role, 'content': c.content} for c in reversed(recent)]

        # Save user message
        WorkspaceChat.objects.create(workspace=ws, role='user', content=message)

        # Get AI response
        response_text, sources = ask_research_ai(message, ws, history)

        # Save assistant message
        chat = WorkspaceChat.objects.create(
            workspace=ws, role='assistant',
            content=response_text, sources=sources
        )

        return JsonResponse({
            'response': response_text,
            'sources': sources,
            'timestamp': chat.created_at.strftime('%H:%M'),
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def clear_chat(request, ws_id):
    ws = get_object_or_404(ResearchWorkspace, id=ws_id, user=request.user)
    ws.chats.all().delete()
    return JsonResponse({'ok': True})


@login_required
def summarize_doc(request, ws_id, doc_id):
    """Summarize a specific document."""
    ws = get_object_or_404(ResearchWorkspace, id=ws_id, user=request.user)
    doc = get_object_or_404(WorkspaceDocument, id=doc_id, workspace=ws)
    try:
        summary = summarize_document(doc)
        return JsonResponse({'summary': summary})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def simplify_view(request, ws_id):
    """Simplify highlighted text."""
    ws = get_object_or_404(ResearchWorkspace, id=ws_id, user=request.user)
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        mode = data.get('mode', 'explain')
        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)
        result = simplify_text(text, mode)
        return JsonResponse({'result': result})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def tts_view(request, ws_id):
    """Server-side TTS via ElevenLabs (fallback: browser TTS used client-side)."""
    ws = get_object_or_404(ResearchWorkspace, id=ws_id, user=request.user)
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()[:2000]
        if not text:
            return JsonResponse({'error': 'No text'}, status=400)

        api_key = os.getenv('ELEVENLABS_API_KEY', '')
        if not api_key:
            return JsonResponse({'error': 'TTS not configured'}, status=503)

        import requests as req
        from django.http import HttpResponse
        resp = req.post(
            'https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM',
            headers={'xi-api-key': api_key, 'Content-Type': 'application/json'},
            json={'text': text, 'model_id': 'eleven_monolingual_v1',
                  'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75}},
            timeout=20
        )
        if resp.status_code == 200:
            return HttpResponse(resp.content, content_type='audio/mpeg')
        return JsonResponse({'error': 'TTS service error'}, status=502)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def search_papers_view(request, ws_id):
    """Search academic papers."""
    ws = get_object_or_404(ResearchWorkspace, id=ws_id, user=request.user)
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
    try:
        results = search_papers(query)
        return JsonResponse({'results': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def quick_ask(request):
    """Quick ask from the research home page (no workspace needed)."""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        mode = data.get('mode', 'auto')
        if not message:
            return JsonResponse({'error': 'Empty message'}, status=400)

        from .rag import get_openrouter_client, build_research_system_prompt
        client = get_openrouter_client()

        system = build_research_system_prompt()
        if mode == 'search':
            # Search papers and answer
            papers = search_papers(message)
            if papers:
                context = '\n'.join(f"- {p['title']} ({p['year']}): {p['abstract']}" for p in papers[:3])
                system += f'\n\nRelevant papers found:\n{context}'

        response = client.chat.completions.create(
            model='openai/gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': message}
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        return JsonResponse({'response': response.choices[0].message.content})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
