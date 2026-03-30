"""
Library AI — two teaching modes:
1. ai_teach_topic: AI uses its own knowledge (no book)
2. book_teach_topic: AI teaches from extracted book text
"""
from ai_tutor.ai_utils import get_openai_client


SYSTEM_PROMPT = """You are Nexa, an advanced AI Tutor for SHS students preparing for WAEC exams.

CRITICAL OUTPUT FORMAT — READ CAREFULLY:

You MUST format ALL responses using the board-style step format below.
NEVER write long prose paragraphs. NEVER use markdown bold (**text**).
NEVER number steps with "1." "2." — use the Step keyword instead.

BOARD FORMAT (mandatory for every response):

For math/science/programming topics:

Problem
[State what you are about to teach]

Step 1: [Title]
[One or two sentences of explanation]
$[LaTeX math if needed]$

Step 2: [Title]
[Explanation]
[code block or diagram if needed]

Final Answer
[Summary or result]

For concepts, history, definitions (non-math):

Step 1: [Section title]
[Explanation in 2-3 sentences max]

Step 2: [Section title]
[Explanation]

Final Answer
[Key takeaway]

MATH FORMATTING (MANDATORY):
- Inline math: $expression$
- Display math: $expression$
- Fractions: $\\frac{a}{b}$
- Powers: $x^2$
- Square roots: $\\sqrt{x}$
- NEVER write raw math like 1/2, x^2, sqrt(x)

CODE/DIAGRAM FORMATTING:
- Wrap ALL code and tree diagrams in triple backticks
- Example:
```
    7
   / \\
  3   9
```

BULLET POINTS:
- Use • for bullet lists inside steps
- Example: • Item one

CRITICAL RULES:
- Each Step MUST be on its own line followed by a blank line
- NEVER run two steps together
- NEVER use markdown **bold** or *italic*
- Keep each step short and focused
- Always end with "Final Answer" or "Practice Questions"
- After teaching, add 3 practice questions (Easy / Medium / Hard) each with a full solution using the same step format"""


def _call(system, prompt, max_tokens=1600):
    client = get_openai_client()
    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content


def ai_teach_topic(subject, topic, question="Teach me this topic"):
    """AI teaches from its own knowledge — no book needed."""
    prompt = f"""SUBJECT: {subject}
TOPIC: {topic}
STUDENT REQUEST: {question}

Teach this topic thoroughly using the board-style step format for math/science, or paragraph format for other subjects."""
    return _call(SYSTEM_PROMPT, prompt, max_tokens=1600)


def book_teach_topic(subject, topic, book_text, question="Teach me this topic"):
    """AI teaches using extracted book content as the source."""
    prompt = f"""SUBJECT: {subject}
TOPIC: {topic}

BOOK CONTENT:
{book_text[:4000]}

STUDENT REQUEST: {question}

Use the book content above as your PRIMARY reference. Teach using the board-style step format for math/science, or paragraph format for other subjects."""
    return _call(SYSTEM_PROMPT, prompt, max_tokens=1600)


def generate_quiz(subject, topic, book_text=None):
    """Generate a structured JSON quiz for interactive grading."""
    import json as _json
    source = f"Using this book content:\n{book_text[:3000]}\n\n" if book_text else ""
    prompt = f"""You are a WAEC examiner for {subject} — topic: {topic}.

{source}Generate a quiz with exactly 5 multiple-choice questions and 3 theory questions.

Use LaTeX for ALL math: $expression$ for inline, $$expression$$ for display.

Respond with ONLY valid JSON in this exact structure (no markdown, no code fences):
{{
  "mc": [
    {{
      "q": "question text",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "answer": "A",
      "explanation": "why A is correct"
    }}
  ],
  "theory": [
    {{
      "q": "question text",
      "answer": "full model answer with LaTeX math where needed"
    }}
  ]
}}"""
    raw = _call(SYSTEM_PROMPT, prompt, max_tokens=2000)
    # Strip any accidental markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("`").strip()
    try:
        return _json.loads(raw)
    except Exception:
        # Fallback: return error dict so frontend can handle gracefully
        return {"error": "Could not parse quiz. Please try again.", "raw": raw}

