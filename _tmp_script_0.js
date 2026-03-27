
const WS_ID = 'PLACEHOLDER';
const CSRF = 'PLACEHOLDER';
const MY_USERNAME = 'PLACEHOLDER';
const IS_ADMIN = PLACEHOLDER;
const PEERJS_KEY = 'PLACEHOLDER';

// ── Utilities ────────────────────────────────────────────────────────────────
function esc(s){ const d=document.createElement('div');d.textContent=s||'';return d.innerHTML; }
function toast(msg,color='#22c55e',dur=3000){
  const t=document.getElementById('wsToast');
  t.textContent=msg;t.style.borderColor=color;t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),dur);
}
function autoResize(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,120)+'px';}

// ── Panel navigation ─────────────────────────────────────────────────────────
function showPanel(name, navEl){
  document.querySelectorAll('.ws-panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.ws-nav-item').forEach(n=>n.classList.remove('active'));
  document.querySelectorAll('.ws-mob-tab').forEach(n=>n.classList.remove('active'));
  const panel = document.getElementById('panel-'+name);
  if(panel) panel.classList.add('active');
  // Sync desktop sidebar nav
  if(navEl && navEl.classList.contains('ws-nav-item')) navEl.classList.add('active');
  else { const n=document.getElementById('nav-'+name); if(n) n.classList.add('active'); }
  // Sync mobile top nav
  if(navEl && navEl.classList.contains('ws-mob-tab')) navEl.classList.add('active');
  else { const m=document.getElementById('mob-nav-'+name); if(m) m.classList.add('active'); }
  if(name==='dashboard') loadDashboard();
  // scroll panel content to top
  if(panel){
    panel.scrollTop = 0;
    panel.querySelectorAll('*').forEach(el=>{ if(el.scrollTop > 0) el.scrollTop = 0; });
  }
  const main = document.querySelector('.ws-main');
  if(main) main.scrollTop = 0;
}
function toggleSidebar(){
  document.getElementById('wsSidebar').classList.toggle('open');
  document.getElementById('sidebarOverlay').classList.toggle('open');
}

// ── Chat ─────────────────────────────────────────────────────────────────────
// Voice recording
let _mediaRec=null, _audioChunks=[], _voiceTimerInterval=null, _voiceSeconds=0, _voiceBlob=null, _voiceCancelled=false;

function toggleVoice(){
  if(_mediaRec && _mediaRec.state==='recording') stopVoice();
  else startVoice();
}

async function startVoice(){
  try{
    const stream=await navigator.mediaDevices.getUserMedia({audio:true});
    _audioChunks=[];
    _voiceCancelled=false;
    _mediaRec=new MediaRecorder(stream);
    _mediaRec.ondataavailable=e=>{if(e.data && e.data.size>0) _audioChunks.push(e.data);};
    // onstop set once here — checks _voiceCancelled flag to decide what to do
    _mediaRec.onstop=function(){
      if(_voiceCancelled){ _voiceCancelled=false; return; }
      showVoicePreview();
    };
    _mediaRec.start(100); // timeslice=100ms ensures chunks arrive before onstop
    const btn=document.getElementById('btnMic');
    btn.classList.add('recording');
    btn.style.background='#dc2626';
    document.getElementById('voiceBar').classList.add('active');
    _voiceSeconds=0;
    _voiceTimerInterval=setInterval(()=>{
      _voiceSeconds++;
      const m=Math.floor(_voiceSeconds/60), s=_voiceSeconds%60;
      document.getElementById('voiceTimer').textContent=m+':'+(s<10?'0':'')+s;
    },1000);
  }catch(err){alert('Microphone access denied.');}
}

function stopVoice(){
  if(!_mediaRec) return;
  clearInterval(_voiceTimerInterval);
  _mediaRec.stop();
  _mediaRec.stream.getTracks().forEach(t=>t.stop());
  const btn=document.getElementById('btnMic');
  btn.classList.remove('recording');
  btn.style.background='#25d366';
  document.getElementById('voiceBar').classList.remove('active');
}

function showVoicePreview(){
  if(!_audioChunks.length) return;
  _voiceBlob=new Blob(_audioChunks,{type:'audio/webm'});
  const url=URL.createObjectURL(_voiceBlob);
  const audio=document.getElementById('voicePreviewAudio');
  audio.src=url;
  document.getElementById('voicePreviewBar').classList.add('active');
  updateActionBtn();
}

