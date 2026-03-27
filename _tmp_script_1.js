
// ── Tasks ────────────────────────────────────────────────────────────────────
function toggleTaskForm(){
  const f=document.getElementById('taskAddForm');
  f.style.display=f.style.display==='none'?'block':'none';
  if(f.style.display==='block') document.getElementById('taskTitle').focus();
}

function addTask(){
  const title=document.getElementById('taskTitle').value.trim();
  if(!title){toast('Title required','#ef4444');return;}
  const fd=new FormData();
  fd.append('title',title); fd.append('csrfmiddlewaretoken',CSRF);
  const assignee=document.getElementById('taskAssignee').value;
  const due=document.getElementById('taskDue').value;
  const desc=document.getElementById('taskDesc').value;
  if(assignee) fd.append('assigned_to',assignee);
  if(due) fd.append('due_date',due);
  if(desc) fd.append('description',desc);
  fetch('/community/workspaces/'+WS_ID+'/tasks/',{method:'POST',body:fd})
    .then(r=>r.json()).then(data=>{
      addTaskCard(data,'todo');
      document.getElementById('taskTitle').value='';
      document.getElementById('taskDesc').value='';
      document.getElementById('taskDue').value='';
      toggleTaskForm();
      toast('Task added'+(data.assigned_to?' and assigned to @'+data.assigned_to:'')+'. Visible in MyNexa.','#22c55e');
    }).catch(()=>{});
}

function addTaskCard(data, col){
  const colEl=document.getElementById('col-'+(col||data.status||'todo'));
  if(!colEl) return;
  const card=document.createElement('div');
  card.className='task-card'; card.id='task-'+data.id;
  card.onclick=()=>openTaskDetail(data.id,data.title,data.description||'',data.status||'todo',data.assigned_to||'',data.due_date||'',data.review_status||'none');
  const assigneeBadge=data.assigned_to?`<span class="task-tag assignee">@${esc(data.assigned_to)}</span>`:'';
  const dueBadge=data.due_date?`<span class="task-tag due">${esc(data.due_date)}</span>`:'';
  card.innerHTML=`<div class="task-card-title">${esc(data.title)}</div><div class="task-card-meta">${assigneeBadge}${dueBadge}</div>`;
  colEl.appendChild(card);
  updateTaskCounts();
}

function updateTaskCounts(){
  ['todo','doing','done'].forEach(s=>{
    const col=document.getElementById('col-'+s);
    const cnt=document.getElementById('cnt-'+s);
    if(col&&cnt) cnt.textContent=col.querySelectorAll('.task-card').length;
  });
  const total=document.querySelectorAll('.task-card').length;
  const badge=document.getElementById('task-count-badge');
  if(badge){badge.textContent=total;badge.style.display=total?'':'none';}
  const mobBadge=document.getElementById('mob-task-badge');
  if(mobBadge){mobBadge.textContent=total;mobBadge.style.display=total?'':'none';}
}

// ── Members ──────────────────────────────────────────────────────────────────
function toggleAddMember(){
  const f=document.getElementById('addMemberForm');
  f.style.display=f.style.display==='none'?'block':'none';
  if(f.style.display==='block') document.getElementById('memberSearch').focus();
}

let searchTimer=null;
function searchUsers(q){
  clearTimeout(searchTimer);
  if(q.length<2){document.getElementById('memberSearchResults').innerHTML='';return;}
  searchTimer=setTimeout(()=>{
    fetch('/community/workspaces/users/search/?q='+encodeURIComponent(q))
      .then(r=>r.json()).then(data=>{
        const res=document.getElementById('memberSearchResults');
        if(!data.users.length){res.innerHTML='<div style="font-size:.75rem;color:var(--ws-text3);">No users found.</div>';return;}
        res.innerHTML=data.users.map(u=>`<div style="display:flex;align-items:center;justify-content:space-between;padding:.375rem 0;border-bottom:1px solid var(--ws-border);"><span style="font-size:.8rem;color:var(--ws-text);">${esc(u.display)} <span style="color:var(--ws-text3);">@${esc(u.username)}</span></span><button class="btn-ws btn-ws-primary btn-ws-sm" onclick="addMember('${esc(u.username)}')">Add</button></div>`).join('');
      });
  },300);
}

function addMember(username){
  const fd=new FormData(); fd.append('username',username); fd.append('csrfmiddlewaretoken',CSRF);
  fetch('/community/workspaces/'+WS_ID+'/members/add/',{method:'POST',body:fd})
    .then(r=>r.json()).then(d=>{
      if(d.error){toast(d.error,'#ef4444');return;}
      toast(d.added?'@'+username+' added to workspace':'@'+username+' is already a member','#22c55e');
      if(d.added) document.getElementById('memberSearchResults').innerHTML='';
    });
}

function removeMember(userId, username){
  if(!confirm('Remove @'+username+' from this workspace?')) return;
  const fd=new FormData(); fd.append('csrfmiddlewaretoken',CSRF);
  fetch('/community/workspaces/'+WS_ID+'/members/'+userId+'/remove/',{method:'POST',body:fd})
    .then(r=>r.json()).then(d=>{if(d.ok){toast('@'+username+' removed','#22c55e');location.reload();}});
}

function copyInvite(){
  const code=document.getElementById('inviteCodeDisplay').textContent;
  const url=location.origin+'/community/workspaces/join/'+code+'/';
  navigator.clipboard.writeText(url).then(()=>toast('Invite link copied!','#22c55e'));
}

// ── Dashboard ────────────────────────────────────────────────────────────────
function loadDashboard(){
  fetch('/community/workspaces/'+WS_ID+'/tasks/list/')
    .then(r=>r.json()).then(data=>{
      const tasks=data.tasks||[];
      const total=tasks.length;
      const todo=tasks.filter(t=>t.status==='todo').length;
      const doing=tasks.filter(t=>t.status==='doing').length;
      const done=tasks.filter(t=>t.status==='done').length;
      const submitted=tasks.filter(t=>t.review_status&&t.review_status!=='none').length;
      const approved=tasks.filter(t=>t.review_status==='approved').length;
      const pct=total?Math.round((done/total)*100):0;
      document.getElementById('stat-total').textContent=total;
      document.getElementById('stat-todo').textContent=todo;
      document.getElementById('stat-doing').textContent=doing;
      document.getElementById('stat-done').textContent=done;
      document.getElementById('stat-submitted').textContent=submitted;
      document.getElementById('stat-approved').textContent=approved;
      document.getElementById('overallProgress').style.width=pct+'%';
      document.getElementById('overallPct').textContent=pct+'% complete';
      // Per-member breakdown
      const byMember={};
      tasks.forEach(t=>{
        const m=t.assigned_to||'Unassigned';
        if(!byMember[m]) byMember[m]={total:0,done:0};
        byMember[m].total++;
        if(t.status==='done') byMember[m].done++;
      });
      let html='<div style="background:var(--ws-surface2);border:1px solid var(--ws-border);border-radius:10px;padding:1rem;"><div style="font-size:.75rem;font-weight:700;color:var(--ws-text2);margin-bottom:.75rem;">Member Progress</div>';
      Object.entries(byMember).forEach(([m,s])=>{
        const p=s.total?Math.round((s.done/s.total)*100):0;
        html+=`<div style="margin-bottom:.75rem;"><div style="display:flex;justify-content:space-between;font-size:.775rem;color:var(--ws-text2);margin-bottom:.25rem;"><span>@${esc(m)}</span><span style="color:var(--ws-text3);">${s.done}/${s.total}</span></div><div class="progress-bar-wrap"><div class="progress-bar-fill" style="width:${p}%;background:${p===100?'var(--ws-green)':'var(--ws-accent)'}"></div></div></div>`;
      });
      html+='</div>';
      document.getElementById('memberProgressList').innerHTML=html;
    }).catch(()=>{});
}

// ── Finish / Final Assembly ───────────────────────────────────────────────────
function runFinalAssembly(){
  const btn=document.getElementById('finishBtn');
  btn.disabled=true; btn.textContent='Compiling…';
  const out=document.getElementById('finalOutputSection');
  const content=document.getElementById('finalOutputContent');
  out.style.display='block';
  content.innerHTML='<div class="loading-dots"><span></span><span></span><span></span></div><span style="font-size:.8rem;color:var(--ws-text3);margin-left:.5rem;">AI is compiling all approved work…</span>';
  fetch('/community/workspaces/'+WS_ID+'/assembly/')
    .then(r=>r.json()).then(data=>{
      btn.disabled=false; btn.textContent='Compile Final Output';
      if(data.error){content.innerHTML=`<div style="color:var(--ws-red);font-size:.8rem;">${esc(data.error)}</div>`;return;}
      let html='';
      if(data.title) html+=`<div style="font-size:1rem;font-weight:800;color:var(--ws-text);margin-bottom:.75rem;">${esc(data.title)}</div>`;
      if(data.summary) html+=`<div style="font-size:.8125rem;color:var(--ws-text2);line-height:1.6;margin-bottom:1rem;">${esc(data.summary)}</div>`;
      if(data.sections&&data.sections.length){
        data.sections.forEach(s=>{
          html+=`<div style="margin-bottom:1rem;"><div style="font-size:.875rem;font-weight:700;color:var(--ws-accent2);margin-bottom:.375rem;">${esc(s.title||s.heading||'')}</div><div style="font-size:.8rem;color:var(--ws-text2);line-height:1.6;">${esc(s.content||s.body||'')}</div></div>`;
        });
      }
      if(data.content) html+=`<div style="font-size:.8rem;color:var(--ws-text2);line-height:1.7;white-space:pre-wrap;">${esc(data.content)}</div>`;
      content.innerHTML=html||'<div style="color:var(--ws-text3);font-size:.8rem;">Assembly complete.</div>';
      toast('Project compiled successfully!','#22c55e',4000);
    }).catch(()=>{btn.disabled=false;btn.textContent='Compile Final Output';content.innerHTML='<div style="color:var(--ws-red);font-size:.8rem;">Assembly failed. Try again.</div>';});
}
