/* workspace.js — all workspace page JS, loaded as a static file */
/* WS_ID, CSRF, MY_USERNAME, IS_ADMIN are set inline in the template before this file loads */

// ── Utilities ────────────────────────────────────────────────────────────────
function esc(s) {
  var d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

function toast(msg, color, dur) {
  color = color || '#22c55e';
  dur = dur || 3000;
  var t = document.getElementById('wsToast');
  if (!t) return;
  t.textContent = msg;
  t.style.background = color;
  t.classList.add('show');
  setTimeout(function() { t.classList.remove('show'); }, dur);
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

// ── Panel navigation ─────────────────────────────────────────────────────────
function showPanel(name, navEl) {
  document.querySelectorAll('.ws-panel').forEach(function(p) { p.classList.remove('active'); });
  document.querySelectorAll('.ws-nav-item').forEach(function(n) { n.classList.remove('active'); });
  document.querySelectorAll('.ws-mob-tab').forEach(function(n) { n.classList.remove('active'); });
  var panel = document.getElementById('panel-' + name);
  if (panel) panel.classList.add('active');
  if (navEl && navEl.classList.contains('ws-nav-item')) {
    navEl.classList.add('active');
  } else {
    var n = document.getElementById('nav-' + name);
    if (n) n.classList.add('active');
  }
  if (navEl && navEl.classList.contains('ws-mob-tab')) {
    navEl.classList.add('active');
  } else {
    var m = document.getElementById('mob-nav-' + name);
    if (m) m.classList.add('active');
  }
  if (name === 'dashboard') loadDashboard();
}

function toggleSidebar() {
  var sb = document.getElementById('wsSidebar');
  var ov = document.getElementById('sidebarOverlay');
  if (sb) sb.classList.toggle('open');
  if (ov) ov.classList.toggle('open');
}

// ── Chat state ────────────────────────────────────────────────────────────────
var replyToId = null;
var lastMsgTime = '';
var _mediaRec = null;
var _audioChunks = [];
var _voiceTimerInterval = null;
var _voiceSeconds = 0;
var _voiceBlob = null;
var _voiceCancelled = false;

function sendChatMsg() {
  var input = document.getElementById('chatInput');
  var content = input ? input.value.trim() : '';
  var fileInput = document.getElementById('chatFileInput');
  if (!content && (!fileInput || !fileInput.files.length)) {
    toast('Type a message first', '#ef4444', 2000);
    return;
  }
  var fd = new FormData();
  if (content) fd.append('content', content);
  if (fileInput && fileInput.files.length) fd.append('file', fileInput.files[0]);
  if (replyToId) fd.append('reply_to_id', replyToId);
  fd.append('csrfmiddlewaretoken', CSRF);
  if (input) { input.value = ''; input.style.height = 'auto'; }
  clearReply();
  clearMedia();
  if (fileInput) fileInput.value = '';
  fetch('/community/workspaces/' + WS_ID + '/chat/', { method: 'POST', body: fd })
    .then(function(r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(function(data) {
      if (data.error) { toast(data.error, '#ef4444'); return; }
      appendMsg(data, true);
    })
    .catch(function(err) { toast('Send failed: ' + err.message, '#ef4444'); });
}

function chatKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMsg(); }
}

function clearReply() {
  replyToId = null;
  var bar = document.getElementById('replyBar');
  if (bar) bar.style.display = 'none';
}

function clearMedia() {
  var prev = document.getElementById('mediaPreview');
  if (prev) prev.style.display = 'none';
}

function onChatFileSelect(input) {
  if (input.files.length) {
    var prev = document.getElementById('mediaPreview');
    var name = document.getElementById('mediaPreviewName');
    if (prev) prev.style.display = 'flex';
    if (name) name.textContent = '📎 ' + input.files[0].name;
  }
}

function updateActionBtn() { /* both buttons always visible */ }

// ── Voice recording ───────────────────────────────────────────────────────────
function onMicBtn() {
  if (_voiceBlob) { sendVoiceMsg(); return; }
  if (_mediaRec && _mediaRec.state === 'recording') { stopVoice(); return; }
  startVoice();
}

function startVoice() {
  navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
    _audioChunks = [];
    _voiceCancelled = false;
    _mediaRec = new MediaRecorder(stream);
    _mediaRec.ondataavailable = function(e) {
      if (e.data && e.data.size > 0) _audioChunks.push(e.data);
    };
    _mediaRec.onstop = function() {
      if (_voiceCancelled) { _voiceCancelled = false; return; }
      showVoicePreview();
    };
    _mediaRec.start(100);
    var btn = document.getElementById('btnMic');
    if (btn) { btn.classList.add('recording'); btn.style.background = '#dc2626'; }
    var bar = document.getElementById('voiceBar');
    if (bar) bar.classList.add('active');
    _voiceSeconds = 0;
    _voiceTimerInterval = setInterval(function() {
      _voiceSeconds++;
      var m = Math.floor(_voiceSeconds / 60), s = _voiceSeconds % 60;
      var timer = document.getElementById('voiceTimer');
      if (timer) timer.textContent = m + ':' + (s < 10 ? '0' : '') + s;
    }, 1000);
  }).catch(function() { alert('Microphone access denied.'); });
}

