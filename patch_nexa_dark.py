import re

f = open('community/templates/community/nexa_home.html', 'rb')
c = f.read().decode('utf-8', errors='replace')
f.close()

# ── 1. Replace CSS variables block ──
old_vars = """:root{
  --nx-bg:#f7f7f5;--nx-sb:#fff;--nx-bdr:#e8e8e4;
  --nx-t1:#1a1a1a;--nx-t2:#555;--nx-t3:#999;
  --nx-hov:#f0f0ec;--nx-acc:#f97316;
}
body,.shell,.main-area,.content-scroll,.page{background:var(--nx-bg)!important;}"""

new_vars = """:root{
  --nx-bg:#0c0c0e;--nx-sb:#111114;--nx-bdr:#1f1f26;
  --nx-t1:#f2f2f4;--nx-t2:#9898a6;--nx-t3:#5a5a6a;
  --nx-hov:#17171b;--nx-acc:#6366f1;
  --nx-surface2:#17171b;--nx-surface3:#1e1e23;--nx-surface4:#26262d;
}
body,.shell,.main-area,.content-scroll,.page{background:var(--nx-bg)!important;}"""

c = c.replace(old_vars, new_vars, 1)

# ── 2. Sidebar background/border ──
c = c.replace('.nx-sidebar{width:220px;background:var(--nx-sb);border-right:1px solid var(--nx-bdr);', '.nx-sidebar{width:220px;background:var(--nx-sb);border-right:1px solid var(--nx-bdr);', 1)

# ── 3. nx-new-btn ──
c = c.replace('background:var(--nx-bg);border:1px solid var(--nx-bdr);border-radius:8px;color:var(--nx-t2)', 'background:var(--nx-surface3);border:1px solid var(--nx-bdr);border-radius:8px;color:var(--nx-t2)', 1)

# ── 4. active nav item: was orange, now indigo ──
c = c.replace('.nx-nav-item.active{background:#fff3ed;color:#ea6c00;font-weight:600;}', '.nx-nav-item.active{background:rgba(99,102,241,.15);color:#a5b4fc;font-weight:600;}', 1)

# ── 5. Mobile top bar ──
c = c.replace('.nx-mob-bar{display:none;height:52px;background:#fff;border-bottom:1px solid var(--nx-bdr);', '.nx-mob-bar{display:none;height:52px;background:var(--nx-sb);border-bottom:1px solid var(--nx-bdr);', 1)

# ── 6. Mobile bottom nav ──
c = c.replace('.nx-bot-nav{display:none;height:58px;background:#fff;border-top:1px solid var(--nx-bdr);', '.nx-bot-nav{display:none;height:58px;background:var(--nx-sb);border-top:1px solid var(--nx-bdr);', 1)

# ── 7. Message bubbles ──
c = c.replace('.nx-msg.user .nx-bubble{background:#1a1a1a;color:#fff;', '.nx-msg.user .nx-bubble{background:#6366f1;color:#fff;', 1)
c = c.replace('.nx-msg.ai .nx-bubble{background:#fff;color:#1a1a1a;border-radius:4px 18px 18px 18px;border:1px solid #e8e8e4;', '.nx-msg.ai .nx-bubble{background:#17171b;color:var(--nx-t1);border-radius:4px 18px 18px 18px;border:1px solid var(--nx-bdr);', 1)

# ── 8. Typing dots ──
c = c.replace('.nx-typing span{width:6px;height:6px;border-radius:50%;background:#ccc;', '.nx-typing span{width:6px;height:6px;border-radius:50%;background:#5a5a6a;', 1)

# ── 9. Task buttons ──
c = c.replace('.nx-task-btn{display:flex;align-items:center;gap:.5rem;width:100%;padding:.5rem .75rem;background:#fff;border:1px solid #e8e8e4;', '.nx-task-btn{display:flex;align-items:center;gap:.5rem;width:100%;padding:.5rem .75rem;background:#17171b;border:1px solid var(--nx-bdr);', 1)
c = c.replace('.nx-task-btn:hover,.nx-task-btn:active{background:var(--nx-hov);border-color:#ccc;}', '.nx-task-btn:hover,.nx-task-btn:active{background:var(--nx-surface3);border-color:#2a2a33;}', 1)