function discardVoice(){
  _voiceBlob=null; _audioChunks=[];
  const audio=document.getElementById('voicePreviewAudio');
  if(audio.src) URL.revokeObjectURL(audio.src);
  audio.src='';
  document.getElementById('voicePreviewBar').classList.remove('active');
  updateActionBtn();
}

function cancelVoice(){
  if(!_mediaRec) return;
  _voiceCancelled=true;
  clearInterval(_voiceTimerInterval);
  _mediaRec.stop();
  _mediaRec.stream.getTracks().forEach(t=>t.stop());
  _mediaRec=null; _audioChunks=[];
  const btn=document.getElementById('btnMic');
  btn.classList.remove('recording');
  btn.style.background='#25d366';
  document.getElementById('voiceBar').classList.remove('active');
  updateActionBtn();
}

function sendVoiceMsg(){
  if(!_voiceBlob) return;
  const fd=new FormData();
  fd.append('file', _voiceBlob, 'voice_'+Date.now()+'.webm');
  fd.append('content','🎙 Voice message');
  fd.append('csrfmiddlewaretoken',CSRF);
  if(replyToId) fd.append('reply_to_id',replyToId);
  fetch('/community/workspaces/'+WS_ID+'/chat/',{method:'POST',body:fd})
    .then(r=>r.json()).then(data=>{if(!data.error) appendVoiceMsg(data,true);})
    .catch(()=>{});
  discardVoice();
  _mediaRec=null; _audioChunks=[];
  clearReply();
}

function appendVoiceMsg(data, mine){
  // reuse appendMsg — it handles audio files
  appendMsg(data, mine);
  updateActionBtn();
}


let replyToId=null, replyToText='', chatPollTimer=null, lastMsgTime='';

function chatKeydown(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();onActionBtn();}}

// Switch button: mic when empty, send when has content
function updateActionBtn(){
  const hasText=document.getElementById('chatInput').value.trim().length>0;
  const hasFile=document.getElementById('chatFileInput').files.length>0;
  const showSend=hasText||hasFile||!!_voiceBlob;
  document.getElementById('btnMic').style.display=showSend?'none':'flex';
  document.getElementById('btnSend').style.display=showSend?'flex':'none';
}

// Mic button: start/stop voice recording
function onMicBtn(){
  if(_voiceBlob){ sendVoiceMsg(); updateActionBtn(); return; }
  if(_mediaRec && _mediaRec.state==='recording'){ stopVoice(); return; }
  startVoice();
}

// Single button: mic when empty, send when has content (kept for Enter key compat)
function onActionBtn(){
  if(_voiceBlob){ sendVoiceMsg(); updateActionBtn(); return; }
  if(_mediaRec && _mediaRec.state==='recording'){ stopVoice(); return; }
  const hasText=document.getElementById('chatInput').value.trim().length>0;
  const hasFile=document.getElementById('chatFileInput').files.length>0;
  if(hasText||hasFile){ sendChatMsg(); return; }
  startVoice();
}

function sendChatMsg(){
  const input=document.getElementById('chatInput');
  const content=input.value.trim();
  const fileInput=document.getElementById('chatFileInput');
  if(!content && !fileInput.files.length) return;
  const fd=new FormData();
  if(content) fd.append('content',content);
  if(fileInput.files.length) fd.append('file',fileInput.files[0]);
  if(replyToId) fd.append('reply_to_id',replyToId);
  fd.append('csrfmiddlewaretoken',CSRF);
  input.value=''; input.style.height='auto';
  clearReply(); clearMedia(); fileInput.value='';
  updateActionBtn();
  fetch('/community/workspaces/'+WS_ID+'/chat/',{method:'POST',body:fd})
    .then(r=>r.json()).then(data=>{if(!data.error) appendMsg(data,true);})
    .catch(()=>{});
}

function buildVoiceBubble(src, mine){
  // Generate random-ish waveform bars (30 bars)
  const bars=Array.from({length:30},(_,i)=>{
    const h=8+Math.round(Math.abs(Math.sin(i*0.7+1)*16));
    return `<div class="vn-bar" style="height:${h}px" data-idx="${i}"></div>`;
  }).join('');
  const id='vn-'+Date.now()+'-'+Math.random().toString(36).slice(2,6);
  return `<div class="vn-bubble" id="${id}">
    <button class="vn-play" onclick="vnToggle('${id}')">
      <svg id="${id}-icon" viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21"/></svg>
    </button>
    <div class="vn-body">
      <div class="vn-waveform" id="${id}-wave" onclick="vnSeek(event,'${id}')">
        ${bars}
        <div class="vn-scrubber" id="${id}-dot" style="left:0px"></div>
      </div>
      <div class="vn-footer">
        <span class="vn-duration" id="${id}-dur">0:00</span>
      </div>
    </div>
    <audio id="${id}-audio" src="${src}" preload="metadata"
      ontimeupdate="vnTick('${id}')"
      onloadedmetadata="vnMeta('${id}')"
      onended="vnEnded('${id}')"></audio>
  </div>`;
}

