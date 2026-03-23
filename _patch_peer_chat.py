with open('community/templates/community/workspace_detail.html', 'rb') as f:
    content = f.read().decode('utf-8', errors='replace')

# ── 1. Add peer chat CSS before the closing </style> of the first style block ──
PEER_CSS = """
/* ── Peer Chat ── */
.peer-layout{display:flex;height:100%;overflow:hidden;}
.peer-members-list{width:200px;flex-shrink:0;border-right:1px solid var(--ws-border);background:var(--ws-surface);display:flex;flex-direction:column;overflow:hidden;}
.peer-members-head{padding:.75rem 1rem;border-bottom:1px solid var(--ws-border);font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--ws-text3);}
.peer-member-item{display:flex;align-items:center;gap:.625rem;padding:.5rem .875rem;cursor:pointer;transition:background .12s;border-left:2px solid transparent;}
.peer-member-item:hover{background:var(--ws-surface2);}
.peer-member-item.active{background:var(--ws-surface2);border-left-color:var(--ws-text);}
.peer-member-av{width:32px;height:32px;border-radius:50%;background:var(--ws-surface3);flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:.75rem;font-weight:700;color:var(--ws-text2);border:1px solid var(--ws-border);overflow:hidden;}
.peer-member-av img{width:100%;height:100%;object-fit:cover;}
.peer-member-name{font-size:.8rem;font-weight:600;color:var(--ws-text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.peer-member-role{font-size:.65rem;color:var(--ws-text3);}
.peer-chat-area{flex:1;display:flex;flex-direction:column;overflow:hidden;}
.peer-chat-header{padding:.625rem 1rem;border-bottom:1px solid var(--ws-border);background:var(--ws-surface);flex-shrink:0;display:flex;align-items:center;gap:.75rem;}
.peer-chat-header-name{font-size:.875rem;font-weight:700;color:var(--ws-text);}
.peer-chat-header-role{font-size:.7rem;color:var(--ws-text3);}
.peer-chat-msgs{flex:1;overflow-y:auto;padding:1rem 1.25rem;display:flex;flex-direction:column;gap:.5rem;background:var(--ws-bg);}
.peer-chat-input-row{display:flex;gap:.5rem;align-items:flex-end;padding:.75rem 1rem;border-top:1px solid var(--ws-border);background:var(--ws-surface);flex-shrink:0;}
.peer-chat-input{flex:1;background:var(--ws-surface2);border:1px solid var(--ws-border);border-radius:10px;padding:.5rem .875rem;color:var(--ws-text);font-size:.8125rem;resize:none;min-height:38px;max-height:100px;outline:none;font-family:inherit;}
.peer-chat-input:focus{border-color:var(--ws-border2);background:var(--ws-surface);}
.peer-contrib-panel{width:220px;flex-shrink:0;border-left:1px solid var(--ws-border);background:var(--ws-surface);display:flex;flex-direction:column;overflow:hidden;}
.peer-contrib-head{padding:.75rem 1rem;border-bottom:1px solid var(--ws-border);font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--ws-text3);}
.peer-contrib-scroll{flex:1;overflow-y:auto;padding:.75rem;}
.peer-contrib-section{margin-bottom:1rem;}
.peer-contrib-section-title{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--ws-text3);margin-bottom:.375rem;}
.peer-contrib-item{background:var(--ws-surface2);border:1px solid var(--ws-border);border-radius:6px;padding:.375rem .625rem;margin-bottom:.375rem;font-size:.75rem;color:var(--ws-text2);}
.peer-contrib-item-title{font-weight:600;color:var(--ws-text);margin-bottom:.15rem;line-height:1.3;}
.peer-empty{display:flex;align-items:center;justify-content:center;flex:1;flex-direction:column;gap:.5rem;color:var(--ws-text3);font-size:.8rem;text-align:center;padding:2rem;}
.peer-empty svg{width:36px;height:36px;opacity:.2;stroke:var(--ws-text3);}
@media(max-width:768px){
  .peer-members-list{width:160px;}
  .peer-contrib-panel{display:none;}
}
@media(max-width:480px){
  .peer-members-list{width:56px;}
  .peer-member-name,.peer-member-role{display:none;}
  .peer-member-item{justify-content:center;padding:.5rem;}
}
"""

# Insert before the closing </style> of the last style block before {% endblock %}
# Find the last </style> before {% endblock %}
endblock_idx = content.index('{% endblock %}\n\n{% block content %}')
style_close = content.rindex('</style>', 0, endblock_idx)
content = content[:style_close] + PEER_CSS + content[style_close:]
print('CSS inserted')

# ── 2. Add peer chat panel HTML before the finish panel ──
PEER_PANEL = """
    <!-- ══ PEER CHAT PANEL ══ -->
    <div class="ws-panel" id="panel-peer">
      <div class="ws-panel-header">
        <div class="ws-panel-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          Peer Chat
        </div>
        <div class="ws-panel-actions">
          <span style="font-size:.75rem;color:var(--ws-text3);">Private messages &amp; contributions</span>
        </div>
      </div>
      <div class="peer-layout">
        <!-- Member list -->
        <div class="peer-members-list">
          <div class="peer-members-head">Members</div>
          <div style="flex:1;overflow-y:auto;">
            {% for m in members %}
            {% if m.user != request.user %}
            <div class="peer-member-item" id="peer-member-{{ m.user.username }}" onclick="openPeerChat('{{ m.user.username }}','{{ m.user.get_full_name|default:m.user.username|escapejs }}','{{ m.get_role_display }}')">
              <div class="peer-member-av">
                {% if m.user.community_profile.avatar %}<img src="{{ m.user.community_profile.avatar.ur