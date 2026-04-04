import sys

path = r'c:\Users\danie\Downloads\UNIXA-main\materials\views.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# find range for quiz_ajax
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if 'def quiz_ajax(request, pk):' in line:
        start_idx = i
    if start_idx != -1 and 'def flashcards_view(request, pk):' in line:
        end_idx = i - 1
        break

if start_idx == -1 or end_idx == -1:
    print(f"Could not find quiz_ajax block. Start: {start_idx}, End: {end_idx}")
    sys.exit(1)

new_logic = [
    'def quiz_ajax(request, pk):\n',
    '    """AJAX: generate quiz with topic selection support."""\n',
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
    '    selected_model = resolve_model(data.get("model"))\n',
    '    \n',
    '    context_info = ""\n',
    '    if selected_topics:\n',
    '        topic_objs = material.concepts.filter(name__in=selected_topics)\n',
    '        for t in topic_objs:\n',
    '            context_info += f"- {t.name}: {t.definition}\\n"\n',
    '    if custom_topic:\n',
    '        context_info += f"- FOCUS AREA: {custom_topic}\\n"\n',
    '\n',
    '    target_desc = "the entire material" if not context_info else "the specific topics listed below"\n',
    '    \n',
    '    prompt = f"""Create a 5-question multiple choice quiz from this study material, focusing on {target_desc}.\n',
    '    \n',
    '    {f"TARGET TOPICS/DEFINITIONS:\\\\n{context_info}" if context_info else ""}\n',
    '    \n',
    '    MATERIAL TEXT (Excerpt):\n',
    '    {material.extracted_text[:4000]}\n',
    '    \n',
    '    Return ONLY a valid JSON array of objects. NO markdown, NO code blocks.\n',
    '    Each object must have: "q", "opts", "ans", "explanation".\n',
    '    \n',
    '    JSON:"""\n',
    '\n',
    '    try:\n',
    '        raw = ask_ai(prompt, user=request.user, use_rag=False, model=selected_model)\n',
    '        import re\n',
    '        clean_raw = re.sub(r"```json\\s*|\\s*```", "", raw).strip()\n',
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

# Keep the @login_required decorator
new_lines = lines[:start_idx] + new_logic + lines[end_idx+1:]

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Successfully updated materials/views.py")