def grade_quiz(subject, topic, mc_questions, mc_answers, theory_questions, theory_answers):
    """Grade student answers and return structured feedback JSON."""
    import json as _json

    mc_section = ""
    for i, (q, student_ans) in enumerate(zip(mc_questions, mc_answers)):
        mc_section += (
            f"Q{i+1}: {q['q']}\n"
            f"Options: A) {q['options'].get('A','')}  B) {q['options'].get('B','')}  "
            f"C) {q['options'].get('C','')}  D) {q['options'].get('D','')}\n"
            f"Correct answer: {q['answer']}\n"
            f"Student answered: {student_ans or '(no answer)'}\n"
            f"Explanation: {q.get('explanation','')}\n---\n"
        )

    theory_section = ""
    for i, (q, student_ans) in enumerate(zip(theory_questions, theory_answers)):
        theory_section += (
            f"Q{i+1}: {q['q']}\n"
            f"Model answer: {q['answer']}\n"
            f"Student answer: {student_ans or '(no answer)'}\n---\n"
        )

    prompt = f"""You are grading a {subject} quiz on "{topic}" for an SHS student.

MULTIPLE CHOICE:
{mc_section}
THEORY:
{theory_section}

Grade each theory answer out of 10. Use LaTeX for any math in feedback: $expression$

Respond with ONLY valid JSON (no markdown, no code fences):
{{
  "mc_results": [
    {{"correct": true, "student": "A", "correct_ans": "A", "feedback": "brief explanation"}}
  ],
  "theory_results": [
    {{"score": 7, "out_of": 10, "feedback": "what was good and what was missing"}}
  ],
  "mc_score": 3,
  "mc_total": 5,
  "theory_score": 21,
  "theory_total": 30,
  "overall_comment": "encouraging summary of performance"
}}"""

    raw = _call(SYSTEM_PROMPT, prompt, max_tokens=1500)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("`").strip()
    try:
        return _json.loads(raw)
    except Exception:
        return {"error": "Could not parse grading response.", "raw": raw}



# Legacy wrappers (keep old API working)
def teach_resource(subject, topic, content, question):
    return book_teach_topic(subject, topic, content, question)


def quiz_resource(subject, topic, content):
    return generate_quiz(subject, topic, book_text=content)


