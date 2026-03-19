import os
path = os.path.join('materials', 'templates', 'materials', 'learn.html')
parts = []

parts.append(r"""{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} - NEXA</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/marked@9.1.6/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#0d0d0d;--surface:#161616;--surface2:#1e1e1e;--border:#2a2a2a;
  --text:#e8e8e8;--text2:#a0a0a0;--text3:#6b6b6b;
  --purple:#a855f7;--blue:#3b82f6;--green:#22c55e;--red:#ef4444;--yellow:#f59e0b;
}
body{font-family:"Inter",-apple-system,sans-serif;background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column;overflow:hidden}

/* HEADER */
.header{height:52px;background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;padding:0 1.25rem;flex-shrink:0;gap:10px}
.back-btn{display:flex;align-items:center;gap:6px;color:var(--text2);text-decoration:none;font-size:13px;padding:6px 10px;border-radius:6px;white-space:nowrap}
.back-btn:hover{background:var(--surface2);color:var(--text)}
.header-center{display:flex;align-items:center;gap:10px;flex:1;justify-content:center}
.header-title{font-size:15px;font-weight:600}
.material-badge{font-size:12px;color:var(--text3);background:var(--surface2);padding:3px 10px;border-radius:20px;border:1px solid var(--border);max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.btn-sm{background:var(--surface2);border:1px solid var(--border);color:var(--text2);font-size:12px;padding:5px 12px;border-radius:6px;cursor:pointer;font-family:inherit;transition:all .15s}
.btn-sm:hover{color:var(--text);border-color:var(--purple)}
.btn-sm.active{background:linear-gradient(135deg,var(--purple),var(--blue));color:#fff;border-color:transparent}

/* XP BAR */
.xp-bar-wrap{height:3px;background:var(--border);flex-shrink:0;position:relative}
.xp-bar-fill{height:100%;background:linear-gradient(90deg,var(--purple),var(--blue));width:0%;transition:width 0.6s cubic-bezier(.4,0,.2,1)}
.xp-toast{position:fixed;top:60px;right:20px;background:linear-gradient(135deg,var(--purple),var(--blue));color:#fff;font-size:13px;font-weight:600;padding:8px 16px;border-radius:20px;z-index:999;opacity:0;transform:translateY(-8px);transition:all .3s;pointer-events:none}
.xp-toast.show{opacity:1;transform:translateY(0)}

/* SPLIT */
.split{flex:1;display:flex;overflow:hidden;min-height:0}
.panel{display:flex;flex-direction:column;overflow:hidden;min-height:0}
.panel-left{flex:1;border-right:1px solid var(--border)}
.panel-right{width:420px;flex-shrink:0;background:var(--surface)}
.panel-header{height:44px;background:var(--surface2);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;padding:0 16px;flex-shrink:0}
.panel-label{font-size:12px;font-weight:600;color:var(--text2);text-transform:uppercase;letter-spacing:.05em}

/* CHAT */
.chat-area{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px}
.chat-area::-webkit-scrollbar{width:4px}
.chat-area::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.msg{display:flex;gap:8px;max-width:100%;opacity:0;transform:translateY(8px);animation:msgIn .3s ease forwards}
@keyframes msgIn{to{opacity:1;transform:translateY(0)}}
.msg.user{flex-direction:row-reverse}
.avatar{width:28px;height:28px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0}
.msg.ai .avatar{background:linear-gradient(135deg,#a855f7,#3b82f6);color:#fff}
.msg.user .avatar{background:#1a1a1a;color:var(--text);border:1px solid var(--border)}
.bubble{padding:10px 14px;border-radius:10px;font-size:14px;line-height:1.75;max-width:calc(100% - 38px)}
.msg.ai .bubble{background:var(--surface2);border:1px solid var(--border)}
.msg.user .bubble{background:#1a1a1a;border:1px solid var(--border);border-radius:10px 10px 3px 10px}

/* BUBBLE CONTENT */
.bubble p{margin:0 0 6px;color:var(--text2)}.bubble p:last-child{margin-bottom:0}
.bubble strong{color:var(--text);font-weight:600}
.bubble em{color:var(--text2);font-style:italic}
.bubble ul,.bubble ol{padding-left:18px;margin:6px 0;color:var(--text2)}
.bubble li{margin-bottom:4px}
.bubble h1,.bubble h2,.bubble h3{color:var(--text);font-weight:700;margin:10px 0 5px;font-size:14px}
.bubble code{background:var(--bg);padding:1px 5px;border-radius:4px;font-family:monospace;font-size:12px;color:#a78bfa}
.bubble pre{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px 12px;overflow-x:auto;margin:6px 0}
.bubble pre code{background:none;padding:0;color:var(--text2)}
.bubble blockquote{border-left:3px solid var(--purple);padding-left:10px;margin:6px 0;color:var(--text3)}
.br-math-display{text-align:center;padding:10px 0;overflow-x:auto}
.katex-display{overflow-x:auto;padding:4px 0}

/* STREAM CURSOR */
.stream-cursor{display:inline-block;width:2px;height:1em;background:var(--purple);margin-left:1px;vertical-align:text-bottom;animation:blink .7s step-end infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}

/* TYPING DOTS */
.typing{display:flex;align-items:center;gap:4px;padding:4px 0}
.typing span{width:5px;height:5px;background:var(--text3);border-radius:50%;animation:tdot 1.2s infinite}
.typing span:nth-child(2){animation-delay:.2s}.typing span:nth-child(3){animation-delay:.4s}
@keyframes tdot{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-5px)}}

/* CHIPS */
.chips{display:flex;flex-wrap:wrap;gap:6px;padding:0 16px 8px}
.chip{background:var(--surface2);border:1px solid var(--border);color:var(--text2);font-size:12px;padding:6px 14px;border-radius:16px;cursor:pointer;transition:all .15s;font-family:inherit}
.chip:hover{border-color:var(--purple);color:var(--text);background:rgba(168,85,247,.08)}
.chip.answer-chip{border-color:var(--blue);color:var(--blue)}
.chip.answer-chip:hover{background:rgba(59,130,246,.1)}

/* INPUT */
.input-area{padding:10px 16px;border-top:1px solid var(--border);background:var(--surface);flex-shrink:0}
.input-wrap{display:flex;gap:6px;align-items:flex-end;background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:6px 6px 6px 12px;transition:border-color .15s}
.input-wrap:focus-within{border-color:var(--purple)}
.chat-input{flex:1;background:transparent;border:none;color:var(--text);font-size:13px;font-family:inherit;resize:none;outline:none;max-height:80px;line-height:1.5;padding:2px 0}
.chat-input::placeholder{color:var(--text3)}
.send-btn{width:32px;height:32px;background:linear-gradient(135deg,var(--purple),var(--blue));border:none;border-radius:7px;color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:opacity .15s}
.send-btn:hover{opacity:.85}.send-btn:disabled{opacity:.35;cursor:not-allowed}

/* QUIZ PANEL */
.quiz-panel{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px}
.quiz-panel::-webkit-scrollbar{width:4px}
.quiz-panel::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
.quiz-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;padding:24px;gap:12px}
.quiz-empty-icon{font-size:40px;opacity:.4}
.quiz-empty h3{font-size:15px;font-weight:600;color:var(--text2)}
.quiz-empty p{font-size:13px;color:var(--text3);line-height:1.5;max-width:240px}
.gen-quiz-btn{background:linear-gradient(135deg,var(--purple),var(--blue));color:#fff;border:none;padding:10px 24px;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit;margin-top:4px;transition:opacity .15s}
.gen-quiz-btn:hover{opacity:.85}.gen-quiz-btn:disabled{opacity:.4;cursor:not-allowed}
.score-bar{background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:12px 16px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.score-label{font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:.04em}
.score-val{font-size:22px;font-weight:700;color:var(--text)}
.score-pct{font-size:13px;color:var(--text2)}
.q-card{background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:16px;display:flex;flex-direction:column;gap:12px;opacity:0;animation:msgIn .35s ease forwards}
.q-num{font-size:11px;font-weight:600;color:var(--text3);text-transform:uppercase;letter-spacing:.05em}
.q-text{font-size:14px;color:var(--text);line-height:1.6;font-weight:500}
.q-options{display:flex;flex-direction:column;gap:8px}
.q-opt{display:flex;align-items:flex-start;gap:10px;padding:10px 12px;border-radius:8px;border:1px solid var(--border);cursor:pointer;transition:all .15s;background:var(--bg);font-size:13px;color:var(--text2);font-family:inherit;text-align:left;width:100%}
.q-opt:hover:not(:disabled){border-color:var(--purple);color:var(--text);background:rgba(168,85,247,.06);transform:translateX(2px)}
.opt-letter{width:22px;height:22px;border-radius:5px;background:var(--surface2);border:1px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;color:var(--text2);transition:all .15s}
.q-opt.correct{border-color:var(--green);background:rgba(34,197,94,.08);color:var(--text)}
.q-opt.correct .opt-letter{background:var(--green);border-color:var(--green);color:#fff}
.q-opt.wrong{border-color:var(--red);background:rgba(239,68,68,.08);color:var(--text)}
.q-opt.wrong .opt-letter{background:var(--red);border-color:var(--red);color:#fff}
.q-opt:disabled{cursor:not-allowed}
.q-feedback{padding:10px 12px;border-radius:8px;font-size:13px;line-height:1.5;opacity:0;animation:msgIn .3s ease forwards}
.q-feedback.correct{background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.3);color:#86efac}
.q-feedback.wrong{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);color:#fca5a5}
.q-next-btn{background:var(--surface);border:1px solid var(--border);color:var(--text2);font-size:13px;padding:8px 16px;border-radius:7px;cursor:pointer;font-family:inherit;align-self:flex-end;transition:all .15s}
.q-next-btn:hover{border-color:var(--purple);color:var(--text)}
.quiz-result{background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:24px;text-align:center;display:flex;flex-direction:column;gap:10px;align-items:center;opacity:0;animation:msgIn .4s ease forwards}
.big-score{font-size:42px;font-weight:700}
.score-msg{font-size:14px;color:var(--text2)}
.retry-btn{background:linear-gradient(135deg,var(--purple),var(--blue));color:#fff;border:none;padding:9px 22px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit}

/* WELCOME */
.welcome-left{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;padding:32px;gap:14px}
.welcome-icon{width:60px;height:60px;background:linear-gradient(135deg,var(--purple),var(--blue));border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:26px}
.welcome-left h2{font-size:18px;font-weight:700}
.welcome-left p{color:var(--text2);font-size:13px;line-height:1.6;max-width:320px}
.start-btn{background:linear-gradient(135deg,var(--purple),var(--blue));color:#fff;border:none;padding:11px 28px;border-radius:9px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit;transition:opacity .15s}
.start-btn:hover{opacity:.85}

/* STREAK */
.streak-badge{display:flex;align-items:center;gap:5px;font-size:12px;font-weight:600;color:var(--yellow);background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.2);padding:3px 10px;border-radius:20px}

/* REACTION BURST */
.reaction{position:fixed;pointer-events:none;font-size:22px;z-index:9999;animation:burst .8s ease forwards}
@keyframes burst{0%{opacity:1;transform:translateY(0) scale(1)}100%{opacity:0;transform:translateY(-60px) scale(1.4)}}

@media(max-width:768px){.panel-right{display:none}.panel-left{border-right:none}}
@media(max-width:480px){.material-badge{display:none}}
</style>
</head>
<body>
""")

