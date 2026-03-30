import os
import re

NEW_NAV_HTML = """
<style>
/* Unified Bottom Nav Styles */
.bottom-nav-unified {
  display: flex !important;
  position: fixed !important;
  bottom: 0 !important;
  left: 0 !important;
  right: 0 !important;
  background: var(--surface, #ffffff) !important;
  border-top: 1px solid var(--border-ink, #e5e5e5) !important;
  padding: 0 0.5rem !important;
  padding-bottom: env(safe-area-inset-bottom, 0) !important;
  z-index: 2000 !important;
  justify-content: space-around !important;
  align-items: center !important;
  height: 60px !important;
  box-shadow: 0 -4px 15px rgba(0,0,0,0.03) !important;
}
.bn-unified-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0.35rem 0.25rem;
  color: var(--text3, #8a8a93);
  text-decoration: none;
  flex: 1;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 0;
  background: none;
  border: none;
  cursor: pointer;
}
.bn-unified-item svg { width: 22px; height: 22px; transition: transform 0.2s; stroke-width: 2.2px; }
.bn-unified-label { font-size: 0.65rem; font-weight: 700; font-family: var(--font-hand, 'Inter', sans-serif); letter-spacing: 0.02em; white-space: nowrap; text-transform: uppercase; }
.bn-unified-item:hover, .bn-unified-item:focus, .bn-unified-item.active { color: var(--text, #111111); }
.bn-unified-item:active svg { transform: scale(0.9); }

@media (min-width: 900px) {
  .bottom-nav-unified { display: none !important; }
}
</style>
<nav class="bottom-nav bottom-nav-unified" id="bottom-nav">
  <a href="{% url 'community:feed' %}" class="bn-unified-item" aria-label="Feed">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
    <span class="bn-unified-label">Feed</span>
  </a>
  <a href="{% url 'ai_chat' %}" class="bn-unified-item" aria-label="Tutor">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
    <span class="bn-unified-label">Tutor</span>
  </a>
  <a href="{% url 'community:workspace_list' %}" class="bn-unified-item" aria-label="Workspace">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
    <span class="bn-unified-label">Workspace</span>
  </a>
  <a href="{% url 'community:ai_tools' %}" class="bn-unified-item" aria-label="Tools">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
    <span class="bn-unified-label">Tools</span>
  </a>
  <a href="{% url 'list_materials' %}" class="bn-unified-item" aria-label="Upload">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
    <span class="bn-unified-label">Upload</span>
  </a>
</nav>
"""

def update_files():
    root_dir = r"c:\Users\danie\Downloads\UNIXA-main"
    count = 0
    # Search for all HTML files
    for subdir, _, files in os.walk(root_dir):
        if 'venv' in subdir or 'node_modules' in subdir or '.git' in subdir:
            continue
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(subdir, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check if bottom-nav exists
                if '<nav class="bottom-nav' in content:
                    # Replace existing bottom nav block with new one
                    # We use a regex to capture <nav class="bottom-nav... through the first </nav> that follows it.
                    pattern = r'<nav[^>]*class="[^"]*bottom-nav[^"]*"[^>]*>.*?</nav>'
                    new_content, num_replacements = re.subn(pattern, NEW_NAV_HTML.strip(), content, flags=re.DOTALL)
                    
                    if num_replacements > 0:
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        count += 1
                        print(f"Updated: {filepath}")

    print(f"Total files updated: {count}")

if __name__ == "__main__":
    update_files()
