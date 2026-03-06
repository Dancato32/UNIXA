"""
AI Utilities for the AI Tutor app.
Handles OpenAI API calls and RAG (Retrieval-Augmented Generation) integration.
"""
import os
import json
from django.conf import settings


def get_openai_client():
    """Get OpenAI client with API key from settings or environment."""
    api_key = getattr(settings, 'OPENAI_API_KEY', None) or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured. Please set it in .env file.")
    
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
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


def ask_ai(message, user=None, use_rag=True):
    """
    Send a message to AI and get a response.
    
    Args:
        message: User's message
        user: Django User object (optional, for RAG context)
        use_rag: Whether to use RAG with study materials
    
    Returns:
        AI response string
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        client = get_openai_client()
        logger.info("OpenAI client created successfully")
        
        # Build context with RAG if enabled and user provided
        system_message = "You are a helpful AI tutor for students. Provide clear, educational explanations."
        
        if use_rag and user:
            rag_context = get_study_materials_for_rag(user)
            if rag_context:
                system_message += f"\n\nRelevant study materials from the student's uploads:\n{rag_context}"
        
        # Make API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
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
        return f"Configuration Error: {str(e)}"
    except Exception as e:
        import traceback
        logger.error(f"Exception in ask_ai: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        # For demo purposes, return a simulated response if API fails
        return f"AI Response: Thank you for your question about '{message}'. This is a demo response. To get real AI responses, please configure your OpenAI API key in the .env file."


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
        
        # Build research context
        research_context = f"""
        Topic: {topic}
        
        Please write a comprehensive, well-structured essay of approximately {word_count} words on this topic.
        Include:
        - Introduction
        - Main body with key points
        - Conclusion
        - Proper citations where applicable
        """
        
        # Add RAG context if available
        if user:
            rag_context = get_study_materials_for_rag(user)
            if rag_context:
                research_context += f"\n\nRelevant study materials:\n{rag_context}"
        
        # Make API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert academic writer. Write comprehensive, well-researched essays with proper structure."
                },
                {
                    "role": "user", 
                    "content": research_context
                }
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except ValueError as e:
        return f"Configuration Error: {str(e)}"
    except Exception as e:
        # Return a demo essay for testing
        return f"""# Essay on {topic}

## Introduction
{topic} is an important subject that deserves thorough examination. This essay explores the key aspects and provides a comprehensive overview of the topic.

## Main Discussion

### Background and Context
Understanding {topic} requires looking at both historical developments and current understanding. Scholars have debated various aspects of this topic for years.

### Key Concepts
The fundamental concepts surrounding {topic} include several important elements that need to be addressed. These include theoretical frameworks, practical applications, and real-world implications.

### Analysis and Perspectives
Different perspectives exist regarding {topic}. Some experts argue for one approach while others suggest alternative viewpoints. This diversity of opinion enriches our understanding.

## Conclusion
In conclusion, {topic} remains a significant area of study with ongoing research and developments. Further exploration and discussion will continue to advance our knowledge.

---
*This is a demo essay. To generate real AI essays, please configure your OpenAI API key in the .env file.*"""


def text_to_speech(text, voice='alloy'):
    """
    Convert text to speech using OpenAI's TTS API.
    
    Args:
        text: Text to convert to speech
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
    
    Returns:
        Audio content as bytes or None if unavailable
    """
    try:
        client = get_openai_client()
        
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text[:4096]  # Limit input length
        )
        
        return response.content
        
    except Exception as e:
        print(f"TTS Error: {e}")
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
            model="gpt-4o-mini",
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

