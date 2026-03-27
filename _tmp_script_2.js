
// ── Worksheet / Task Detail ───────────────────────────────────────────────────
let currentTaskId=null, currentTaskTitle='', worksheetItems=[], taskStarted=false;

function openTaskDetail(id, title, desc, status, assignee, due, reviewStatus){
  currentTaskId=id; currentTaskTitle=title;
  document.getElementById('worksheetTitle').textContent=title;
  document.getElementById('wsTaskDesc').textContent=desc||'No description.';
  document.getElementById('wsTaskAssignee').textContent=assignee||'Unassigned';
  document.getElementById('wsTaskDue').textContent=due||'No due date';
  const statusEl=document.getElementById('wsTaskStatus');
  if(statusEl){statusEl.textContent=status;statusEl.style.color=status==='done'?'var(--ws-green)':status==='doing'?'var(--ws-yellow)':' var(--ws-text3)';}
  document.getElementById('worksheetOverlay').style.display='flex';
}
function closeTaskModal(){document.getElementById('worksheetOverlay').style.display='none';}


function closeWorksheet(){
  document.getElementById('worksheetOverlay').classList.remove('open');
  currentTaskId=null;
}

function setPhase(phase){
  ['start','work','submit'].forEach(p=>{
    document.getElementById('phase-'+p).classList.toggle('active',p===phase);
  });
  if(phase==='submit'){
    // Show submit panel
    document.querySelectorAll('.ws-tool-panel').forEach(p=>p.classList.remove('active'));
    document.querySelectorAll('.ws-tool-btn').forEach(b=>b.classList.remove('active'));
    document.getElementById('tool-submit-phase').style.display='flex';
    document.getElementById('tool-submit-phase').classList.add('active');
    buildSubmitPreview();
  } else if(phase==='work'){
    document.getElementById('tool-submit-phase').style.display='none';
    switchTool('editor', document.getElementById('tool-btn-editor'));
  } else {
    document.getElementById('tool-submit-phase').style.display='none';
    switchTool('overview', document.getElementById('tool-btn-overview'));
  }
}

function startTask(){
  if(!currentTaskId) return;
  const fd=new FormData(); fd.append('csrfmiddlewaretoken',CSRF);
  fetch('/community/workspaces/'+WS_ID+'/tasks/'+currentTaskId+'/start/',{method:'POST',body:fd})
    .then(r=>r.json()).then(()=>{
      taskStarted=true;
      document.getElementById('startTaskBtn').style.display='none';
      document.getElementById('submitTaskBtn').style.display='';
      setPhase('work');
      toast('Task started! Use the tools to complete your work.','#6366f1');
    });
}

function switchTool(name, btn){
  document.querySelectorAll('.ws-tool-panel').forEach(p=>{p.classList.remove('active');p.style.display='none';});
  document.querySelectorAll('.ws-tool-btn').forEach(b=>b.classList.remove('active'));
  const panel=document.getElementById('tool-'+name);
  if(panel){panel.style.display='flex';panel.classList.add('active');}
  if(btn) btn.classList.add('active');
}

// ── Worksheet items ──────────────────────────────────────────────────────────
function addToSheet(label, text){
  worksheetItems.push({label, text});
  updateSheetUI();
  toast('Added to worksheet','#6366f1');
}

function updateSheetUI(){
  const container=document.getElementById('worksheetEntries');
  const count=document.getElementById('sheetCount');
  count.textContent=worksheetItems.length;
  if(!worksheetItems.length){
    container.innerHTML='<div style="font-size:.75rem;color:var(--ws-text3);text-align:center;padding:.5rem;">Use tools above and click "+ Add to Worksheet" to collect your work here.</div>';
    return;
  }
  container.innerHTML=worksheetItems.map((item,i)=>`<div class="worksheet-entry"><span class="worksheet-entry-label">${esc(item.label)}</span><span class="worksheet-entry-text">${esc(item.text.slice(0,120))}${item.text.length>120?'…':''}</span><span class="worksheet-entry-del" onclick="removeSheetItem(${i})">✕</span></div>`).join('');
}