function stopVoice() {
  if (!_mediaRec) return;
  clearInterval(_voiceTimerInterval);
  _mediaRec.stop();
  _mediaRec.stream.getTracks().forEach(function(t) { t.stop(); });
  var btn = document.getElementById('btnMic');
  if (btn) { btn.classList.remove('recording'); btn.style.background = '#25d366'; }
  var bar = document.getElementById('voiceBar');
  if (bar) bar.classList.remove('active');
}

function cancelVoice() {
  if (!_mediaRec) return;
  _voiceCancelled = true;
  clearInterval(_voiceTimerInterval);
  _mediaRec.stop();
  _mediaRec.stream.getTracks().forEach(function(t) { t.stop(); });
  _mediaRec = null; _audioChunks = [];
  var btn = document.getElementById('btnMic');
  if (btn) { btn.classList.remove('recording'); btn.style.background = '#25d366'; }
  var bar = document.getElementById('voiceBar');
  if (bar) bar.classList.remove('active');
}

function showVoicePreview() {
  if (!_audioChunks.length) return;
  _voiceBlob = new Blob(_audioChunks, { type: 'audio/webm' });
  var url = URL.createObjectURL(_voiceBlob);
  var audio = document.getElementById('voicePreviewAudio');
  if (audio) audio.src = url;
  var bar = document.getElementById('voicePreviewBar');
  if (bar) bar.classList.add('active');
}

function discardVoice() {
  _voiceBlob = null; _audioChunks = [];
  var audio = document.getElementById('voicePreviewAudio');
  if (audio) { if (audio.src) URL.revokeObjectURL(audio.src); audio.src = ''; }
  var bar = document.getElementById('voicePreviewBar');
  if (bar) bar.classList.remove('active');
}

function sendVoiceMsg() {
  if (!_voiceBlob) return;
  var fd = new FormData();
  fd.append('file', _voiceBlob, 'voice_' + Date.now() + '.webm');
  fd.append('content', 'Voice message');
  fd.append('csrfmiddlewaretoken', CSRF);
  if (replyToId) fd.append('reply_to_id', replyToId);
  fetch('/community/workspaces/' + WS_ID + '/chat/', { method: 'POST', body: fd })
    .then(function(r) { return r.json(); })
    .then(function(data) { if (!data.error) appendMsg(data, true); })
    .catch(function() {});
  discardVoice();
  _mediaRec = null; _audioChunks = [];
  clearReply();
}

// ── Voice note playback ───────────────────────────────────────────────────────
function vnFmt(s) {
  if (!isFinite(s)) return '0:00';
  var m = Math.floor(s / 60), sec = Math.floor(s % 60);
  return m + ':' + (sec < 10 ? '0' : '') + sec;
}

function vnToggle(id) {
  var audio = document.getElementById(id + '-audio');
  var icon = document.getElementById(id + '-icon');
  if (!audio) return;
  if (audio.paused) {
    document.querySelectorAll('.vn-bubble audio').forEach(function(a) {
      if (a !== audio) { a.pause(); vnEnded(a.id.replace('-audio', '')); }
    });
    audio.play();
    if (icon) icon.innerHTML = '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>';
  } else {
    audio.pause();
    if (icon) icon.innerHTML = '<polygon points="5,3 19,12 5,21"/>';
  }
}

function vnMeta(id) {
  var audio = document.getElementById(id + '-audio');
  var dur = document.getElementById(id + '-dur');
  if (audio && isFinite(audio.duration) && dur) dur.textContent = vnFmt(audio.duration);
}

