#!/usr/bin/env python3
"""
Script to update the AI Tutor chat.html with learning mode selector.
Run this script to automatically add the learning mode UI components.
"""

import re

def update_chat_html():
    """Update chat.html with learning mode selector."""
    
    file_path = 'ai_tutor/templates/ai_tutor/chat.html'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("✓ Read chat.html successfully")
        
        # 1. Add CSS for mode selector (after voice-mode-btn styles)
        css_to_add = """
        
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
"""
        
        # Find where to insert CSS (after .voice-mode-btn:hover)
        css_pattern = r'(\.voice-mode-btn:hover\s*\{[^}]+\})'
        if re.search(css_pattern, content):
            content = re.sub(css_pattern, r'\1' + css_to_add, content)
            print("✓ Added mode selector CSS")
        else:
            print("⚠ Could not find insertion point for CSS")
        
        # 2. Update header-actions HTML
        header_html = """<div class="header-actions">
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
                </div>"""
        
        # Find and replace header-actions
        header_pattern = r'<div class="header-actions">.*?</div>\s*</header>'
        if re.search(header_pattern, content, re.DOTALL):
            content = re.sub(header_pattern, header_html + '\n            </header>', content, flags=re.DOTALL)
            print("✓ Updated header with mode selector")
        else:
            print("⚠ Could not find header-actions section")
        
        # 3. Add JavaScript for mode management
        js_to_add = """
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
        
"""
        
        # Find script tag and add at the beginning
        script_pattern = r'(<script>)'
        if re.search(script_pattern, content):
            content = re.sub(script_pattern, r'\1' + js_to_add, content)
            print("✓ Added learning mode JavaScript")
        else:
            print("⚠ Could not find script tag")
        
        # 4. Update sendMessage function to include learning_mode
        # Find the fetch call in sendMessage and add learning_mode
        fetch_pattern = r'(body: JSON\.stringify\(\{[^}]+use_rag: useRag)'
        if re.search(fetch_pattern, content):
            content = re.sub(fetch_pattern, r'\1,\n            learning_mode: currentLearningMode', content)
            print("✓ Updated sendMessage to include learning_mode")
        else:
            print("⚠ Could not find sendMessage fetch call")
        
        # Write updated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("\n✅ Successfully updated chat.html!")
        print("\nNext steps:")
        print("1. Review the changes in chat.html")
        print("2. Test the learning mode selector in your browser")
        print("3. Try each mode (Explain, Coach, Exam) with different questions")
        
    except FileNotFoundError:
        print(f"❌ Error: Could not find {file_path}")
        print("Make sure you're running this script from the nexa directory")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    update_chat_ui()