# ── 10. Search card ──
c = c.replace('.nx-search-card{background:#fff;border:1px solid #e8e8e4;', '.nx-search-card{background:#17171b;border:1px solid var(--nx-bdr);', 1)
c = c.replace('.nx-search-card-title{font-weight:700;font-size:.9375rem;color:#1a1a1a;}', '.nx-search-card-title{font-weight:700;font-size:.9375rem;color:var(--nx-t1);}', 1)
c = c.replace('.nx-search-summary{font-size:.875rem;line-height:1.7;color:#444;margin-bottom:.875rem;padding-bottom:.875rem;border-bottom:1px solid #f0f0ec;}', '.nx-search-summary{font-size:.875rem;line-height:1.7;color:var(--nx-t2);margin-bottom:.875rem;padding-bottom:.875rem;border-bottom:1px solid var(--nx-bdr);}', 1)
c = c.replace('.nx-source{display:flex;align-items:flex-start;gap:.5rem;padding:.5rem .625rem;background:#f7f7f5;', '.nx-source{display:flex;align-items:flex-start;gap:.5rem;padding:.5rem .625rem;background:#17171b;', 1)
c = c.replace('.nx-source:hover{background:var(--nx-hov);}', '.nx-source:hover{background:var(--nx-surface3);}', 1)
c = c.replace('.nx-source-title{font-weight:600;color:#1a1a1a;}', '.nx-source-title{font-weight:600;color:var(--nx-t1);}', 1)

# ── 11. Paraphraser panels ──
c = c.replace('.para-right{width:420px;display:flex;flex-direction:column;overflow:hidden;flex-shrink:0;background:#fff;}', '.para-right{width:420px;display:flex;flex-direction:column;overflow:hidden;flex-shrink:0;background:var(--nx-sb);}', 1)
c = c.replace('.para-topbar{padding:.625rem 1rem;border-bottom:1px solid var(--nx-bdr);background:#fff;', '.para-topbar{padding:.625rem 1rem;border-bottom:1px solid var(--nx-bdr);background:var(--nx-sb);', 1)
c = c.replace('.para-modes{display:flex;gap:.375rem;flex-wrap:wrap;padding:.625rem 1rem;border-bottom:1px solid var(--nx-bdr);background:#fafaf8;', '.para-modes{display:flex;gap:.375rem;flex-wrap:wrap;padding:.625rem 1rem;border-bottom:1px solid var(--nx-bdr);background:var(--nx-bg);', 1)
c = c.replace('.para-mode-pill{padding:.3rem .75rem;border-radius:20px;border:1.5px solid var(--nx-bdr);background:#fff;font-size:.75rem;font-weight:600;color:var(--nx-t2);', '.para-mode-pill{padding:.3rem .75rem;border-radius:20px;border:1.5px solid var(--nx-bdr);background:var(--nx-surface3);font-size:.75rem;font-weight:600;color:var(--nx-t2);', 1)
c = c.replace('.para-textarea{flex:1;width:100%;border:1.5px solid var(--nx-bdr);border-radius:10px;padding:.875rem 1rem;font-size:.9375rem;line-height:1.7;color:#1a1a1a;background:#fff;', '.para-textarea{flex:1;width:100%;border:1.5px solid var(--nx-bdr);border-radius:10px;padding:.875rem 1rem;font-size:.9375rem;line-height:1.7;color:var(--nx-t1);background:var(--nx-surface3);', 1)
c = c.replace('.para-go-btn{padding:.5rem 1.25rem;background:#1a1a1a;color:#fff;border:none;border-radius:8px;', '.para-go-btn{padding:.5rem 1.25rem;background:var(--nx-acc);color:#fff;border:none;border-radius:8px;', 1)
c = c.replace('.para-go-btn:hover{background:#333;}', '.para-go-btn:hover{background:#5254cc;}', 1)
c = c.replace('.para-output-text{font-size:.9375rem;line-height:1.8;color:#1a1a1a;', '.para-output-text{font-size:.9375rem;line-height:1.8;color:var(--nx-t1);', 1)
c = c.replace('.para-action-btn{padding:.375rem .875rem;border:1.5px solid var(--nx-bdr);background:#fff;border-radius:8px;', '.para-action-btn{padding:.375rem .875rem;border:1.5px solid var(--nx-bdr);background:var(--nx-surface3);border-radius:8px;', 1)
c = c.replace('.para-change-item{padding:.625rem .75rem;background:#f7f7f5;border-radius:8px;margin-bottom:.5rem;border-left:3px solid #f97316;}', '.para-change-item{padding:.625rem .75rem;background:var(--nx-surface3);border-radius:8px;margin-bottom:.5rem;border-left:3px solid var(--nx-acc);}', 1)
c = c.replace('.para-change-new{font-size:.875rem;font-weight:600;color:#1a1a1a;margin-bottom:.2rem;}', '.para-change-new{font-size:.875rem;font-weight:600;color:var(--nx-t1);margin-bottom:.2rem;}', 1)
c = c.replace('.para-style-panel{padding:1rem;border-top:1px solid var(--nx-bdr);background:#fafaf8;', '.para-style-panel{padding:1rem;border-top:1px solid var(--nx-bdr);background:var(--nx-bg);', 1)
c = c.replace('.para-style-panel textarea{width:100%;height:80px;border:1.5px solid var(--nx-bdr);border-radius:8px;padding:.625rem .75rem;font-size:.8125rem;resize:none;outline:none;font-family:inherit;box-sizing:border-box;}', '.para-style-panel textarea{width:100%;height:80px;border:1.5px solid var(--nx-bdr);border-radius:8px;padding:.625rem .75rem;font-size:.8125rem;resize:none;outline:none;font-family:inherit;box-sizing:border-box;background:var(--nx-surface3);color:var(--nx-t1);}', 1)