parts.append(r"""
<div class="xp-toast" id="xpToast"></div>

<div class="header">
  <a href="{% url 'list_materials' %}" class="back-btn">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
    Back
  </a>
  <div class="header-center">
    <span class="header-title">Learn Mode</span>
    <span class="material-badge">{{ material.title }}</span>
  </div>
  <div style="display:flex;gap:8px;align-items:center">
    <div class="streak-badge" id="streakBadge" style="display:none">&#128293; <span id="streakCount">0</span></div>
    <button class="btn-sm" id="genQuizBtnHeader" onclick="generateQuiz()" disabled>&#129504; Quiz</button>
    <button class="btn-sm" onclick="resetChat()">Restart</button>
  </div>
</div>
<div class="xp-bar-wrap"><div class="xp-bar-fill" id="xpBar"></div></div>

<div class="split">
  <div class="panel panel-left">
    <div class="panel-header">
      <span class="panel-label">AI Tutor</span>
      <span id="lessonStatus" style="font-size:11px;color:var(--text3)">Ready to learn</span>
    </div>
    <div class="chat-area" id="chatArea">
      <div class="welcome-left" id="welcomeScreen">
        <div class="welcome-icon">&#127891;</div>
        <h2>Learn: {{ material.title }}</h2>
        <p>Your AI tutor will guide you step by step, ask questions, and make sure you actually understand — not just read.</p>
        <button class="start-btn" id="startBtn" onclick="startLearn()">Start Learning &#8594;</button>
      </div>
    </div>
    <div class="chips" id="chipsArea" style="display:none"></div>
    <div class="input-area">
      <div class="input-wrap">
        <textarea class="chat-input" id="chatInput" placeholder="Type your answer..." rows="1"></textarea>
        <button class="send-btn" id="sendBtn" onclick="sendMessage()" disabled>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
    </div>
  </div>

  <div class="panel panel-right">
    <div class="panel-header">
      <span class="panel-label">Quiz</span>
      <span id="quizScoreLabel" style="font-size:12px;color:var(--text3)">0 / 0</span>
    </div>
    <div class="quiz-panel" id="quizPanel">
      <div class="quiz-empty">
        <div class="quiz-empty-icon">&#129504;</div>
        <h3>Quiz Panel</h3>
        <p>Complete a lesson topic, then generate a quiz to test your knowledge.</p>
        <button class="gen-quiz-btn" id="genQuizBtn" onclick="generateQuiz()" disabled>Generate Quiz</button>
      </div>
    </div>
  </div>
</div>
""")