function vnTick(id) {
  var audio = document.getElementById(id + '-audio');
  if (!audio || !audio.duration) return;
  var pct = audio.currentTime / audio.duration;
  var wave = document.getElementById(id + '-wave');
  var dot = document.getElementById(id + '-dot');
  var dur = document.getElementById(id + '-dur');
  if (!wave) return;
  var bars = wave.querySelectorAll('.vn-bar');
  var ww = wave.offsetWidth - 10;
  if (dot) dot.style.left = (pct * ww) + 'px';
  var played = Math.round(pct * bars.length);
  bars.forEach(function(b, i) { b.classList.toggle('played', i < played); });
  if (dur) dur.textContent = vnFmt(audio.currentTime);
}

function vnSeek(e, id) {
  var audio = document.getElementById(id + '-audio');
  var wave = document.getElementById(id + '-wave');
  if (!audio || !audio.duration || !wave) return;
  var rect = wave.getBoundingClientRect();
  var pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  audio.currentTime = pct * audio.duration;
}

function vnEnded(id) {
  var icon = document.getElementById(id + '-icon');
  var wave = document.getElementById(id + '-wave');
  var dot = document.getElementById(id + '-dot');
  var audio = document.getElementById(id + '-audio');
  var dur = document.getElementById(id + '-dur');
  if (icon) icon.innerHTML = '<polygon points="5,3 19,12 5,21"/>';
  if (wave) wave.querySelectorAll('.vn-bar').forEach(function(b) { b.classList.remove('played'); });
  if (dot) dot.style.left = '0px';
  if (audio && dur) dur.textContent = vnFmt(audio.duration || 0);
}

function buildVoiceBubble(src) {
  var bars = '';
  for (var i = 0; i < 30; i++) {
    var h = 8 + Math.round(Math.abs(Math.sin(i * 0.7 + 1) * 16));
    bars += '<div class="vn-bar" style="height:' + h + 'px" data-idx="' + i + '"></div>';
  }
  var id = 'vn-' + Date.now() + '-' + Math.random().toString(36).slice(2, 6);
  return '<div class="vn-bubble" id="' + id + '">' +
    '<button class="vn-play" onclick="vnToggle(\'' + id + '\')">' +
    '<svg id="' + id + '-icon" viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21"/></svg>' +
    '</button>' +
    '<div class="vn-body">' +
    '<div class="vn-waveform" id="' + id + '-wave" onclick="vnSeek(event,\'' + id + '\')">' +
    bars +
    '<div class="vn-scrubber" id="' + id + '-dot" style="left:0px"></div>' +
    '</div>' +
    '<div class="vn-footer"><span class="vn-duration" id="' + id + '-dur">0:00</span></div>' +
    '</div>' +
    '<audio id="' + id + '-audio" src="' + src + '" preload="metadata"' +
    ' ontimeupdate="vnTick(\'' + id + '\')"' +
    ' onloadedmetadata="vnMeta(\'' + id + '\')"' +
    ' onended="vnEnded(\'' + id + '\')"></audio>' +
    '</div>';
}

