"""
AI utilities for Assignment Assistant.
Integrates with study materials for RAG.
"""
import os
import logging
from django.conf import settings
from materials.models import StudyMaterial

logger = logging.getLogger(__name__)


def get_openai_client():
    """Get OpenAI client with API key from settings or environment."""
    api_key = getattr(settings, 'OPENAI_API_KEY', None) or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured.")
    
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except ImportError:
        raise ImportError("OpenAI package not installed.")


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


def process_assignment_with_ai(assignment, user):
    """
    Process an assignment using AI with RAG.
    
    Args:
        assignment: Assignment model instance
        user: Django User instance
    
    Returns:
        Generated content string
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
        
        materials = get_user_study_materials_for_rag(user)
        rag_context = build_rag_context(materials)
        
        task_prompt = get_task_prompt(
            assignment.task_type,
            assignment_content,
            assignment.instructions
        )
        
        if rag_context:
            full_prompt = f"""{rag_context}

IMPORTANT: Use the study materials above as reference when answering.
If the study materials are relevant, incorporate them into your response.

{task_prompt}"""
        else:
            full_prompt = f"""Note: No study materials uploaded. Answer based on general knowledge.

{task_prompt}"""
        
        try:
            client = get_openai_client()
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert academic assistant. Generate high-quality, well-structured content based on the assignment and any provided study materials."
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
            logger.error(f"OpenAI API error: {e}")
            result_content = _generate_demo_response(assignment, materials)
        
        used_materials_text = "\n".join([m['title'] for m in materials]) or "No materials used"
        
        return result_content, used_materials_text
        
    except Exception as e:
        logger.error(f"Error processing assignment: {e}")
        raise


def _generate_demo_response(assignment, materials):
    """Generate a demo response when API is unavailable."""
    
    demo_responses = {
        'essay': f"""# Assignment Essay: {assignment.title}

## Introduction
This essay addresses the assignment requirements based on the provided content and study materials.

## Main Discussion

### Key Points
The assignment has been analyzed and the following key points emerge from the content:

1. The primary topic addresses important concepts that require thorough examination
2. Supporting materials provide additional context and depth
3. The analysis reveals several interconnected themes

### Detailed Analysis
Based on the assignment content and available study materials, this section provides comprehensive coverage of the topic. The materials referenced include: {', '.join([m['title'] for m in materials]) if materials else 'general knowledge'}

## Conclusion
In summary, this assignment demonstrates understanding of the core concepts. The response has been generated using AI with reference to available study materials.

---
*Note: This is a demo response. Configure your OpenAI API key for full AI generation.*""",
        
        'summarize': f"""# Summary: {assignment.title}

## Overview
This summary is based on the assignment content and available study materials.

## Key Points
- Main topic addresses core concepts from the assignment
- Study materials provide additional context
- Content has been processed and condensed for clarity

## Materials Used
{', '.join([m['title'] for m in materials]) if materials else 'No additional materials'}

---
*Demo response - Configure OpenAI API key for full generation*""",
        
        'answer': f"""# Answers: {assignment.title}

## Question 1
Based on the assignment content, the answer addresses the key requirements.

## Question 2
The response incorporates information from study materials when applicable.

## Question 3
Additional context has been provided based on available reference materials.

---
*Demo response - Configure OpenAI API key for full generation*""",
        
        'slides': f"""# Slides: {assignment.title}

## Slide 1: Introduction
- Overview of the assignment topic
- Key objectives

## Slide 2: Main Concepts
- Core concepts from the content
- Reference to study materials

## Slide 3: Analysis
- Detailed breakdown
- Supporting points

## Slide 4: Conclusion
- Summary of findings
- Key takeaways

---
*Demo response - Configure OpenAI API key for full generation*""",
        
        'structured': f"""# Structured Response: {assignment.title}

## Section 1: Overview
Based on the assignment requirements.

## Section 2: Details
Information derived from assignment content and study materials.

## Section 3: Conclusion
Key findings and summary.

---
*Demo response - Configure OpenAI API key for full generation*"""
    }
    
    return demo_responses.get(assignment.task_type, demo_responses['essay'])
