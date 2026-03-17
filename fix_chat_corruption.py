#!/usr/bin/env python3
"""
Fix the corrupted chat.html file by replacing the broken JavaScript section
"""

import re

# Read the file
with open('ai_tutor/templates/ai_tutor/chat.html', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find the start of the detectAndWrapMath function
start_marker = "        // Detect and wrap mathematical expressions for KaTeX"
end_marker = "        // Simple streaming for voice mode (plain text only)"

# Find positions
start_pos = content.find(start_marker)
end_pos = content.find(end_marker)

if start_pos == -1 or end_pos == -1:
    print("ERROR: Could not find markers in file")
    print(f"Start found: {start_pos != -1}, End found: {end_pos != -1}")
    exit(1)

# The clean replacement for detectAndWrapMath function
clean_function = """        // Detect and wrap mathematical expressions for KaTeX
        function detectAndWrapMath(text) {
            // Don't process if already has dollar sign delimiters
            if (text.indexOf('$') !== -1) {
                return text;
            }
            
            // Common math patterns to detect
            const mathPatterns = [
                // Fractions: 1/2, x/y
                /(\\b\\d+\\/\\d+\\b)/g,
                /(\\b[a-z]\\/[a-z]\\b)/gi,
                
                // Powers: x^2, 2^n
                /(\\b[a-zA-Z0-9]+\\^[a-zA-Z0-9]+\\b)/g,
                
                // Equations with = sign and operators
                /(\\b[a-zA-Z0-9\\s\\+\\-\\*\\/\\^]+\\s*=\\s*[a-zA-Z0-9\\s\\+\\-\\*\\/\\^]+\\b)/g,
                
                // Square roots: √x, sqrt(x)
                /(√[a-zA-Z0-9]+|sqrt\\([^)]+\\))/gi
            ];
            
            // Wrap detected patterns in dollar signs for inline math
            mathPatterns.forEach(pattern => {
                text = text.replace(pattern, (match) => {
                    // Convert to LaTeX format
                    let latex = match;
                    
                    // Convert fractions
                    latex = latex.replace(/(\\d+)\\/(\\d+)/g, '\\\\frac{$1}{$2}');
                    latex = latex.replace(/([a-z])\\/([a-z])/gi, '\\\\frac{$1}{$2}');
                    
                    // Convert powers
                    latex = latex.replace(/\\^/g, '^');
                    
                    // Convert sqrt
                    latex = latex.replace(/sqrt\\(([^)]+)\\)/gi, '\\\\sqrt{$1}');
                    latex = latex.replace(/√([a-zA-Z0-9]+)/g, '\\\\sqrt{$1}');
                    
                    return '$' + latex + '$';
                });
            });
            
            return text;
        }
        
"""

# Replace the corrupted section
new_content = content[:start_pos] + clean_function + content[end_pos:]

# Write back
with open('ai_tutor/templates/ai_tutor/chat.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✓ Fixed chat.html - replaced corrupted detectAndWrapMath function")
