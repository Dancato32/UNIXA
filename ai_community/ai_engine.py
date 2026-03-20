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
