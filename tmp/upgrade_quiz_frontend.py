import sys

path = r'c:\Users\danie\Downloads\UNIXA-main\materials\templates\materials\quiz.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# ═══════════════════════════════════════════════════
# 1. INJECT NEW CSS before </style>
# ═══════════════════════════════════════════════════
new_css = """
    /* ── Difficulty Selector ── */
    .difficulty-selector {
        display: flex; gap: 8px; margin-top: 1.25rem; justify-content: center;
    }
    .diff-btn {
        flex: 1; padding: 10px 8px; background: var(--surface2);
        border: 1.5px solid var(--border); border-radius: 12px;
        color: var(--text2); font-size: 11px; font-weight: 700;
        text-align: center; cursor: pointer; transition: all 0.2s;
        font-family: inherit; text-transform: uppercase; letter-spacing: 0.05em;
    }
    .diff-btn:hover { border-color: var(--acc); color: var(--text); }
    .diff-btn.active { border-color: var(--acc); background: rgba(249,115,22,0.1); color: var(--acc); }
    .diff-label { font-size: 10px; font-weight: 600; display: block; margin-top: 2px; opacity: 0.6; text-transform: none; letter-spacing: 0; }

    /* ── Confidence Slider ── */
    .confidence-overlay {
        position: fixed; inset: 0; background: rgba(0,0,0,0.7);
        backdrop-filter: blur(8px); z-index: 6000;
        display: none; align-items: center; justify-content: center;
    }
    .confidence-overlay.open { display: flex; }
    .confidence-card {
        background: var(--surface); border: 1px solid var(--border2);
        border-radius: 20px; padding: 2rem 2.5rem; max-width: 380px; width: 90%;
        text-align: center; animation: confSlide 0.3s ease;
    }
    @keyframes confSlide { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    .confidence-title { font-size: 1rem; font-weight: 700; margin-bottom: 0.25rem; }
    .confidence-sub { font-size: 0.8125rem; color: var(--text2); margin-bottom: 1.5rem; }
    .confidence-dots {
        display: flex; gap: 12px; justify-content: center; margin-bottom: 1.5rem;
    }
    .conf-dot {
        width: 44px; height: 44px; border-radius: 50%;
        border: 2px solid var(--border2); background: var(--surface2);
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem; font-weight: 800; color: var(--text2);
        cursor: pointer; transition: all 0.2s; font-family: inherit;
    }
    .conf-dot:hover { border-color: var(--acc); color: var(--acc); transform: scale(1.1); }
    .conf-dot.selected { border-color: var(--acc); background: var(--acc); color: #fff; transform: scale(1.15); }
    .conf-labels { display: flex; justify-content: space-between; font-size: 10px; color: var(--text3); margin-bottom: 1rem; }

    /* ── Trap Explanation ── */
    .trap-box {
        margin: 0 1.5rem 0.5rem; padding: 0.75rem 1rem; border-radius: 10px;
        background: rgba(245,158,11,0.07); border: 1px solid rgba(245,158,11,0.2);
        display: none; animation: trapFade 0.3s ease;
    }
    @keyframes trapFade { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    .trap-label {
        font-size: 0.6875rem; font-weight: 800; text-transform: uppercase;
        letter-spacing: 0.08em; color: var(--yellow); margin-bottom: 0.375rem;
    }
    .trap-text { font-size: 0.8125rem; color: #d4a574; line-height: 1.55; }
    .trap-type-badge {
        display: inline-block; font-size: 9px; font-weight: 800;
        text-transform: uppercase; letter-spacing: 0.08em;
        padding: 2px 8px; border-radius: 10px; margin-bottom: 6px;
        background: rgba(245,158,11,0.15); color: var(--yellow);
    }

    /* ── Remediation Bridge ── */
    .bridge-box {
        margin: 0 1.5rem 0.75rem; padding: 1rem; border-radius: 12px;
        background: rgba(59,130,246,0.06); border: 1px solid rgba(59,130,246,0.2);
        display: none; animation: trapFade 0.4s ease;
    }
    .bridge-label {
        font-size: 0.6875rem; font-weight: 800; text-transform: uppercase;
        letter-spacing: 0.08em; color: #60A5FA; margin-bottom: 0.5rem;
    }
    .bridge-q { font-size: 0.875rem; font-weight: 600; color: var(--text); margin-bottom: 0.75rem; line-height: 1.5; }
    .bridge-opts { display: flex; flex-direction: column; gap: 6px; }
    .bridge-opt {
        display: flex; align-items: center; gap: 8px;
        padding: 8px 10px; background: var(--surface2);
        border: 1.5px solid var(--border); border-radius: 8px;
        color: #aaa; font-size: 0.8125rem; cursor: pointer;
        transition: all 0.15s; font-family: inherit; text-align: left; width: 100%;
    }
    .bridge-opt:hover:not(:disabled) { border-color: #60A5FA; color: var(--text); }
    .bridge-opt:disabled { cursor: default; }
    .bridge-opt.b-correct { border-color: var(--green); background: rgba(34,197,94,0.08); color: #86efac; }
    .bridge-opt.b-wrong { border-color: var(--red); background: rgba(239,68,68,0.08); color: #fca5a5; }
    .bridge-opt-letter {
        width: 24px; height: 24px; border-radius: 50%;
        border: 1.5px solid var(--border2); display: flex;
        align-items: center; justify-content: center;
        font-size: 0.6875rem; font-weight: 700; flex-shrink: 0;
    }
    .bridge-result { margin-top: 0.75rem; font-size: 0.8125rem; color: #86efac; line-height: 1.5; display: none; }

    /* ── Mastery Analytics (Results) ── */
    .analytics-card {
        background: var(--surface); border: 1px solid var(--border2);
        border-radius: 20px; padding: 1.75rem 1.5rem; max-width: 480px;
        width: 100%; text-align: left;
    }
    .analytics-title {
        font-size: 0.75rem; font-weight: 800; text-transform: uppercase;
        letter-spacing: 0.1em; color: var(--text3); margin-bottom: 1rem;
    }
    .calibration-row {
        display: flex; align-items: center; gap: 12px;
        padding: 0.75rem 1rem; background: var(--surface2);
        border: 1px solid var(--border); border-radius: 12px;
        margin-bottom: 10px;
    }
    .cal-icon { font-size: 1.25rem; }
    .cal-info { flex: 1; }
    .cal-label { font-size: 0.75rem; color: var(--text2); }
    .cal-value { font-size: 1.125rem; font-weight: 800; }
    .cal-warn { font-size: 0.6875rem; color: var(--yellow); margin-top: 2px; }

    .error-breakdown { margin-top: 12px; }
    .error-row {
        display: flex; align-items: center; justify-content: space-between;
        padding: 8px 12px; border-bottom: 1px solid var(--border);
    }
    .error-row:last-child { border-bottom: none; }
    .error-type-name { font-size: 0.8125rem; font-weight: 600; color: var(--text); text-transform: capitalize; }
    .error-count {
        font-size: 0.75rem; font-weight: 800; color: var(--acc);
        background: rgba(249,115,22,0.1); padding: 2px 10px;
        border-radius: 10px;
    }

    .concept-mastery-list { margin-top: 12px; }
    .mastery-item {
        display: flex; align-items: center; gap: 10px;
        padding: 10px 12px; background: var(--surface2);
        border: 1px solid var(--border); border-radius: 12px;
        margin-bottom: 6px;
    }
    .mastery-bar-wrap { flex: 1; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
    .mastery-bar-fill { height: 100%; border-radius: 3px; transition: width 0.6s ease; }
    .mastery-name { font-size: 0.8125rem; font-weight: 600; color: var(--text); min-width: 100px; }
    .mastery-pct { font-size: 0.75rem; font-weight: 800; min-width: 36px; text-align: right; }
    .mastery-badge {
        font-size: 8px; font-weight: 800; text-transform: uppercase;
        padding: 2px 6px; border-radius: 8px; letter-spacing: 0.05em;
    }
"""

