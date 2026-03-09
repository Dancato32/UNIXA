# Chat.html Corruption Fix Instructions

## Problem
The `ai_tutor/templates/ai_tutor/chat.html` file has severe corruption in the JavaScript section around lines 1430-1500. The `detectAndWrapMath()` function contains binary characters that break the code.

## Symptoms
- Send button doesn't work when clicked
- JavaScript console shows syntax errors
- Math rendering fails
- Steps don't appear one by one

## Solution

### Option 1: Manual Fix (Recommended)

1. Open `nexa/ai_tutor/templates/ai_tutor/chat.html` in a text editor
2. Find the `detectAndWrapMath` function (around line 1434)
3. Look for this corrupted line:
   ```javascript
   if (text.includes('$')) {  // This line has binary corruption
   ```

4. Replace the ENTIRE `detectAndWrapMath` function with the clean version from `correct_katex_section.txt`:

```javascript
        // Detect and wrap mathematical expressions for KaTeX
        function detectAndWrapMath(text) {
            // Don't process if already has dollar sign delimiters
            if (text.indexOf('$') !== -1) {
                return text;
            }
            
            // Common math patterns to detect
            const mathPatterns = [
                // Fractions: 1/2, x/y
                /(\b\d+\/\d+\b)/g,
                /(\b[a-z]\/[a-z]\b)/gi,
                
                // Powers: x^2, 2^n
                /(\b[a-zA-Z0-9]+\^[a-zA-Z0-9]+\b)/g,
                
                // Equations with = sign and operators
                /(\b[a-zA-Z0-9\s\+\-\*\/\^]+\s*=\s*[a-zA-Z0-9\s\+\-\*\/\^]+\b)/g,
                
                // Square roots: √x, sqrt(x)
                /(√[a-zA-Z0-9]+|sqrt\([^)]+\))/gi
            ];
            
            // Wrap detected patterns in dollar signs for inline math
            mathPatterns.forEach(pattern => {
                text = text.replace(pattern, (match) => {
                    // Convert to LaTeX format
                    let latex = match;
                    
                    // Convert fractions
                    latex = latex.replace(/(\d+)\/(\d+)/g, '\\frac{$1}{$2}');
                    latex = latex.replace(/([a-z])\/([a-z])/gi, '\\frac{$1}{$2}');
                    
                    // Convert powers
                    latex = latex.replace(/\^/g, '^');
                    
                    // Convert sqrt
                    latex = latex.replace(/sqrt\(([^)]+)\)/gi, '\\sqrt{$1}');
                    latex = latex.replace(/√([a-zA-Z0-9]+)/g, '\\sqrt{$1}');
                    
                    return '$' + latex + '$';
                });
            });
            
            return text;
        }
```

5. Also check around line 1470 for this corrupted line:
   ```javascript
   return `${latex}$`;  // Should be: return '$' + latex + '$';
   ```
   
   Replace it with:
   ```javascript
   return '$' + latex + '$';
   ```

6. Save the file

### Option 2: Use a Fresh Copy

If the corruption is too severe, you may need to recreate the file. The clean version should have:

1. All HTML and CSS (lines 1-980) - these are fine
2. HTML body content (lines 980-1200) - these are fine  
3. JavaScript section (lines 1200-end) - this is where the corruption is

### Key Changes Made:
- Changed `text.includes('$')` to `text.indexOf('$') !== -1` (avoids binary corruption)
- Changed template literal `` `${latex}$` `` to string concatenation `'$' + latex + '$'`
- These changes avoid the binary character issues that were breaking the file

### After Fixing:
1. Restart your Django development server
2. Clear your browser cache (Ctrl+Shift+Delete)
3. Reload the AI Tutor page
4. Test by asking a math question like "Solve 2x + 3 = 7"

### Expected Behavior After Fix:
- Send button works when clicked
- Steps appear one by one with 400ms delay between them
- Math expressions render with KaTeX
- No JavaScript console errors

## Root Cause
The corruption happened when the file was edited multiple times with string replacements that introduced binary characters into JavaScript string literals. Template literals (backticks) and `.includes()` method were particularly affected.

## Prevention
- Use simple string concatenation instead of template literals in large files
- Use `.indexOf()` instead of `.includes()` for compatibility
- Always test after making changes to large template files