// ── Append message to chat ────────────────────────────────────────────────────
function appendMsg(data, mine) {
  var msgs = document.getElementById('chatMessages');
  if (!msgs) return;
  var div = document.createElement('div');
  div.className = 'chat-msg' + (mine ? ' mine' : (data.is_ai ? ' ai-msg' : ''));
  div.id = 'msg-' + data.id;
  var time = new Date(data.created_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  var tick = mine ? '<span class="chat-tick"><svg viewBox="0 0 16 11" fill="none"><path d="M1 5.5l3.5 3.5L10 2" stroke="#53bdeb" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M5 5.5l3.5 3.5L14 2" stroke="#53bdeb" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span>' : '';
  var avatarHtml = '';
  if (!mine) {
    if (data.is_ai) {
      avatarHtml = '<div class="chat-avatar" style="background:#7c3aed"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" style="width:13px;height:13px"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg></div>';
    } else {
      avatarHtml = '<div class="chat-avatar">' + (data.sender_avatar ? '<img src="' + data.sender_avatar + '" alt="">' : esc((data.sender || '?')[0].toUpperCase())) + '</div>';
    }
  }
  var senderHtml = '';
  if (!mine) {
    senderHtml = data.is_ai ? '<div class="chat-sender" style="color:#7c3aed">Nexa AI</div>' : '<div class="chat-sender">' + esc(data.sender) + '</div>';
  }
  var replyHtml = '';
  if (data.reply_preview) {
    replyHtml = '<div class="chat-reply-preview">' + esc(data.reply_preview.sender) + ': ' + esc(data.reply_preview.content) + '</div>';
  }
  var mediaHtml = '';
  if (data.media_url) {
    var n = (data.media_name || '').toLowerCase();
    if (n.slice(-5) === '.webm' || n.slice(-4) === '.mp3' || n.slice(-4) === '.ogg') {
      mediaHtml = buildVoiceBubble(data.media_url);
    } else {
      mediaHtml = '<a class="chat-media-link" href="' + data.media_url + '" target="_blank">📎 ' + esc(data.media_name) + '</a>';
    }
  }
  var isVoice = !!(data.media_url && (data.media_name || '').toLowerCase().match(/\.(webm|mp3|ogg)$/));
  var rawContent = data.is_ai ? esc(data.content).replace(/^\[AI\]/, '') : esc(data.content);
  var content = isVoice ? '' : rawContent;
  div.innerHTML = avatarHtml + '<div class="chat-bubble-wrap">' + senderHtml + replyHtml + '<div class="chat-bubble">' + content + mediaHtml + '<div class="chat-meta">' + time + tick + '</div></div></div>';
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  if (data.created_at) lastMsgTime = data.created_at;
}

function deleteMsg(id) {
  if (!confirm('Delete this message?')) return;
  var fd = new FormData();
  fd.append('csrfmiddlewaretoken', CSRF);
  fetch('/community/workspaces/' + WS_ID + '/chat/' + id + '/delete/', { method: 'POST', body: fd })
    .then(function(r) { return r.json(); })
    .then(function(d) { if (d.ok) { var el = document.getElementById('msg-' + id); if (el) el.remove(); } });
}

function pollChat() {
  var params = lastMsgTime ? '?since=' + encodeURIComponent(lastMsgTime) : '';
  fetch('/community/workspaces/' + WS_ID + '/poll/' + params)
    .then(function(r) { return r.json(); })
    .then(function(data) {
      (data.messages || []).forEach(function(m) {
        if (!document.getElementById('msg-' + m.id)) appendMsg(m, m.is_mine);
      });
    }).catch(function() {});
}

// ── Files ─────────────────────────────────────────────────────────────────────
function uploadFile(input) {
  if (!input.files.length) return;
  var fd = new FormData();
  fd.append('file', input.files[0]);
  fd.append('csrfmiddlewaretoken', CSRF);
  toast('Uploading...', '#6366f1');
  fetch('/community/workspaces/' + WS_ID + '/files/', { method: 'POST', body: fd })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.error) { toast(data.error, '#ef4444'); return; }
      addFileCard(data);
      toast('File uploaded. Analyzing...', '#6366f1');
      analyzeFiles(data.name);
    }).catch(function() { toast('Upload failed', '#ef4444'); });
  input.value = '';
}

function onFileDrop(e) {
  e.preventDefault();
  var zone = document.getElementById('uploadZone');
  if (zone) zone.classList.remove('drag-over');
  var file = e.dataTransfer.files[0];
  if (!file) return;
  var fd = new FormData();
  fd.append('file', file);
  fd.append('csrfmiddlewaretoken', CSRF);
  toast('Uploading...', '#6366f1');
  fetch('/community/workspaces/' + WS_ID + '/files/', { method: 'POST', body: fd })
    .then(function(r) { return r.json(); })
    .then(function(data) { if (!data.error) { addFileCard(data); analyzeFiles(data.name); } })
    .catch(function() {});
}

function addFileCard(data) {
  var grid = document.getElementById('fileGrid');
  if (!grid) return;
  var empty = grid.querySelector('.empty-state');
  if (empty && empty.parentElement) empty.parentElement.remove();
  var card = document.createElement('div');
  card.className = 'file-card';
  card.id = 'file-' + data.id;
  card.innerHTML = '<div class="file-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>' +
    '<div class="file-name" title="' + esc(data.name) + '">' + esc(data.name) + '</div>' +
    '<div class="file-meta">' + esc(data.uploaded_by) + ' · just now</div>' +
    '<div class="file-actions"><a href="' + data.url + '" target="_blank" class="btn-ws btn-ws-ghost btn-ws-sm">Download</a>' +
    '<button class="btn-ws btn-ws-danger btn-ws-sm" onclick="deleteFile(\'' + data.id + '\')">Delete</button></div>';
  grid.appendChild(card);
}