# ── 12. Citation panels ──
c = c.replace('.cite-left{width:340px;display:flex;flex-direction:column;overflow:hidden;border-right:1px solid var(--nx-bdr);flex-shrink:0;background:#fff;}', '.cite-left{width:340px;display:flex;flex-direction:column;overflow:hidden;border-right:1px solid var(--nx-bdr);flex-shrink:0;background:var(--nx-sb);}', 1)
c = c.replace('.cite-right{flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0;background:var(--nx-bg);}', '.cite-right{flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0;background:var(--nx-bg);}', 1)
c = c.replace('.cite-topbar{padding:.625rem 1rem;border-bottom:1px solid var(--nx-bdr);background:#fff;', '.cite-topbar{padding:.625rem 1rem;border-bottom:1px solid var(--nx-bdr);background:var(--nx-sb);', 1)
c = c.replace('.cite-topbar-title{font-size:.9375rem;font-weight:700;color:#1a1a1a;}', '.cite-topbar-title{font-size:.9375rem;font-weight:700;color:var(--nx-t1);}', 1)
c = c.replace('.cite-style-pill{padding:.25rem .625rem;border-radius:20px;border:1.5px solid var(--nx-bdr);background:#fff;font-size:.75rem;font-weight:600;color:var(--nx-t2);', '.cite-style-pill{padding:.25rem .625rem;border-radius:20px;border:1.5px solid var(--nx-bdr);background:var(--nx-surface3);font-size:.75rem;font-weight:600;color:var(--nx-t2);', 1)
c = c.replace('.cite-type-pill{padding:.25rem .625rem;border-radius:20px;border:1.5px solid var(--nx-bdr);background:#fff;font-size:.75rem;font-weight:600;color:var(--nx-t2);', '.cite-type-pill{padding:.25rem .625rem;border-radius:20px;border:1.5px solid var(--nx-bdr);background:var(--nx-surface3);font-size:.75rem;font-weight:600;color:var(--nx-t2);', 1)
c = c.replace('.cite-field input,.cite-field textarea,.cite-field select{width:100%;border:1.5px solid var(--nx-bdr);border-radius:8px;padding:.4rem .625rem;font-size:.8375rem;color:#1a1a1a;background:#fff;', '.cite-field input,.cite-field textarea,.cite-field select{width:100%;border:1.5px solid var(--nx-bdr);border-radius:8px;padding:.4rem .625rem;font-size:.8375rem;color:var(--nx-t1);background:var(--nx-surface3);', 1)
c = c.replace('.cite-right-tabs{display:flex;border-bottom:1px solid var(--nx-bdr);background:#fff;flex-shrink:0;}', '.cite-right-tabs{display:flex;border-bottom:1px solid var(--nx-bdr);background:var(--nx-sb);flex-shrink:0;}', 1)
c = c.replace('.cite-card{background:#fff;border:1px solid var(--nx-bdr);border-radius:12px;padding:1rem 1.125rem;margin-bottom:.875rem;box-shadow:0 1px 4px rgba(0,0,0,.05);}', '.cite-card{background:var(--nx-surface3);border:1px solid var(--nx-bdr);border-radius:12px;padding:1rem 1.125rem;margin-bottom:.875rem;box-shadow:0 1px 4px rgba(0,0,0,.3);}', 1)
c = c.replace('.cite-card-text{font-size:.9rem;line-height:1.8;color:#1a1a1a;', '.cite-card-text{font-size:.9rem;line-height:1.8;color:var(--nx-t1);', 1)
c = c.replace('.cite-card-btn{padding:.3rem .75rem;border:1.5px solid var(--nx-bdr);background:#fff;border-radius:8px;', '.cite-card-btn{padding:.3rem .75rem;border:1.5px solid var(--nx-bdr);background:var(--nx-surface3);border-radius:8px;', 1)
c = c.replace('.cite-bib-item{display:flex;align-items:flex-start;gap:.625rem;padding:.625rem .75rem;background:#fff;border:1px solid var(--nx-bdr);', '.cite-bib-item{display:flex;align-items:flex-start;gap:.625rem;padding:.625rem .75rem;background:var(--nx-surface3);border:1px solid var(--nx-bdr);', 1)
c = c.replace('.cite-bib-text{font-size:.8375rem;line-height:1.6;color:#1a1a1a;', '.cite-bib-text{font-size:.8375rem;line-height:1.6;color:var(--nx-t1);', 1)
c = c.replace('.cite-bib-export-row{display:flex;gap:.5rem;padding:.75rem 1rem;border-top:1px solid var(--nx-bdr);flex-shrink:0;background:#fff;}', '.cite-bib-export-row{display:flex;gap:.5rem;padding:.75rem 1rem;border-top:1px solid var(--nx-bdr);flex-shrink:0;background:var(--nx-sb);}', 1)
c = c.replace('.cite-bib-export-btn{padding:.4rem .875rem;border:1.5px solid var(--nx-bdr);background:#fff;border-radius:8px;', '.cite-bib-export-btn{padding:.4rem .875rem;border:1.5px solid var(--nx-bdr);background:var(--nx-surface3);border-radius:8px;', 1)

