#!/usr/bin/env python3
"""
Fix binary corruption in chat.html by replacing the corrupted detectAndWrapMath function
"""

import os

# Read the file in binary mode to handle corruption
file_path = 'ai_tutor/templates/ai_tutor/chat.html'

with open(file_path, 'rb') as f:
    content = f.read()

# Convert to string, replacing problematic bytes
content_str = content.decode('utf-8', errors='replace')

# Find the function start
start_marker = "        // Detect and wrap mathematical expressions for KaTeX"
end_marker = "        // Simple streaming for voice mode (plain text only)"

start_pos = content_str.find(start_marker)
end_pos = content_str.find(end_marker)

if start_pos == -1:
    print("ERROR: Could not find start marker")
    exit(1)
    
if end_pos == -1:
    print("ERROR: Could not find end marker")
    exit(1)

print(f"Found function at position {start_pos} to {end_pos}")

# The clean replacement
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
new_content = content_str[:start_pos] + clean_function + content_str[end_pos:]

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✓ Successfully fixed chat.html")
print("✓ Replaced corrupted detectAndWrapMath function")
print("\nNext steps:")
print("1. Restart your Django server")
print("2. Clear browser cache")
print("3. Test the AI Tutor chat")