function deleteFile(id) {
  if (!confirm('Delete this file?')) return;
  var fd = new FormData();
  fd.append('csrfmiddlewaretoken', CSRF);
  fetch('/community/workspaces/' + WS_ID + '/files/' + id + '/delete/', { method: 'POST', body: fd })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.ok) { var el = document.getElementById('file-' + id); if (el) el.remove(); toast('File deleted', '#22c55e'); }
    });
}

function analyzeFiles(fileName) {
  var result = document.getElementById('aiAnalysisResult');
  if (!result) return;
  result.style.display = 'block';
  result.innerHTML = '<div class="ai-analysis-banner"><h4>Analyzing "' + esc(fileName) + '"...</h4><div class="loading-dots"><span></span><span></span><span></span></div></div>';
  fetch('/community/workspaces/' + WS_ID + '/ai/analyze/', { method: 'POST', headers: { 'X-CSRFToken': CSRF, 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
    .then(function(r) { return r.json(); })
    .then(function(data) { renderAnalysis(data); })
    .catch(function() { result.innerHTML = '<div class="ai-analysis-banner"><h4>Analysis failed</h4><p>You can still add tasks manually.</p></div>'; });
}

function renderAnalysis(data) {
  var result = document.getElementById('aiAnalysisResult');
  if (!result) return;
  if (data.error) { result.innerHTML = '<div class="ai-analysis-banner"><h4>Analysis Error</h4><p>' + esc(data.error) + '</p></div>'; return; }
  var html = '<div class="ai-analysis-banner"><h4>AI Analysis Complete</h4><p>' + esc(data.summary || data.overview || 'Analysis complete.') + '</p></div>';
  var tasks = data.suggested_tasks || data.tasks || [];
  if (tasks.length) {
    html += '<div style="margin-top:.75rem;"><div style="font-size:.8rem;font-weight:700;color:var(--ws-text2);margin-bottom:.5rem;">Suggested Tasks (' + tasks.length + ')</div>';
    tasks.forEach(function(t, i) {
      var title = typeof t === 'string' ? t : (t.title || t.task || String(t));
      var assignee = t.suggested_assignee || t.assignee || '';
      html += '<div class="ai-task-suggestion" id="ai-ts-' + i + '">' +
        '<div class="ai-task-suggestion-info"><div class="ai-task-suggestion-title">' + esc(title) + '</div>' +
        (assignee ? '<div class="ai-task-suggestion-meta">Suggested for @' + esc(assignee) + '</div>' : '') +
        '</div><button class="btn-ws btn-ws-primary btn-ws-sm" onclick="addSuggestedTask(' + i + ')">+ Assign</button></div>';
    });
    html += '<button class="btn-ws btn-ws-green btn-ws-sm" style="margin-top:.5rem;" onclick="addAllSuggestedTasks()">Assign All</button></div>';
    window._aiSuggestedTasks = tasks;
  }
  result.innerHTML = html;
}

function addSuggestedTask(idx) {
  var tasks = window._aiSuggestedTasks || [];
  var t = tasks[idx];
  if (!t) return;
  var title = typeof t === 'string' ? t : (t.title || t.task || String(t));
  var assignee = t.suggested_assignee || t.assignee || '';
  var btn = document.querySelector('#ai-ts-' + idx + ' .btn-ws-primary');
  if (btn) { btn.disabled = true; btn.textContent = 'Adding...'; }
  var fd = new FormData();
  fd.append('title', title);
  fd.append('csrfmiddlewaretoken', CSRF);
  if (assignee) fd.append('assigned_to', assignee);
  fetch('/community/workspaces/' + WS_ID + '/tasks/', { method: 'POST', body: fd })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (btn) { btn.textContent = 'Added'; }
      addTaskCard(data, 'todo');
      toast('Task added.', '#22c55e');
    }).catch(function() { if (btn) { btn.disabled = false; btn.textContent = '+ Assign'; } });
}

function addAllSuggestedTasks() {
  var tasks = window._aiSuggestedTasks || [];
  if (!tasks.length) return;
  Promise.all(tasks.map(function(t) {
    var title = typeof t === 'string' ? t : (t.title || t.task || String(t));
    var assignee = t.suggested_assignee || t.assignee || '';
    var fd = new FormData();
    fd.append('title', title);
    fd.append('csrfmiddlewaretoken', CSRF);
    if (assignee) fd.append('assigned_to', assignee);
    return fetch('/community/workspaces/' + WS_ID + '/tasks/', { method: 'POST', body: fd }).then(function(r) { return r.json(); });
  })).then(function(results) {
    results.forEach(function(d) { if (d.id) addTaskCard(d, 'todo'); });
    toast(results.length + ' tasks assigned.', '#22c55e', 4000);
    window._aiSuggestedTasks = [];
  });
}

// ── Tasks ─────────────────────────────────────────────────────────────────────
function toggleTaskForm() {
  var f = document.getElementById('taskAddForm');
  if (!f) return;
  f.style.display = f.style.display === 'none' ? 'block' : 'none';
  if (f.style.display === 'block') { var t = document.getElementById('taskTitle'); if (t) t.focus(); }
}

function addTask() {
  var titleEl = document.getElementById('taskTitle');
  var title = titleEl ? titleEl.value.trim() : '';
  if (!title) { toast('Title required', '#ef4444'); return; }
  var fd = new FormData();
  fd.append('title', title);
  fd.append('csrfmiddlewaretoken', CSRF);
  var assignee = document.getElementById('taskAssignee');
  var due = document.getElementById('taskDue');
  var desc = document.getElementById('taskDesc');
  if (assignee && assignee.value) fd.append('assigned_to', assignee.value);
  if (due && due.value) fd.append('due_date', due.value);
  if (desc && desc.value) fd.append('description', desc.value);
  fetch('/community/workspaces/' + WS_ID + '/tasks/', { method: 'POST', body: fd })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      addTaskCard(data, 'todo');
      if (titleEl) titleEl.value = '';
      if (desc) desc.value = '';
      if (due) due.value = '';
      toggleTaskForm();
      toast('Task added' + (data.assigned_to ? ' for @' + data.assigned_to : '') + '.', '#22c55e');
    }).catch(function() {});
}