# ── 13. Tasks panel ──
c = c.replace('.nx-tasks-header{display:flex;align-items:center;justify-content:space-between;padding:.75rem 1.25rem;border-bottom:1px solid var(--nx-bdr);background:#fff;flex-shrink:0;}', '.nx-tasks-header{display:flex;align-items:center;justify-content:space-between;padding:.75rem 1.25rem;border-bottom:1px solid var(--nx-bdr);background:var(--nx-sb);flex-shrink:0;}', 1)
c = c.replace('.nx-tasks-header-title{font-size:.9375rem;font-weight:700;color:#1a1a1a;', '.nx-tasks-header-title{font-size:.9375rem;font-weight:700;color:var(--nx-t1);', 1)
c = c.replace('.nx-task-row{display:flex;align-items:flex-start;gap:.625rem;padding:.625rem .75rem;background:#fff;border:1px solid var(--nx-bdr);', '.nx-task-row{display:flex;align-items:flex-start;gap:.625rem;padding:.625rem .75rem;background:var(--nx-surface3);border:1px solid var(--nx-bdr);', 1)
c = c.replace('.nx-task-title{font-size:.875rem;font-weight:600;color:#1a1a1a;line-height:1.4;}', '.nx-task-title{font-size:.875rem;font-weight:600;color:var(--nx-t1);line-height:1.4;}', 1)
c = c.replace('.nx-task-ws{font-size:.6875rem;background:#f0f0ec;color:#555;', '.nx-task-ws{font-size:.6875rem;background:var(--nx-surface4);color:var(--nx-t2);', 1)
c = c.replace('.nx-task-view-btn{display:flex;align-items:center;gap:.25rem;padding:.25rem .625rem;border:1.5px solid var(--nx-bdr);background:#fff;border-radius:6px;', '.nx-task-view-btn{display:flex;align-items:center;gap:.25rem;padding:.25rem .625rem;border:1.5px solid var(--nx-bdr);background:var(--nx-surface3);border-radius:6px;', 1)