function vnToggle(id){
  const audio=document.getElementById(id+'-audio');
  const icon=document.getElementById(id+'-icon');
  if(audio.paused){
    // pause all others
    document.querySelectorAll('.vn-bubble audio').forEach(a=>{if(a!==audio){a.pause();const oid=a.id.replace('-audio','');vnEnded(oid);}});
    audio.play();
    icon.innerHTML='<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>';
  } else {
    audio.pause();
    icon.innerHTML='<polygon points="5,3 19,12 5,21"/>';
  }
}

function vnMeta(id){
  const audio=document.getElementById(id+'-audio');
  if(audio && isFinite(audio.duration)) document.getElementById(id+'-dur').textContent=vnFmt(audio.duration);
}

function vnTick(id){
  const audio=document.getElementById(id+'-audio');
  if(!audio||!audio.duration) return;
  const pct=audio.currentTime/audio.duration;
  const wave=document.getElementById(id+'-wave');
  const dot=document.getElementById(id+'-dot');
  const bars=wave.querySelectorAll('.vn-bar');
  const ww=wave.offsetWidth-10;
  dot.style.left=(pct*ww)+'px';
  const played=Math.round(pct*bars.length);
  bars.forEach((b,i)=>b.classList.toggle('played',i<played));
  document.getElementById(id+'-dur').textContent=vnFmt(audio.currentTime);
}

function vnSeek(e,id){
  const audio=document.getElementById(id+'-audio');
  if(!audio||!audio.duration) return;
  const wave=document.getElementById(id+'-wave');
  const rect=wave.getBoundingClientRect();
  const pct=Math.max(0,Math.min(1,(e.clientX-rect.left)/rect.width));
  audio.currentTime=pct*audio.duration;
}

function vnEnded(id){
  const icon=document.getElementById(id+'-icon');
  if(icon) icon.innerHTML='<polygon points="5,3 19,12 5,21"/>';
  const wave=document.getElementById(id+'-wave');
  if(wave) wave.querySelectorAll('.vn-bar').forEach(b=>b.classList.remove('played'));
  const dot=document.getElementById(id+'-dot');
  if(dot) dot.style.left='0px';
  const audio=document.getElementById(id+'-audio');
  if(audio) document.getElementById(id+'-dur').textContent=vnFmt(audio.duration||0);
}

function vnFmt(s){
  if(!isFinite(s)) return '0:00';
  const m=Math.floor(s/60),sec=Math.floor(s%60);
  return m+':'+(sec<10?'0':'')+sec;
}

function appendMsg(data, mine){
  const msgs=document.getElementById('chatMessages');
  const div=document.createElement('div');
  div.className='chat-msg'+(mine?' mine':data.is_ai?' ai-msg':'');
  div.id='msg-'+data.id;
  const time=new Date(data.created_at).toLocaleTimeString([],{hour:'numeric',minute:'2-digit'});
  const tick=mine?`<span class="chat-tick"><svg viewBox="0 0 16 11" fill="none"><path d="M1 5.5l3.5 3.5L10 2" stroke="#53bdeb" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><path d="M5 5.5l3.5 3.5L14 2" stroke="#53bdeb" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span>`:'';
  const avatarHtml=mine?'':data.is_ai
    ?`<div class="chat-avatar" style="background:#7c3aed"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" style="width:13px;height:13px"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg></div>`
    :`<div class="chat-avatar">${data.sender_avatar?`<img src="${data.sender_avatar}" alt="">`:(data.sender||'?')[0].toUpperCase()}</div>`;
  const senderHtml=mine?'':data.is_ai?`<div class="chat-sender" style="color:#7c3aed">Nexa AI</div>`:`<div class="chat-sender">${esc(data.sender)}</div>`;
  const replyHtml=data.reply_preview?`<div class="chat-reply-preview">${esc(data.reply_preview.sender)}: ${esc(data.reply_preview.content)}</div>`:'';
  let mediaHtml='';
  if(data.media_url){
    const n=(data.media_name||'').toLowerCase();
    if(n.endsWith('.webm')||n.endsWith('.mp3')||n.endsWith('.ogg'))
      mediaHtml=buildVoiceBubble(data.media_url, mine);
    else
      mediaHtml=`<a class="chat-media-link" href="${data.media_url}" target="_blank">📎 ${esc(data.media_name)}</a>`;
  }
  const isVoice=!!(data.media_url&&(data.media_name||'').toLowerCase().match(/\.(webm|mp3|ogg)$/));
  const rawContent=data.is_ai?esc(data.content).replace(/^\[AI\]/,''):esc(data.content);
  const content=isVoice?'':rawContent;
  div.innerHTML=`${avatarHtml}<div class="chat-bubble-wrap">${senderHtml}${replyHtml}<div class="chat-bubble">${content}${mediaHtml}<div class="chat-meta">${time}${tick}</div></div></div>`;
  msgs.appendChild(div);
  msgs.scrollTop=msgs.scrollHeight;
  if(data.created_at) lastMsgTime=data.created_at;
}

