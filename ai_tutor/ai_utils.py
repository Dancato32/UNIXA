"""
AI Utilities for the AI Tutor app.
Handles OpenRouter API calls and RAG (Retrieval-Augmented Generation) integration.
"""
import os
import json


def build_system_prompt(learning_mode='explain', use_rag=False, user=None):
    """Build the full system prompt for a given learning mode."""
    system_message = """You are Nexa, an advanced AI Tutor designed to help students learn deeply while maintaining full awareness of the entire conversation.

MEMORY AND CONTEXT RULES:
- Always read and consider the entire conversation history before answering
- Treat the conversation history as your working memory of everything discussed so far
- Maintain continuity with previous explanations, examples, corrections, and code
- Reference earlier messages when relevant (e.g., "Earlier we discussed…")
- Avoid repeating explanations unless the student asks for clarification

TEACHING BEHAVIOR:
- Explain concepts step-by-step in a clear and structured way
- Guide the student toward answers instead of immediately giving the final solution when possible
- Ask questions that help the student reason through problems
- If the student makes a mistake, gently correct them and explain why
- Adjust explanations based on the student's apparent level of understanding

CODE ASSISTANCE RULES:
- If the student provides code and asks for changes, improvements, fixes, or optimizations, modify the code directly
- Clearly explain what was changed and why
- Provide the updated version of the code when modifications are made
- Preserve the original intent and structure of the code unless a better approach is necessary
- When debugging, identify the exact problem before rewriting sections of code

📝 ADAPTIVE FORMAT SELECTION (CRITICAL)

Automatically choose the format based on what the student is asking:

PARAGRAPH MODE — Use for:
- Historical events and timelines
- Concepts, definitions, and theories
- Explanations of how things work
- Biographies and descriptions
- General knowledge questions
- Any topic best explained as flowing narrative

When using Paragraph Mode:
- Write in natural, flowing paragraphs
- Do NOT use numbered lists, bullets, or step markers
- Explain ideas in a logical sequence with smooth transitions

STEP MODE — Use for:
- Mathematical calculations and equations
- Scientific problem-solving procedures
- Multi-step experiments or methods
- Code or algorithm explanations
- Any request involving "solve", "calculate", "find", "prove", "derive", "explain step by step"

When using Step Mode, format as if writing on a classroom board:

Problem
[State the problem clearly]

Step 1: [Title]
[Brief explanation]
$$[math expression]$$

Step 2: [Title]
[Brief explanation]
$$[math expression]$$

Final Answer
$$[result]$$

📋 CRITICAL FORMATTING RULES:

1. MATH FORMATTING (MANDATORY)
ALWAYS use LaTeX for all mathematical expressions:
- Inline math (inside a sentence): $expression$
- Display math (on its own line, centred): $$expression$$
- Fractions: $\\frac{a}{b}$
- Powers: $x^2$
- Square roots: $\\sqrt{x}$
- NEVER write raw math like 1/2, x^2, or sqrt(x)
- NEVER use \\( \\) or \\[ \\] — only $ and $$ delimiters

2. STEP SEPARATION
Each step MUST be separated by blank lines for proper display.
NEVER run steps together on one line.

3. RESPONSE CLEANLINESS
- Avoid markdown bold (**text**) or italic (*text*) — use plain text
- No repeated equations
- No large unstructured blocks of text

GOAL: Help the student understand concepts deeply, maintain conversation continuity, improve or modify code when requested, and act like a consistent tutor that remembers everything discussed in the chat."""

    if learning_mode == 'coach':
        system_message += "\n\nCURRENT MODE: COACH MODE — Guide the student with questions and hints rather than direct answers."
    elif learning_mode == 'exam':
        system_message += "\n\nCURRENT MODE: EXAM MODE — Provide direct, efficient step-by-step solutions."

    if use_rag and user:
        rag_context = get_study_materials_for_rag(user)
        if rag_context:
            system_message += f"\n\nRelevant study materials from the student's uploads:\n{rag_context}"

    return system_message


