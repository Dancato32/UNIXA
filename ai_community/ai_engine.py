"""
AI engine for community features.
Uses existing OpenRouter setup — no new API keys needed.
"""
import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


def _client():
    api_key = os.getenv('OPENROUTER_API_KEY', '')
    return OpenAI(
        api_key=api_key,
        base_url='https://openrouter.ai/api/v1',
        default_headers={
            'HTTP-Referer': 'https://unixa.onrender.com',
            'X-Title': 'Nexa AI Community',
        },
    )


def _chat(messages, model='openai/gpt-4o-mini', max_tokens=800):
    try:
        resp = _client().chat.completions.create(
            model=model, messages=messages, max_tokens=max_tokens, temperature=0.7
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error('AI engine error: %s', e)
        return ''


def match_people(current_user_data, candidates_data):
    """
    Score and rank candidates for people matching.
    Returns list of {username, score, reason, match_type}.
    """
    prompt = f"""You are a social matching AI for a university platform.

Current user:
{json.dumps(current_user_data, indent=2)}

Candidates (list of user profiles):
{json.dumps(candidates_data[:20], indent=2)}

For each candidate, output a JSON array where each item has:
- "username": string
- "score": float 0-1 (how good a match)
- "reason": one sentence why they match
- "match_type": one of "study", "project", "startup", "general"

Only include candidates with score >= 0.4. Sort by score descending.
Return ONLY valid JSON array, no markdown."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=1200)
    try:
        start = raw.find('[')
        end = raw.rfind(']') + 1
        return json.loads(raw[start:end]) if start >= 0 else []
    except Exception:
        return []


def generate_icebreaker(user_a, user_b, context=''):
    """Generate conversation starters for two users."""
    prompt = f"""Generate 3 short, friendly conversation starters for two university students meeting for the first time.

Student A: {json.dumps(user_a)}
Student B: {json.dumps(user_b)}
Context: {context}

Return a JSON array of 3 strings. Each starter should be natural, specific, and under 20 words.
Return ONLY valid JSON array."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=300)
    try:
        start = raw.find('[')
        end = raw.rfind(']') + 1
        return json.loads(raw[start:end]) if start >= 0 else [
            "What are you studying this semester?",
            "Any interesting projects you're working on?",
            "What communities are you most active in?",
        ]
    except Exception:
        return [
            "What are you studying this semester?",
            "Any interesting projects you're working on?",
            "What communities are you most active in?",
        ]


def detect_opportunities(post_content):
    """
    Detect if a post contains an opportunity.
    Returns dict with {is_opportunity, type, title, description} or None.
    """
    prompt = f"""Analyze this university community post and detect if it contains an opportunity.

Post: "{post_content[:1000]}"

If it contains an internship, scholarship, job, competition, research opening, or grant:
Return JSON: {{"is_opportunity": true, "type": "internship|scholarship|job|competition|research|grant|other", "title": "...", "description": "..."}}

If not an opportunity:
Return JSON: {{"is_opportunity": false}}

Return ONLY valid JSON."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=300)
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        return json.loads(raw[start:end]) if start >= 0 else None
    except Exception:
        return None


def campus_assistant_query(question, context_data):
    """
    Answer a campus assistant question using platform context.
    Returns a structured response with answer + recommendations.
    """
    prompt = f"""You are the Nexa Campus AI Assistant for a university community platform.

User question: "{question}"

Available platform data:
{json.dumps(context_data, indent=2)}

Answer the question helpfully. If you can recommend specific people, groups, or posts from the data, do so.
Keep your answer under 150 words. Be friendly and specific.

Return JSON: {{"answer": "...", "recommendations": [{{"type": "user|community|post", "name": "...", "reason": "..."}}]}}
Return ONLY valid JSON."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=600)
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        return json.loads(raw[start:end]) if start >= 0 else {
            'answer': 'I couldn\'t find specific results right now. Try browsing communities or searching for users.',
            'recommendations': [],
        }
    except Exception:
        return {
            'answer': 'I couldn\'t find specific results right now. Try browsing communities or searching for users.',
            'recommendations': [],
        }


def assemble_startup_team(founder_data, idea_data, candidates_data):
    """
    Assemble a balanced startup team from candidates.
    Returns {team_name, intro, members: [{username, role, reason}]}.
    """
    prompt = f"""You are a startup team formation AI for a university platform.

Founder:
{json.dumps(founder_data)}

Startup idea:
{json.dumps(idea_data)}

Available candidates:
{json.dumps(candidates_data[:30], indent=2)}

Assemble the best balanced founding team (max {idea_data.get('team_size', 4)} people including founder).
Avoid redundant skill sets. Aim for: technical, product/design, business/marketing, and any specialist roles.

Return JSON:
{{
  "team_name": "...",
  "intro": "2-3 sentence AI introduction explaining why this team was assembled",
  "members": [
    {{"username": "...", "role": "Technical Founder|Product Lead|Marketing Lead|...", "reason": "one sentence"}}
  ]
}}
Return ONLY valid JSON."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=800)
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        return json.loads(raw[start:end]) if start >= 0 else None
    except Exception:
        return None


def rank_feed_posts(posts_data, user_profile):
    """
    Re-rank feed posts by relevance to user.
    Returns list of post IDs in ranked order.
    """
    if not posts_data:
        return []
    prompt = f"""Rank these posts by relevance to this user. Consider academic interests, communities, engagement.

User profile: {json.dumps(user_profile)}

Posts (id + summary):
{json.dumps([{'id': str(p['id']), 'content': p['content'][:100], 'likes': p.get('like_count', 0), 'comments': p.get('comment_count', 0)} for p in posts_data[:20]])}

Return a JSON array of post IDs in order from most to least relevant.
Return ONLY valid JSON array of strings."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=400)
    try:
        start = raw.find('[')
        end = raw.rfind(']') + 1
        return json.loads(raw[start:end]) if start >= 0 else [str(p['id']) for p in posts_data]
    except Exception:
        return [str(p['id']) for p in posts_data]


def generate_study_group(subject, members_data):
    """Generate a study group name and intro message."""
    prompt = f"""Create a study group for university students studying: {subject}

Members: {json.dumps(members_data)}

Return JSON: {{"group_name": "...", "intro_message": "Welcome message under 50 words"}}
Return ONLY valid JSON."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=200)
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        return json.loads(raw[start:end]) if start >= 0 else {
            'group_name': f'{subject} Study Group',
            'intro_message': f'Welcome to your AI-matched {subject} study group! Introduce yourselves and get started.',
        }
    except Exception:
        return {
            'group_name': f'{subject} Study Group',
            'intro_message': f'Welcome to your AI-matched {subject} study group! Introduce yourselves and get started.',
        }


def generate_join_briefing(joining_user, group_name, subject, members_data, recent_messages):
    """
    When a user joins a study group, generate:
    - A personalized self-introduction for them
    - A summary of where the group's studies have gotten to
    - A brief description of each member
    Returns {intro, summary, member_bios}
    """
    prompt = f"""A student is joining a study group. Generate a warm, personalized onboarding briefing.

Joining student: {json.dumps(joining_user)}
Group name: {group_name}
Subject: {subject}
Current members: {json.dumps(members_data)}
Recent group chat (last messages): {json.dumps(recent_messages[:10])}

Return JSON with exactly these keys:
{{
  "intro": "A 2-3 sentence self-introduction the joining student can post, based on their profile. Make it specific and friendly.",
  "summary": "2-3 sentences summarizing what the group has been studying/discussing so far, based on the chat history. If no history, say the group is just getting started.",
  "member_bios": [
    {{"username": "...", "bio": "One sentence about this member and what they bring to the group"}}
  ]
}}
Return ONLY valid JSON."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=600)
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        result = json.loads(raw[start:end]) if start >= 0 else None
        if result:
            return result
    except Exception:
        pass
    return {
        'intro': f"Hey everyone! I'm excited to join this {subject} study group. Looking forward to learning together!",
        'summary': 'The group is just getting started. Jump in and introduce yourself!',
        'member_bios': [{'username': m.get('username', ''), 'bio': 'A fellow student in this group.'} for m in members_data],
    }


# ── Workspace AI Manager ──────────────────────────────────────────────────────

def analyze_project_files(files_data, workspace_name, members):
    """
    Analyze uploaded workspace files and return a full project brief.
    files_data: list of {name, content_preview}
    Returns {title, objectives, deliverables, deadline_hint, tasks, risks}
    """
    files_text = '\n\n'.join(
        f"FILE: {f['name']}\n{f['content_preview'][:800]}" for f in files_data
    )
    members_list = ', '.join(m['username'] for m in members)
    prompt = f"""You are an AI Project Manager analyzing academic project files for a university team.

Workspace: {workspace_name}
Team members: {members_list}

Uploaded files:
{files_text}

Extract and return a structured project brief as JSON:
{{
  "title": "Project title",
  "objectives": ["objective 1", "objective 2"],
  "deliverables": ["deliverable 1", "deliverable 2"],
  "deadline_hint": "any deadline mentioned or null",
  "grading_criteria": ["criterion 1", "criterion 2"],
  "tasks": [
    {{
      "title": "Task title",
      "description": "What needs to be done",
      "difficulty": "easy|medium|hard",
      "estimated_hours": 2,
      "suggested_assignee": "username or null",
      "priority": "high|medium|low"
    }}
  ],
  "risks": ["risk 1", "risk 2"],
  "summary": "2-3 sentence project overview"
}}
Return ONLY valid JSON."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=1500)
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        return json.loads(raw[start:end]) if start >= 0 else None
    except Exception:
        return None


def workspace_ai_chat(message, context):
    """
    Conversational AI manager for workspace.
    context: {workspace_name, workspace_type, members, tasks, files, recent_chat}
    Returns {reply, actions: [{type, data}]}
    """
    ws_type = context.get('workspace_type', 'general')

    type_personas = {
        'startup': """You are an experienced startup advisor embedded in this workspace.
Your priorities: idea validation, market analysis, business model, MVP scope, growth strategy, pitch preparation.
Proactively flag unrealistic assumptions. Suggest pivots when needed. Think like a YC mentor.""",

        'study_group': """You are a supportive academic coach embedded in this workspace.
Your priorities: explaining concepts clearly, building study schedules, generating flashcards/practice questions from uploaded notes, identifying knowledge gaps, and preparing the team for assessments.
Be encouraging and adapt explanations to different difficulty levels.""",

        'group_project': """You are a project manager and academic assistant embedded in this workspace.
Your priorities: extracting requirements from uploaded files, breaking work into structured tasks with dependencies, suggesting fair member assignments, reviewing submitted work for completeness, and assembling a final submission-ready output.
Think like a GitHub-style contribution system — each member owns a piece, you integrate them.""",

        'general': """You are a neutral productivity assistant embedded in this workspace.
Your priorities: task organization, brainstorming, decision support, planning guidance, and keeping the team aligned.""",
    }

    persona = type_personas.get(ws_type, type_personas['general'])

    system = f"""{persona}

Workspace: "{context.get('workspace_name', 'this workspace')}"
Type: {ws_type.replace('_', ' ').title()}
Team members: {', '.join(context.get('members', []))}
Current tasks: {json.dumps(context.get('tasks', []))}
Uploaded files: {', '.join(context.get('files', []))}
Recent chat context: {json.dumps(context.get('recent_chat', [])[:5])}

Be concise, structured, and actionable.

IMPORTANT: When you suggest tasks (e.g. when asked to break down work, generate tasks, assign tasks, or split work),
you MUST include them as a JSON block at the END of your response in this exact format:
```tasks
[{{"title":"Task title","description":"What to do","priority":"high|medium|low","estimated_hours":2,"suggested_assignee":"username or null"}}]
```
Only include the tasks block when you are actually suggesting tasks to add to the board."""

    raw = _chat([
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': message},
    ], max_tokens=1000)

    actions = []
    reply = raw

    # Extract tasks block if present
    if '```tasks' in raw:
        try:
            parts = raw.split('```tasks')
            reply = parts[0].strip()
            json_part = parts[1].split('```')[0].strip()
            parsed = json.loads(json_part)
            if isinstance(parsed, list) and parsed:
                actions = [{'type': 'tasks', 'data': parsed}]
        except Exception:
            pass
    elif '```json' in raw:
        try:
            parts = raw.split('```json')
            json_part = parts[1].split('```')[0].strip()
            parsed = json.loads(json_part)
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict) and 'title' in parsed[0]:
                actions = [{'type': 'tasks', 'data': parsed}]
                reply = parts[0].strip()
        except Exception:
            pass

    return {'reply': reply, 'actions': actions}


def generate_project_health(workspace_name, members, tasks, files, deadline_hint=None):
    """
    Generate a project health report.
    Returns {completion_pct, risk_level, work_distribution, next_actions, summary}
    """
    todo = [t for t in tasks if t.get('status') == 'todo']
    doing = [t for t in tasks if t.get('status') == 'doing']
    done = [t for t in tasks if t.get('status') == 'done']
    total = len(tasks)
    completion = round((len(done) / total * 100) if total else 0)

    # Contribution map
    contrib = {}
    for t in tasks:
        assignee = t.get('assigned_to') or 'Unassigned'
        contrib[assignee] = contrib.get(assignee, 0) + 1

    prompt = f"""Generate a project health report for a university team project.

Project: {workspace_name}
Team: {', '.join(m['username'] for m in members)}
Tasks: {total} total — {len(done)} done, {len(doing)} in progress, {len(todo)} to do
Completion: {completion}%
Deadline hint: {deadline_hint or 'not specified'}
Files uploaded: {len(files)}
Contribution map: {json.dumps(contrib)}

Return JSON:
{{
  "completion_pct": {completion},
  "risk_level": "low|medium|high|critical",
  "risk_reason": "one sentence",
  "work_distribution": [{{"member": "...", "tasks": 0, "pct": 0}}],
  "inactive_members": ["username"],
  "next_actions": ["action 1", "action 2", "action 3"],
  "summary": "2-3 sentence overall assessment"
}}
Return ONLY valid JSON."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=700)
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        result = json.loads(raw[start:end]) if start >= 0 else None
        if result:
            result['completion_pct'] = completion
            return result
    except Exception:
        pass

    return {
        'completion_pct': completion,
        'risk_level': 'medium',
        'risk_reason': 'Unable to fully assess — add more tasks for better tracking.',
        'work_distribution': [{'member': m['username'], 'tasks': contrib.get(m['username'], 0), 'pct': 0} for m in members],
        'inactive_members': [],
        'next_actions': ['Add tasks to the board', 'Assign tasks to members', 'Upload project files'],
        'summary': f'Project is {completion}% complete with {len(todo)} tasks remaining.',
    }


def analyze_meeting_transcript(transcript, workspace_name, members):
    """
    Analyze a meeting transcript and extract:
    - summary, decisions, action_items (with assignee + deadline hints)
    Returns {summary, decisions, action_items}
    """
    members_list = ', '.join(members)
    prompt = f"""You are an AI meeting analyst for a university project team.

Workspace: {workspace_name}
Team members: {members_list}

Meeting transcript:
{transcript[:3000]}

Extract and return structured meeting notes as JSON:
{{
  "summary": "2-3 sentence meeting summary",
  "decisions": ["decision 1", "decision 2"],
  "action_items": [
    {{
      "task": "What needs to be done",
      "assignee": "username or null if unclear",
      "deadline_hint": "any deadline mentioned or null"
    }}
  ],
  "key_topics": ["topic 1", "topic 2"]
}}
Return ONLY valid JSON."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=900)
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        return json.loads(raw[start:end]) if start >= 0 else None
    except Exception:
        return None


def generate_autocomplete_doc(workspace_name, members, tasks, files_data, doc_type='report'):
    """
    Generate a final document draft, presentation outline, or executive summary.
    doc_type: 'report' | 'slides' | 'summary'
    Returns {type, title, content, sections}
    """
    files_text = '\n\n'.join(
        f"FILE: {f['name']}\n{f['content_preview'][:600]}" for f in files_data
    ) if files_data else 'No files uploaded.'

    done_tasks = [t['title'] for t in tasks if t.get('status') == 'done']
    todo_tasks = [t['title'] for t in tasks if t.get('status') != 'done']

    type_instructions = {
        'report': 'Generate a structured academic project report with: Title, Abstract, Introduction, Methodology, Results/Findings, Conclusion, and References placeholder.',
        'slides': 'Generate a presentation outline with 6-10 slides. For each slide: title + 3-5 bullet points.',
        'summary': 'Generate a concise executive summary (max 300 words) covering objectives, progress, key findings, and next steps.',
    }
    instruction = type_instructions.get(doc_type, type_instructions['report'])

    prompt = f"""You are an AI writing assistant for a university project team.

Project: {workspace_name}
Team: {', '.join(members)}
Completed tasks: {json.dumps(done_tasks)}
Remaining tasks: {json.dumps(todo_tasks)}

Uploaded files context:
{files_text}

Task: {instruction}

Return JSON:
{{
  "type": "{doc_type}",
  "title": "Document title",
  "sections": [
    {{"heading": "Section heading", "content": "Section content or bullet points as a string"}}
  ],
  "word_count_estimate": 0
}}
Return ONLY valid JSON."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=1800)
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        return json.loads(raw[start:end]) if start >= 0 else None
    except Exception:
        return None


def review_task_submission(task_title, task_description, submission, workspace_name, files_context):
    """
    AI reviews a member's task submission.
    Returns {status: 'approved'|'revision', feedback, score, suggestions}
    """
    files_text = '\n\n'.join(
        f"FILE: {f['name']}\n{f['content_preview']}" for f in files_context
    ) if files_context else 'No project files available.'

    prompt = f"""You are an AI project reviewer for a university group project.

Project: {workspace_name}
Task: {task_title}
Task description: {task_description or 'No description provided.'}

Project context from uploaded files:
{files_text}

Member's submission:
{submission[:2000]}

Review this submission and return JSON:
{{
  "status": "approved" or "revision",
  "score": 0-100,
  "feedback": "2-3 sentences of specific, constructive feedback",
  "strengths": ["strength 1", "strength 2"],
  "suggestions": ["improvement 1", "improvement 2"]
}}

Approve if the submission adequately addresses the task. Request revision if it's incomplete, off-topic, or needs significant improvement.
Return ONLY valid JSON."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=600)
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        result = json.loads(raw[start:end]) if start >= 0 else None
        if result and result.get('status') in ('approved', 'revision'):
            return result
    except Exception:
        pass
    return {
        'status': 'revision',
        'score': 50,
        'feedback': 'Could not fully analyze the submission. Please ensure it addresses the task requirements.',
        'strengths': [],
        'suggestions': ['Review the task description and ensure all requirements are covered.'],
    }


def assemble_final_document(workspace_name, contributions):
    """
    Merge all approved task contributions into a coherent final document.
    contributions: [{title, author, content}]
    Returns {title, document, word_count, sections}
    """
    contribs_text = '\n\n'.join(
        f"SECTION: {c['title']} (by {c['author']})\n{c['content'][:800]}"
        for c in contributions
    )

    prompt = f"""You are an AI editor assembling a final academic project document.

Project: {workspace_name}
Number of contributions: {len(contributions)}

Individual contributions:
{contribs_text}

Assemble these into a single coherent, professionally formatted document.
- Ensure consistent tone and formatting throughout
- Add smooth transitions between sections
- Fix any inconsistencies
- Add a brief introduction and conclusion if missing

Return JSON:
{{
  "title": "Final document title",
  "sections": [
    {{"heading": "Section heading", "content": "Full section content", "author": "original author"}}
  ],
  "word_count": 0,
  "editor_notes": "Brief note about what was adjusted for consistency"
}}
Return ONLY valid JSON."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=2000)
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        return json.loads(raw[start:end]) if start >= 0 else None
    except Exception:
        return None


def proactive_chat_suggestion(workspace_name, workspace_type, recent_messages, tasks, members):
    """
    Analyze recent chat and decide if the AI should proactively post a suggestion.
    Returns {should_post: bool, message: str}
    Only posts when genuinely useful — avoids spam.
    """
    if not recent_messages:
        return {'should_post': False, 'message': ''}

    chat_text = '\n'.join(f"{m['sender__username']}: {m['content']}" for m in recent_messages[-8:])
    todo_count = sum(1 for t in tasks if t.get('status') == 'todo')
    done_count = sum(1 for t in tasks if t.get('status') == 'done')

    type_context = {
        'startup': 'startup team building a product/business',
        'study_group': 'study group preparing for exams',
        'group_project': 'group working on an academic project',
        'general': 'collaborative team',
    }.get(workspace_type, 'team')

    prompt = f"""You are an AI assistant monitoring a {type_context} workspace chat.

Workspace: {workspace_name}
Members: {', '.join(members)}
Tasks: {done_count} done, {todo_count} remaining

Recent chat:
{chat_text}

Should you proactively post a helpful suggestion, warning, or insight based on this conversation?

Rules:
- Only post if there's something genuinely useful to add (a risk, a missed point, a helpful resource, a decision that needs clarification)
- Do NOT post just to be present — silence is better than noise
- Keep it short (1-2 sentences max)
- Be specific to what was discussed

Return JSON:
{{"should_post": true or false, "message": "your message if should_post is true, else empty string"}}
Return ONLY valid JSON."""

    raw = _chat([{'role': 'user', 'content': prompt}], max_tokens=200)
    try:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        result = json.loads(raw[start:end]) if start >= 0 else None
        if result and isinstance(result.get('should_post'), bool):
            return result
    except Exception:
        pass
    return {'should_post': False, 'message': ''}
