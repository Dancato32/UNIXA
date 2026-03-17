# AI Tutor Learning Mode Selector - Implementation Guide

## Overview
This document describes the updates needed to add learning mode selection to the AI Tutor chat interface.

## Backend Changes (COMPLETED ✓)

### 1. ai_utils.py
- Updated `ask_ai()` function to accept `learning_mode` parameter
- Added comprehensive Nexa system prompt with adaptive learning capabilities
- Implemented mode-specific instructions for:
  - **Explain Mode**: Clear explanations with examples and understanding checks
  - **Coach Mode**: Socratic questioning and guided discovery
  - **Exam Mode**: Direct answers with step-by-step solutions

### 2. views.py
- Updated `chat_ajax()` to receive and pass `learning_mode` parameter from frontend

## Frontend Changes (NEEDED)

### 1. Add Learning Mode Selector CSS
Add these styles to the `<style>` section in chat.html (after `.voice-mode-btn` styles):

```css
/* Learning Mode Selector */
.mode-selector {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.25rem;
}

.mode-btn {
    padding: 0.5rem 0.875rem;
    background: transparent;
    border: none;
    border-radius: 6px;
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
}

.mode-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
}

.mode-btn.active {
    background: linear-gradient(135deg, #ffffff 0%, #e5e5e5 100%);
    color: #1a1a1a;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(255, 255, 255, 0.2);
}

.mode-indicator {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.375rem 0.75rem;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-left: 0.5rem;
}

.mode-indicator-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ffffff 0%, #e5e5e5 100%);
}
```

### 2. Update Header HTML
Replace the `.header-actions` div content with:

```html
<div class="header-actions">
    <!-- Learning Mode Selector -->
    <div class="mode-selector">
        <button class="mode-btn active" data-mode="explain" onclick="setLearningMode('explain')">
            📖 Explain
        </button>
        <button class="mode-btn" data-mode="coach" onclick="setLearningMode('coach')">
            🎯 Coach
        </button>
        <button class="mode-btn" data-mode="exam" onclick="setLearningMode('exam')">
            📝 Exam
        </button>
    </div>
    
    <button class="voice-mode-btn" id="voice-mode-btn" title="Voice Mode" onclick="openVoiceMode()">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="23"></line>
            <line x1="8" y1="23" x2="16" y2="23"></line>
        </svg>
        <span>Voice Mode</span>
    </button>
    <div class="user-avatar">{{ user.username|slice:":1"|upper }}</div>
</div>
```

### 3. Add JavaScript Functions
Add these functions to the `<script>` section at the end of chat.html:

```javascript
// Learning Mode Management
let currentLearningMode = 'explain';

function setLearningMode(mode) {
    currentLearningMode = mode;
    
    // Update button states
    document.querySelectorAll('.mode-btn').forEach(btn => {
        if (btn.dataset.mode === mode) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Show mode change notification
    const modeNames = {
        'explain': 'Explain Mode - Clear explanations with examples',
        'coach': 'Coach Mode - Guided learning with questions',
        'exam': 'Exam Mode - Direct answers and solutions'
    };
    
    console.log(`Switched to ${modeNames[mode]}`);
}

// Update sendMessage function to include learning_mode
function sendMessage() {
    const textarea = document.getElementById('chat-textarea');
    const message = textarea.value.trim();
    
    if (!message) return;
    
    const useRag = document.getElementById('rag-toggle').checked;
    
    // Disable input while sending
    textarea.disabled = true;
    document.getElementById('send-btn').disabled = true;
    
    // Show loading indicator
    document.getElementById('loading-indicator').classList.add('active');
    
    // Hide welcome screen if visible
    const welcomeScreen = document.getElementById('welcome-screen');
    if (welcomeScreen) {
        welcomeScreen.style.display = 'none';
    }
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    
    // Clear textarea
    textarea.value = '';
    
    // Send to backend
    fetch('{% url "chat_ajax" %}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            message: message,
            use_rag: useRag,
            learning_mode: currentLearningMode  // Include learning mode
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addMessageToChat(data.response, 'ai', data.timestamp);
        } else {
            addMessageToChat('Error: ' + (data.error || 'Unknown error'), 'ai');
        }
    })
    .catch(error => {
        addMessageToChat('Error: Failed to get response. Please try again.', 'ai');
        console.error('Error:', error);
    })
    .finally(() => {
        // Re-enable input
        textarea.disabled = false;
        document.getElementById('send-btn').disabled = false;
        document.getElementById('loading-indicator').classList.remove('active');
        textarea.focus();
    });
}
```

### 4. Update Welcome Screen (Optional)
Add mode descriptions to the suggestion cards:

```html
<div class="suggestion-card" onclick="sendSuggestion('Explain how photosynthesis works')">
    <div class="suggestion-card-title">📖 Learn a Concept</div>
    <div class="suggestion-card-desc">Get clear explanations with examples</div>
</div>
<div class="suggestion-card" onclick="sendSuggestion('Help me solve this problem step by step')">
    <div class="suggestion-card-title">🎯 Practice Problem-Solving</div>
    <div class="suggestion-card-desc">Get guided hints and coaching</div>
</div>
<div class="suggestion-card" onclick="sendSuggestion('Give me practice questions on algebra')">
    <div class="suggestion-card-title">📝 Test Your Knowledge</div>
    <div class="suggestion-card-desc">Get direct answers and solutions</div>
</div>
<div class="suggestion-card" onclick="sendSuggestion('What are the key points about climate change?')">
    <div class="suggestion-card-title">💡 Quick Summary</div>
    <div class="suggestion-card-desc">Get concise overviews of topics</div>
</div>
```

## Testing

1. Start the Django server: `python manage.py runserver`
2. Navigate to the AI Tutor chat page
3. Test each learning mode:
   - **Explain Mode**: Ask "What is photosynthesis?" - Should get detailed explanation with examples
   - **Coach Mode**: Ask "How do I solve 2x + 5 = 15?" - Should get guiding questions
   - **Exam Mode**: Ask "What is the capital of France?" - Should get direct answer
4. Verify mode switching updates the UI correctly
5. Test with RAG toggle enabled/disabled

## Mode Descriptions

### Explain Mode (Default)
- Clear, structured explanations
- Uses analogies and real-world examples
- Includes understanding checks
- Best for learning new concepts

### Coach Mode
- Socratic questioning approach
- Provides hints instead of direct answers
- Encourages independent thinking
- Best for problem-solving practice

### Exam Mode
- Direct, concise answers
- Step-by-step solutions
- Practice questions available
- Best for quick answers and exam prep

## Notes
- The learning mode persists during the session (stored in JavaScript variable)
- Each message sent includes the current learning mode
- The AI adapts its response style based on the selected mode
- RAG (study materials) works with all modes