function addTaskCard(data, col) {
  var colEl = document.getElementById('col-' + (col || data.status || 'todo'));
  if (!colEl) return;
  var card = document.createElement('div');
  card.className = 'task-card';
  card.id = 'task-' + data.id;
  card.onclick = function() { openTaskDetail(data.id, data.title, data.description || '', data.status || 'todo', data.assigned_to || '', data.due_date || '', data.review_status || 'none'); };
  var assigneeBadge = data.assigned_to ? '<span class="task-tag assignee">@' + esc(data.assigned_to) + '</span>' : '';
  var dueBadge = data.due_date ? '<span class="task-tag due">' + esc(data.due_date) + '</span>' : '';
  card.innerHTML = '<div class="task-card-title">' + esc(data.title) + '</div><div class="task-card-meta">' + assigneeBadge + dueBadge + '</div>';
  colEl.appendChild(card);
  updateTaskCounts();
}

function updateTaskCounts() {
  ['todo', 'doing', 'done'].forEach(function(s) {
    var col = document.getElementById('col-' + s);
    var cnt = document.getElementById('cnt-' + s);
    if (col && cnt) cnt.textContent = col.querySelectorAll('.task-card').length;
  });
  var total = document.querySelectorAll('.task-card').length;
  var badge = document.getElementById('task-count-badge');
  if (badge) { badge.textContent = total; badge.style.display = total ? '' : 'none'; }
  var mobBadge = document.getElementById('mob-task-badge');
  if (mobBadge) { mobBadge.textContent = total; mobBadge.style.display = total ? '' : 'none'; }
}

function openTaskDetail(id, title, desc, status, assignee, due, reviewStatus) {
  document.getElementById('worksheetTitle').textContent = title;
  document.getElementById('wsTaskDesc').textContent = desc || 'No description.';
  document.getElementById('wsTaskAssignee').textContent = assignee || 'Unassigned';
  document.getElementById('wsTaskDue').textContent = due || 'No due date';
  var statusEl = document.getElementById('wsTaskStatus');
  if (statusEl) { statusEl.textContent = status; statusEl.style.color = status === 'done' ? 'var(--ws-green)' : status === 'doing' ? 'var(--ws-yellow)' : 'var(--ws-text3)'; }
  var overlay = document.getElementById('worksheetOverlay');
  if (overlay) overlay.style.display = 'flex';
}

