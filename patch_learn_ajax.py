import re

with open('materials/views.py', encoding='utf-8') as f:
    content = f.read()

# Find learn_ajax function
func_start = content.find('def learn_ajax(request, pk):')
assert func_start != -1, "learn_ajax not found"

# Find the system_prompt block start
sp_start = content.find('        system_prompt = f"""', func_start)
assert sp_start != -1, "system_prompt not found"

# Find the closing triple-quote of the system_prompt
sp_end = content.find('"""', sp_start + 30)
assert sp_end != -1, "closing triple-quote not found"
sp_end += 3  # include the closing """

print(f"Replacing chars {sp_start} to {sp_end}")
print("Old block preview:", repr(content[sp_start:sp_start+80]))

# Also find and replace the max_tokens line
old_max_tokens = '            max_tokens=600,'
new_max_tokens = '            max_tokens=1200,'

new_block = '''        # Full material text — up to 12000 chars for rich context
        full_text = material.extracted_text[:12000]

        # When user picks a topic, inject a focused excerpt from the material
        import re as _re
        topic_context = ""
        if user_message and history:
            for h in reversed(history):
                if h.get('role') == 'assistant' and 'Topics you can learn' in h.get('content', ''):
                    topic_match = _re.search(r'\\d+\\.\\s*(.+)', user_message)
                    if topic_match:
                        topic_name = topic_match.group(1).strip().lower()
                        paragraphs = [p.strip() for p in full_text.split('\\n') if len(p.strip()) > 40]
                        relevant = [p for p in paragraphs if any(w in p.lower() for w in topic_name.split() if len(w) > 3)]
                        if relevant:
                            topic_context = "\\n\\n== FOCUSED MATERIAL EXCERPT FOR THIS TOPIC ==\\n" + "\\n".join(relevant[:25])
                    break

        system_prompt = f"""You are NEXA Learn Mode, an expert AI tutor. Teach the student using the actual study material below as your PRIMARY source — combined with your own knowledge to add examples, analogies, and deeper explanations.

== STUDY MATERIAL: {material.title} ==
{full_text}
{topic_context}
== END OF MATERIAL ==

CRITICAL RULES:
- Ground ALL teaching in the actual material above — quote or paraphrase it directly
- Use your own knowledge to add examples, analogies, and fill gaps
- For math: use $expression$ for inline, $$expression$$ for display (own line)
- Never contradict the material

== PHASE 1: TOPIC LIST (first message only) ==
Read the material carefully. Extract ALL distinct topics and subtopics.
Output EXACTLY:
📚 Topics you can learn:
1. [Topic Name]
2. [Topic Name]
(list every topic found in the material)

Say: "Pick a topic number to start learning."
STOP and wait.

== PHASE 2: TEACH THE TOPIC (when user picks a number) ==
Say: "Great choice! Let's learn about [Topic Name]."

Teach in structured numbered steps, pulling DIRECTLY from the material:
- Each step: **bold title** + thorough explanation (3-5 sentences) + formulas
- Quote key definitions from the material when useful
- Add real-world examples from your own knowledge
- Show all math using $$...$$ for display equations
- Cover EVERY detail in the material for this topic — be thorough

End with: "✅ Lesson complete! I have covered everything from the material on this topic. Ready for the quiz? Type yes to start."

== PHASE 3: QUIZ (when user says yes/ready/quiz) ==
Create 5 questions based DIRECTLY on the material just taught.
ONE question at a time, EXACTLY:

**Question X of 5**
[Question text]

A) [option]
B) [option]
C) [option]
D) [option]

Reply with A, B, C, or D.
STOP and wait.

== PHASE 4: QUIZ FEEDBACK ==
- CORRECT: "✅ Correct! [explain why, referencing the material]" then next question
- WRONG: "❌ Not quite. The correct answer is [X]. [2-3 sentence explanation from the material]" then next question

== PHASE 5: COMPLETION ==
After all 5 questions:
- Show Score: X/5
- List 1-2 things to review from the material
- Ask: "Would you like to learn another topic? Type topics to see the list."

== FORMATTING ==
- Inline math: $expression$
- Display math: $$expression$$
- Bold key terms with **term**"""'''

content = content[:sp_start] + new_block + content[sp_end:]

# Also bump max_tokens
content = content.replace(old_max_tokens, new_max_tokens, 1)

with open('materials/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done! Patched successfully.")
