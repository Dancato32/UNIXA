"""
RAG (Retrieval-Augmented Generation) pipeline for Research Workspaces.
Uses simple TF-IDF style chunking + OpenRouter LLM — no heavy vector DB needed.
"""
import os
import re


def extract_text_from_file(file_obj, file_type):
    """Extract plain text from uploaded PDF, DOCX, or TXT file."""
    try:
        if file_type == 'txt':
            return file_obj.read().decode('utf-8', errors='ignore')

        elif file_type == 'pdf':
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(file_obj)
                return '\n'.join(
                    page.extract_text() or '' for page in reader.pages
                )
            except Exception:
                return ''

        elif file_type == 'docx':
            try:
                from docx import Document
                doc = Document(file_obj)
                return '\n'.join(p.text for p in doc.paragraphs)
            except Exception:
                return ''

    except Exception:
        return ''
    return ''


def chunk_text(text, chunk_size=800, overlap=100):
    """Split text into overlapping chunks for context retrieval."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def find_relevant_chunks(query, chunks, top_k=4):
    """
    Simple keyword-based relevance scoring.
    Returns the top_k most relevant chunks for the query.
    """
    query_words = set(re.findall(r'\w+', query.lower()))
    scored = []
    for i, chunk in enumerate(chunks):
        chunk_words = set(re.findall(r'\w+', chunk.lower()))
        score = len(query_words & chunk_words)
        scored.append((score, i, chunk))
    scored.sort(reverse=True)
    return [chunk for _, _, chunk in scored[:top_k]]


def get_rag_context(query, workspace):
    """
    Build RAG context from all ready documents in a workspace.
    Returns (context_text, source_names).
    """
    from .models import WorkspaceDocument
    docs = WorkspaceDocument.objects.filter(workspace=workspace, status='ready')
    if not docs.exists():
        return '', []

    all_chunks = []
    source_map = {}  # chunk -> doc name

    for doc in docs:
        if not doc.extracted_text:
            continue
        chunks = chunk_text(doc.extracted_text)
        for chunk in chunks:
            all_chunks.append(chunk)
            source_map[chunk] = doc.name

    if not all_chunks:
        return '', []

    relevant = find_relevant_chunks(query, all_chunks)
    sources = list({source_map[c] for c in relevant if c in source_map})
    context = '\n\n---\n\n'.join(relevant)
    return context, sources


def get_openrouter_client():
    from openai import OpenAI
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError('OPENROUTER_API_KEY not set')
    return OpenAI(
        api_key=api_key,
        base_url='https://openrouter.ai/api/v1',
        default_headers={
            'HTTP-Referer': 'https://unixa.onrender.com',
            'X-Title': 'Nexa Research',
        }
    )


def build_research_system_prompt(subject='general'):
    base = """You are Nexa, an AI research assistant and tutor optimized for students.

Your job is to help students understand academic content clearly and simply.

RULES:
- Explain concepts like a teacher talking to a student
- Use simple English — avoid unnecessary jargon
- When jargon is needed, always explain it
- For WAEC/SHS subjects: align explanations to the syllabus level
- Use step-by-step breakdowns for math and science
- Use LaTeX for math: $expression$ for inline, $$expression$$ for display
- Give real-life examples where helpful
- Be encouraging and student-friendly
- When answering from documents, cite the source naturally
- If you don't know something, say so honestly"""

    subject_hints = {
        'mathematics': '\n\nSUBJECT: Mathematics — show all working steps, use LaTeX for all equations.',
        'physics': '\n\nSUBJECT: Physics — explain concepts with real-world examples, show formulas with LaTeX.',
        'chemistry': '\n\nSUBJECT: Chemistry — explain reactions clearly, use proper chemical notation.',
        'biology': '\n\nSUBJECT: Biology — use diagrams described in text, relate to real organisms.',
        'english': '\n\nSUBJECT: English — focus on grammar, comprehension, and essay structure.',
        'economics': '\n\nSUBJECT: Economics — use real-world examples, explain graphs clearly.',
    }
    return base + subject_hints.get(subject, '')


def ask_research_ai(message, workspace, history=None):
    """
    Main RAG chat function. Retrieves context from workspace docs and answers.
    Returns (response_text, sources_list).
    """
    context, sources = get_rag_context(message, workspace)
    client = get_openrouter_client()

    system = build_research_system_prompt(workspace.subject)
    if context:
        system += f'\n\nRELEVANT CONTENT FROM UPLOADED DOCUMENTS:\n{context[:3000]}'

    messages = [{'role': 'system', 'content': system}]
    if history:
        for h in history[-8:]:  # last 8 turns for memory
            messages.append({'role': h['role'], 'content': h['content']})
    messages.append({'role': 'user', 'content': message})

    response = client.chat.completions.create(
        model='openai/gpt-4o-mini',
        messages=messages,
        max_tokens=1200,
        temperature=0.7,
    )
    return response.choices[0].message.content, sources


def summarize_document(doc):
    """Generate a summary of a document."""
    if not doc.extracted_text:
        return 'No text extracted from this document.'

    client = get_openrouter_client()
    text = doc.extracted_text[:4000]

    response = client.chat.completions.create(
        model='openai/gpt-4o-mini',
        messages=[
            {
                'role': 'system',
                'content': (
                    'You are a student-friendly summarizer. '
                    'Summarize the document clearly for a high school student. '
                    'Include: 1) What the document is about, 2) Key points (bullet list), '
                    '3) Simple explanation of the main idea. Be concise and clear.'
                )
            },
            {'role': 'user', 'content': f'Summarize this document:\n\n{text}'}
        ],
        max_tokens=600,
        temperature=0.5,
    )
    return response.choices[0].message.content


def simplify_text(text, mode='explain'):
    """Simplify a piece of text for a student."""
    client = get_openrouter_client()

    mode_prompts = {
        'explain': 'Explain this text simply, like teaching a high school student. Use plain English.',
        'eli10': 'Explain this like I am 10 years old. Use very simple words and a fun analogy.',
        'exam': 'Rewrite this as a clear exam-style answer. Be precise and structured.',
        'summary': 'Give a quick 3-sentence summary of this text.',
    }
    instruction = mode_prompts.get(mode, mode_prompts['explain'])

    response = client.chat.completions.create(
        model='openai/gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': instruction},
            {'role': 'user', 'content': text[:2000]}
        ],
        max_tokens=500,
        temperature=0.6,
    )
    return response.choices[0].message.content


def search_papers(query):
    """Search Semantic Scholar for academic papers."""
    import requests as req
    try:
        url = 'https://api.semanticscholar.org/graph/v1/paper/search'
        params = {
            'query': query,
            'limit': 6,
            'fields': 'title,authors,abstract,year,externalIds,openAccessPdf'
        }
        r = req.get(url, params=params, timeout=8)
        if r.status_code == 200:
            data = r.json().get('data', [])
            results = []
            for p in data:
                authors = ', '.join(a.get('name', '') for a in p.get('authors', [])[:3])
                pdf_url = ''
                if p.get('openAccessPdf'):
                    pdf_url = p['openAccessPdf'].get('url', '')
                doi = p.get('externalIds', {}).get('DOI', '')
                link = f'https://doi.org/{doi}' if doi else f'https://www.semanticscholar.org/paper/{p.get("paperId","")}'
                results.append({
                    'title': p.get('title', 'Untitled'),
                    'authors': authors or 'Unknown',
                    'abstract': (p.get('abstract') or '')[:300],
                    'year': p.get('year', ''),
                    'link': link,
                    'pdf_url': pdf_url,
                })
            return results
    except Exception:
        pass
    return []