function closeTaskModal() {
  var overlay = document.getElementById('worksheetOverlay');
  if (overlay) overlay.style.display = 'none';
}

// ── Members ───────────────────────────────────────────────────────────────────
function toggleAddMember() {
  var f = document.getElementById('addMemberForm');
  if (!f) return;
  f.style.display = f.style.display === 'none' ? 'block' : 'none';
  if (f.style.display === 'block') { var s = document.getElementById('memberSearch'); if (s) s.focus(); }
}

var _searchTimer = null;
function searchUsers(q) {
  clearTimeout(_searchTimer);
  var res = document.getElementById('memberSearchResults');
  if (!res) return;
  if (q.length < 2) { res.innerHTML = ''; return; }
  _searchTimer = setTimeout(function() {
    fetch('/community/workspaces/users/search/?q=' + encodeURIComponent(q))
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (!data.users.length) { res.innerHTML = '<div style="font-size:.75rem;color:var(--ws-text3);">No users found.</div>'; return; }
        res.innerHTML = data.users.map(function(u) {
          return '<div style="display:flex;align-items:center;justify-content:space-between;padding:.375rem 0;border-bottom:1px solid var(--ws-border);">' +
            '<span style="font-size:.8rem;color:var(--ws-text);">' + esc(u.display) + ' <span style="color:var(--ws-text3);">@' + esc(u.username) + '</span></span>' +
            '<button class="btn-ws btn-ws-primary btn-ws-sm" onclick="addMember(\'' + esc(u.username) + '\')">Add</button></div>';
        }).join('');
      });
  }, 300);
}

function addMember(username) {
  var fd = new FormData();
  fd.append('username', username);
  fd.append('csrfmiddlewaretoken', CSRF);
  fetch('/community/workspaces/' + WS_ID + '/members/add/', { method: 'POST', body: fd })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.error) { toast(d.error, '#ef4444'); return; }
      toast(d.added ? '@' + username + ' added' : '@' + username + ' already a member', '#22c55e');
      if (d.added) { var res = document.getElementById('memberSearchResults'); if (res) res.innerHTML = ''; }
    });
}

function removeMember(userId, username) {
  if (!confirm('Remove @' + username + ' from this workspace?')) return;
  var fd = new FormData();
  fd.append('csrfmiddlewaretoken', CSRF);
  fetch('/community/workspaces/' + WS_ID + '/members/' + userId + '/remove/', { method: 'POST', body: fd })
    .then(function(r) { return r.json(); })
    .then(function(d) { if (d.ok) { toast('@' + username + ' removed', '#22c55e'); location.reload(); } });
}

function copyInvite() {
  var codeEl = document.getElementById('inviteCodeDisplay');
  if (!codeEl) return;
  var url = location.origin + '/community/workspaces/join/' + codeEl.textContent.trim() + '/';
  navigator.clipboard.writeText(url).then(function() { toast('Invite link copied!', '#22c55e'); });
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
function loadDashboard() {
  fetch('/community/workspaces/' + WS_ID + '/tasks/list/')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      var tasks = data.tasks || [];
      var total = tasks.length;
      var todo = tasks.filter(function(t) { return t.status === 'todo'; }).length;
      var doing = tasks.filter(function(t) { return t.status === 'doing'; }).length;
      var done = tasks.filter(function(t) { return t.status === 'done'; }).length;
      var submitted = tasks.filter(function(t) { return t.review_status && t.review_status !== 'none'; }).length;
      var approved = tasks.filter(function(t) { return t.review_status === 'approved'; }).length;
      var pct = total ? Math.round((done / total) * 100) : 0;
      var set = function(id, val) { var el = document.getElementById(id); if (el) el.textContent = val; };
      set('stat-total', total); set('stat-todo', todo); set('stat-doing', doing);
      set('stat-done', done); set('stat-submitted', submitted); set('stat-approved', approved);
      var bar = document.getElementById('overallProgress');
      if (bar) bar.style.width = pct + '%';
      set('overallPct', pct + '% complete');
      var byMember = {};
      tasks.forEach(function(t) {
        var m = t.assigned_to || 'Unassigned';
        if (!byMember[m]) byMember[m] = { total: 0, done: 0 };
        byMember[m].total++;
        if (t.status === 'done') byMember[m].done++;
      });
      var html = '<div style="background:var(--ws-surface2);border:1px solid var(--ws-border);border-radius:10px;padding:1rem;"><div style="font-size:.75rem;font-weight:700;color:var(--ws-text2);margin-bottom:.75rem;">Member Progress</div>';
      Object.keys(byMember).forEach(function(m) {
        var s = byMember[m];
        var p = s.total ? Math.round((s.done / s.total) * 100) : 0;
        html += '<div style="margin-bottom:.75rem;"><div style="display:flex;justify-content:space-between;font-size:.775rem;color:var(--ws-text2);margin-bottom:.25rem;"><span>@' + esc(m) + '</span><span style="color:var(--ws-text3);">' + s.done + '/' + s.total + '</span></div><div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:' + p + '%;background:' + (p === 100 ? 'var(--ws-green)' : 'var(--ws-accent)') + '"></div></div></div>';
      });
      html += '</div>';
      var list = document.getElementById('memberProgressList');
      if (list) list.innerHTML = html;
    }).catch(function() {});
}