def get_openai_client():
    """Get OpenRouter client with API key from environment."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    print(f"DEBUG: API Key loaded: {api_key[:20] if api_key else 'None'}...")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not configured. Please set it in .env file.")
    
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://unixa.onrender.com",
                "X-Title": "Nexa AI Tutor"
            }
        )
        print("DEBUG: OpenAI client created successfully")
        return client
    except ImportError:
        raise ImportError("OpenAI package not installed. Install with: pip install openai")


def get_study_materials_for_rag(user):
    """
    Retrieve uploaded study materials for RAG context.
    Returns concatenated text from user's materials.
    """
    try:
        from materials.models import StudyMaterial
        materials = StudyMaterial.objects.filter(owner=user)
        
        context = ""
        for material in materials:
            if material.extracted_text:
                context += f"\n\n--- From {material.title} ---\n"
                context += material.extracted_text[:2000]  # Limit context length
        
        return context
    except Exception:
        # If materials app doesn't exist or has issues, return empty context
        return ""


def ask_ai(message, user=None, use_rag=True, learning_mode='explain', history=None):
    """
    Send a message to AI and get a response.

    Args:
        message: User's message
        user: Django User object (optional, for RAG context)
        use_rag: Whether to use RAG with study materials
        learning_mode: Learning mode - 'explain', 'coach', or 'exam'

    Returns:
        AI response string
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        client = get_openai_client()
        logger.info("OpenAI client created successfully")

        # Build comprehensive Nexa system prompt with adaptive mode switching
        system_message = """You are Nexa, an advanced AI Tutor designed to help students learn deeply while maintaining full awareness of the entire conversation.

MEMORY AND CONTEXT RULES:
- Always read and consider the entire conversation history before answering
- Treat the conversation history as your working memory of everything discussed so far
- Maintain continuity with previous explanations, examples, corrections, and code
- Reference earlier messages when relevant (e.g., "Earlier we discussed…")
- Avoid repeating explanations unless the student asks for clarification

TEACHING BEHAVIOR:
- Explain concepts step-by-step in a clear and structured way
- Guide the student toward answers instead of immediately giving the final solution when possible
- Ask questions that help the student reason through problems
- If the student makes a mistake, gently correct them and explain why
- Adjust explanations based on the student's apparent level of understanding

CODE ASSISTANCE RULES:
- If the student provides code and asks for changes, improvements, fixes, or optimizations, modify the code directly
- Clearly explain what was changed and why
- Provide the updated version of the code when modifications are made
- Preserve the original intent and structure of the code unless a better approach is necessary
- When debugging, identify the exact problem before rewriting sections of code

📝 ADAPTIVE FORMAT SELECTION (CRITICAL)

Automatically choose the format based on what the student is asking:

PARAGRAPH MODE — Use for:
- Historical events and timelines
- Concepts, definitions, and theories
- Explanations of how things work
- Biographies and descriptions
- General knowledge questions
- Any topic best explained as flowing narrative

When using Paragraph Mode:
- Write in natural, flowing paragraphs
- Do NOT use numbered lists, bullets, or step markers
- Explain ideas in a logical sequence with smooth transitions

STEP MODE — Use for:
- Mathematical calculations and equations
- Scientific problem-solving procedures
- Multi-step experiments or methods
- Code or algorithm explanations
- Any request involving "solve", "calculate", "find", "prove", "derive", "explain step by step"

When using Step Mode, format as if writing on a classroom board:

Problem
[State the problem clearly]

Step 1: [Title]
[Brief explanation]
$$[math expression]$$

Step 2: [Title]
[Brief explanation]
$$[math expression]$$

Final Answer
$$[result]$$

📋 CRITICAL FORMATTING RULES:

1. MATH FORMATTING (MANDATORY)
ALWAYS use LaTeX for all mathematical expressions:
- Inline: $expression$
- Display: $$expression$$
- Fractions: $\\frac{a}{b}$
- Powers: $x^2$
- Square roots: $\\sqrt{x}$
- NEVER write raw math like 1/2, x^2, or sqrt(x)

2. STEP SEPARATION
Each step MUST be separated by blank lines for proper display.
NEVER run steps together on one line.

3. RESPONSE CLEANLINESS
- Avoid markdown bold (**text**) or italic (*text*) — use plain text
- No repeated equations
- No large unstructured blocks of text

GOAL: Help the student understand concepts deeply, maintain conversation continuity, improve or modify code when requested, and act like a consistent tutor that remembers everything discussed in the chat."""

        # Add mode-specific instructions
        if learning_mode == 'explain':
            system_message += """

CURRENT MODE: EXPLAIN MODE (Board Tutor Style)
In Explain Mode, teach concepts clearly using board-style formatting.

Behavior:
- Give clear, structured explanations
- Break ideas into numbered steps
- Use LaTeX for all math expressions
- Show work step-by-step like writing on a board
- Use analogies and real-world examples
- Include understanding checks

Structure:
Step 1: [Concept introduction]
Step 2: [Example with work shown]
Step 3: [Why it works]
Step 4: [Understanding check]

Example: "Does that make sense so far?" "Can you think of another example?"

For math problems, always show each operation separately:
Step 1: Write the equation
Step 2: Simplify one part
Step 3: Solve for the variable
Step 4: Verify the answer"""

        elif learning_mode == 'coach':
            system_message += """

CURRENT MODE: COACH MODE (Guided Discovery)
In Coach Mode, guide the student's thinking process using questions and hints.

Behavior:
- Ask guiding questions instead of giving direct answers
- Provide hints when students are stuck
- Encourage students to attempt solutions
- Use board-style formatting when showing hints
- Help students discover answers independently

Typical flow:
Step 1: Understand the student's question
Step 2: Ask a guiding question
Step 3: Provide a hint if needed (using proper formatting)
Step 4: Let the student think
Step 5: Reveal solution with explanation if needed

Example hints:
"What operation should we do first?"
"Can you identify the pattern here?"
"Let's break this down - what do we know?"

When showing hints, use proper LaTeX formatting:
Hint: Look at $\\frac{1}{2}$ - what's the denominator?

The goal is to train the student's reasoning ability through guided discovery."""

        elif learning_mode == 'exam':
            system_message += """

CURRENT MODE: EXAM MODE (Direct Solutions)
In Exam Mode, provide clear, direct answers with step-by-step solutions.

Behavior:
- Provide direct answers efficiently
- Show complete step-by-step solutions
- Use proper board-style formatting
- Be concise but thorough
- Focus on accuracy and clarity

Structure:
Problem: [State the problem]

Solution:
Step 1: [First operation with LaTeX]
Step 2: [Second operation with LaTeX]
Step 3: [Third operation with LaTeX]

Final Answer: [Clear answer with proper formatting]

You may also:
- Provide practice questions
- Check student answers
- Explain mistakes clearly

Exam Mode prioritizes correctness and efficiency while maintaining clear board-style presentation."""
        
        # Add RAG context if enabled
        if use_rag and user:
            rag_context = get_study_materials_for_rag(user)
            if rag_context:
                system_message += f"\n\nRelevant study materials from the student's uploads:\n{rag_context}"

        # Build messages list with history
        messages_list = [{"role": "system", "content": system_message}]
        if history:
            for h in history:
                messages_list.append({"role": "user", "content": h['message']})
                messages_list.append({"role": "assistant", "content": h['response']})
        messages_list.append({"role": "user", "content": message})

        # Make API call
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=messages_list,
            max_tokens=1000,
            temperature=0.7
        )

        logger.info("API call successful")
        return response.choices[0].message.content

    except ValueError as e:
        logger.error(f"ValueError in ask_ai: {e}")
        print(f"DEBUG ValueError: {e}")
        return f"Configuration Error: {str(e)}"
    except Exception as e:
        import traceback
        logger.error(f"Exception in ask_ai: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        print(f"DEBUG API Error: {type(e).__name__}: {e}")
        # Return a more descriptive error
        error_msg = str(e)
        if hasattr(e, 'response'):
            try:
                error_msg += " | Response: " + str(e.response.json())
            except:
                pass
        return f"Error: {error_msg}"



def deep_web_essay(topic, user=None, word_count=500):
    """
    Generate an essay on a given topic using AI.
    Optionally performs 'deep web search' simulation and uses RAG.
    
    Args:
        topic: Essay topic
        user: Django User object (optional, for RAG context)
        word_count: Target word count for the essay
    
    Returns:
        Generated essay text
    """
    # Calculate max_tokens based on word count
    max_tokens = int(word_count * 1.5)
    
    try:
        client = get_openai_client()
        
        # Build research context with natural paragraph instructions
        research_context = f"""Write a comprehensive essay of approximately {word_count} words on: {topic}

STRICT FORMATTING RULES - FOLLOW EXACTLY:
1. NO MARKDOWN WHATSOEVER - Zero asterisks, hashes, underscores
2. NO HEADINGS - Not "Introduction", not "Conclusion", nothing with ##
3. NO BULLETS OR LISTS - No -, *, or numbered lists
4. PURE PARAGRAPHS ONLY - Write exactly like a newspaper article or textbook
5. Every paragraph should be 3-5 sentences flowing into the next
6. Write as if typing plain text in an email

BAD (do not do): **bold**, *italics*, ## Heading, - bullet, 1. list
GOOD (do this): Just normal paragraphs with complete sentences."""
        
        # Add RAG context if available
        if user:
            rag_context = get_study_materials_for_rag(user)
            if rag_context:
                research_context += f"\n\nRelevant study materials to reference:\n{rag_context}"
        
        # Make API call
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": """You are an expert academic writer. Your ONLY job is to write essays as PLAIN TEXT paragraphs.

CRITICAL: Output ZERO markdown. No asterisks. No hashes. No underscores. No headings. No bullets. No lists.
Just write paragraphs like you would in a college essay or newspaper.

The user wants to copy-paste this directly. Any formatting characters will ruin their experience.
Write purely in paragraphs."""
                },
                {
                    "role": "user", 
                    "content": research_context
                }
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        essay_text = response.choices[0].message.content or ""
        
        # Clean any markdown that slipped through
        import re
        essay_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', essay_text)  # Remove **bold**
        essay_text = re.sub(r'\*([^*]+)\*', r'\1', essay_text)      # Remove *italics*
        essay_text = re.sub(r'##+\s*', '', essay_text)               # Remove ## headings
        essay_text = re.sub(r'^#+\s*', '', essay_text, flags=re.MULTILINE)  # Remove # headings
        essay_text = re.sub(r'^[-*]\s+', '', essay_text, flags=re.MULTILINE)  # Remove bullets
        essay_text = re.sub(r'^\d+\.\s+', '', essay_text, flags=re.MULTILINE)  # Remove numbered lists
        essay_text = re.sub(r'__([^\s]+)__', r'\1', essay_text)    # Remove __underline__
        
        return essay_text
        
    except ValueError as e:
        return f"Configuration Error: {str(e)}"
    except Exception as e:
        # Return a demo essay for testing
        return f"""{topic} is an important subject that deserves thorough examination. This essay provides a comprehensive overview of the topic, exploring its key aspects and significance in today's context.

The study of {topic} has evolved significantly over time, with scholars and practitioners contributing valuable insights. Understanding the fundamentals requires examining both historical developments and contemporary perspectives. This exploration reveals the complexity and depth of the subject matter.

Several key concepts form the foundation of {topic}. First, the theoretical framework provides a basis for understanding how different elements interact and influence each other. Second, practical applications demonstrate real-world relevance and demonstrate how theory translates into practice. Third, the broader implications extend beyond immediate contexts to affect society at large.

Different perspectives exist regarding {topic}, and this diversity of opinion enriches our understanding. Some experts emphasize certain aspects while others highlight different elements, creating a nuanced picture that reflects the complexity of the subject. By considering multiple viewpoints, we can develop a more complete understanding.

The significance of {topic} cannot be understated in today's world. Its relevance extends across various domains and continues to influence how we think about related issues. As research progresses and new discoveries emerge, our understanding will undoubtedly deepen and expand further."""


def text_to_speech(text, voice='alloy'):
    """
    Convert text to speech using Resemble.ai TTS API.
    Falls back to browser TTS if unavailable.
    """
    import os
    import requests
    import base64

    try:
        api_key = os.environ.get("RESEMBLE_API_KEY") or os.getenv("RESEMBLE_API_KEY")
        if not api_key:
            print("No Resemble API key found")
            return None

        # Use NEXA custom voice
        voice_uuid = "f644f59c"  # My Custom Voice NEXA

        response = requests.post(
            "https://f.cluster.resemble.ai/synthesize",
            headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
            json={"voice_uuid": voice_uuid, "data": text[:2000], "output_format": "mp3"},
            timeout=60
        )

        if response.status_code == 200:
            audio_b64 = response.json().get("audio_content")
            if audio_b64:
                print("Resemble TTS successful")
                return base64.b64decode(audio_b64)
        print(f"Resemble TTS Error {response.status_code}: {response.text[:200]}")

    except Exception as e:
        print(f"Resemble TTS failed: {e}")

    print("Resemble TTS failed - frontend will use browser TTS")
    return None


def search_web(query):
    """
    Simulate deep web search.
    In production, integrate with Bing Search API, Google Custom Search, or similar.
    
    Args:
        query: Search query
    
    Returns:
        List of search results (title, url, snippet)
    """
    # Demo implementation - returns simulated results
    # In production, integrate with actual search API
    
    simulated_results = [
        {
            'title': f'Result for {query} - Academic Source 1',
            'url': 'https://example.com/academic/source1',
            'snippet': f'Comprehensive information about {query} from academic sources.'
        },
        {
            'title': f'{query} - Wikipedia',
            'url': 'https://en.wikipedia.org/wiki/Example',
            'snippet': f'General overview of {query} from Wikipedia.'
        },
        {
            'title': f'Latest Research on {query}',
            'url': 'https://example.com/research',
            'snippet': f'Recent research findings related to {query}.'
        }
    ]
    
    return simulated_results


def humanize_essay(essay_text, user=None):
    """
    Rewrite an AI-generated essay to sound naturally human-written.
    """
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert editor who rewrites AI-generated essays to sound "
                        "naturally written by a human student. You preserve all ideas and arguments "
                        "but vary sentence structure, use natural transitions, and avoid robotic phrasing."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "Rewrite the following essay so it sounds like it was written naturally by a human student.\n\n"
                        "Guidelines:\n"
                        "- Keep the same ideas and arguments.\n"
                        "- Use varied sentence lengths and structures.\n"
                        "- Avoid repetitive patterns or robotic phrasing.\n"
                        "- Use natural transitions and logical flow.\n"
                        "- Make the tone thoughtful and slightly personal when appropriate.\n"
                        "- Avoid overly perfect or formulaic writing.\n"
                        "- Maintain clarity and academic quality.\n"
                        "- Do not add new facts or remove important points.\n\n"
                        "Output only the improved essay.\n\n"
                        f"Essay:\n{essay_text}"
                    )
                }
            ],
            temperature=0.85
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Humanize essay error: {e}")
        return essay_text  # fall back to original if humanization fails


def generate_essay_with_sources(topic, user=None, word_count=500):
    """
    Generate essay with citations from web search.
    
    Args:
        topic: Essay topic
        user: Django User object
        word_count: Target word count for the essay
    
    Returns:
        Tuple of (essay_text, sources_list)
    """
    # Perform search
    sources = search_web(topic)
    
    # Calculate max_tokens based on word count (approximately 1.33 tokens per word)
    max_tokens = int(word_count * 1.5)
    
    # Build source context
    source_context = "Search results:\n"
    for i, result in enumerate(sources, 1):
        source_context += f"{i}. {result['title']}: {result['snippet']}\n"
    
    # Generate essay with sources
    try:
        client = get_openai_client()
        
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Write a well-structured essay with proper citations based on the provided research."
                },
                {
                    "role": "user",
                    "content": f"Topic: {topic}\n\n{source_context}\n\nPlease write an essay of approximately {word_count} words incorporating these sources. Include introduction, body paragraphs, and conclusion."
                }
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        essay = response.choices[0].message.content
        
    except Exception:
        essay = deep_web_essay(topic, user, word_count)

    # Humanize the essay so it reads naturally
    essay = humanize_essay(essay, user)

    return essay, sources