content = content.replace('</style>', new_css + '</style>')
print("1. Injected CSS")

# ═══════════════════════════════════════════════════
# 2. ADD DIFFICULTY SELECTOR after Custom Topic Input
# ═══════════════════════════════════════════════════
difficulty_html = """
      <!-- Difficulty Selector -->
      <div class="difficulty-selector">
        <button class="diff-btn" data-diff="casual" onclick="setDifficulty(this)">
          🎯 Casual<span class="diff-label">Recall & Definitions</span>
        </button>
        <button class="diff-btn active" data-diff="academic" onclick="setDifficulty(this)">
          📚 Academic<span class="diff-label">Application & Why</span>
        </button>
        <button class="diff-btn" data-diff="mastery" onclick="setDifficulty(this)">
          🧠 Mastery<span class="diff-label">Synthesis & Reasoning</span>
        </button>
      </div>
"""

# Insert after the custom-topic-wrap closing div
content = content.replace(
    """      <div class="idle-chips" style="margin-top: 1.5rem;">""",
    difficulty_html + """      <div class="idle-chips" style="margin-top: 1.5rem;">"""
)
print("2. Added Difficulty Selector")

# ═══════════════════════════════════════════════════
# 3. ADD CONFIDENCE OVERLAY before </body>
# ═══════════════════════════════════════════════════
confidence_html = """
<!-- Confidence Calibration Overlay -->
<div class="confidence-overlay" id="confidenceOverlay">
  <div class="confidence-card">
    <div class="confidence-title">How confident are you?</div>
    <div class="confidence-sub">Rate before seeing the answer</div>
    <div class="confidence-dots">
      <button class="conf-dot" data-conf="1" onclick="submitConfidence(1)">1</button>
      <button class="conf-dot" data-conf="2" onclick="submitConfidence(2)">2</button>
      <button class="conf-dot" data-conf="3" onclick="submitConfidence(3)">3</button>
      <button class="conf-dot" data-conf="4" onclick="submitConfidence(4)">4</button>
      <button class="conf-dot" data-conf="5" onclick="submitConfidence(5)">5</button>
    </div>
    <div class="conf-labels"><span>Guessing</span><span>Certain</span></div>
  </div>
</div>
"""

