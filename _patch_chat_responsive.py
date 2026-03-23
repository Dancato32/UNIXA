with open('community/templates/community/workspace_detail.html', 'rb') as f:
    content = f.read().decode('utf-8', errors='replace')

# ── Fix 1: Replace the entire @media(max-width:768px) block ──
OLD = """@media(max-width:768px){
  /* Hide desktop sidebar */
  .ws-sidebar{display:none !important;}
  .ws-sidebar-overlay{display:none !important;}
  /* Show mobile top nav */
  .ws-mobile-nav{display:block;}
  /* Stack layout vertically */
  .ws-shell{flex-direction:column;}
  /* Panels fill remaining space */
  .ws-main{flex:1;min-height:0;}
  /* Task board single column */
  .task-board{grid-template-columns:1fr;height:auto;overflow-y:auto;}
  .task-col{max-height:60vh;}
  .member-grid{grid-template-columns:1fr;}
  .file-grid{grid-template-columns:1fr 1fr;}
  .form-row{grid-template-columns:1fr;}
  /* Tighter padding on mobile */
  .ws-panel-header{padding:.625rem 1rem;}
  .panel-scroll{padding:1rem;}
  .chat-messages{padding:.875rem 1rem;}
  .chat-input-area{padding:.625rem 1rem;}
  /* Chat bubbles full width on mobile */
  .chat-msg{max-width:88%;}
  .chat-msg.ai-msg{max-width:92%;}
}"""

NEW = """@media(max-width:768px){
  /* Hide desktop sidebar */
  .ws-sidebar{display:none !important;}
  .ws-sidebar-overlay{display:none !important;}
  /* Show mobile top nav */
  .ws-mobile-nav{display:block;}
  /* Stack layout vertically — shell fills full height */
  .ws-shell{flex-direction:column;height:100%;}
  /* Main fills all remaining space below the top nav */
  .ws-main{flex:1;min-height:0;display:flex;flex-direction:column;overflow:hidden;}
  /* Every panel fills the main area */
  .ws-panel{flex:1;min-height:0;display:none;flex-direction:column;overflow:hidden;}
  .ws-panel.active{display:flex;}
  /* Chat messages fill available space */
  .chat-messages{flex:1;min-height:0;overflow-y:auto;padding:.75rem 1rem;}
  /* Input bar stays at bottom, never shrinks */
  .chat-input-area{flex-shrink:0;padding:.625rem .875rem;}
  /* Chat bubbles wider on mobile */
  .chat-msg{max-width:82%;}
  .chat-msg.mine{max-width:82%;}
  .chat-msg.ai-msg{max-width:90%;}
  /* Panel header tighter */
  .ws-panel-header{padding:.5rem 1rem;min-height:44px;}
  /* Scrollable panels */
  .panel-scroll{flex:1;overflow-y:auto;padding:.875rem 1rem;}
  /* Task board single column */
  .task-board{grid-template-columns:1fr;height:auto;overflow-y:auto;}
  .task-col{max-height:55vh;}
  .member-grid{grid-template-columns:1fr;}
  .file-grid{grid-template-columns:1fr 1fr;}
  .form-row{grid-template-columns:1fr;}
  /* Upload zone compact */
  .upload-zone{padding:1.25rem;}
  /* Progress grid 2 cols */
  .progress-grid{grid-template-columns:repeat(2,1fr);}
}"""

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    print('Media query patch applied (LF)')
elif OLD.replace('\n','\r\n') in content:
    content = content.replace(OLD.replace('\n','\r\n'), NEW.replace('\n','\r\n'), 1)
    print('Media query patch applied (CRLF)')
else:
    print('ERROR: media query block not found')
    import sys; sys.exit(1)

# ── Fix 2: Also ensure the layout overrides handle the height chain correctly ──
OLD2 = """.page:has(.ws-shell){padding:0;max-width:100%;margin:0;height:100%;display:flex;flex-direction:column;}
.content-scroll:has(.ws-shell){overflow:hidden;padding:0;flex:1;height:0;}
.ws-shell{display:flex;height:100%;width:100%;background:var(--ws-bg);overflow:hidden;}"""

NEW2 = """.page:has(.ws-shell){padding:0;max-width:100%;margin:0;height:100%;display:flex;flex-direction:column;}
.content-scroll:has(.ws-shell){overflow:hidden;padding:0;flex:1;height:0;display:flex;flex-direction:column;}
.ws-shell{display:flex;flex:1;height:100%;width:100%;background:var(--ws-bg);overflow:hidden;}"""

if OLD2 in content:
    content = content.replace(OLD2, NEW2, 1)
    print('Layout fix applied (LF)')
elif OLD2.replace('\n','\r\n') in content:
    content = content.replace(OLD2.replace('\n','\r\n'), NEW2.replace('\n','\r\n'), 1)
    print('Layout fix applied (CRLF)')
else:
    print('Layout fix: not found (non-critical)')

with open('community/templates/community/workspace_detail.html', 'wb') as f:
    f.write(content.encode('utf-8'))
print('Written successfully')
