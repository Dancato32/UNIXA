with open('materials/views.py', encoding='utf-8') as f:
    content = f.read()

# Find the system_prompt block and the messages_payload construction
sp_start = content.find('        # Full material text', content.find('def learn_ajax'))
assert sp_start != -1

# Find where messages_payload is built
mp_start = content.find('        messages_payload = [{"role": "system"', sp_start)
assert mp_start != -1

# Find end of messages_payload block (the closing of the for loop + if/else)
# Look for the line that appends the final user message
trigger_end = content.find(
    '            messages_payload.append({"role": "user", "content": "Start',
    mp_start
)
trigger_end = content.find('\n', trigger_end) + 1  # end of that line
assert trigger_end > 0

old_block = content[sp_start:trigger_end]

new_block = '''        # Extract relevant section when user picks a topic
        import re as _re
        full_text = material.extracted_text[:6000]
        topic_context = ""
        if user_message and history:
            for h in reversed(history):
                if h.get('role') == 'assistant' and 'Topics you can learn' in h.get('content', ''):
                    topic_match = _re.search(r'\\d+\\.\\s*(.+)', user_message)
                    if topic_match:
                        topic_name = topic_match.group(1).strip().lower()
                        keywords = [w for w in topic_name.split() if len(w) > 3]
                        paragraphs = [p.strip() for p in full_text.split('\\n') if len(p.strip()) > 40]
                        relevant = [p for p in paragraphs if any(w in p.lower() for w in keywords)]
                        if relevant:
                            topic_context = "\\n".join(relevant[:20])
                    break

        # Lean system prompt — material injected as a context message instead
        system_prompt = """You are NEXA Learn Mode, an expert AI tutor. You will be given study material and must teach it interactively.

TEACHING RULES:
- Always teach from the provided study material — quote and paraphrase it directly
- Use your own knowledge only to add examples, analogies, and fill gaps
- Never contradict the material
- Math: use $expression$ for inline, $$expression$$ for display (own line, centred)
- Bold key terms with **term**

PHASE 1 — TOPIC LIST (first message only):
Read the material. List ALL topics found:
📚 Topics you can learn:
1. [Topic]
2. [Topic]
Say: "Pick a topic number to start learning." Then STOP.

PHASE 2 — TEACH (when user picks a number):
Say: "Great choice! Let's learn about [Topic]."
Teach in numbered steps pulled from the material:
- **Step title** + 3-5 sentence explanation + formulas
- Quote key definitions from the material
- Add real-world examples from your knowledge
- Cover EVERY detail in the material for this topic
End with: "✅ Lesson complete! Ready for the quiz? Type yes to start."

PHASE 3 — QUIZ (when user says yes):
5 questions from the material, ONE at a time:
**Question X of 5**
[question]
A) [option]  B) [option]  C) [option]  D) [option]
Reply A, B, C, or D. STOP and wait.

PHASE 4 — FEEDBACK:
Correct: "✅ Correct! [why]" then next question.
Wrong: "❌ Not quite. Answer is [X]. [explanation from material]" then next question.

PHASE 5 — DONE:
Score X/5, what to review, ask if they want another topic."""

        # Build messages — material as a separate context message (proper RAG pattern)
        material_context = f"STUDY MATERIAL: {material.title}\\n\\n{full_text}"
        if topic_context:
            material_context += f"\\n\\n--- MOST RELEVANT SECTION FOR THIS TOPIC ---\\n{topic_context}"

        messages_payload = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": material_context},
            {"role": "assistant", "content": "I have read the study material carefully. I am ready to help you learn it. What would you like to do?"},
        ]

        # Append conversation history (skip first exchange if it's the material injection)
        for h in history[-8:]:
            role = h.get('role', 'user')
            msg_content = h.get('content', '')
            if role in ('user', 'assistant') and msg_content:
                messages_payload.append({"role": role, "content": str(msg_content)})

        if user_message:
            messages_payload.append({"role": "user", "content": user_message})
        else:
            messages_payload.append({"role": "user", "content": "Start — show me the topics I can learn from this material."})
'''

content = content[:sp_start] + new_block + content[trigger_end:]

with open('materials/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done! Prompt restructured.")