content = content.replace('</body>', confidence_html + '</body>')
print("3. Added Confidence Overlay")

# ═══════════════════════════════════════════════════
# 4. ADD TRAP + BRIDGE boxes after exp-box in question panel
# ═══════════════════════════════════════════════════
trap_bridge_html = """    <div class="trap-box" id="trapBox">
      <div class="trap-type-badge" id="trapTypeBadge"></div>
      <div class="trap-label">🔍 Common Trap</div>
      <div class="trap-text" id="trapText"></div>
    </div>
    <div class="bridge-box" id="bridgeBox">
      <div class="bridge-label">🌉 Bridge to Understanding</div>
      <div class="bridge-q" id="bridgeQ"></div>
      <div class="bridge-opts" id="bridgeOpts"></div>
      <div class="bridge-result" id="bridgeResult"></div>
    </div>"""

content = content.replace(
    """    <div class="q-footer">""",
    trap_bridge_html + """
    <div class="q-footer">"""
)
print("4. Added Trap + Bridge boxes")

# ═══════════════════════════════════════════════════
# 5. UPGRADE RESULTS SCREEN with analytics
# ═══════════════════════════════════════════════════
old_results = """<div class="results-btns">
      <button class="btn-primary" onclick="generate()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6"/><path d="M3.51 15a9 9 0 1 0 .49-3.5"/></svg>
        New Quiz
      </button>
      <button class="btn-ghost" onclick="reviewMode()">Review Answers</button>
    </div>
  </div>
</div>"""

new_results = """<div class="results-btns">
      <button class="btn-primary" onclick="generate()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6"/><path d="M3.51 15a9 9 0 1 0 .49-3.5"/></svg>
        New Quiz
      </button>
      <button class="btn-ghost" onclick="reviewMode()">Review Answers</button>
    </div>
  </div>
  <!-- Mastery Analytics Card -->
  <div class="analytics-card" id="analyticsCard" style="display:none;">
    <div class="analytics-title">🧠 Pattern Intelligence Report</div>
    
    <div class="calibration-row" id="calibrationRow">
      <div class="cal-icon">🎯</div>
      <div class="cal-info">
        <div class="cal-label">Confidence Calibration</div>
        <div class="cal-value" id="calScore">—</div>
        <div class="cal-warn" id="calWarn" style="display:none;"></div>
      </div>
    </div>
    
    <div class="analytics-title" style="margin-top:1rem;">Error Type Breakdown</div>
    <div class="error-breakdown" id="errorBreakdown"></div>
    
    <div class="analytics-title" style="margin-top:1rem;">Concept Mastery</div>
    <div class="concept-mastery-list" id="conceptMasteryList"></div>
  </div>
</div>"""

