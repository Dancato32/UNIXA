import sys
import json

path = r'c:\Users\danie\Downloads\UNIXA-main\materials\views.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# === 1. Update quiz_ajax to detect persistence ===
start_idx = -1
for i, line in enumerate(lines):
    if 'def quiz_ajax(request, pk):' in line:
        start_idx = i
        break

if start_idx == -1:
    print("Could not find quiz_ajax")
    sys.exit(1)

# I'll inject the Persistence Detection logic at the beginning of the function
persistence_injection = [
    '    from .models import ConceptNode, StudentConceptState\n',
    '    from django.utils import timezone\n',
    '    import datetime\n',
    '    week_ago = timezone.now() - datetime.timedelta(days=7)\n',
    '    \n',
    '    persistence_notes = ""\n',
]

# I'll replace the old quiz_ajax with an even smarter one that handles persistence
# Find the end of quiz_ajax
end_idx = -1
for i in range(start_idx + 1, len(lines)):
    if lines[i].strip().startswith('def quiz_report_ajax('):
        end_idx = i
        break

if end_idx == -1:
    print("Could not find end of quiz_ajax")
    sys.exit(1)

new_quiz_ajax = [
    'def quiz_ajax(request, pk):\n',
    '    """AJAX: generate quiz with pattern-based rewiring and persistence escalation."""\n',
    '    if request.method != "POST":\n',
    '        return JsonResponse({"error": "POST required"}, status=405)\n',
    '    material = get_object_or_404(StudyMaterial, pk=pk, owner=request.user)\n',
    '    if not material.extracted_text:\n',
    '        return JsonResponse({"error": "No text could be extracted from this material."}, status=400)\n',
    '    \n',
    '    data = {}\n',
    '    if request.body:\n',
    '        try: data = json.loads(request.body)\n',
    '        except: pass\n',
    '    \n',
    '    selected_topics = data.get("topics", [])\n',
    '    custom_topic = data.get("custom_topic", "").strip()\n',
    '    difficulty = data.get("difficulty", "academic")\n',
    '    selected_model = resolve_model(data.get("model"))\n',
    '    \n',
    '    from .models import ConceptNode, StudentConceptState\n',
    '    from django.utils import timezone\n',
    '    import datetime\n',
    '    week_ago = timezone.now() - datetime.timedelta(days=7)\n',
    '    \n',
    '    # Context building & Persistence Detection\n',
    '    context_info = ""\n',
    '    dep_info = ""\n',
    '    escalation_instructions = ""\n',
    '    \n',
    '    if selected_topics:\n',
    '        topic_objs = material.concepts.filter(name__in=selected_topics)\n',
    '        for t in topic_objs:\n',
    '            context_info += f"- {t.name}: {t.definition}\\n"\n',
    '            # Detect recurrence\n',
    '            try:\n',
    '                state = StudentConceptState.objects.get(user=request.user, concept=t)\n',
    '                errors = state.error_profile or {}\n',
    '                misconception_count = errors.get("misconception", 0)\n',
    '                if misconception_count >= 2:\n',
    '                    escalation_instructions += f"- ESCALATE {t.name}: The student has a PERSISTANT MISCONCEPTION on this topic. Instead of a standard fix, use an ANALOGY or FIRST PRINCIPLES breakdown in the remediation bridge.\\n"\n',
    '            except StudentConceptState.DoesNotExist:\n',
    '                pass\n',
    '\n',
    '            for prereq in t.prerequisites.all():\n',
    '                dep_info += f"  - {t.name} depends on: {prereq.name}\\n"\n',
    '    \n',
    '    if custom_topic:\n',
    '        context_info += f"- FOCUS AREA: {custom_topic}\\n"\n',
    '    \n',
    '    target_desc = "the entire material" if not context_info else "the specific topics listed below"\n',
    '    \n',
    '    diff_instructions = {\n',
    '        "casual": "Focus on RECALL and basic DEFINITIONS. Questions should test whether the student remembers key terms and facts. Keep language simple.",\n',
    '        "academic": "Focus on APPLICATION and WHY questions. Test understanding of how concepts work and connect to each other.",\n',
    '        "mastery": "Focus on SYNTHESIS and REASONING. Ask multi-concept questions that require deep analysis, comparison, or evaluation."\n',
    '    }\n',
    '    diff_prompt = diff_instructions.get(difficulty, diff_instructions["academic"])\n',
    '    \n',
    '    prompt = f"""You are a cognitive science assessment expert. Create a 5-question multiple choice quiz.\n',
    '\n',
    'DIFFICULTY LEVEL: {difficulty.upper()}\n',
    '{diff_prompt}\n',
    '\n',
    '{"TARGET TOPICS:\\\\n" + context_info if context_info else "Cover the entire material broadly."}\n',
    '{"PREREQUISITE MAP:\\\\n" + dep_info if dep_info else ""}\n',
    '{"URGENT ESCALATIONS:\\\\n" + escalation_instructions if escalation_instructions else ""}\n',
    '\n',
    'MATERIAL TEXT (Excerpt):\n',
    '{material.extracted_text[:4000]}\n',
    '\n',
    'Return ONLY a valid JSON array. NO markdown, NO code blocks, NO extra text.\n',
    'Each object MUST have: "q", "concept", "opts", "ans", "explanation", "traps", "remediation", "dependencies".\n',
    'For "traps": map letter to {{"error_type", "trap_explanation"}}. Error Types: misconception | partial_confusion | misapplied_rule | calculation | recall | guessing.\n',
    'For "remediation": map to {{"bridge_question", "bridge_options", "bridge_answer", "bridge_explanation"}}. \n',
    'IMPORTANT: If an ESCALATION is requested for a topic, the "bridge_explanation" MUST be an analogy or first-principles breakdown.\n',
    '\n',
    'JSON:"""\n',
    '\n',
    '    try:\n',
    '        raw = ask_ai(prompt, user=request.user, use_rag=False, model=selected_model)\n',
    '        import re\n',
    '        clean_raw = re.sub(r"```json\\\\s*|\\\\s*```", "", raw).strip()\n',
    '        json_start = clean_raw.find("[")\n',
    '        json_end = clean_raw.rfind("]") + 1\n',
    '        if json_start != -1 and json_end != 0:\n',
    '            clean_raw = clean_raw[json_start:json_end]\n',
    '            \n',
    '        questions = json.loads(clean_raw)\n',
    '        return JsonResponse({"success": True, "questions": questions})\n',
    '    except Exception as e:\n',
    '        return JsonResponse({"error": f"NEXA Quiz Generation Failed: {str(e)}"}, status=500)\n',
    '\n'
]