# ── 14. Task detail modal ──
c = c.replace('.nxtd-modal{background:#fff;width:100%;', '.nxtd-modal{background:var(--nx-sb);width:100%;', 1)
c = c.replace('.nxtd-title{font-size:1rem;font-weight:800;color:#1a1a1a;line-height:1.3;}', '.nxtd-title{font-size:1rem;font-weight:800;color:var(--nx-t1);line-height:1.3;}', 1)
c = c.replace('.nxtd-close{width:32px;height:32px;border:none;background:#f0f0ec;border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;color:#555;', '.nxtd-close{width:32px;height:32px;border:none;background:var(--nx-surface3);border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;color:var(--nx-t2);', 1)
c = c.replace('.nxtd-desc{font-size:.9rem;line-height:1.7;color:#444;background:#f7f7f5;border-radius:10px;padding:.75rem 1rem;}', '.nxtd-desc{font-size:.9rem;line-height:1.7;color:var(--nx-t2);background:var(--nx-surface3);border-radius:10px;padding:.75rem 1rem;}', 1)
c = c.replace('.nxtd-step{display:flex;gap:.75rem;align-items:flex-start;padding:.625rem .875rem;background:#fff;border:1px solid var(--nx-bdr);', '.nxtd-step{display:flex;gap:.75rem;align-items:flex-start;padding:.625rem .875rem;background:var(--nx-surface3);border:1px solid var(--nx-bdr);', 1)
c = c.replace('.nxtd-step-title{font-size:.875rem;font-weight:700;color:#1a1a1a;}', '.nxtd-step-title{font-size:.875rem;font-weight:700;color:var(--nx-t1);}', 1)
c = c.replace('.nxtd-tool-card{background:#fff;border:1.5px solid var(--nx-bdr);border-radius:10px;padding:.75rem;cursor:pointer;transition:all .15s;display:flex;flex-direction:column;gap:.375rem;}', '.nxtd-tool-card{background:var(--nx-surface3);border:1.5px solid var(--nx-bdr);border-radius:10px;padding:.75rem;cursor:pointer;transition:all .15s;display:flex;flex-direction:column;gap:.375rem;}', 1)
c = c.replace('.nxtd-tool-name{font-size:.8125rem;font-weight:700;color:#1a1a1a;}', '.nxtd-tool-name{font-size:.8125rem;font-weight:700;color:var(--nx-t1);}', 1)
c = c.replace('.nxtd-meta-chip{display:flex;align-items:center;gap:.375rem;padding:.375rem .75rem;background:#f7f7f5;border-radius:8px;font-size:.8125rem;color:#555;}', '.nxtd-meta-chip{display:flex;align-items:center;gap:.375rem;padding:.375rem .75rem;background:var(--nx-surface3);border-radius:8px;font-size:.8125rem;color:var(--nx-t2);}', 1)
c = c.replace('.nxtd-footer{padding:.875rem 1.25rem;border-top:1px solid var(--nx-bdr);flex-shrink:0;display:flex;gap:.625rem;align-items:center;background:#fff;}', '.nxtd-footer{padding:.875rem 1.25rem;border-top:1px solid var(--nx-bdr);flex-shrink:0;display:flex;gap:.625rem;align-items:center;background:var(--nx-sb);}', 1)
c = c.replace('.nxtd-tabs{display:flex;gap:0;border-bottom:1px solid var(--nx-bdr);flex-shrink:0;background:#fff;}', '.nxtd-tabs{display:flex;gap:0;border-bottom:1px solid var(--nx-bdr);flex-shrink:0;background:var(--nx-sb);}', 1)
c = c.replace('.nxtd-activity-entry{display:flex;gap:.625rem;align-items:flex-start;padding:.5rem .625rem;border-radius:8px;background:#f9f9f7;}', '.nxtd-activity-entry{display:flex;gap:.625rem;align-items:flex-start;padding:.5rem .625rem;border-radius:8px;background:var(--nx-surface3);}', 1)
c = c.replace('.nxtd-activity-text{font-size:.8125rem;color:#1a1a1a;line-height:1.5;word-break:break-word;}', '.nxtd-activity-text{font-size:.8125rem;color:var(--nx-t1);line-height:1.5;word-break:break-word;}', 1)
c = c.replace('.nxtd-mode-bar{display:flex;gap:.5rem;padding:.75rem 1.25rem;border-bottom:1px solid var(--nx-bdr);background:#fafaf8;flex-shrink:0;}', '.nxtd-mode-bar{display:flex;gap:.5rem;padding:.75rem 1.25rem;border-bottom:1px solid var(--nx-bdr);background:var(--nx-bg);flex-shrink:0;}', 1)
c = c.replace('.nxtd-mode-btn{flex:1;display:flex;flex-direction:column;align-items:center;gap:.25rem;padding:.625rem .5rem;border:1.5px solid var(--nx-bdr);border-radius:10px;background:#fff;cursor:pointer;font-family:inherit;transition:all .15s;}', '.nxtd-mode-btn{flex:1;display:flex;flex-direction:column;align-items:center;gap:.25rem;padding:.625rem .5rem;border:1.5px solid var(--nx-bdr);border-radius:10px;background:var(--nx-surface3);cursor:pointer;font-family:inherit;transition:all .15s;}', 1)
c = c.replace('.nxtd-mode-btn-label{font-size:.6875rem;font-weight:700;color:#1a1a1a;}', '.nxtd-mode-btn-label{font-size:.6875rem;font-weight:700;color:var(--nx-t1);}', 1)
c = c.replace('.nxtd-ap-output-box{background:#f7f7f5;border-radius:8px;padding:.75rem 1rem;font-size:.8125rem;line-height:1.7;color:#333;', '.nxtd-ap-output-box{background:var(--nx-surface3);border-radius:8px;padding:.75rem 1rem;font-size:.8125rem;line-height:1.7;color:var(--nx-t2);', 1)
c = c.replace('.nxtd-ap-btn.secondary{background:#fff;color:#1a1a1a;border:1.5px solid var(--nx-bdr);}', '.nxtd-ap-btn.secondary{background:var(--nx-surface3);color:var(--nx-t1);border:1.5px solid var(--nx-bdr);}', 1)
c = c.replace('.nxtd-regen-input{width:100%;border:1.5px solid var(--nx-bdr);border-radius:8px;padding:.5rem .75rem;font-size:.8125rem;font-family:inherit;outline:none;resize:none;margin-bottom:.5rem;box-sizing:border-box;}', '.nxtd-regen-input{width:100%;border:1.5px solid var(--nx-bdr);border-radius:8px;padding:.5rem .75rem;font-size:.8125rem;font-family:inherit;outline:none;resize:none;margin-bottom:.5rem;box-sizing:border-box;background:var(--nx-surface3);color:var(--nx-t1);}', 1)