content = content.replace(old_results, new_results)
print("5. Upgraded Results Screen")

# ═══════════════════════════════════════════════════
# 6. REPLACE ENTIRE <script> BLOCK with new logic
# ═══════════════════════════════════════════════════
old_script_start = "<script>\nconst AJAX_URL"
old_script_end = "setTimeout(() => ModelPicker.load(MODELS_URL), 600);\n</script>"

script_start_idx = content.find("<script>\nconst AJAX_URL")
if script_start_idx == -1:
    # Try with \r\n
    script_start_idx = content.find("<script>\r\nconst AJAX_URL")

script_end_marker = "setTimeout(() => ModelPicker.load(MODELS_URL), 600);"
script_end_idx = content.find(script_end_marker)
if script_end_idx != -1:
    # Find the </script> after it
    close_script = content.find("</script>", script_end_idx)
    if close_script != -1:
        script_end_idx = close_script + len("</script>")

if script_start_idx == -1 or script_end_idx == -1:
    print(f"WARNING: Could not find script boundaries. Start: {script_start_idx}, End: {script_end_idx}")
    print("Attempting alternate approach...")
    # Try to just find <script> followed by const AJAX_URL
    import re
    m = re.search(r'<script>\s*\nconst AJAX_URL', content)
    if m:
        script_start_idx = m.start()
        print(f"Found script start at {script_start_idx}")