parts.append(r"""
<script>
var MATERIAL_PK = {{ material.pk }};
var CSRF = '{{ csrf_token }}';
var chatHistory = [];
var isLoading = false;
var xp = 0;
var streak = 0;
var lessonComplete = false;
var currentTopic = '';
var quizQuestions = [], quizIndex = 0, quizScore = 0, quizTotal = 0;

var chatArea = document.getElementById('chatArea');
var chatInput = document.getElementById('chatInput');
var sendBtn = document.getElementById('sendBtn');
var chipsArea = document.getElementById('chipsArea');
var xpBar = document.getElementById('xpBar');
var quizPanel = document.getElementById('quizPanel');
var quizScoreLabel = document.getElementById('quizScoreLabel');
var lessonStatus = document.getElementById('lessonStatus');

chatInput.addEventListener('input', function() {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 80) + 'px';
  sendBtn.disabled = !this.value.trim();
});
chatInput.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (this.value.trim()) sendMessage(); }
});

// ── EXACT renderBoardHTML from AI Tutor ──
function renderBoardHTML(raw) {
  if (!raw) return '';
  var text = raw;
  // Normalise \( \) -> $  and  \[ \] -> $$
  text = text.replace(/\\\(/g, '$').replace(/\\\)/g, '$');
  text = text.replace(/\\\[/g, '$$').replace(/\\\]/g, '$$');
  // Promote lone $...$ on its own line to display $$...$$
  text = text.replace(/(^|\n)\$([^$\n]+)\$(\n|$)/g, function(_, pre, m, post) {
    return (pre || '\n') + '$$' + m + '$$' + (post || '\n');
  });
  var mathStore = [];
  // Display math $$...$$ (multiline safe)
  text = text.replace(/\$\$([\s\S]+?)\$\$/g, function(_, m) {
    var i = mathStore.length;
    mathStore.push({display: true, src: m.trim()});
    return '\n\nNEXAMATH_D_' + i + '_END\n\n';
  });
  // Inline math $...$
  text = text.replace(/\$([^$\n]+?)\$/g, function(_, m) {
    var i = mathStore.length;
    mathStore.push({display: false, src: m.trim()});
    return 'NEXAMATH_I_' + i + '_END';
  });
  var html = '';
  if (typeof marked !== 'undefined') {
    marked.setOptions({breaks: true, gfm: true});
    html = marked.parse(text);
  } else {
    html = '<p>' + text.replace(/\n\n+/g, '</p><p>').replace(/\n/g, '<br>') + '</p>';
  }
  html = html.replace(/<p>\s*NEXAMATH_D_(\d+)_END\s*<\/p>/g, function(_, i) { return _katex(mathStore[parseInt(i)]); });
  html = html.replace(/NEXAMATH_D_(\d+)_END/g, function(_, i) { return _katex(mathStore[parseInt(i)]); });
  html = html.replace(/NEXAMATH_I_(\d+)_END/g, function(_, i) { return _katex(mathStore[parseInt(i)]); });
  return html;
}

function _katex(m) {
  if (typeof katex === 'undefined') {
    return m.display ? '<div class="br-math-display">$$' + m.src + '$$</div>' : '$' + m.src + '$';
  }
  try {
    var out = katex.renderToString(m.src, {displayMode: m.display, throwOnError: false});
    return m.display ? '<div class="br-math-display">' + out + '</div>' : out;
  } catch(e) {
    return m.display ? '<div class="br-math-display">$$' + m.src + '$$</div>' : '$' + m.src + '$';
  }
}

// ── TYPEWRITER — same feel as AI tutor streaming ──
function typewriterRender(el, fullText, onDone) {
  // Render in chunks to simulate streaming
  var words = fullText.split(' ');
  var built = '';
  var i = 0;
  var speed = Math.max(8, Math.min(25, Math.round(3000 / words.length)));
  el.innerHTML = '<span class="stream-cursor">&#9611;</span>';
  function step() {
    if (i >= words.length) {
      el.innerHTML = renderBoardHTML(fullText);
      if (onDone) onDone();
      return;
    }
    var chunk = Math.min(3, words.length - i); // 3 words at a time
    for (var c = 0; c < chunk; c++) {
      built += (built ? ' ' : '') + words[i++];
    }
    el.innerHTML = renderBoardHTML(built) + '<span class="stream-cursor">&#9611;</span>';
    chatArea.scrollTop = chatArea.scrollHeight;
    setTimeout(step, speed);
  }
  step();
}

function addMsg(role, content, instant) {
  var ws = document.getElementById('welcomeScreen');
  if (ws) ws.remove();
  var d = document.createElement('div');
  d.className = 'msg ' + role;
  var init = role === 'ai' ? 'N' : '{{ user.username|slice:":1"|upper }}';
  var bubbleId = 'bubble-' + Date.now();
  d.innerHTML = '<div class="avatar">' + init + '</div><div class="bubble" id="' + bubbleId + '"></div>';
  chatArea.appendChild(d);
  chatArea.scrollTop = chatArea.scrollHeight;
  var bubbleEl = document.getElementById(bubbleId);
  if (role === 'ai' && !instant) {
    typewriterRender(bubbleEl, content, function() {
      chatArea.scrollTop = chatArea.scrollHeight;
    });
  } else {
    bubbleEl.innerHTML = renderBoardHTML(content);
  }
  return bubbleEl;
}

function showTyping() {
  var d = document.createElement('div');
  d.className = 'msg ai'; d.id = 'typing';
  d.innerHTML = '<div class="avatar">N</div><div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>';
  chatArea.appendChild(d);
  chatArea.scrollTop = chatArea.scrollHeight;
}
function hideTyping() { var t = document.getElementById('typing'); if (t) t.remove(); }

// ── XP & STREAK ──
function addXP(amount, label) {
  xp = Math.min(xp + amount, 100);
  xpBar.style.width = xp + '%';
  if (xp >= 100) { xp = 0; xpBar.style.width = '0%'; showXPToast('Level Up! &#127881;'); }
  else if (label) showXPToast('+' + amount + ' XP ' + label);
}

function showXPToast(msg) {
  var t = document.getElementById('xpToast');
  t.innerHTML = msg; t.classList.add('show');
  setTimeout(function() { t.classList.remove('show'); }, 2000);
}

function bumpStreak() {
  streak++;
  var badge = document.getElementById('streakBadge');
  var cnt = document.getElementById('streakCount');
  badge.style.display = 'flex';
  cnt.textContent = streak;
  if (streak % 3 === 0) burst('&#128293;');
}

function burst(emoji) {
  var el = document.createElement('div');
  el.className = 'reaction';
  el.innerHTML = emoji;
  el.style.left = (Math.random() * 60 + 20) + '%';
  el.style.top = '60%';
  document.body.appendChild(el);
  setTimeout(function() { el.remove(); }, 900);
}

function enableQuizBtns() {
  ['genQuizBtn','genQuizBtnHeader'].forEach(function(id) {
    var b = document.getElementById(id); if (b) { b.disabled = false; }
  });
}

function showChips(text) {
  chipsArea.innerHTML = '';
  // Topic list
  var matches = text.match(/^\d+\.\s*.+/gm);
  if (matches && matches.length >= 2 && matches.length <= 12) {
    chipsArea.style.display = 'flex';
    matches.forEach(function(m) {
      var b = document.createElement('button');
      b.className = 'chip'; b.textContent = m.trim();
      b.onclick = function() { sendMessage(m.trim()); };
      chipsArea.appendChild(b);
    });
    return;
  }
  // Quiz ready prompt
  if (/ready for the quiz|type yes|start the quiz/i.test(text)) {
    chipsArea.style.display = 'flex';
    ['Yes, start quiz!', 'Not yet'].forEach(function(label) {
      var b = document.createElement('button');
      b.className = 'chip answer-chip'; b.textContent = label;
      b.onclick = function() { sendMessage(label); };
      chipsArea.appendChild(b);
    });
    lessonComplete = true; enableQuizBtns();
    lessonStatus.textContent = 'Lesson complete &#10003;';
    addXP(20, '&#127891;');
    return;
  }
  // Another topic
  if (/another topic|type topics/i.test(text)) {
    chipsArea.style.display = 'flex';
    var b = document.createElement('button');
    b.className = 'chip'; b.textContent = 'Show topics';
    b.onclick = function() { sendMessage('topics'); };
    chipsArea.appendChild(b);
    return;
  }
  // A/B/C/D quiz chips in chat
  if (/^A\)/m.test(text) && /^B\)/m.test(text)) {
    chipsArea.style.display = 'flex';
    ['A','B','C','D'].forEach(function(l) {
      var re = new RegExp('^' + l + '\\)\\s*(.+)', 'm');
      var m = text.match(re);
      if (!m) return;
      var b = document.createElement('button');
      b.className = 'chip answer-chip';
      b.textContent = l + ') ' + m[1].trim();
      b.onclick = function() { sendMessage(l); };
      chipsArea.appendChild(b);
    });
    return;
  }
  chipsArea.style.display = 'none';
}

async function callAI(userMsg) {
  if (isLoading) return;
  isLoading = true; sendBtn.disabled = true;
  chipsArea.style.display = 'none';
  showTyping();
  try {
    var res = await fetch('/materials/learn/' + MATERIAL_PK + '/ajax/', {
      method: 'POST',
      headers: {'Content-Type':'application/json','X-CSRFToken':CSRF},
      body: JSON.stringify({message: userMsg, history: chatHistory})
    });
    var data = await res.json();
    hideTyping();
    if (data.success) {
      if (userMsg) chatHistory.push({role:'user', content:userMsg});
      chatHistory.push({role:'assistant', content:data.response});
      addMsg('ai', data.response);
      showChips(data.response);
      if (/lesson complete|ready for the quiz/i.test(data.response)) {
        lessonComplete = true; enableQuizBtns();
        lessonStatus.textContent = 'Lesson complete';
      }
      var tm = data.response.match(/learn about ([^.!\n]+)/i);
      if (tm) { currentTopic = tm[1].trim(); lessonStatus.textContent = 'Learning: ' + currentTopic; }
      addXP(5);
    } else {
      addMsg('ai', 'Error: ' + (data.error || 'Something went wrong.'), true);
    }
  } catch(e) {
    hideTyping();
    addMsg('ai', 'Connection error: ' + e.message, true);
  }
  isLoading = false;
  sendBtn.disabled = !chatInput.value.trim();
}

function startLearn() {
  document.getElementById('startBtn').disabled = true;
  document.getElementById('startBtn').textContent = 'Loading...';
  callAI('');
}

function sendMessage(text) {
  var msg = (typeof text === 'string') ? text : chatInput.value.trim();
  if (!msg || isLoading) return;
  addMsg('user', msg, true);
  chatInput.value = ''; chatInput.style.height = 'auto'; sendBtn.disabled = true;
  callAI(msg);
}

function resetChat() {
  if (!confirm('Restart this learning session?')) return;
  chatHistory = []; xp = 0; streak = 0; lessonComplete = false; currentTopic = '';
  quizQuestions = []; quizIndex = 0; quizScore = 0; quizTotal = 0;
  xpBar.style.width = '0%';
  lessonStatus.textContent = 'Ready to learn';
  quizScoreLabel.textContent = '0 / 0';
  document.getElementById('streakBadge').style.display = 'none';
  chatArea.innerHTML = '';
  chipsArea.style.display = 'none';
  quizPanel.innerHTML = '<div class="quiz-empty"><div class="quiz-empty-icon">&#129504;</div><h3>Quiz Panel</h3><p>Complete a lesson topic, then generate a quiz.</p><button class="gen-quiz-btn" id="genQuizBtn" onclick="generateQuiz()" disabled>Generate Quiz</button></div>';
  ['genQuizBtn','genQuizBtnHeader'].forEach(function(id){ var b=document.getElementById(id); if(b) b.disabled=true; });
  var ws = document.createElement('div');
  ws.className = 'welcome-left'; ws.id = 'welcomeScreen';
  ws.innerHTML = '<div class="welcome-icon">&#127891;</div><h2>Learn: {{ material.title|escapejs }}</h2><p>Your AI tutor will guide you step by step.</p><button class="start-btn" id="startBtn" onclick="startLearn()">Start Learning &#8594;</button>';
  chatArea.appendChild(ws);
}
</script>
""")