function removeSheetItem(i){ worksheetItems.splice(i,1); updateSheetUI(); }
function clearSheet(){ worksheetItems=[]; updateSheetUI(); }

function buildSubmitPreview(){
  const preview=document.getElementById('submitPreview');
  if(!worksheetItems.length){
    preview.innerHTML='<div style="color:var(--ws-text3);">No items in worksheet yet. Go back and add content using the tools.</div>';
    return;
  }
  preview.innerHTML=worksheetItems.map(item=>`<div style="margin-bottom:.625rem;"><span style="font-size:.65rem;font-weight:700;text-transform:uppercase;color:var(--ws-text3);">${esc(item.label)}</span><div style="margin-top:.2rem;">${esc(item.text.slice(0,200))}${item.text.length>200?'…':''}</div></div>`).join('<div class="divider"></div>');
  document.getElementById('aiReviewResult').style.display='none';
  document.getElementById('finalSubmitBtn').style.display='none';
  document.getElementById('reviewBeforeSubmitBtn').style.display='';
}

function aiPreSubmitReview(){
  if(!worksheetItems.length){toast('Add content to your worksheet first','#ef4444');return;}
  const btn=document.getElementById('reviewBeforeSubmitBtn');
  btn.disabled=true; btn.textContent='Reviewing…';
  const submission=worksheetItems.map(i=>`[${i.label}]\n${i.text}`).join('\n\n');
  // Use AI chat endpoint to review
  fetch('/community/workspaces/'+WS_ID+'/ai/chat/',{
    method:'POST',
    headers:{'X-CSRFToken':CSRF,'Content-Type':'application/json'},
    body:JSON.stringify({message:`Review this task submission for "${currentTaskTitle}". Check if it adequately addresses the task requirements. Submission:\n\n${submission.slice(0,2000)}\n\nRespond with: APPROVED or NEEDS_REVISION, then a brief explanation.`})
  }).then(r=>r.json()).then(data=>{
    btn.disabled=false; btn.textContent='AI Review First';
    const res=document.getElementById('aiReviewResult');
    res.style.display='block';
    const reply=data.reply||data.message||'Review complete.';
    const approved=reply.toUpperCase().includes('APPROVED')&&!reply.toUpperCase().includes('NEEDS_REVISION');
    res.innerHTML=`<div style="background:${approved?'rgba(34,197,94,.1)':'rgba(245,158,11,.1)'};border:1px solid ${approved?'rgba(34,197,94,.3)':'rgba(245,158,11,.3)'};border-radius:8px;padding:.75rem;font-size:.8rem;color:var(--ws-text2);line-height:1.5;"><div style="font-weight:700;color:${approved?'var(--ws-green)':'var(--ws-yellow)'};margin-bottom:.375rem;">${approved?'✅ Ready to Submit':'⚠️ Review Feedback'}</div>${esc(reply)}</div>`;
    document.getElementById('finalSubmitBtn').style.display='';
  }).catch(()=>{btn.disabled=false;btn.textContent='AI Review First';});
}

function finalSubmit(){
  if(!currentTaskId||!worksheetItems.length){toast('Nothing to submit','#ef4444');return;}
  const btn=document.getElementById('finalSubmitBtn');
  btn.disabled=true; btn.textContent='Submitting…';
  const submission=worksheetItems.map(i=>`[${i.label}]\n${i.text}`).join('\n\n');
  fetch('/community/workspaces/'+WS_ID+'/tasks/'+currentTaskId+'/submit/',{
    method:'POST',
    headers:{'X-CSRFToken':CSRF,'Content-Type':'application/json'},
    body:JSON.stringify({submission})
  }).then(r=>r.json()).then(data=>{
    btn.disabled=false; btn.textContent='Submit to Workspace';
    if(data.error){toast(data.error,'#ef4444');return;}
    toast('Task submitted for review!','#22c55e',4000);
    closeWorksheet();
    // Move card to doing
    const card=document.getElementById('task-'+currentTaskId);
    if(card){
      const doing=document.getElementById('col-doing');
      if(doing) doing.appendChild(card);
      updateTaskCounts();
    }
  }).catch(()=>{btn.disabled=false;btn.textContent='Submit to Workspace';});
}

