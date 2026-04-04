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
                "HTTP-Referer": "https://unixa.onrender.com",
                "X-Title": "Nexa AI Assignment"
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
        'essay': f"""Write a comprehensive academic essay or research report. 
Include a compelling introduction, thematic body paragraphs with evidentiary support, and a definitive conclusion.
Instructions: {instructions}
Content: {assignment_content}""",
        
        'research': f"""Conduct a deep research investigation into this topic. 
Include literature review, methodology, data analysis, and cited findings.
Instructions: {instructions}
Content: {assignment_content}""",
        
        'coding': f"""You are a Senior Software Engineer. Build a high-quality technical solution.
Include: 
1. System Architecture & Tech Stack rationale.
2. Complete, well-commented code implementation.
3. Unit testing strategy.
4. Technical README.md.
Instructions: {instructions}
Content: {assignment_content}""",
        
        'lab_report': f"""Generate a professional Scientific/Engineering Lab Report.
Structure: Title, Aim, Apparatus, Methodology, Results (use table structure if needed), Discussion, and Conclusion.
Instructions: {instructions}
Content: {assignment_content}""",
        
        'presentation': f"""Draft comprehensive content for a high-impact presentation.
Format as Slide Sections (Slide 1, Slide 2, etc.) with Speaker Notes and Bullet Points.
Wait! Do not use slides formatting if user wants a script. Focus on visual communication.
Instructions: {instructions}
Content: {assignment_content}""",
        
        'problem_set': f"""Solve the mathematical or analytical problem set provided.
Show step-by-step calculations, explain the logic for each formula used, and provide the final answer clearly.
Instructions: {instructions}
Content: {assignment_content}""",
        
        'group': f"""Develop a collaborative Group Project or Startup System.
Include: Team roles, Project Scope, System Modules, and a Collaborative Implementation Strategy.
Instructions: {instructions}
Content: {assignment_content}""",
        
        'case_study': f"""Perform a detailed Case Study analysis.
Structure: Situation Overview, Problem Identification, Root Cause Analysis, Proposed Solutions, and Implementation Roadmap.
Instructions: {instructions}
Content: {assignment_content}""",
        
        'capstone': f"""This is a FINAL YEAR CAPSTONE project. You are the Lead Architect.
Draft a massive, high-level project vision. 
Include: Abstract, Requirement Specification, Full Tech Stack (Django/React/AI), Database Schema, Component Architecture, and a 12-week Development Roadmap.
Instructions: {instructions}
Content: {assignment_content}""",
    }
    
    return base_prompts.get(task_type, base_prompts['essay'])


def generate_assignment_stream(assignment, user):
    """
    Paged Sectional Builder:
    1. Generate an 8-section outline.
    2. Iterate through each section to generate deep, detailed content (~800 words/section).
    3. Yield tokens continuously for the SPA.
    """
    try:
        assignment_content = ""
        if assignment.file:
            from .doc_generator import extract_text_from_file
            assignment.file.seek(0)
            assignment_content = extract_text_from_file(assignment.file)
            assignment.file.seek(0)
        
        if assignment.text_content:
            assignment_content += "\n" + assignment.text_content
            
        if not assignment_content.strip():
            yield "Error: No assignment content provided."
            return

        # RAG Context
        materials = []
        rag_context = ""
        if assignment.use_rag:
            selected = assignment.selected_materials.all()
            if selected.exists():
                materials = [{'title': m.title, 'text': m.extracted_text[:3000]} for m in selected if m.extracted_text]
            else:
                materials = get_user_study_materials_for_rag(user)
            rag_context = build_rag_context(materials)
            
        task_prompt = get_task_prompt(assignment.task_type, assignment_content, assignment.instructions)
        base_prompt = f"{rag_context}\n\n{task_prompt}"
        if getattr(assignment, 'research_notes', None):
            base_prompt = f"DEEP RESEARCH INTELLIGENCE:\n{assignment.research_notes}\n\n{base_prompt}"

        client = get_openai_client()

        # PHASE 1: GENERATE OUTLINE
        yield "[PROGRESS] Planning Paper Structure (7-Stage Logic)..."
        outline_resp = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Create a detailed 7-section outline for this assignment. Return ONLY the titles of the 7 sections, one per line."},
                {"role": "user", "content": base_prompt}
            ]
        )
        outline = [line.strip() for line in outline_resp.choices[0].message.content.strip().split('\n') if line.strip()][:7]
        
        # PHASE 2: GENERATE SECTIONS
        full_text_history = []
        
        for i, section_title in enumerate(outline):
            yield f"[PROGRESS] Drafting {section_title}..."
            yield f"\n\n# {section_title}\n\n" # Visual Header
            
            # Context for the current section
            section_prompt = f"""
Previous Sections Summary: {' '.join(full_text_history[-500:]) if full_text_history else 'None'}
NOW, write the section '{section_title}' in extreme detail (aim for 800+ words). 
Be exhaustive. Do not use markdown ## or ** symbols. Use only plain-text structure.
Original Assignment Context: {base_prompt[:1000]}
"""
            stream = client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional academic writer focusing on depth and length. You write 800-1000 words per section."},
                    {"role": "user", "content": section_prompt}
                ],
                max_tokens=2000,
                temperature=0.7,
                stream=True
            )
            
            section_content = []
            for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                if token:
                    section_content.append(token)
                    yield token
            
            full_text_history.append("".join(section_content))
            yield "\n\n[PAGE_BREAK]\n\n" # Page break signal for frontend

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"Error: {str(e)}"

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
        
        if getattr(assignment, 'research_notes', None):
            full_prompt = f"DEEP RESEARCH FINDINGS (EXTERNAL):\n{assignment.research_notes}\n\n{full_prompt}"
        
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


def transform_to_presentation_json(content, num_slides=7):
    """
    Transforms dense text (e.g. an essay) into a structured JSON array for PowerPoint slides.
    Returns a list of dictionaries.
    """
    import json
    try:
        client = get_openai_client()
        prompt = f"""You are an expert presentation designer. Convert the following academic/professional text into exactly {num_slides} highly detailed, professional presentation slides.
For each slide, extract the core ideas as detailed bullet points, keep the full explanation for speaker notes, and write a specific, descriptive English prompt for an AI image generator that perfectly matches the slide's specific topic.

Format the output strictly as a JSON array of objects. Do not use markdown blocks outside the JSON.
Example structure:
[
  {{
    "title": "Slide Title",
    "bullets": ["Detailed comprehensive bullet point 1", "Detailed comprehensive bullet point 2", "Detailed comprehensive bullet point 3"],
    "notes": "Full speaker notes containing the extensive details...",
    "image_prompt": "high resolution photograph of a modern server room with glowing blue lights"
  }}
]

Content to transform:
{content[:15000]}
"""
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.7
        )
        result_text = response.choices[0].message.content.strip()
        
        # Clean up possible markdown json block
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        slides_data = json.loads(result_text.strip())
        if isinstance(slides_data, list):
            return slides_data
        return []
    except Exception as e:
        logger.error(f"Error transforming presentation JSON: {e}")
        return []
