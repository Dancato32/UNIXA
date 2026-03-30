/**
 * NEXA Community Feed Logic
 */

// Global constant expected: CSRF (from django {{ csrf_token }})
const loadedComments = {};

function esc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function timeAgo(iso) {
    const s = Math.floor((Date.now() - new Date(iso)) / 1000);
    if (s < 60) return 'just now';
    if (s < 3600) return Math.floor(s / 60) + 'm ago';
    if (s < 86400) return Math.floor(s / 3600) + 'h ago';
    return Math.floor(s / 86400) + 'd ago';
}

function showToast(msg) {
    let t = document.getElementById('share-toast');
    if (!t) {
        t = document.createElement('div');
        t.id = 'share-toast';
        t.className = 'toast';
        document.body.appendChild(t);
    }
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2000);
}

/* Like toggle */
function toggleLike(id, btn) {
    fetch(`/community/api/posts/${id}/like/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF, 'Content-Type': 'application/json' }
    })
    .then(r => r.json())
    .then(d => {
        btn.classList.toggle('liked', d.liked);
        const svgEl = btn.querySelector('svg');
        if (svgEl) svgEl.setAttribute('fill', d.liked ? 'currentColor' : 'none');
        const countSpan = btn.querySelector('span');
        if (countSpan) countSpan.textContent = d.like_count;
    }).catch(() => {});
}

/* Comment logic */
function toggleCommentBox(id) {
    const box = document.getElementById('ic-' + id);
    if (!box) return;
    const isOpen = box.classList.toggle('open');
    if (isOpen && !loadedComments[id]) {
        loadedComments[id] = true;
        fetchComments(id);
    }
    if (isOpen) {
        const inp = document.getElementById('ic-text-' + id);
        if (inp) setTimeout(() => inp.focus(), 50);
    }
}

function fetchComments(postId) {
    const list = document.getElementById('ic-list-' + postId);
    if (!list) return;
    list.innerHTML = '<div class="loading-dots" style="padding:1rem;"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>';
    fetch(`/community/api/posts/${postId}/comments/`)
    .then(r => r.json())
    .then(d => {
        const results = Array.isArray(d) ? d : (d.results || []);
        if (!results.length) { list.innerHTML = ''; return; }
        list.innerHTML = results.map(c => buildCommentHtml(c)).join('');
    }).catch(() => { list.innerHTML = ''; });
}

function submitComment(e, postId) {
    e.preventDefault();
    const inp = document.getElementById('ic-text-' + postId);
    const text = inp.value.trim();
    if (!text) return;
    const btn = e.target.querySelector('[type=submit]');
    if (btn) { btn.disabled = true; btn.textContent = '...'; }
    fetch(`/community/api/posts/${postId}/comments/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF, 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text })
    }).then(r => r.json())
    .then(c => {
        inp.value = '';
        if (btn) { btn.disabled = false; btn.textContent = 'Post'; }
        const list = document.getElementById('ic-list-' + postId);
        if (list) list.insertAdjacentHTML('beforeend', buildCommentHtml(c));
        const cc = document.getElementById('cc-' + postId);
        if (cc) cc.textContent = parseInt(cc.textContent || 0) + 1;
    }).catch(() => {
        if (btn) { btn.disabled = false; btn.textContent = 'Post'; }
    });
}

function buildCommentHtml(c) {
    const initials = c.author.username.slice(0, 1).toUpperCase();
    const avatar = c.author.profile_picture 
        ? `<div class="pc-av" style="width:32px;height:32px;"><img src="${esc(c.author.profile_picture)}"></div>`
        : `<div class="pc-av" style="width:32px;height:32px;">${esc(initials)}</div>`;

    return `<div class="comment-item" style="margin-bottom:1rem; padding-bottom:0.75rem; border-bottom:1px solid rgba(0,0,0,0.05);">
        <div style="display:flex; gap:0.75rem; align-items:start;">
            ${avatar}
            <div style="flex:1;">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-weight:700; font-size:0.875rem;">${esc(c.author.username)}</span>
                    <span style="font-size:0.75rem; color:var(--text-secondary);">${timeAgo(c.created_at)}</span>
                </div>
                <div style="font-size:0.875rem; line-height:1.5; margin-top:0.25rem;">${esc(c.content)}</div>
            </div>
        </div>
    </div>`;
}

/* Follow toggle */
function quickFollow(username, userId, btn) {
    fetch('/community/api/follow-toggle/', {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF, 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
    }).then(r => r.json()).then(d => {
        btn.classList.toggle('following', d.following);
        btn.textContent = d.following ? 'Following' : '+ Follow';
        if (d.following) btn.classList.add('btn-secondary');
        else btn.classList.remove('btn-secondary');
    }).catch(() => {});
}

/* User search */
function friendSearch(q) {
    const results = document.getElementById('friend-search-results');
    if (!q.trim()) { results.innerHTML = ''; return; }
    results.innerHTML = '<div style="padding:1rem; font-size:0.75rem; color:var(--text-secondary);">Searching...</div>';
    fetch(`/community/api/users/search/?q=${encodeURIComponent(q)}`)
        .then(r => r.json()).then(d => {
            if (!d.length) { results.innerHTML = '<div style="padding:1rem; font-size:0.75rem; color:var(--text-secondary);">No users found.</div>'; return; }
            results.innerHTML = d.map(u => `
                <div class="rc-item">
                    <div class="rc-icon">${esc(u.username.slice(0, 1).toUpperCase())}</div>
                    <div style="flex:1; min-width:0;">
                        <div class="rc-name">${esc(u.display_name || u.username)}</div>
                        <div class="rc-count">@${esc(u.username)}</div>
                    </div>
                    <button class="btn btn-ghost btn-xs" onclick="quickFollow('${esc(u.username)}','${u.id}',this)">+ Follow</button>
                </div>`).join('');
        }).catch(() => { results.innerHTML = ''; });
}

/* Join Study Group */
function joinStudyGroup(btn) {
    const wsId = btn.dataset.wsid;
    if (!wsId) return;
    const orig = btn.innerHTML;
    btn.disabled = true; btn.innerHTML = 'Joining...';
    fetch(`/community/ai/api/study-group/${wsId}/join/`)
        .then(r => r.json())
        .then(d => {
            btn.disabled = false;
            if (!d.ok) { btn.innerHTML = orig; alert(d.error || 'Failed to join.'); return; }
            btn.innerHTML = 'Joined';
            btn.classList.add('btn-success');
            if (d.workspace_url) window.location.href = d.workspace_url;
        }).catch(() => { btn.disabled = false; btn.innerHTML = orig; });
}

// Share logic simplified
function openShareModal(postId) {
    const url = window.location.origin + '/community/posts/' + postId + '/';
    navigator.clipboard.writeText(url).then(() => {
        showToast('Link copied to clipboard!');
    });
}