new_script = """<script>
const AJAX_URL = '{% url "quiz_ajax" material.pk %}';
const REPORT_URL = '{% url "quiz_report_ajax" material.pk %}';
const WIKI_URL = '{% url "wiki_image_ajax" %}';
const MODELS_URL = '{% url "ai_get_models" %}';
const CSRF     = '{{ csrf_token }}';
const MAT_TEXT = `{{ material.extracted_text|default:""|escapejs }}`;

let questions = [], idx = 0, score = 0, answered = 0, userAnswers = [];
let selectedDifficulty = 'academic';
let pendingChoice = null; // Holds chosen letter until confidence is submitted
let confidenceRatings = []; // Per-question confidence

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function setDifficulty(btn) {
  document.querySelectorAll('.diff-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  selectedDifficulty = btn.dataset.diff;
}

async function generate() {
  const selectedTopics = Array.from(document.querySelectorAll('input[name="selected_topic"]:checked')).map(cb => cb.value);
  const customTopic = document.getElementById('customTopicInput')?.value || '';

  showScreen('loadingScreen');
  document.getElementById('scoreChip').style.display = 'none';
  document.getElementById('progressCounter').textContent = '';
  try {
    const res = await fetch(AJAX_URL, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF, 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        model: NexaModel.current,
        topics: selectedTopics,
        custom_topic: customTopic,
        difficulty: selectedDifficulty
      })
    });
    const data = await res.json();
    if (data.success && data.questions && data.questions.length > 0) {
      questions = data.questions;
      idx = 0; score = 0; answered = 0; userAnswers = []; confidenceRatings = [];
      loadQ();
      showScreen('quizScreen');
    } else {
      document.getElementById('errorMsg').textContent = data.error || 'No questions could be generated.';
      showScreen('errorScreen');
    }
  } catch (e) {
    document.getElementById('errorMsg').textContent = 'Network error: ' + e.message;
    showScreen('errorScreen');
  }
}

// Show topic tray if concepts exist
document.addEventListener('DOMContentLoaded', () => {
    const tray = document.getElementById('topicTray');
    const items = document.querySelectorAll('.topic-item');
    if (items.length > 0 && tray) {
        tray.style.display = 'block';
    }
});

function loadQ() {
  const q = questions[idx];
  const total = questions.length;

  // topbar
  document.getElementById('progressCounter').textContent = `${idx + 1} / ${total}`;
  document.getElementById('progressFill').style.width = `${(idx / total) * 100}%`;
  document.getElementById('qCounter').textContent = `QUESTION ${idx + 1} OF ${total}`;
  document.getElementById('qText').textContent = q.q;

  if (answered > 0) {
    const chip = document.getElementById('scoreChip');
    chip.style.display = 'inline-block';
    chip.textContent = `${score} / ${answered}`;
  }

  // passage
  if (MAT_TEXT) {
    const chunk = 700, len = MAT_TEXT.length;
    const start = Math.max(0, Math.floor((idx / total) * len) - 100);
    document.getElementById('passageText').textContent =
      MAT_TEXT.substring(start, start + chunk).trim() + (len > chunk ? '\\u2026' : '');
  } else {
    document.getElementById('passageText').textContent = 'No passage available.';
  }

  // image reset
  document.getElementById('imgWrap').style.display = 'none';
  document.getElementById('imgSkeleton').style.display = 'block';
  fetchWikiImage(q.q);

  // options
  const wrap = document.getElementById('optionsWrap');
  wrap.innerHTML = '';
  Object.entries(q.opts).forEach(([letter, text]) => {
    const btn = document.createElement('button');
    btn.className = 'opt-btn';
    btn.dataset.letter = letter;
    btn.innerHTML = `<span class="opt-letter">${letter}</span><span>${text}</span>`;
    btn.onclick = () => onOptionClick(letter);
    wrap.appendChild(btn);
  });

  // reset state
  const exp = document.getElementById('expBox');
  exp.style.display = 'none'; exp.className = 'exp-box';
  document.getElementById('trapBox').style.display = 'none';
  document.getElementById('bridgeBox').style.display = 'none';
  document.getElementById('proceedBtn').disabled = true;
  document.getElementById('proceedBtn').textContent = idx < total - 1 ? 'Proceed' : 'Finish';
  document.getElementById('skipBtn').style.display = 'inline-block';

  document.getElementById('passagePanel').scrollTop = 0;
  document.getElementById('qBody').scrollTop = 0;
}

// ── Confidence Flow ──
function onOptionClick(letter) {
  pendingChoice = letter;
  // Show confidence overlay
  document.querySelectorAll('.conf-dot').forEach(d => d.classList.remove('selected'));
  document.getElementById('confidenceOverlay').classList.add('open');
}

function submitConfidence(level) {
  document.querySelectorAll('.conf-dot').forEach(d => d.classList.remove('selected'));
  document.querySelector(`.conf-dot[data-conf="${level}"]`).classList.add('selected');
  confidenceRatings[idx] = level;
  
  setTimeout(() => {
    document.getElementById('confidenceOverlay').classList.remove('open');
    pick(pendingChoice, level);
    pendingChoice = null;
  }, 250);
}

function pick(chosen, confidence) {
  const q = questions[idx];
  const correct = q.ans;
  document.querySelectorAll('.opt-btn').forEach(b => {
    b.disabled = true;
    if (b.dataset.letter === correct) b.classList.add('correct');
    if (b.dataset.letter === chosen && chosen !== correct) b.classList.add('wrong');
  });

  const isRight = chosen === correct;
  answered++;
  if (isRight) score++;
  
  // Determine error type for wrong answers
  let errorType = 'unknown';
  if (!isRight && q.traps && q.traps[chosen]) {
    errorType = q.traps[chosen].error_type || 'unknown';
  }
  
  userAnswers[idx] = { chosen, correct, isRight, confidence: confidence || 3, concept: q.concept || 'General', error_type: errorType };

  const chip = document.getElementById('scoreChip');
  chip.style.display = 'inline-block';
  chip.textContent = `${score} / ${answered}`;

  // Standard explanation
  const exp = document.getElementById('expBox');
  document.getElementById('expText').textContent =
    q.explanation || (isRight ? '' : `The correct answer is ${correct}: ${q.opts[correct]}`);

  if (!isRight) {
    exp.className = 'exp-box wrong-exp';
    document.getElementById('expLabel').textContent = `Correct answer: ${correct}`;
    exp.style.display = 'block';
    
    // ── Show Trap ──
    if (q.traps && q.traps[chosen]) {
      const trap = q.traps[chosen];
      const trapBox = document.getElementById('trapBox');
      document.getElementById('trapTypeBadge').textContent = (trap.error_type || 'error').replace('_', ' ');
      document.getElementById('trapText').textContent = trap.trap_explanation || '';
      trapBox.style.display = 'block';
    }
    
    // ── Show Remediation Bridge ──
    if (q.remediation && q.remediation.bridge_question) {
      const bridge = q.remediation;
      const bridgeBox = document.getElementById('bridgeBox');
      document.getElementById('bridgeQ').textContent = bridge.bridge_question;
      document.getElementById('bridgeResult').style.display = 'none';
      
      const optsWrap = document.getElementById('bridgeOpts');
      optsWrap.innerHTML = '';
      const bridgeOpts = bridge.bridge_options || {};
      Object.entries(bridgeOpts).forEach(([letter, text]) => {
        const btn = document.createElement('button');
        btn.className = 'bridge-opt';
        btn.innerHTML = `<span class="bridge-opt-letter">${letter}</span><span>${text}</span>`;
        btn.onclick = () => pickBridge(letter, bridge.bridge_answer, bridge.bridge_explanation);
        optsWrap.appendChild(btn);
      });
      bridgeBox.style.display = 'block';
    }
    
  } else if (q.explanation) {
    exp.className = 'exp-box right-exp';
    document.getElementById('expLabel').textContent = 'Correct!';
    exp.style.display = 'block';
  }

  document.getElementById('proceedBtn').disabled = false;
  document.getElementById('skipBtn').style.display = 'none';
}

function pickBridge(chosen, correctAns, explanation) {
  document.querySelectorAll('.bridge-opt').forEach(b => {
    b.disabled = true;
    const letter = b.querySelector('.bridge-opt-letter').textContent;
    if (letter === correctAns) b.classList.add('b-correct');
    if (letter === chosen && chosen !== correctAns) b.classList.add('b-wrong');
  });
  const result = document.getElementById('bridgeResult');
  if (chosen === correctAns) {
    result.innerHTML = `<span style="color:#86efac;">✓ Correct!</span> ${explanation || ''}`;
  } else {
    result.innerHTML = `<span style="color:#fca5a5;">✗ Not quite.</span> The answer is <strong>${correctAns}</strong>. ${explanation || ''}`;
  }
  result.style.display = 'block';
}

function proceed() {
  if (idx < questions.length - 1) { idx++; loadQ(); }
  else showResults();
}

function skip() {
  userAnswers[idx] = { chosen: null, correct: questions[idx].ans, isRight: false, confidence: 0, concept: questions[idx].concept || 'General', error_type: 'guessing' };
  confidenceRatings[idx] = 0;
  answered++;
  if (idx < questions.length - 1) { idx++; loadQ(); }
  else showResults();
}

async function showResults() {
  const total = questions.length;
  const pct = Math.round((score / total) * 100);
  document.getElementById('resultsPct').textContent = pct + '%';
  document.getElementById('resultsTitle').textContent =
    pct >= 80 ? '🎉 Excellent work!' : pct >= 60 ? '👍 Good effort!' : '📚 Keep studying!';
  document.getElementById('resultsSub').textContent = `You scored ${score} out of ${total} questions.`;
  const ring = document.getElementById('resultsRing');
  const pctEl = document.getElementById('resultsPct');
  if (pct >= 80) { ring.style.borderColor = 'var(--green)'; pctEl.style.color = 'var(--green)'; }
  else if (pct >= 60) { ring.style.borderColor = 'var(--yellow)'; pctEl.style.color = 'var(--yellow)'; }
  else { ring.style.borderColor = 'var(--red)'; pctEl.style.color = '#f87171'; }
  document.getElementById('progressFill').style.width = '100%';
  showScreen('resultsScreen');
  
  // ── Send analytics to backend ──
  try {
    const reportRes = await fetch(REPORT_URL, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF, 'Content-Type': 'application/json' },
      body: JSON.stringify({ results: userAnswers })
    });
    const report = await reportRes.json();
    if (report.success) {
      renderAnalytics(report);
    }
  } catch(e) {
    console.warn('Analytics report failed:', e);
  }
}

function renderAnalytics(report) {
  const card = document.getElementById('analyticsCard');
  card.style.display = 'block';
  
  // Calibration
  const calScore = report.calibration_score || 0;
  const calEl = document.getElementById('calScore');
  calEl.textContent = calScore + '%';
  calEl.style.color = calScore >= 70 ? 'var(--green)' : calScore >= 40 ? 'var(--yellow)' : 'var(--red)';
  
  const calWarn = document.getElementById('calWarn');
  if (calScore < 50) {
    calWarn.textContent = '⚠ Overconfidence detected — you were confident on wrong answers.';
    calWarn.style.display = 'block';
  } else if (calScore >= 80) {
    calWarn.textContent = '✓ Well calibrated — your confidence matches your accuracy.';
    calWarn.style.color = 'var(--green)';
    calWarn.style.display = 'block';
  }
  
  // Error breakdown
  const errDiv = document.getElementById('errorBreakdown');
  errDiv.innerHTML = '';
  const errors = report.error_breakdown || {};
  if (Object.keys(errors).length === 0) {
    errDiv.innerHTML = '<div style="padding:12px;color:var(--green);font-size:0.8125rem;">✓ No errors detected — perfect score!</div>';
  } else {
    const errLabels = {
      misconception: '🔴 Misconception — Believes wrong rule',
      partial_confusion: '🟠 Partial Confusion — Missing key detail',
      misapplied_rule: '🟡 Misapplied Rule — Wrong context',
      calculation: '🔵 Calculation — Step/arithmetic error',
      recall: '⚪ Recall — Forgot the fact',
      guessing: '⚫ Guessing — No strategy used'
    };
    Object.entries(errors).forEach(([type, count]) => {
      const row = document.createElement('div');
      row.className = 'error-row';
      row.innerHTML = `<span class="error-type-name">${errLabels[type] || type}</span><span class="error-count">${count}x</span>`;
      errDiv.appendChild(row);
    });
  }
  
  // Concept mastery
  const masteryDiv = document.getElementById('conceptMasteryList');
  masteryDiv.innerHTML = '';
  const mastery = report.concept_mastery || {};
  Object.entries(mastery).forEach(([name, data]) => {
    const acc = data.accuracy || 0;
    const color = acc >= 80 ? 'var(--green)' : acc >= 50 ? 'var(--yellow)' : 'var(--red)';
    const item = document.createElement('div');
    item.className = 'mastery-item';
    item.innerHTML = `
      <span class="mastery-name">${name}</span>
      <div class="mastery-bar-wrap"><div class="mastery-bar-fill" style="width:${acc}%;background:${color};"></div></div>
      <span class="mastery-pct" style="color:${color};">${acc}%</span>
      ${data.overconfident > 0 ? '<span class="mastery-badge" style="background:rgba(245,158,11,0.15);color:var(--yellow);">⚠ Overconfident</span>' : ''}
    `;
    masteryDiv.appendChild(item);
  });
}

function reviewMode() {
  idx = 0; loadQ();
  setTimeout(() => { const ua = userAnswers[0]; if (ua && ua.chosen) pick(ua.chosen, ua.confidence); }, 50);
  showScreen('quizScreen');
}

async function fetchWikiImage(questionText) {
  const stopwords = /\\b(which|what|how|why|where|when|who|the|a|an|of|is|are|was|were|in|on|at|to|for|with|that|this|does|do|did|following|both|between|relates|condition|conditions)\\b/gi;
  let kw = questionText.replace(/\\?/g, '').replace(stopwords, ' ').replace(/\\s+/g, ' ').trim();
  kw = kw.split(' ').slice(0, 4).join(' ');

  const imgWrap = document.getElementById('imgWrap');
  const imgEl   = document.getElementById('passageImg');
  const cap     = document.getElementById('imgCaption');
  const skel    = document.getElementById('imgSkeleton');

  if (!kw) { skel.style.display = 'none'; return; }

  try {
    const res = await fetch(WIKI_URL, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF, 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: kw })
    });
    const data = await res.json();
    skel.style.display = 'none';
    if (data.image_url) {
      imgEl.src = data.image_url;
      cap.textContent = `Wikipedia: ${data.title}`;
      imgWrap.style.display = 'block';
    }
  } catch {
    skel.style.display = 'none';
  }
}

generate();
// Preload models
setTimeout(() => ModelPicker.load(MODELS_URL), 600);
</script>"""

if script_start_idx != -1 and script_end_idx != -1:
    content = content[:script_start_idx] + new_script + content[script_end_idx:]
    print("6. Replaced entire script block")
else:
    print(f"ERROR: Could not find script block. Indices: {script_start_idx}, {script_end_idx}")

# Write the file
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\\nDone! Frontend fully upgraded.")