# === 2. Update quiz_view to pass persistence risk badges ===
# Find quiz_view
start_v_idx = -1
for i, line in enumerate(lines):
    if 'def quiz_view(request, pk):' in line:
        start_v_idx = i
        break

if start_v_idx != -1:
    # Find end of quiz_view
    end_v_idx = -1
    for i in range(start_v_idx + 1, len(lines)):
        if lines[i].strip().startswith('@login_required'):
            end_v_idx = i
            break
        elif lines[i].strip().startswith('def '): # in case of no decorator
             end_v_idx = i
             break

    if end_v_idx != -1:
        new_quiz_view = [
            'def quiz_view(request, pk):\n',
            '    """Dedicated page: AI-generated interactive quiz with meta-cognitive awareness."""\n',
            '    material = get_object_or_404(StudyMaterial, pk=pk, owner=request.user)\n',
            '    concepts = material.concepts.all()\n',
            '    from .models import StudentConceptState\n',
            '    \n',
            '    concept_data = []\n',
            '    for c in concepts:\n',
            '        has_risk = False\n',
            '        try:\n',
            '            state = StudentConceptState.objects.get(user=request.user, concept=c)\n',
            '            if (state.error_profile or {}).get("misconception", 0) >= 2:\n',
            '                has_risk = True\n',
            '        except StudentConceptState.DoesNotExist:\n',
            '            pass\n',
            '        \n',
            '        concept_data.append({\n',
            '            "id": c.id,\n',
            '            "name": c.name,\n',
            '            "definition": c.definition,\n',
            '            "recurrence_risk": has_risk\n',
            '        })\n',
            '    \n',
            '    return render(request, "materials/quiz.html", {\n',
            '        "material": material,\n',
            '        "title": f"Quiz: {material.title}",\n',
            '        "concepts": concept_data\n',
            '    })\n',
            '\n'
        ]
        
        # Merge all changes
        # Replace quiz_ajax (lines start_idx to end_idx)
        # Replace quiz_view (lines start_v_idx to end_v_idx)
        
        # This is tricky with line indices changing. I'll do it safely.
        final_lines = lines[:start_v_idx] + new_quiz_view + lines[end_v_idx:start_idx] + new_quiz_ajax + lines[end_idx:]
        
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(final_lines)
        print("Updated materials/views.py with escalation logic and persistence risk detection.")
else:
    print("Could not find quiz_view")
    sys.exit(1)
