/**
 * NEXA AI Tutor - Modernized Main Chat Logic
 */

// Global constants expected from the template:
// CSRF_TOKEN, AJAX_URL, STREAM_URL, CHAT_IMAGE_URL, WEB_SEARCH_URL, CREATE_THREAD_URL, CURRENT_THREAD_ID

// ── NexaUI ──
const NexaUI = {
    elements: {},
    init() {
        this.elements = {
            chatInput: document.getElementById('chat-input'),
            sendBtn: document.getElementById('send-btn'),
            chatMessages: document.getElementById('chat-messages'),
            chatContainer: document.getElementById('chat-area'), // The scrollable area
            loading: document.getElementById('loading'),
            welcomeScreen: document.getElementById('welcome-screen'),
            useRag: document.getElementById('use-rag'),
        };
        this.bindEvents();
    },
    bindEvents() {
        const { chatInput, sendBtn } = this.elements;
        if (!chatInput || !sendBtn) return;
        
        sendBtn.addEventListener('click', e => { 
            e.preventDefault(); 
            NexaChat.send(); 
        });
        
        chatInput.addEventListener('keydown', e => { 
            if (e.key === 'Enter' && !e.shiftKey) { 
                e.preventDefault(); 
                NexaChat.send(); 
            } 
        });
        
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        });
    },
    showLoading() { 
        if (this.elements.loading) {
            this.elements.loading.classList.add('active'); 
            this.scrollToBottom();
        }
    },
    hideLoading() { 
        if (this.elements.loading) {
            this.elements.loading.classList.remove('active'); 
        }
    },
    hideWelcome() { 
        if (this.elements.welcomeScreen) {
            this.elements.welcomeScreen.style.display = 'none'; 
        }
    },
    showWelcome() { 
        if (this.elements.welcomeScreen) {
            this.elements.welcomeScreen.style.display = 'flex'; 
        }
    },
    scrollToBottom() { 
        const c = this.elements.chatContainer;
        if (c) {
            c.scrollTop = c.scrollHeight;
        }
    },
    escapeHtml(text) { 
        const d = document.createElement('div'); 
        d.textContent = text; 
        return d.innerHTML; 
    },
    copyText(text) { 
        navigator.clipboard.writeText(text).then(() => {
            // Toast notification could be added here
        }); 
    }
};

// ── NexaAI ──
const NexaAI = {
    get csrfToken() { return CSRF_TOKEN; },
    get ajaxUrl() { return AJAX_URL; },
    get streamUrl() { return STREAM_URL; },
    async sendToAI(message, useRag = true) {
        const response = await fetch(this.ajaxUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
            body: JSON.stringify({ message, use_rag: useRag, thread_id: CURRENT_THREAD_ID, model: NexaModel.current })
        });
        return response.json();
    }
};

// NexaModel is now defined globally in nexa_models.js