function deleteMsg(id){
  if(!confirm('Delete this message?')) return;
  const fd=new FormData(); fd.append('csrfmiddlewaretoken',CSRF);
  fetch('/community/workspaces/'+WS_ID+'/chat/'+id+'/delete/',{method:'POST',body:fd})
    .then(r=>r.json()).then(d=>{if(d.ok){const el=document.getElementById('msg-'+id);if(el)el.remove();}});
}

function clearReply(){replyToId=null;replyToText='';document.getElementById('replyBar').style.display='none';}
function clearMedia(){document.getElementById('mediaPreview').style.display='none';}
function onChatFileSelect(input){
  if(input.files.length){
    document.getElementById('mediaPreview').style.display='flex';
    document.getElementById('mediaPreviewName').textContent='📎 '+input.files[0].name;
  }
}

function pollChat(){
  const params=lastMsgTime?'?since='+encodeURIComponent(lastMsgTime):'';
  fetch('/community/workspaces/'+WS_ID+'/poll/'+params)
    .then(r=>r.json()).then(data=>{
      (data.messages||[]).forEach(m=>{
        if(!document.getElementById('msg-'+m.id)) appendMsg(m, m.is_mine);
      });
    }).catch(()=>{});
}

// ── Files ────────────────────────────────────────────────────────────────────
function uploadFile(input){
  if(!input.files.length) return;
  const fd=new FormData(); fd.append('file',input.files[0]); fd.append('csrfmiddlewaretoken',CSRF);
  toast('Uploading…','#6366f1');
  fetch('/community/workspaces/'+WS_ID+'/files/',{method:'POST',body:fd})
    .then(r=>r.json()).then(data=>{
      if(data.error){toast(data.error,'#ef4444');return;}
      addFileCard(data);
      toast('File uploaded. Analyzing…','#6366f1');
      analyzeFiles(data.name);
    }).catch(()=>toast('Upload failed','#ef4444'));
  input.value='';
}

function onFileDrop(e){
  e.preventDefault();
  document.getElementById('uploadZone').classList.remove('drag-over');
  const file=e.dataTransfer.files[0]; if(!file) return;
  const fd=new FormData(); fd.append('file',file); fd.append('csrfmiddlewaretoken',CSRF);
  toast('Uploading…','#6366f1');
  fetch('/community/workspaces/'+WS_ID+'/files/',{method:'POST',body:fd})
    .then(r=>r.json()).then(data=>{if(!data.error){addFileCard(data);analyzeFiles(data.name);}})
    .catch(()=>{});
}

function addFileCard(data){
  const grid=document.getElementById('fileGrid');
  const empty=grid.querySelector('.empty-state');
  if(empty) empty.parentElement.remove();
  const card=document.createElement('div');
  card.className='file-card'; card.id='file-'+data.id;
  card.innerHTML=`<div class="file-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div><div class="file-name" title="${esc(data.name)}">${esc(data.name)}</div><div class="file-meta">${esc(data.uploaded_by)} · just now</div><div class="file-actions"><a href="${data.url}" target="_blank" class="btn-ws btn-ws-ghost btn-ws-sm">Download</a><button class="btn-ws btn-ws-danger btn-ws-sm" onclick="deleteFile('${data.id}')">Delete</button></div>`;
  grid.appendChild(card);
}

