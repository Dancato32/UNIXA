# URGENT: Fix Chat.html Rendering Issue

## Problem

The math rendering is showing raw HTML and LaTeX during streaming because:
1. The `renderMathInElement` delimiters got corrupted in the file
2. The streaming function needs to render math AFTER setting the HTML

## Solution

### Step 1: Fix the renderMathInElement call

Find this section in `ai_tutor/templates/ai_tutor/chat.html` (around line 1280-1295):

```javascript
// Show action buttons after streaming completes
messageElement.parentElement.querySelector('.message-actions').style.display = 'flex';

// Render math expressions
renderMathInElement(messageElement, {
    delimiters: [
        {left: '$', right: '$', display: true},
        {left: '   // <-- CORRUPTED HERE
```

**Replace with:**

```javascript
// Render math expressions with KaTeX FIRST
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

// Show action buttons after math is rendered
messageElement.parentElement.querySelector('.message-actions').style.display = 'flex';
```

### Step 2: Verify the streamText function

The `streamText` function should now look like this (around line 1322):

```javascript
async function streamText(element, text, speed = 15) {
    // Process text for math and step formatting
    const processedText = processTextForDisplay(text);
    
    // Set the full HTML at once (don't stream character by character)
    // This prevents breaking HTML tags and allows proper rendering
    element.innerHTML = processedText;
    
    // Now apply a reveal animation instead of character streaming
    // This gives the typing effect without breaking HTML
    element.style.opacity = '0';
    element.style.transform = 'translateY(10px)';
    
    // Trigger animation
    await new Promise(resolve => setTimeout(resolve, 50));
    element.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    element.style.opacity = '1';
    element.style.transform = 'translateY(0)';
    
    // Auto-scroll
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    return Promise.resolve();
}
```

## Why This Works

1. **No Character-by-Character Streaming**: We set the full HTML at once, which prevents breaking HTML tags like `<br>`, `<div>`, etc.

2. **Fade-in Animation**: Instead of typing character-by-character, we use a smooth fade-in animation that looks professional

3. **Math Renders Properly**: KaTeX can process the complete HTML structure with proper `$...$` and `$$...$$` delimiters

4. **Step Boxes Work**: The `<div class="math-step">` elements render correctly

## Expected Result

After fixing:
- Math expressions render beautifully: $\frac{1}{2}$ shows as ½
- Step boxes appear with proper formatting
- No raw HTML tags visible
- Smooth fade-in animation
- All LaTeX renders correctly

## Quick Test

After fixing, ask: "Solve 1/2 + 1/3"

You should see:
- Clean step-by-step boxes
- Proper fraction rendering
- No `<br>` or `<div>` tags visible
- Beautiful LaTeX math

## Alternative: Manual HTML Edit

If the Python script doesn't work, manually edit `chat.html`:

1. Open `nexa/ai_tutor/templates/ai_tutor/chat.html`
2. Search for "renderMathInElement"
3. Replace the corrupted delimiters section
4. Save and refresh browser

The key is ensuring the delimiters are:
```javascript
{left: '$$', right: '$$', display: true},
{left: '$', right: '$', display: false}
```

NOT corrupted with broken strings.
