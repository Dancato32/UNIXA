"""
AI utilities for Assignment Assistant.
Integrates with study materials for RAG.
"""
import os
import logging
from materials.models import StudyMaterial

logger = logging.getLogger(__name__)


def get_openai_client():
    """Get OpenRouter client with API key from environment."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not configured.")
    
    try:
        from openai import OpenAI
        return OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost",
                "X-Title": "Nexa AI System"
            }
        )
    except ImportError:
        raise ImportError("OpenAI package not installed.")


def humanize_assignment(content, task_type):
    """
    Rewrite AI-generated assignment content to sound naturally human-written.
    Only applied to essay/answer/structured/summarize types (not slides).
    Falls back to original if it fails.
    """
    if task_type == 'slides':
        return content  # Keep slides structured

    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert editor who rewrites AI-generated academic content to sound naturally human-written."
                },
                {
                    "role": "user",
                    "content": f"""Rewrite the following content so it sounds like it was written naturally by a human student.

Guidelines:
- Keep the same ideas, arguments, and structure.
- Use varied sentence lengths and structures.
- Avoid repetitive patterns or robotic phrasing.
- Use natural transitions and logical flow.
- Make the tone thoughtful and slightly personal when appropriate.
- Avoid overly perfect or formulaic writing.
- Maintain clarity and academic quality.
- Do not add new facts or remove important points.
- Preserve any headings and formatting (##, ###, bullet points).

Output only the improved content.

Content:
{content}"""
                }
            ],
            max_tokens=4000,
            temperature=0.75
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Humanization error: {e}")
        return content  # Fall back to original


def get_user_study_materials_for_rag(user):
    """
    Retrieve uploaded study materials for RAG context.
    Returns a list of materials with their extracted text.
    """
    try:
        materials = StudyMaterial.objects.filter(owner=user)
        
        material_list = []
        for material in materials:
            if material.extracted_text:
                material_list.append({
                    'title': material.title,
                    'text': material.extracted_text[:3000]
                })
            elif material.file:
                material_list.append({
                    'title': material.title,
                    'text': '[File uploaded but text not extracted]'
                })
        
        return material_list
    except Exception as e:
        logger.error(f"Error fetching study materials: {e}")
        return []


def build_rag_context(materials):
    """Build context string from study materials."""
    if not materials:
        return ""
    
    context = "STUDY MATERIALS REFERENCE:\n\n"
    for i, mat in enumerate(materials, 1):
        context += f"--- Material {i}: {mat['title']} ---\n"
        context += mat['text'][:2000] + "\n\n"
    
    return context


def get_task_prompt(task_type, assignment_content, instructions):
    """Build the AI prompt based on task type."""
    
    base_prompts = {
        'essay': f"""Write a comprehensive essay based on the following assignment. 
Include introduction, main body with key points, and conclusion.
{instructions}

Assignment/Content:
{assignment_content}

Write a well-structured, academic essay.""",
        
        'summarize': f"""Provide a clear and concise summary of the following assignment or content.
{instructions}

Content:
{assignment_content}

Create a summary that captures the main points.""",
        
        'answer': f"""Answer the questions in the following assignment.
{instructions}

Assignment:
{assignment_content}

Provide clear, detailed answers to each question.""",
        
        'slides': f"""Create slide content for a presentation based on the assignment.
{instructions}

Assignment:
{assignment_content}

Format the content as slide sections with bullet points.
Use ## for slide titles and - for bullet points.""",
        
        'structured': f"""Provide structured answers to the following assignment.
{instructions}

Assignment:
{assignment_content}

Use clear headings and organized structure.""",
    }
    
    return base_prompts.get(task_type, base_prompts['essay'])