parts.append(r"""
<script>
// ── QUIZ PANEL ──
function updateScoreLabel() {
  quizScoreLabel.textContent = quizScore + ' / ' + quizTotal;
}

async function generateQuiz() {
  ['genQuizBtn','genQuizBtnHeader'].forEach(function(id){
    var b=document.getElementById(id); if(b){b.disabled=true;b.textContent='Generating...';}
  });
  quizPanel.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text3);font-size:13px;gap:8px"><div class="typing"><span></span><span></span><span></span></div> Generating quiz...</div>';
  try {
    var topicHint = currentTopic ? ' about ' + currentTopic : '';
    var prompt = 'Generate a 5-question multiple choice quiz' + topicHint + '. Format each question exactly as:\nQ: [question]\nA) [option]\nB) [option]\nC) [option]\nD) [option]\nAnswer: [letter]\nExplanation: [why the answer is correct]';
    var res = await fetch('/materials/learn/' + MATERIAL_PK + '/ajax/', {
      method: 'POST',
      headers: {'Content-Type':'application/json','X-CSRFToken':CSRF},
      body: JSON.stringify({message: prompt, history: chatHistory})
    });
    var data = await res.json();
    if (data.success) {
      var parsed = parseQuizFromText(data.response);
      if (parsed.length > 0) {
        quizQuestions = parsed; quizIndex = 0; quizScore = 0; quizTotal = parsed.length;
        updateScoreLabel(); renderQuizQuestion();
      } else {
        showQuizError('Could not parse quiz. Try again after completing a lesson.');
      }
    } else { showQuizError(data.error || 'Unknown error'); }
  } catch(e) { showQuizError(e.message); }
  ['genQuizBtn','genQuizBtnHeader'].forEach(function(id){
    var b=document.getElementById(id); if(b){b.disabled=false;b.textContent=id==='genQuizBtnHeader'?'&#129504; Quiz':'New Quiz';}
  });
}

function showQuizError(msg) {
  quizPanel.innerHTML = '<div class="quiz-empty"><div class="quiz-empty-icon">&#9888;</div><h3>Error</h3><p>' + msg + '</p><button class="gen-quiz-btn" onclick="generateQuiz()">Retry</button></div>';
}

function parseQuizFromText(text) {
  var questions = [];
  var blocks = text.split(/\n(?=Q\d*:|Question\s*\d+:)/i);
  blocks.forEach(function(block) {
    var qm = block.match(/Q\d*:\s*([\s\S]+?)(?=\nA\))/i) || block.match(/Question\s*\d+:\s*([\s\S]+?)(?=\nA\))/i);
    if (!qm) return;
    var opts = {};
    ['A','B','C','D'].forEach(function(l) {
      var re = new RegExp(l + '\\)\\s*([\\s\\S]+?)(?=\\n[A-D]\\)|Answer:|$)', 'i');
      var m = block.match(re); if (m) opts[l] = m[1].trim();
    });
    var am = block.match(/Answer:\s*([A-D])/i);
    var em = block.match(/Explanation:\s*([\s\S]+?)(?=\nQ|\nQuestion|$)/i);
    if (qm && am && Object.keys(opts).length >= 2) {
      questions.push({q: qm[1].trim(), opts: opts, ans: am[1].toUpperCase(), exp: em ? em[1].trim() : ''});
    }
  });
  return questions;
}

function renderQuizQuestion() {
  if (quizIndex >= quizQuestions.length) { renderQuizResult(); return; }
  var q = quizQuestions[quizIndex];
  var pct = quizTotal > 0 ? Math.round(quizScore / quizTotal * 100) : 0;
  var frag = document.createDocumentFragment();

  var sb = document.createElement('div');
  sb.className = 'score-bar';
  sb.innerHTML = '<div><div class="score-label">Score</div><div class="score-val">' + quizScore + '/' + quizTotal + '</div></div><div class="score-pct">' + pct + '%</div>';
  frag.appendChild(sb);

  var card = document.createElement('div');
  card.className = 'q-card'; card.id = 'qCard';

  var qnum = document.createElement('div');
  qnum.className = 'q-num';
  qnum.textContent = 'Question ' + (quizIndex + 1) + ' of ' + quizQuestions.length;
  card.appendChild(qnum);

  var qtext = document.createElement('div');
  qtext.className = 'q-text';
  qtext.innerHTML = renderBoardHTML(q.q);
  card.appendChild(qtext);

  var qopts = document.createElement('div');
  qopts.className = 'q-options';
  ['A','B','C','D'].forEach(function(l) {
    if (!q.opts[l]) return;
    var btn = document.createElement('button');
    btn.className = 'q-opt'; btn.id = 'opt' + l;
    btn.innerHTML = '<span class="opt-letter">' + l + '</span><span>' + renderBoardHTML(q.opts[l]) + '</span>';
    btn.addEventListener('click', function() { answerQuiz(l); });
    qopts.appendChild(btn);
  });
  card.appendChild(qopts);

  var fb = document.createElement('div'); fb.id = 'qFeedback';
  card.appendChild(fb);
  frag.appendChild(card);
  quizPanel.innerHTML = '';
  quizPanel.appendChild(frag);
}

function answerQuiz(letter) {
  var q = quizQuestions[quizIndex];
  var correct = letter === q.ans;
  if (correct) { quizScore++; bumpStreak(); addXP(15, '&#9989;'); burst('&#127881;'); }
  else { streak = 0; document.getElementById('streakBadge').style.display = 'none'; burst('&#128128;'); }
  updateScoreLabel();
  ['A','B','C','D'].forEach(function(l) {
    var el = document.getElementById('opt' + l); if (!el) return;
    el.disabled = true;
    if (l === q.ans) el.classList.add('correct');
    else if (l === letter && !correct) el.classList.add('wrong');
  });
  var fb = document.getElementById('qFeedback');
  if (fb) {
    fb.className = 'q-feedback ' + (correct ? 'correct' : 'wrong');
    fb.innerHTML = correct
      ? '<strong>Correct! &#9989;</strong> ' + (q.exp || 'Well done!')
      : '<strong>Not quite. &#10060;</strong> The correct answer is <strong>' + q.ans + '</strong>. ' + renderBoardHTML(q.exp || '');
  }
  var card = document.getElementById('qCard');
  if (card) {
    var nb = document.createElement('button');
    nb.className = 'q-next-btn';
    nb.textContent = quizIndex + 1 < quizQuestions.length ? 'Next Question \u2192' : 'See Results';
    nb.onclick = function() { quizIndex++; renderQuizQuestion(); };
    card.appendChild(nb);
  }
}

function renderQuizResult() {
  var pct = Math.round(quizScore / quizTotal * 100);
  var emoji = pct >= 80 ? '&#127881;' : pct >= 60 ? '&#128077;' : '&#128170;';
  var msg = pct >= 80 ? 'Excellent work! You nailed it.' : pct >= 60 ? 'Good effort! Review the ones you missed.' : 'Keep practicing — you\'ll get there!';
  addXP(pct >= 80 ? 30 : pct >= 60 ? 15 : 5, 'Quiz done');
  if (pct >= 80) burst('&#127881;');
  quizPanel.innerHTML =
    '<div class="quiz-result">' +
    '<div style="font-size:40px">' + emoji + '</div>' +
    '<div class="big-score">' + quizScore + '/' + quizTotal + '</div>' +
    '<div style="font-size:13px;color:var(--text3)">' + pct + '% correct</div>' +
    '<div class="score-msg">' + msg + '</div>' +
    '<button class="retry-btn" onclick="generateQuiz()">New Quiz</button>' +
    '</div>';
}
</script>
</body>
</html>
""")

with open(path, 'w', encoding='utf-8') as f:
    f.write(''.join(parts))
print('Done!')
