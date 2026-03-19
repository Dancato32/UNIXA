with open('ai_tutor/ai_utils.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all single-$ display math in step templates with $$
# The pattern is: a line that is ONLY "$[math expression]$" or "$[result]$"
import re

# Replace standalone $[...]$ lines (display math in templates) with $$[...]$$
# These are lines where the entire line content is $something$
old = content
content = content.replace('\n$[math expression]$\n', '\n$$[math expression]$$\n')
content = content.replace('\n$[result]$\n', '\n$$[result]$$\n')

count = old.count('\n$[math expression]$\n') + old.count('\n$[result]$\n')
print(f'Replaced {count} template lines')

with open('ai_tutor/ai_utils.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
