import re
with open('community/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The regex matches the Live Campus Hub header down to the Skill Marketplace header
new_content = re.sub(
    r'# ── Live Campus Hub ──.*?# ── Skill Marketplace ──',
    '# ── Skill Marketplace ──',
    content,
    flags=re.DOTALL
)

with open('community/views.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