// ── Editor tool ──────────────────────────────────────────────────────────────
function editorFormat(cmd){
  const ed=document.getElementById('wsEditor');
  ed.focus();
  if(cmd==='bold') document.execCommand('bold');
  else if(cmd==='italic') document.execCommand('italic');
  else if(cmd==='h2') document.execCommand('formatBlock',false,'h2');
  else if(cmd==='ul') document.execCommand('insertUnorderedList');
}

function addEditorToSheet(){
  const ed=document.getElementById('wsEditor');
  const text=ed.innerText.trim();
  if(!text){toast('Editor is empty','#ef4444');return;}
  addToSheet('Editor',text);
}

function aiImproveEditor(){
  const ed=document.getElementById('wsEditor');
  const text=ed.innerText.trim();
  if(!text){toast('Write something first','#ef4444');return;}
  fetch('/community/workspaces/'+WS_ID+'/ai/chat/',{
    method:'POST',
    headers:{'X-CSRFToken':CSRF,'Content-Type':'application/json'},
    body:JSON.stringify({message:`Improve this text for the task "${currentTaskTitle}". Make it clearer, more professional, and well-structured. Return only the improved text:\n\n${text.slice(0,1500)}`})
  }).then(r=>r.json()).then(data=>{
    const improved=data.reply||data.message||'';
    if(improved) ed.innerText=improved;
    toast('Text improved by AI','#6366f1');
  }).catch(()=>{});
}

// ── Search tool ──────────────────────────────────────────────────────────────
function doSearch(){
  const q=document.getElementById('searchQuery').value.trim();
  if(!q) return;
  const res=document.getElementById('searchResults');
  res.innerHTML='<div class="loading-dots"><span></span><span></span><span></span></div>';
  fetch('/community/workspaces/'+WS_ID+'/ai/deep-search/',{
    method:'POST',
    headers:{'X-CSRFToken':CSRF,'Content-Type':'application/json'},
    body:JSON.stringify({query:q})
  }).then(r=>r.json()).then(data=>{
    if(data.error){res.innerHTML=`<div style="color:var(--ws-red);font-size:.8rem;">${esc(data.error)}</div>`;return;}
    const findings=data.findings||data.results||[];
    if(!findings.length){res.innerHTML='<div style="color:var(--ws-text3);font-size:.8rem;">No results found.</div>';return;}
    res.innerHTML=findings.map((f,i)=>`<div class="search-result-card"><div class="search-result-title">${esc(f.title||f.heading||'Result '+(i+1))}</div><div class="search-result-snippet">${esc(f.content||f.snippet||f.summary||'')}</div>${f.url?`<div class="search-result-url">${esc(f.url)}</div>`:''}<button class="add-to-sheet-btn" onclick="addToSheet('Search','${(f.content||f.snippet||f.title||'').replace(/'/g,"\\'").slice(0,500)}')">+ Add to Worksheet</button></div>`).join('');
  }).catch(()=>{res.innerHTML='<div style="color:var(--ws-red);font-size:.8rem;">Search failed. Try again.</div>';});
}

// ── Paraphrase tool ──────────────────────────────────────────────────────────
let paraStyle='academic';
function selectParaStyle(btn){
  document.querySelectorAll('.para-style').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active'); paraStyle=btn.dataset.style;
}

function doParaphrase(){
  const text=document.getElementById('paraInput').value.trim();
  if(!text){toast('Enter text to paraphrase','#ef4444');return;}
  const out=document.getElementById('paraOutput');
  out.innerHTML='<div class="loading-dots"><span></span><span></span><span></span></div>';
  fetch('/community/workspaces/'+WS_ID+'/ai/chat/',{
    method:'POST',
    headers:{'X-CSRFToken':CSRF,'Content-Type':'application/json'},
    body:JSON.stringify({message:`Paraphrase the following text in a ${paraStyle} style. Return only the paraphrased text:\n\n${text.slice(0,1500)}`})
  }).then(r=>r.json()).then(data=>{
    const result=data.reply||data.message||'';
    out.innerHTML=`<div style="background:var(--ws-surface2);border:1px solid var(--ws-border);border-radius:8px;padding:.75rem;font-size:.8rem;color:var(--ws-text2);line-height:1.6;">${esc(result)}</div><button class="add-to-sheet-btn" onclick="addToSheet('Paraphrase','${result.replace(/'/g,"\\'").slice(0,500)}')">+ Add to Worksheet</button>`;
  }).catch(()=>{out.innerHTML='<div style="color:var(--ws-red);font-size:.8rem;">Failed. Try again.</div>';});
}

