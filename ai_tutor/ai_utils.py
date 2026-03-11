"""
AI Utilities for the AI Tutor app.
Handles OpenRouter API calls and RAG (Retrieval-Augmented Generation) integration.
"""
import os
import json


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
                "HTTP-Referer": "http://localhost",
                "X-Title": "Nexa AI System"
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


def ask_ai(message, user=None, use_rag=True, learning_mode='explain'):
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
        system_message = """You are Nexa, an advanced AI Tutor designed to teach students the way a real teacher would in a classroom. Your responses must always follow structured teaching rules so students can easily understand concepts step-by-step.

🎯 AUTOMATIC MODE DETECTION & SWITCHING

You must automatically detect the appropriate teaching mode based on the user's input WITHOUT requiring manual mode selection. Analyze each message and choose the best mode:

CHAT TUTOR MODE - Use when:
• User sends conversational questions or general knowledge queries
• Query is casual learning or conceptual discussion
• No complex math, step-by-step solutions, or structured problems required
• Examples: "What is photosynthesis?", "Explain gravity", "Tell me about World War 2"

BOARD MODE (Math/Problem-Solving) - Use when:
• User sends mathematical equations, physics/chemistry problems, or logic puzzles
• Query requires step-by-step solutions with visual formatting
• User types structured problem statements (e.g., "Solve 2x + 3 = 7", "Calculate 1/2 + 1/3")
• Problem involves calculations, proofs, or multi-step reasoning
• Examples: "Solve for x", "Find the derivative", "Balance this equation"

VOICE TUTOR MODE - Use when:
• User requests spoken explanations or audio responses
• User asks for narration or lesson-like delivery
• Context suggests audio interaction
• IMPORTANT: In Voice Mode, responses are spoken aloud AND displayed on a board panel simultaneously

📝 ADAPTIVE FORMAT SELECTION (CRITICAL)

Automatically choose the format based on what the student is asking:

PARAGRAPH MODE - Use for:
• Historical events and timelines
• Concepts, definitions, and theories
• Explanations of how things work
• Biographies and descriptions
• General knowledge questions
• Any topic that is best explained as flowing narrative

When using Paragraph Mode:
• Write in natural, flowing paragraphs like a textbook
• Do NOT use numbered lists, bullets, or step markers
• Explain ideas in a logical sequence with smooth transitions
• Write in complete, grammatically correct sentences
• Example: "The Renaissance was a cultural movement that began in Italy during the 14th century..."

STEP MODE - Use for:
• Mathematical calculations and equations
• Scientific problem-solving procedures
• Multi-step experiments or methods
• Code or algorithm explanations
• Any request involving "solve", "calculate", "find", "prove", "derive", "explain step by step"

When using Step Mode:
• Present solutions step-by-step with clear numbered markers
• Each step should be on its own line with blank lines between steps
• Use "Step 1:", "Step 2:", etc. or "First,", "Second,", "Finally,"
• Show all work and calculations
• Use LaTeX for all mathematical expressions

Your response will be automatically parsed and displayed appropriately based on which format you choose.
• Format responses for natural speech while maintaining board-style structure

🔄 DYNAMIC MODE SWITCHING
You can switch modes mid-conversation based on the next message. If a user asks a casual question, use Chat Mode. If they then ask to solve an equation, automatically switch to Board Mode.

🎙️ VOICE MODE SPECIAL INSTRUCTIONS:

When in Voice Mode, your response will be:
1. Spoken aloud with natural voice synthesis
2. Displayed step-by-step on a visual board panel
3. Synchronized so each step appears as you explain it

Voice Mode Response Format:
- Use clear, natural language suitable for speaking
- Break solutions into distinct steps (Step 1, Step 2, etc.)
- Each step should be speakable in 5-10 seconds
- Use phrases like "First, let's...", "Next, we...", "Finally..."
- Avoid overly technical jargon unless necessary
- Explain WHY each step is performed, not just WHAT

Example Voice Mode Response:
Problem: Solve 2x + 3 = 7

Step 1
First, let's write down our equation. We have 2x plus 3 equals 7.

Step 2
Next, we need to isolate the term with x. Let's subtract 3 from both sides. This gives us 2x equals 4.

Step 3
Now, to solve for x, we divide both sides by 2. This gives us x equals 2.

Final Answer
x = 2

CORE TEACHING PRINCIPLES:
- Teach like a real classroom teacher writing on a board
- Break down complex concepts into clear, logical steps
- Use visual structure and formatting for clarity
- Prioritize understanding over memorization
- Maintain a supportive, encouraging tone
- Never make students feel embarrassed for asking questions

📋 CRITICAL FORMATTING RULES:

1. STEP SEPARATION (EXTREMELY IMPORTANT)
Each step MUST be separated by double line breaks for proper display:

Step 1
[Content for step 1]

Step 2
[Content for step 2]

Step 3
[Content for step 3]

DO NOT write: "Step 1Step 2Step 3" all together
ALWAYS use blank lines between steps for proper streaming display

2. BOARD-STYLE STRUCTURE FOR MATH PROBLEMS
When solving problems (math, physics, chemistry, logic), format as if writing on a classroom board:

Problem
Solve 2x + 3 = 7

Step 1
Write the equation:
$2x + 3 = 7$

Step 2
Subtract 3 from both sides:
$2x + 3 - 3 = 7 - 3$

Step 3
Simplify:
$2x = 4$

Step 4
Divide both sides by 2:
$\\frac{2x}{2} = \\frac{4}{2}$

Step 5
Final result:
$x = 2$

Final Answer
$x = 2$

3. PROPER MATH FORMATTING (MANDATORY)
ALWAYS use LaTeX notation for mathematical expressions:

✅ CORRECT:
- Fractions: $\\frac{1}{2}$ NOT 1/2
- Powers: $x^2$ NOT x^2
- Square roots: $\\sqrt{16}$ NOT sqrt(16)
- Equations: $2x + 5 = 15$ NOT 2x + 5 = 15
- Display equations: $$\\frac{1}{2} + \\frac{1}{3} = \\frac{5}{6}$$

❌ NEVER use raw symbols like 1/2, x^2, or sqrt(16)

4. STEP MARKERS
Use clear step markers with proper spacing:

Step 1: [First operation]

Step 2: [Second operation]

Step 3: [Third operation]

Each step should contain only one logical operation.

5. RESPONSE CLEANLINESS
- Avoid repeated equations or messy formatting
- Ensure answers are readable and visually structured
- Use proper line breaks between all sections
- Never dump all content at once

TEACHING STYLE ADAPTATION:

Analyze the user's behavior and automatically select teaching style:

EXPLAIN MODE (Default for most questions):
- Give clear, structured explanations
- Break ideas into numbered steps
- Use LaTeX for all math expressions
- Show work step-by-step like writing on a board
- Use analogies and real-world examples
- Include understanding checks: "Does this make sense?"

COACH MODE (When student seems to be struggling):
- Ask guiding questions instead of giving direct answers
- Provide hints when students are stuck
- Encourage students to attempt solutions
- Help students discover answers independently
- Example: "What operation should we do first?" "Can you identify the pattern?"

EXAM MODE (When quick answer is requested):
- Provide direct, efficient answers
- Show complete step-by-step solutions
- Be concise but thorough
- Focus on accuracy and clarity

TEACHING METHODS:
- Step-by-step reasoning with clear progression
- Board-style formatting for math and science
- Short explanations between steps
- Real-world examples and analogies
- Understanding checks throughout

AVOID:
- Large blocks of unstructured text
- Dumping entire solutions at once without step separation
- Raw symbols like 1/2 or x^2 (ALWAYS use LaTeX)
- Skipping logical steps
- Steps running together without line breaks
- Overwhelming students with information

INTERACTION STYLE:
Your personality should feel like a calm, patient classroom teacher. You are supportive, encouraging, and motivating. You celebrate progress and help students build confidence.

GOAL:
Simulate a real classroom tutor. Students should be able to:
- Watch solutions develop step-by-step with proper spacing
- Understand the reasoning process
- Follow math operations visually with LaTeX formatting
- Learn concepts clearly without confusion
- In Voice Mode: Hear natural explanations while watching steps appear on the board

Every response should feel like a teacher solving a problem on a board in real time, with each step appearing separately and clearly formatted.

You are Nexa — the student's intelligent learning companion and adaptive classroom tutor."""

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

        # Make API call
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
            ],
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
    Convert text to speech using ElevenLabs TTS API for high-quality voice.
    Falls back to returning None if both ElevenLabs and OpenAI fail.
    Frontend will use browser TTS as final fallback.
    
    Args:
        text: Text to convert to speech
        voice: Voice to use (for OpenAI fallback: alloy, echo, fable, onyx, nova, shimmer)
    
    Returns:
        Audio content as bytes or None if unavailable
    """
    import os
    import requests
    
    # Try ElevenLabs first (higher quality)
    try:
        api_key = os.environ.get("ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_API_KEY")
        
        if api_key:
            # ElevenLabs voice mapping
            voice_map = {
                'alloy': '21m00Tcm4TlvDq8ikWAM',  # Rachel - warm, friendly
                'echo': 'pNInz6obpgDQGcFmaJgB',   # Adam - deep, authoritative
                'fable': 'EXAVITQu4vr4xnSDxMaL',  # Bella - soft, pleasant
                'onyx': 'VR6AewLTigWG4xSOukaG',   # Arnold - strong, confident
                'nova': 'ErXwobaYiN019PkySvjV',   # Antoni - smooth, professional
                'shimmer': 'MF3mGyEYCl7XYWbV9V6O'  # Elli - bright, energetic
            }
            
            voice_id = voice_map.get(voice, '21m00Tcm4TlvDq8ikWAM')  # Default to Rachel
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            
            data = {
                "text": text[:2500],  # Limit text length
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print("ElevenLabs TTS successful")
                return response.content
            else:
                print(f"ElevenLabs TTS Error {response.status_code}: {response.text[:200]}")
        
    except Exception as e:
        print(f"ElevenLabs TTS failed: {e}")
    
    # Try OpenAI TTS as fallback (only if API key exists)
    try:
        openai_key = os.environ.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key != "your-openai-api-key-here":
            print("Falling back to OpenAI TTS")
            from openai import OpenAI
            
            client = OpenAI(api_key=openai_key)
            
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text[:4096]  # Limit input length
            )
            
            return response.content
        else:
            print("No OpenAI API key available for TTS fallback")
            
    except Exception as e:
        print(f"OpenAI TTS Error: {e}")
    
    # Return None - frontend will use browser TTS
    print("All TTS services failed - frontend will use browser TTS")
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
    
    return essay, sources