# ── 15. Workspace links ──
c = c.replace('.nx-ws-link-card{background:#fff;border:1px solid var(--nx-bdr);border-radius:10px;padding:.875rem 1rem;text-decoration:none;color:#1a1a1a;', '.nx-ws-link-card{background:var(--nx-surface3);border:1px solid var(--nx-bdr);border-radius:10px;padding:.875rem 1rem;text-decoration:none;color:var(--nx-t1);', 1)

# ── 16. Nexa Office ──
c = c.replace('.nxo-toolbar{display:flex;align-items:center;gap:.25rem;padding:.5rem .875rem;border-bottom:1px solid var(--nx-bdr);background:#fff;', '.nxo-toolbar{display:flex;align-items:center;gap:.25rem;padding:.5rem .875rem;border-bottom:1px solid var(--nx-bdr);background:var(--nx-sb);', 1)
c = c.replace('.nxo-btn{width:28px;height:28px;border:none;background:none;border-radius:5px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:#555;', '.nxo-btn{width:28px;height:28px;border:none;background:none;border-radius:5px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:var(--nx-t2);', 1)
c = c.replace('.nxo-btn:hover{background:#f0f0ec;color:#1a1a1a;}', '.nxo-btn:hover{background:var(--nx-surface3);color:var(--nx-t1);}', 1)
c = c.replace('.nxo-select{border:1px solid var(--nx-bdr);border-radius:5px;padding:.2rem .4rem;font-size:.75rem;background:#fff;color:#1a1a1a;', '.nxo-select{border:1px solid var(--nx-bdr);border-radius:5px;padding:.2rem .4rem;font-size:.75rem;background:var(--nx-surface3);color:var(--nx-t1);', 1)
c = c.replace('.nxo-tb-title{flex:1;font-size:.875rem;font-weight:700;color:#1a1a1a;', '.nxo-tb-title{flex:1;font-size:.875rem;font-weight:700;color:var(--nx-t1);', 1)
c = c.replace('.nxo-action-btn{display:flex;align-items:center;gap:.375rem;padding:.3rem .75rem;border:1.5px solid var(--nx-bdr);background:#fff;border-radius:7px;font-size:.75rem;font-weight:600;color:#555;', '.nxo-action-btn{display:flex;align-items:center;gap:.375rem;padding:.3rem .75rem;border:1.5px solid var(--nx-bdr);background:var(--nx-surface3);border-radius:7px;font-size:.75rem;font-weight:600;color:var(--nx-t2);', 1)
c = c.replace('.nxo-action-btn.primary{background:#1a1a1a;color:#fff;border-color:#1a1a1a;}', '.nxo-action-btn.primary{background:var(--nx-acc);color:#fff;border-color:var(--nx-acc);}', 1)
c = c.replace('.nxo-action-btn.primary:hover{background:#333;border-color:#333;}', '.nxo-action-btn.primary:hover{background:#5254cc;border-color: