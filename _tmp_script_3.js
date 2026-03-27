
// ── Call (PeerJS) ─────────────────────────────────────────────────────────────
let peer=null, localStream=null, activeCalls={}, isMuted=false, isCamOff=false;

function joinCall(){
  navigator.mediaDevices.getUserMedia({video:true,audio:true}).then(stream=>{
    localStream=stream;
    document.getElementById('joinCallBtn').style.display='none';
    document.getElementById('callControls').style.display='flex';
    addCallTile('me',MY_USERNAME,stream,true);
    const fd=new FormData(); fd.append('csrfmiddlewaretoken',CSRF);
    fetch('/community/workspaces/'+WS_ID+'/call/join/',{method:'POST',body:fd})
      .then(r=>r.json()).then(data=>{
        peer=new Peer(data.peer_id,{key:PEERJS_KEY||'peerjs',debug:0});
        peer.on('call',call=>{
          call.answer(localStream);
          call.on('stream',s=>addCallTile(call.peer,call.peer,s,false));
          activeCalls[call.peer]=call;
        });
        // Connect to existing participants
        (data.participants||[]).forEach(p=>{
          if(p.peer_id&&p.peer_id!==data.peer_id){
            const call=peer.call(p.peer_id,localStream);
            if(call){
              call.on('stream',s=>addCallTile(p.peer_id,p.username||p.peer_id,s,false));
              activeCalls[p.peer_id]=call;
            }
          }
        });
      });
  }).catch(()=>toast('Camera/mic access denied','#ef4444'));
}

function addCallTile(id, name, stream, isLocal){
  const grid=document.getElementById('callGrid');
  const empty=grid.querySelector('.empty-state'); if(empty) empty.parentElement.remove();
  let tile=document.getElementById('call-tile-'+id);
  if(!tile){
    tile=document.createElement('div');
    tile.className='call-tile'; tile.id='call-tile-'+id;
    const video=document.createElement('video');
    video.autoplay=true; video.playsInline=true;
    if(isLocal) video.muted=true;
    video.srcObject=stream;
    tile.appendChild(video);
    const nameEl=document.createElement('div');
    nameEl.className='call-tile-name'; nameEl.textContent=isLocal?'You ('+name+')':name;
    tile.appendChild(nameEl);
    grid.appendChild(tile);
  }
}

function toggleMute(){
  isMuted=!isMuted;
  if(localStream) localStream.getAudioTracks().forEach(t=>t.enabled=!isMuted);
  document.getElementById('muteBtn').classList.toggle('active',isMuted);
}
function toggleCam(){
  isCamOff=!isCamOff;
  if(localStream) localStream.getVideoTracks().forEach(t=>t.enabled=!isCamOff);
  document.getElementById('camBtn').classList.toggle('active',isCamOff);
}
function leaveCall(){
  Object.values(activeCalls).forEach(c=>{try{c.close();}catch(e){}});
  activeCalls={};
  if(localStream) localStream.getTracks().forEach(t=>t.stop());
  if(peer){try{peer.destroy();}catch(e){}} peer=null;
  document.getElementById('callGrid').innerHTML='<div class="empty-state" style="grid-column:1/-1;padding:4rem 1rem;"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg><p>No one is in the call yet.<br>Click "Join Call" to start.</p></div>';
  document.getElementById('joinCallBtn').style.display='';
  document.getElementById('callControls').style.display='none';
  const fd=new FormData(); fd.append('csrfmiddlewaretoken',CSRF);
  fetch('/community/workspaces/'+WS_ID+'/call/leave/',{method:'POST',body:fd});
}

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded',()=>{
  // Scroll chat to bottom
  const msgs=document.getElementById('chatMessages');
  if(msgs) msgs.scrollTop=msgs.scrollHeight;
  // Set last message time for polling
  const allMsgs=msgs?msgs.querySelectorAll('.chat-msg'):[];
  if(allMsgs.length){
    // Use current time as baseline
    lastMsgTime=new Date().toISOString();
  }
  // Update task counts
  updateTaskCounts();
  // Start chat polling
  setInterval(pollChat, 3000);
  // Init action button state
  updateActionBtn();
  // Attach robust input listeners to textarea (belt-and-suspenders for mobile)
  const _ci=document.getElementById('chatInput');
  if(_ci){
    ['input','keyup','keydown','paste','compositionend'].forEach(ev=>{
      _ci.addEventListener(ev,()=>{ autoResize(_ci); setTimeout(updateActionBtn,0); });
    });
  }
  // Mobile sidebar button
  if(window.innerWidth<=768){
    const btn=document.getElementById('mobileSidebarBtn');
    if(btn) btn.style.display='';
  }
});

// Close worksheet on Escape
document.addEventListener('keydown',e=>{
  if(e.key==='Escape') closeWorksheet();
});
