import sys

path = r'c:\Users\danie\Downloads\UNIXA-main\materials\views.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# === 1. Replace quiz_ajax function body ===
# Find start: "def quiz_ajax(request, pk):"
# Find end: next "def " at same indentation (flashcards_view)
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if 'def quiz_ajax(request, pk):' in line:
        start_idx = i
    if start_idx is not None and i > start_idx and line.strip().startswith('def flashcards_view('):
        end_idx = i
        break

if start_idx is None or end_idx is None:
    print(f"Could not find quiz_ajax boundaries. Start: {start_idx}, End: {end_idx}")
    sys.exit(1)

print(f"Found quiz_ajax at lines {start_idx+1}-{end_idx}")

new_quiz_ajax = '''def quiz_ajax(request, pk):
    """AJAX: generate quiz with pattern-based rewiring intelligence."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    material = get_object_or_404(StudyMaterial, pk=pk, owner=request.user)
    if not material.extracted_text:
        return JsonResponse({"error": "No text could be extracted from this material."}, status=400)
    
    data = {}
    if request.body:
        try: data = json.loads(request.body)
        except: pass
    
    selected_topics = data.get("topics", [])
    custom_topic = data.get("custom_topic", "").strip()
    difficulty = data.get("difficulty", "academic")
    selected_model = resolve_model(data.get("model"))
    
    # Context building
    context_info = ""
    dep_info = ""
    if selected_topics:
        topic_objs = material.concepts.filter(name__in=selected_topics)
        for t in topic_objs:
            context_info += f"- {t.name}: {t.definition}\\n"
            # Grab prerequisite info
            for prereq in t.prerequisites.all():
                dep_info += f"  - {t.name} depends on: {prereq.name}\\n"
    if custom_topic:
        context_info += f"- FOCUS AREA: {custom_topic}\\n"
    
    target_desc = "the entire material" if not context_info else "the specific topics listed below"
    
    diff_instructions = {
        "casual": "Focus on RECALL and basic DEFINITIONS. Questions should test whether the student remembers key terms and facts. Keep language simple.",
        "academic": "Focus on APPLICATION and WHY questions. Test understanding of how concepts work and connect to each other.",
        "mastery": "Focus on SYNTHESIS and REASONING. Ask multi-concept questions that require deep analysis, comparison, or evaluation. These should challenge even strong students."
    }
    diff_prompt = diff_instructions.get(difficulty, diff_instructions["academic"])
    
    prompt = f"""You are a cognitive science assessment expert. Create a 5-question multiple choice quiz.

DIFFICULTY LEVEL: {difficulty.upper()}
{diff_prompt}

{"TARGET TOPICS:\\n" + context_info if context_info else "Cover the entire material broadly."}
{"PREREQUISITE MAP:\\n" + dep_info if dep_info else ""}

MATERIAL TEXT:
{material.extracted_text[:4000]}

Return ONLY a valid JSON array. NO markdown, NO code blocks, NO extra text.
Each object MUST have these fields:
- "q": The question text
- "concept": Which concept this question tests (string)
- "opts": {{"A": "...", "B": "...", "C": "...", "D": "..."}}
- "ans": The correct letter ("A", "B", "C", or "D")
- "explanation": Why the correct answer is right
- "traps": {{
    "<wrong_letter>": {{
      "error_type": one of "misconception" | "partial_confusion" | "misapplied_rule" | "calculation" | "recall" | "guessing",
      "trap_explanation": "Why a student might pick this wrong answer (the common trap)"
    }}
  }} (one entry per wrong option)
- "remediation": {{
    "bridge_question": "A simpler follow-up question targeting the core misunderstanding",
    "bridge_options": {{"A": "...", "B": "...", "C": "..."}},
    "bridge_answer": "A" or "B" or "C",
    "bridge_explanation": "Why this is the right bridge answer"
  }}
- "dependencies": ["prerequisite concept names if any"]

JSON:"""

    try:
        raw = ask_ai(prompt, user=request.user, use_rag=False, model=selected_model)
        import re
        clean_raw = re.sub(r'```json\\s*|\\s*```', '', raw).strip()
        json_start = clean_raw.find('[')
        json_end = clean_raw.rfind(']') + 1
        if json_start != -1 and json_end != 0:
            clean_raw = clean_raw[json_start:json_end]
            
        questions = json.loads(clean_raw)
        return JsonResponse({"success": True, "questions": questions})
    except Exception as e:
        return JsonResponse({"error": f"NEXA Quiz Generation Failed: {str(e)}"}, status=500)


@login_required
def quiz_report_ajax(request, pk):
    """AJAX: process post-quiz analytics and update StudentConceptState."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    material = get_object_or_404(StudyMaterial, pk=pk, owner=request.user)
    
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    results = data.get("results", [])
    # results: [{concept, isRight, confidence, error_type, chosen}]
    
    concept_stats = {}
    total_calibration_correct = 0
    total_calibration_count = 0
    
    for r in results:
        concept_name = r.get("concept", "General")
        is_right = r.get("isRight", False)
        confidence = r.get("confidence", 3)  # 1-5 scale
        error_type = r.get("error_type", "unknown")
        
        if concept_name not in concept_stats:
            concept_stats[concept_name] = {"correct": 0, "total": 0, "errors": [], "high_conf_wrong": 0}
        
        concept_stats[concept_name]["total"] += 1
        if is_right:
            concept_stats[concept_name]["correct"] += 1
        else:
            concept_stats[concept_name]["errors"].append(error_type)
        
        # Confidence calibration
        total_calibration_count += 1
        if (is_right and confidence >= 4) or (not is_right and confidence <= 2):
            total_calibration_correct += 1
        if not is_right and confidence >= 4:
            concept_stats[concept_name]["high_conf_wrong"] += 1
    
    # Calculate calibration score
    calibration_score = round((total_calibration_correct / max(total_calibration_count, 1)) * 100)
    
    # Update StudentConceptState for each concept
    from .models import ConceptNode, StudentConceptState
    from django.utils import timezone
    
    for concept_name, stats in concept_stats.items():
        try:
            concept_node = ConceptNode.objects.get(material=material, name__iexact=concept_name)
            state, created = StudentConceptState.objects.get_or_create(
                user=request.user, concept=concept_node
            )
            # Update strength (rolling average)
            new_score = round((stats["correct"] / max(stats["total"], 1)) * 100)
            if created:
                state.concept_strength = new_score
            else:
                state.concept_strength = round((state.concept_strength * 0.6) + (new_score * 0.4))
            
            # Update error profile
            existing_errors = state.error_profile or {}
            for err in stats["errors"]:
                existing_errors[err] = existing_errors.get(err, 0) + 1
            state.error_profile = existing_errors
            
            # Calibration
            state.confidence_calibration = calibration_score
            state.last_reviewed = timezone.now()
            state.save()
        except ConceptNode.DoesNotExist:
            pass  # Custom concepts without nodes are skipped
    
    # Build response with analytics
    error_breakdown = {}
    for stats in concept_stats.values():
        for err in stats["errors"]:
            error_breakdown[err] = error_breakdown.get(err, 0) + 1
    
    return JsonResponse({
        "success": True,
        "calibration_score": calibration_score,
        "concept_mastery": {k: {"accuracy": round((v["correct"]/max(v["total"],1))*100), "errors": v["errors"], "overconfident": v["high_conf_wrong"]} for k, v in concept_stats.items()},
        "error_breakdown": error_breakdown
    })

'''

# Rebuild lines
new_lines = lines[:start_idx] + new_quiz_ajax.split('\n') + lines[end_idx:]

with open(path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print(f"Successfully upgraded quiz_ajax + added quiz_report_ajax")

# === 2. Add URL route ===
urls_path = r'c:\Users\danie\Downloads\UNIXA-main\materials\urls.py'
with open(urls_path, 'r', encoding='utf-8') as f:
    urls_content = f.read()

if 'quiz_report_ajax' not in urls_content:
    # Insert after the quiz_ajax line
    urls_content = urls_content.replace(
        "path('quiz/<int:pk>/ajax/', views.quiz_ajax, name='quiz_ajax'),",
        "path('quiz/<int:pk>/ajax/', views.quiz_ajax, name='quiz_ajax'),\n    path('quiz/<int:pk>/report/', views.quiz_report_ajax, name='quiz_report_ajax'),"
    )
    with open(urls_path, 'w', encoding='utf-8') as f:
        f.write(urls_content)
    print("Added quiz_report_ajax URL route")
else:
    print("quiz_report_ajax URL already exists")