def generate_topic_notes(subject, topic):
    """
    Generate detailed step-by-step notes for a topic, structured as 'slides'.
    Returns a list of dicts: [{'title': '...', 'content': '...'}]
    """
    prompt = f"""Create clear, detailed study notes for "{topic}" in {subject}. Return exactly 10 slides as a JSON array.

IMPORTANT MATH FORMATTING RULES — follow exactly:
- Wrap ALL math in LaTeX delimiters: $...$ for inline, $$...$$ for display equations.
- Write derivatives as $f'(x)$, fractions as $\\frac{{a}}{{b}}$, powers as $x^{{2}}$.
- NEVER write math as plain text.

Slide structure (use these as titles/themes):
1. Introduction & Overview
2. Core Definition / Key Concept
3. Important Properties or Rules
4. Step-by-Step Method
5. Common Mistakes & How to Avoid Them
6. Real-World Application
7. Intermediate Example
8. Advanced Concepts / Extensions
9. Solved Example 1 — full working
10. Solved Example 2 — full working

Each slide: "title" + "content" (3-5 sentences + math where relevant).
Slides 9 and 10 must show complete step-by-step solutions using $$...$$ for each working line.

Return ONLY the JSON array, no extra text:
[
  {{"title": "...", "content": "..."}},
  ... (10 total)
]"""
    client = get_openai_client()
    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": (
                "You are a concise educational content creator writing for a LaTeX-rendering viewer. "
                "ALL math MUST be wrapped in LaTeX delimiters: $...$ for inline, $$...$$ for display. "
                "CRITICAL: This is JSON output. Every LaTeX backslash MUST be written as TWO backslashes. "
                "Write \\\\frac, \\\\lim, \\\\sqrt, \\\\int, \\\\to, \\\\alpha, \\\\theta, \\\\sum, \\\\infty, \\\\cdot. "
                "NEVER single-backslash LaTeX in JSON. Respond with raw JSON array only. No markdown fences."
            )},
            {"role": "user", "content": prompt},
        ],
        max_tokens=3000,
        temperature=0.4,
    )
    import json as _json
    import re as _re

    raw = response.choices[0].message.content.strip()

    # Step 1: Strip markdown code fences
    if raw.startswith("```"):
        raw = _re.sub(r'^```[a-z]*\n?', '', raw).rstrip('`').strip()

    # Step 2: Extract the JSON array by bracket matching
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end != -1:
        raw = raw[start:end+1]

    # Step 3: Fix invalid JSON escape sequences using a proper state-machine.
    # Root cause of the bug: \f, \t, \n, \r, \b are valid JSON escapes but also
    # start LaTeX commands (\frac, \to, \beta, \nabla, \rho). The old fixer kept
    # them, causing json.loads to turn \frac → formfeed+"rac", \to → tab+"o".
    # Fix: only keep \", \\, \/, \uXXXX. Double everything else.
    def fix_escapes(s):
        truly_safe = {'"', '\\', '/'}
        result = []
        i = 0
        in_string = False
        while i < len(s):
            c = s[i]
            if not in_string:
                result.append(c)
                if c == '"':
                    in_string = True
                i += 1
            else:
                if c == '\\' and i + 1 < len(s):
                    nxt = s[i + 1]
                    if nxt in truly_safe:
                        result.append(c)
                        result.append(nxt)
                        if nxt == '"':
                            pass  # escaped quote — stay in string
                        i += 2
                    elif nxt == 'u' and i + 5 < len(s):
                        result.append(c)   # keep \uXXXX unicode escapes
                        result.append(nxt)
                        i += 2
                    else:
                        # \f, \t, \n, \r, \b, \l, \a, \s etc.
                        # Double the backslash so \frac → \\frac → KaTeX gets \frac
                        result.append('\\\\')
                        i += 1  # process next char on its own
                elif c == '"':
                    result.append(c)
                    in_string = False
                    i += 1
                elif c == '\n':
                    result.append('\\n')  # escape raw newlines inside strings
                    i += 1
                elif c == '\r':
                    result.append('\\r')
                    i += 1
                else:
                    result.append(c)
                    i += 1
        return ''.join(result)

    fixed = fix_escapes(raw)

    try:
        return _json.loads(fixed)
    except Exception as e1:
        # Last resort: decode with unicode-escape error handler
        try:
            return _json.loads(raw.encode('utf-8').decode('unicode-escape', errors='replace'))
        except Exception as e2:
            print(f"Notes Generation Error (both attempts failed): {e1} | {e2}")
            return [{"title": "Generation Error", "content": f"There was a problem formatting the notes ({str(e1)}). Please click **Start Learning** again — it usually succeeds on the second attempt."}]


def generate_podcast_script(subject, topic, level=None, context=None):
    """
    Generate a conversational podcast script for Alex and Sam.
    Returns a script with 'Alex:' and 'Sam:' prefixes.
    """
    level_context = f" at the {level} level" if level else ""
    ctx_str = f"\nUse these notes as context for the discussion:\n{context}\n" if context else ""
    prompt = f"""Create a conversational, engaging podcast script explaining "{topic}" in {subject}{level_context}.{ctx_str}
The script should be for two hosts, Alex (male, enthusiastic) and Sam (female, analytical), discussing the topic in a way that is easy to follow by listening.

STRICT RULES:
- Start every line with "Alex: " or "Sam: "
- Keep it educational but conversational — use analogies, banter, and clear explanations.
- Include an Intro, Core Concepts, a Worked Example, and a Summary.
- NO markdown, NO bullet points, NO symbols besides Alex:/Sam:
- Target: about 8-10 minutes of speaking time (~1500 words).

Example:
Alex: Hey everyone, welcome back! Today we're diving into something fascinating: {topic}.
Sam: That's right, Alex. It's a foundational concept in {subject}, and it's actually cooler than people think.
"""

    client = get_openai_client()
    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional educational podcast scriptwriter. Write only Alex/Sam dialogue."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=3000,
        temperature=0.7,
    )
    return response.choices[0].message.content