function deleteFile(id){
  if(!confirm('Delete this file?')) return;
  const fd=new FormData(); fd.append('csrfmiddlewaretoken',CSRF);
  fetch('/community/workspaces/'+WS_ID+'/files/'+id+'/delete/',{method:'POST',body:fd})
    .then(r=>r.json()).then(d=>{
      if(d.ok){
        const el=document.getElementById('file-'+id); if(el) el.remove();
        toast('File deleted','#22c55e');
      }
    });
}

function analyzeFiles(fileName){
  const result=document.getElementById('aiAnalysisResult');
  result.style.display='block';
  result.innerHTML=`<div class="ai-analysis-banner"><h4>🤖 Analyzing "${esc(fileName)}"…</h4><div class="loading-dots"><span></span><span></span><span></span></div></div>`;
  fetch('/community/workspaces/'+WS_ID+'/ai/analyze/',{method:'POST',headers:{'X-CSRFToken':CSRF,'Content-Type':'application/json'},body:JSON.stringify({})})
    .then(r=>r.json()).then(data=>{renderAnalysis(data);})
    .catch(()=>{result.innerHTML='<div class="ai-analysis-banner"><h4>Analysis failed</h4><p>Could not analyze the file. You can still add tasks manually.</p></div>';});
}

function renderAnalysis(data){
  const result=document.getElementById('aiAnalysisResult');
  if(data.error){result.innerHTML=`<div class="ai-analysis-banner"><h4>Analysis Error</h4><p>${esc(data.error)}</p></div>`;return;}
  let html=`<div class="ai-analysis-banner"><h4>📋 AI Analysis Complete</h4><p>${esc(data.summary||data.overview||'Analysis complete.')}</p></div>`;
  const tasks=data.suggested_tasks||data.tasks||[];
  if(tasks.length){
    html+=`<div style="margin-top:.75rem;"><div style="font-size:.8rem;font-weight:700;color:var(--ws-text2);margin-bottom:.5rem;">Suggested Tasks (${tasks.length})</div>`;
    tasks.forEach((t,i)=>{
      const title=typeof t==='string'?t:(t.title||t.task||t);
      const assignee=t.suggested_assignee||t.assignee||'';
      html+=`<div class="ai-task-suggestion" id="ai-ts-${i}"><div class="ai-task-suggestion-info"><div class="ai-task-suggestion-title">${esc(title)}</div>${assignee?`<div class="ai-task-suggestion-meta">Suggested for @${esc(assignee)}</div>`:''}</div><button class="btn-ws btn-ws-primary btn-ws-sm" onclick="addSuggestedTask(${i},'${esc(title).replace(/'/g,"\\'")}','${esc(assignee).replace(/'/g,"\\'")}')">+ Assign</button></div>`;
    });
    html+=`<button class="btn-ws btn-ws-green btn-ws-sm" style="margin-top:.5rem;" onclick="addAllSuggestedTasks()">Assign All to Members</button></div>`;
    window._aiSuggestedTasks=tasks;
  }
  result.innerHTML=html;
}

function addSuggestedTask(idx, title, assignee){
  const btn=document.querySelector(`#ai-ts-${idx} .btn-ws-primary`);
  if(btn){btn.disabled=true;btn.textContent='Adding…';}
  const fd=new FormData();
  fd.append('title',title); fd.append('csrfmiddlewaretoken',CSRF);
  if(assignee) fd.append('assigned_to',assignee);
  fetch('/community/workspaces/'+WS_ID+'/tasks/',{method:'POST',body:fd})
    .then(r=>r.json()).then(data=>{
      if(btn){btn.textContent='✓ Added';btn.classList.add('added');}
      addTaskCard(data,'todo');
      toast('Task added. Visible in MyNexa.','#22c55e');
    }).catch(()=>{if(btn){btn.disabled=false;btn.textContent='+ Assign';}});
}

function addAllSuggestedTasks(){
  const tasks=window._aiSuggestedTasks||[];
  if(!tasks.length) return;
  Promise.all(tasks.map((t,i)=>{
    const title=typeof t==='string'?t:(t.title||t.task||t);
    const assignee=t.suggested_assignee||t.assignee||'';
    const fd=new FormData();
    fd.append('title',title); fd.append('csrfmiddlewaretoken',CSRF);
    if(assignee) fd.append('assigned_to',assignee);
    return fetch('/community/workspaces/'+WS_ID+'/tasks/',{method:'POST',body:fd}).then(r=>r.json());
  })).then(results=>{
    results.forEach(d=>{if(d.id) addTaskCard(d,'todo');});
    toast(results.length+' tasks assigned. Members can see them in MyNexa.','#22c55e',4000);
    window._aiSuggestedTasks=[];
  });
}
