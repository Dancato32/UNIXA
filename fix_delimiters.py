#!/usr/bin/env python3
"""Fix corrupted delimiters in chat.html"""

file_path = 'ai_tutor/templates/ai_tutor/chat.html'

# Read the file
with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find and replace the corrupted renderMathInElement section
# The corruption appears to be in the delimiters array

# Search for the pattern and replace with correct version
import re

# Pattern to match the corrupted section
pattern = r"renderMathInElement\(messageElement,\s*\{[^}]*delimiters:\s*\[[^\]]*\][^}]*\}\);"

# Replacement with correct delimiters
replacement = """renderMathInElement(messageElement, {
                                delimiters: [
                                    {left: '$$', right: '$$', display: true},
                                    {left: '$', right: '$', display: false}
                                ],
                                throwOnError: false
                            });"""

# Replace
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed delimiters in chat.html")
print("Please refresh your browser and try again")