// ── NexaChat ──
const NexaChat = {
    isSending: false,
    pendingImage: null,
    webSearchMode: false,
    typeQueue: [],
    typingInterval: null,
    currentStreamText: '',
    currentStreamUI: null,
    currentThreadId: typeof CURRENT_THREAD_ID !== 'undefined' ? CURRENT_THREAD_ID : null,

    toggleAttachMenu(e) {
        e.stopPropagation();
        const menu = document.getElementById('attach-menu');
        if (menu) menu.classList.toggle('open');
    },
    closeAttachMenu() { 
        const menu = document.getElementById('attach-menu');
        if (menu) menu.classList.remove('open'); 
    },

    handleImageSelected(input) {
        if (!input.files || !input.files[0]) return;
        this.pendingImage = input.files[0];
        const thumb = document.getElementById('image-preview-thumb');
        const strip = document.getElementById('image-preview-strip');
        if (thumb) thumb.src = URL.createObjectURL(this.pendingImage);
        if (strip) strip.style.display = 'flex';
    },
    clearImage() {
        this.pendingImage = null;
        const strip = document.getElementById('image-preview-strip');
        if (strip) strip.style.display = 'none';
        const input = document.getElementById('image-input');
        if (input) input.value = '';
    },
    sendWebSearch() {
        this.webSearchMode = true;
        const badge = document.getElementById('websearch-badge');
        if (badge) badge.style.display = 'flex';
    },
    clearWebSearch() {
        this.webSearchMode = false;
        const badge = document.getElementById('websearch-badge');
        if (badge) badge.style.display = 'none';
    },

    startTypingSystem(el) {
        this.currentStreamUI = el;
        this.currentStreamText = '';
        this.typeQueue = [];
        if (this.typingInterval) clearInterval(this.typingInterval);
        
        this.typingInterval = setInterval(() => {
            if (this.typeQueue.length > 0) {
                // Determine chunk size for higher speed
                const take = this.typeQueue.length > 50 ? 10 : (this.typeQueue.length > 20 ? 5 : 3);
                for(let i=0; i<take && this.typeQueue.length > 0; i++){
                    this.currentStreamText += this.typeQueue.shift();
                }
                
                if (this.currentStreamUI) {
                    this.currentStreamUI.innerHTML = this.renderBoardHTML(this.currentStreamText) + '<span class="stream-cursor"></span>';
                    NexaUI.scrollToBottom();
                }
            }
        }, 15);
    },

    stopTypingSystem() {
        if (this.typingInterval) clearInterval(this.typingInterval);
        this.typingInterval = null;
        if (this.currentStreamUI && this.typeQueue.length > 0) {
            this.currentStreamText += this.typeQueue.join('');
            this.currentStreamUI.innerHTML = this.renderBoardHTML(this.currentStreamText);
            this.typeQueue = [];
        } else if (this.currentStreamUI) {
            this.currentStreamUI.innerHTML = this.renderBoardHTML(this.currentStreamText);
        }
    },

    async send(message) {
        if (this.isSending) return;
        const msg = message || NexaUI.elements.chatInput.value.trim();
        if (!msg && !this.pendingImage) return;
        
        this.isSending = true;
        NexaUI.hideWelcome();
        if (NexaUI.elements.sendBtn) NexaUI.elements.sendBtn.disabled = true;
        if (!message && NexaUI.elements.chatInput) { 
            NexaUI.elements.chatInput.value = ''; 
            NexaUI.elements.chatInput.style.height = 'auto'; 
        }
        this.closeAttachMenu();
        
        try {
            const useRag = NexaUI.elements.useRag?.checked ?? true;
            if (this.pendingImage) {
                this.addUserMessage(msg, this.pendingImage);
                await this.sendImageStreaming(msg, this.pendingImage, useRag);
                this.clearImage();
            } else if (this.webSearchMode) {
                this.addUserMessage('🌐 ' + msg);
                const data = await this.sendToWebSearch(msg);
                if (data.success) {
                    await this.addAIMessage(data.response);
                } else {
                    alert('Error: ' + (data.error || 'Web search failed'));
                }
                this.clearWebSearch();
            } else {
                this.addUserMessage(msg);
                await this.sendStreaming(msg, useRag);
            }
        } catch(error) {
            console.error(error);
            // Optional: add error message to UI
        } finally {
            this.isSending = false;
            NexaUI.hideLoading();
            if (NexaUI.elements.sendBtn) NexaUI.elements.sendBtn.disabled = false;
            NexaUI.scrollToBottom();
        }
    },

    async sendStreaming(message, useRag = true) {
        const msgId = 'ai-msg-' + Date.now();
        this.createAIMessageContainer(msgId);
        
        const el = document.getElementById(msgId);
        const wrap = document.getElementById('wrap-' + msgId);
        
        try {
            wrap.querySelector('.msg-ai').classList.add('streaming');
            const res = await fetch(NexaAI.streamUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': NexaAI.csrfToken },
                body: JSON.stringify({ message, use_rag: useRag, thread_id: this.currentThreadId, model: NexaModel.current })
            });

            if (!res.ok) throw new Error('Stream failed');

            this.startTypingSystem(el);

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n\n');
                buffer = lines.pop();
                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    try {
                        const payload = JSON.parse(line.slice(6));
                        if (payload.error) throw new Error(payload.error);
                        if (payload.done) break;
                        if (payload.token) {
                            for(const char of payload.token) this.typeQueue.push(char);
                        }
                        if (payload.thread_id && !this.currentThreadId) {
                            this.currentThreadId = payload.thread_id;
                        }
                    } catch(e) {}
                }
            }
            
            setTimeout(() => {
                this.stopTypingSystem();
                wrap.querySelector('.msg-ai').classList.remove('streaming');
                if (wrap) wrap.dataset.plain = this.currentStreamText;
                const actions = document.getElementById('actions-' + msgId);
                if (actions) actions.style.display = 'flex';
                NexaUI.scrollToBottom();
            }, 500);

        } catch(e) {
            wrap.querySelector('.msg-ai').classList.remove('streaming');
            el.innerHTML = `<span style="color:var(--text-muted); opacity:0.7; font-size:13px;">AI is thinking...</span>`;
            // Fallback to AJAX
            const data = await NexaAI.sendToAI(message, useRag);
            if (data.success) {
                el.innerHTML = this.renderBoardHTML(data.response);
                wrap.dataset.plain = data.response;
                const actions = document.getElementById('actions-' + msgId);
                if (actions) actions.style.display = 'flex';
            } else {
                el.innerHTML = `<span style="color:#ef4444">Error: ${data.error || 'Failed to get response'}</span>`;
            }
        }
    },

    async sendImageStreaming(message, imageFile, useRag = true) {
        const msgId = 'ai-msg-' + Date.now();
        this.createAIMessageContainer(msgId);
        const el = document.getElementById(msgId);
        const wrap = document.getElementById('wrap-' + msgId);

        try {
            wrap.querySelector('.msg-ai').classList.add('streaming');
            const formData = new FormData();
            formData.append('message', message || 'Analyze this image');
            formData.append('image', imageFile);
            formData.append('use_rag', useRag);
            formData.append('model', NexaModel.current);
            if (this.currentThreadId) formData.append('thread_id', this.currentThreadId);
            formData.append('csrfmiddlewaretoken', NexaAI.csrfToken);

            const res = await fetch(CHAT_IMAGE_URL, {
                method: 'POST',
                body: formData
            });

            if (!res.ok) throw new Error('Image analysis failed');

            this.startTypingSystem(el);
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                let chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n\n');
                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    try {
                        const payload = JSON.parse(line.slice(6));
                        if (payload.token) {
                            for(const char of payload.token) this.typeQueue.push(char);
                        }
                    } catch(e) {}
                }
            }
            
            setTimeout(() => {
                this.stopTypingSystem();
                wrap.querySelector('.msg-ai').classList.remove('streaming');
                wrap.dataset.plain = this.currentStreamText;
                const actions = document.getElementById('actions-' + msgId);
                if (actions) actions.style.display = 'flex';
            }, 500);

        } catch(e) {
            wrap.querySelector('.msg-ai').classList.remove('streaming');
            el.innerHTML = `<span style="color:var(--text-muted); opacity:0.7; font-size:13px;">AI is thinking...</span>`;
        }
    },

    async sendToWebSearch(message) {
        const response = await fetch(WEB_SEARCH_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': NexaAI.csrfToken },
            body: JSON.stringify({ message, thread_id: this.currentThreadId, model: NexaModel.current })
        });
        return response.json();
    },

    createAIMessageContainer(msgId) {
        const html = `
            <div class="msg-wrap" id="wrap-${msgId}">
                <div class="msg msg-ai">
                    <div class="msg-avatar"><div class="avatar-circle">N</div></div>
                    <div class="msg-body">
                        <div class="msg-content">
                            <div class="msg-text board-render" id="${msgId}"></div>
                            <div class="msg-actions" id="actions-${msgId}" style="display:none; margin-top:8px; gap:8px;">
                                <button class="input-btn" onclick="NexaVoice.speak(this.closest('.msg-wrap').dataset.plain)" title="Listen">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg>
                                </button>
                                <button class="input-btn" onclick="NexaUI.copyText(this.closest('.msg-wrap').dataset.plain)" title="Copy">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
        NexaUI.elements.chatMessages.insertAdjacentHTML('beforeend', html);
        NexaUI.scrollToBottom();
    },

    addUserMessage(text, imageFile) {
        const imgHtml = imageFile ? `<img src="${URL.createObjectURL(imageFile)}" style="max-width:240px; border-radius:12px; margin-top:8px; display:block; border:1px solid var(--border);">` : '';
        const html = `
            <div class="msg-wrap">
                <div class="msg msg-user">
                    <div class="msg-avatar"><div class="avatar-circle">${USER_NAME.charAt(0).toUpperCase()}</div></div>
                    <div class="msg-body">
                        <div class="msg-content">
                            <div class="msg-text">${NexaUI.escapeHtml(text)}${imgHtml}</div>
                        </div>
                    </div>
                </div>
            </div>`;
        NexaUI.elements.chatMessages.insertAdjacentHTML('beforeend', html);
        NexaUI.showLoading();
        NexaUI.scrollToBottom();
    },

    async addAIMessage(text) {
        const msgId = 'ai-msg-' + Date.now();
        this.createAIMessageContainer(msgId);
        const el = document.getElementById(msgId);
        const wrap = document.getElementById('wrap-' + msgId);
        el.innerHTML = this.renderBoardHTML(text);
        wrap.dataset.plain = text;
        const actions = document.getElementById('actions-' + msgId);
        if (actions) actions.style.display = 'flex';
        NexaUI.scrollToBottom();
    },

    renderBoardHTML(raw) {
        if (!raw) return '';
        let text = raw;

        // Normalise LaTeX
        text = text.replace(/\\\(/g, '$').replace(/\\\)/g, '$');
        text = text.replace(/\\\[/g, '$$').replace(/\\\]/g, '$$');

        // Extract math
        const mathStore = [];
        text = text.replace(/\$\$([\s\S]+?)\$\$/g, (_, m) => {
            const i = mathStore.length;
            mathStore.push({ display: true, src: m.trim() });
            return `\n\nNEXAMATH_D_${i}_END\n\n`;
        });
        text = text.replace(/\$([^$\n]+?)\$/g, (_, m) => {
            const i = mathStore.length;
            mathStore.push({ display: false, src: m.trim() });
            return `NEXAMATH_I_${i}_END`;
        });

        // Markdown
        let html = '';
        if (typeof marked !== 'undefined') {
            marked.setOptions({ breaks: true, gfm: true });
            html = marked.parse(text);
        } else {
            html = `<p>${text.replace(/\n\n+/g, '</p><p>').replace(/\n/g, '<br>')}</p>`;
        }

        // Restore math
        html = html.replace(/<p>\s*NEXAMATH_D_(\d+)_END\s*<\/p>/g, (_, i) => this._katex(mathStore[i]));
        html = html.replace(/NEXAMATH_D_(\d+)_END/g, (_, i) => this._katex(mathStore[i]));
        html = html.replace(/NEXAMATH_I_(\d+)_END/g, (_, i) => this._katex(mathStore[i]));

        return html;
    },

    _katex(m) {
        if (typeof katex === 'undefined') return m.display ? `$$${m.src}$$` : `$${m.src}$`;
        try {
            const out = katex.renderToString(m.src, { displayMode: m.display, throwOnError: false });
            return m.display ? `<div class="br-math-display">${out}</div>` : out;
        } catch(e) {
            return m.display ? `$$${m.src}$$` : `$${m.src}$`;
        }
    }
};

// Start UI
document.addEventListener('DOMContentLoaded', () => {
    NexaUI.init();
    
    // Initial Render of history
    document.querySelectorAll('.board-render').forEach(el => {
        const wrap = el.closest('.msg-wrap');
        if (wrap && wrap.dataset.plain) {
            el.innerHTML = NexaChat.renderBoardHTML(wrap.dataset.plain);
        }
    });

    NexaUI.scrollToBottom();

    // Restore selected model UI state
    NexaModel.updateUI(NexaModel.current);
});