def process_assignment_with_ai(assignment, user, use_rag=True):
    """
    Process an assignment using AI with optional RAG.
    
    Args:
        assignment: Assignment model instance
        user: Django User instance
        use_rag: Boolean to enable/disable RAG (default: True)
    
    Returns:
        Tuple of (generated content string, used materials text)
    """
    try:
        assignment_content = ""
        
        if assignment.file:
            from .doc_generator import extract_text_from_file
            assignment.file.seek(0)
            assignment_content = extract_text_from_file(assignment.file)
            assignment.file.seek(0)
        
        if assignment.text_content:
            assignment_content += "\n\n" + assignment.text_content
        
        if not assignment_content.strip():
            raise ValueError("No content to process")
        
        # Only fetch and use materials if use_rag is True
        materials = []
        rag_context = ""
        if use_rag:
            # Use specifically selected materials if any, otherwise use all
            selected = assignment.selected_materials.all()
            if selected.exists():
                materials = [
                    {'title': m.title, 'text': m.extracted_text[:3000]}
                    for m in selected if m.extracted_text
                ]
            else:
                materials = get_user_study_materials_for_rag(user)
            rag_context = build_rag_context(materials)
        
        task_prompt = get_task_prompt(
            assignment.task_type,
            assignment_content,
            assignment.instructions
        )
        
        if use_rag and rag_context:
            full_prompt = f"""{rag_context}

IMPORTANT: Use the study materials above as reference when answering.
If the study materials are relevant, incorporate them into your response.
Cite specific information from the materials when applicable.

{task_prompt}"""
        elif use_rag and not rag_context:
            full_prompt = f"""Note: RAG enabled but no study materials uploaded. Answer based on general knowledge.

{task_prompt}"""
        else:
            full_prompt = f"""Note: Generating response based on general knowledge only (RAG disabled).

{task_prompt}"""
        
        try:
            client = get_openai_client()
            
            response = client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert academic assistant. Generate high-quality, well-structured content based on the assignment" + (" and any provided study materials." if use_rag else ".")
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                max_tokens=3000,
                temperature=0.7
            )
            
            result_content = response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            result_content = _generate_demo_response(assignment, materials, use_rag)
        
        # Humanize the result (skipped for slides)
        logger.info("Humanizing assignment content...")
        result_content = humanize_assignment(result_content, assignment.task_type)
        
        if use_rag and materials:
            used_materials_text = "\n".join([m['title'] for m in materials])
        elif use_rag:
            used_materials_text = "RAG enabled but no materials available"
        else:
            used_materials_text = "RAG disabled - generated from general knowledge"
        
        return result_content, used_materials_text
        
    except Exception as e:
        logger.error(f"Error processing assignment: {e}")
        raise


def _generate_demo_response(assignment, materials, use_rag=True):
    """Generate a demo response when API is unavailable."""
    
    materials_note = ""
    if use_rag:
        if materials:
            materials_note = f"Materials referenced: {', '.join([m['title'] for m in materials])}"
        else:
            materials_note = "RAG enabled but no materials available"
    else:
        materials_note = "Generated without study materials (RAG disabled)"
    
    demo_responses = {
        'essay': f"""# Assignment Essay: {assignment.title}

## Introduction
This essay addresses the assignment requirements based on the provided content{' and study materials' if use_rag and materials else ''}.

## Main Discussion

### Key Points
The assignment has been analyzed and the following key points emerge from the content:

1. The primary topic addresses important concepts that require thorough examination
2. Supporting materials provide additional context and depth
3. The analysis reveals several interconnected themes

### Detailed Analysis
Based on the assignment content{' and available study materials' if use_rag and materials else ''}, this section provides comprehensive coverage of the topic. {materials_note}

## Conclusion
In summary, this assignment demonstrates understanding of the core concepts. The response has been generated using AI{' with reference to available study materials' if use_rag and materials else ''}.

---
*Note: This is a demo response. Configure your OpenRouter API key for full AI generation.*""",
        
        'summarize': f"""# Summary: {assignment.title}

## Overview
This summary is based on the assignment content{' and available study materials' if use_rag and materials else ''}.

## Key Points
- Main topic addresses core concepts from the assignment
{f"- Study materials provide additional context" if use_rag and materials else ""}
- Content has been processed and condensed for clarity

## Materials Used
{materials_note}

---
*Demo response - Configure OpenRouter API key for full generation*""",
        
        'answer': f"""# Answers: {assignment.title}

## Question 1
Based on the assignment content, the answer addresses the key requirements.

## Question 2
The response incorporates information{' from study materials' if use_rag and materials else ''} when applicable.

## Question 3
Additional context has been provided based on available reference materials.

{materials_note}

---
*Demo response - Configure OpenRouter API key for full generation*""",
        
        'slides': f"""# Slides: {assignment.title}

## Slide 1: Introduction
- Overview of the assignment topic
- Key objectives

## Slide 2: Main Concepts
- Core concepts from the content
{f"- Reference to study materials" if use_rag and materials else ""}

## Slide 3: Analysis
- Detailed breakdown
- Supporting points

## Slide 4: Conclusion
- Summary of findings
- Key takeaways

{materials_note}

---
*Demo response - Configure OpenRouter API key for full generation*""",
        
        'structured': f"""# Structured Response: {assignment.title}

## Section 1: Overview
Based on the assignment requirements.

## Section 2: Details
Information derived from assignment content{' and study materials' if use_rag and materials else ''}.

## Section 3: Conclusion
Key findings and summary.

{materials_note}

---
*Demo response - Configure OpenRouter API key for full generation*"""
    }
    
    return demo_responses.get(assignment.task_type, demo_responses['essay'])
