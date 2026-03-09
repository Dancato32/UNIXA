#!/usr/bin/env python3
"""Fix the corrupted renderMathInElement section in chat.html"""

file_path = 'ai_tutor/templates/ai_tutor/chat.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the corrupted section
old_section = """                    // Show action buttons after streaming completes
                    messageElement.parentElement.querySelector('.message-actions').style.display = 'flex';
                    
                    // Render math expressions
                    renderMathInElement(messageElement, {
                        delimiters: [
                            {left: '$', right: '$', display: true},
                            {left: '"""

new_section = """                    // Show action buttons after streaming completes
                    messageElement.parentElement.querySelector('.message-actions').style.display = 'flex';
                    
                    // Render math expressions with KaTeX
                    if (typeof renderMathInElement !== 'undefined') {
                        try {
                            renderMathInElement(messageElement, {
                                delimiters: [
                                    {left: '$$', right: '$$', display: true},
                                    {left: '$', right: '$', display: false}
                                ],
                                throwOnError: false
                            });
                        } catch (e) {
                            console.log('KaTeX rendering skipped:', e);
                        }
                    }
                } else {"""

# Find the corrupted part and replace up to the next "} else {"
import re
pattern = r"// Show action buttons after streaming completes.*?renderMathInElement\(messageElement,\s*\{.*?\}\s*\);.*?\} else \{"

replacement = new_section

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed chat.html")