// ── Citation tool ────────────────────────────────────────────────────────────
let citeStyle='APA';
function selectCiteStyle(btn){
  document.querySelectorAll('.cite-style').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active'); citeStyle=btn.dataset.style;
}

function doCitation(){
  const source=document.getElementById('citeInput').value.trim();
  if(!source){toast('Enter a source URL or title','#ef4444');return;}
  const out=document.getElementById('citeOutput');
  out.innerHTML='<div class="loading-dots"><span></span><span></span><span></span></div>';
  fetch('/community/workspaces/'+WS_ID+'/ai/chat/',{
    method:'POST',
    headers:{'X-CSRFToken':CSRF,'Content-Type':'application/json'},
    body:JSON.stringify({message:`Generate a ${citeStyle} citation for this source: "${source}". Return only the formatted citation.`})
  }).then(r=>r.json()).then(data=>{
    const result=data.reply||data.message||'';
    out.innerHTML=`<div style="background:var(--ws-surface2);border:1px solid var(--ws-border);border-radius:8px;padding:.75rem;font-size:.8rem;color:var(--ws-text2);font-family:monospace;line-height:1.6;">${esc(result)}</div><button class="add-to-sheet-btn" onclick="addToSheet('Citation','${result.replace(/'/g,"\\'").slice(0,300)}')">+ Add to Worksheet</button>`;
  }).catch(()=>{out.innerHTML='<div style="color:var(--ws-red);font-size:.8rem;">Failed. Try again.</div>';});
}

// ── AI Assistant tool ────────────────────────────────────────────────────────
function sendAI(){
  const input=document.getElementById('aiInput');
  const msg=input.value.trim(); if(!msg) return;
  input.value='';
  const msgs=document.getElementById('aiMessages');
  msgs.innerHTML+=`<div style="text-align:right;margin-bottom:.5rem;"><div style="display:inline-block;background:rgba(99,102,241,.2);border-radius:8px;padding:.375rem .625rem;font-size:.8rem;color:var(--ws-text);max-width:80%;">${esc(msg)}</div></div>`;
  msgs.innerHTML+=`<div id="ai-typing" style="margin-bottom:.5rem;"><div class="loading-dots"><span></span><span></span><span></span></div></div>`;
  msgs.scrollTop=msgs.scrollHeight;
  fetch('/community/workspaces/'+WS_ID+'/ai/chat/',{
    method:'POST',
    headers:{'X-CSRFToken':CSRF,'Content-Type':'application/json'},
    body:JSON.stringify({message:`[Task: ${currentTaskTitle}] ${msg}`})
  }).then(r=>r.json()).then(data=>{
    const typing=document.getElementById('ai-typing'); if(typing) typing.remove();
    const reply=data.reply||data.message||'';
    msgs.innerHTML+=`<div style="margin-bottom:.75rem;"><div style="font-size:.7rem;font-weight:600;color:var(--ws-accent2);margin-bottom:.2rem;">Nexa AI</div><div style="background:rgba(99,102,241,.08);border:1px solid rgba(99,102,241,.2);border-radius:8px;padding:.5rem .75rem;font-size:.8rem;color:var(--ws-text2);line-height:1.5;max-width:85%;">${esc(reply)}</div><button class="add-to-sheet-btn" onclick="addToSheet('AI','${reply.replace(/'/g,"\\'").slice(0,500)}')">+ Add to Worksheet</button></div>`;
    msgs.scrollTop=msgs.scrollHeight;
  }).catch(()=>{const t=document.getElementById('ai-typing');if(t)t.remove();});
}