// ── Final Assembly ────────────────────────────────────────────────────────────
function runFinalAssembly() {
  var btn = document.getElementById('finishBtn');
  if (btn) { btn.disabled = true; btn.textContent = 'Compiling...'; }
  var out = document.getElementById('finalOutputSection');
  var content = document.getElementById('finalOutputContent');
  if (out) out.style.display = 'block';
  if (content) content.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
  fetch('/community/workspaces/' + WS_ID + '/assembly/')
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (btn) { btn.disabled = false; btn.textContent = 'Compile Final Output'; }
      if (!content) return;
      if (data.error) { content.innerHTML = '<div style="color:var(--ws-red);font-size:.8rem;">' + esc(data.error) + '</div>'; return; }
      var html = '';
      if (data.title) html += '<div style="font-size:1rem;font-weight:800;color:var(--ws-text);margin-bottom:.75rem;">' + esc(data.title) + '</div>';
      if (data.summary) html += '<div style="font-size:.8125rem;color:var(--ws-text2);line-height:1.6;margin-bottom:1rem;">' + esc(data.summary) + '</div>';
      if (data.content) html += '<div style="font-size:.8rem;color:var(--ws-text2);line-height:1.7;white-space:pre-wrap;">' + esc(data.content) + '</div>';
      content.innerHTML = html || '<div style="color:var(--ws-text3);font-size:.8rem;">Assembly complete.</div>';
      toast('Project compiled!', '#22c55e', 4000);
    }).catch(function() { if (btn) { btn.disabled = false; btn.textContent = 'Compile Final Output'; } });
}

// ── Init (runs immediately — script is at bottom of body, DOM is ready) ───────
(function() {
  // Scroll chat to bottom
  var msgs = document.getElementById('chatMessages');
  if (msgs) {
    msgs.scrollTop = msgs.scrollHeight;
    if (msgs.querySelectorAll('.chat-msg').length) lastMsgTime = new Date().toISOString();
  }

  // Wire send button
  var btnSend = document.getElementById('btnSend');
  if (btnSend) btnSend.addEventListener('click', sendChatMsg);

  // Wire mic button
  var btnMic = document.getElementById('btnMic');
  if (btnMic) btnMic.addEventListener('click', onMicBtn);

  // Wire chat input
  var chatInput = document.getElementById('chatInput');
  if (chatInput) {
    chatInput.addEventListener('keydown', chatKeydown);
    chatInput.addEventListener('input', function() { autoResize(chatInput); });
  }

  // Wire file input
  var chatFileInput = document.getElementById('chatFileInput');
  if (chatFileInput) chatFileInput.addEventListener('change', function() { onChatFileSelect(chatFileInput); });

  // Update task counts
  updateTaskCounts();

  // Start polling
  setInterval(pollChat, 3000);

  // Mobile sidebar button
  if (window.innerWidth <= 768) {
    var mobBtn = document.getElementById('mobileSidebarBtn');
    if (mobBtn) mobBtn.style.display = '';
  }

  // Escape closes modal
  document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeTaskModal(); });
})();
