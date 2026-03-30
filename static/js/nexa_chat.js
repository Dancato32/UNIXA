/**
 * NEXA AI Tutor - Main Chat Logic
 */

// Global data initialization (expects these to be set in the template)
// const NEXA_HISTORY_RAW = ...
// const NEXA_HISTORY = ...
// const USER_NAME = ...
// const CSRF_TOKEN = ...
// const AJAX_URL = ...
// const STREAM_URL = ...

// ── NexaUI ──
const NexaUI = {
    elements: {},
    init() {
        this.elements = {
            chatInput: document.getElementById('chat-input'),
            sendBtn: document.getElementById('send-btn'),
            chatMessages: document.getElementById('chat-messages'),
            chatContainer: document.getElementById('chat-container'),
            loading: document.getElementById('loading'),
            welcomeScreen: document.getElementById('welcome-screen'),
            useRag: document.getElementById('use-rag'),
        };
        this.bindEvents();
    },
    bindEvents() {
        const { chatInput, sendBtn } = this.elements;
        if (!chatInput || !sendBtn) return;
        sendBtn.addEventListener('click', e => { e.preventDefault(); NexaChat.send(); });
        chatInput.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); NexaChat.send(); } });
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 180) + 'px';
        });
    },
    showLoading() { if (this.elements.loading) this.elements.loading.classList.add('active'); },
    hideLoading() { if (this.elements.loading) this.elements.loading.classList.remove('active'); },
    hideWelcome() { if (this.elements.welcomeScreen) this.elements.welcomeScreen.style.display = 'none'; },
    showWelcome() { if (this.elements.welcomeScreen) this.elements.welcomeScreen.style.display = 'flex'; },
    scrollToBottom() { if (this.elements.chatContainer) this.elements.chatContainer.scrollTop = this.elements.chatContainer.scrollHeight; },
    escapeHtml(text) { const d = document.createElement('div'); d.textContent = text; return d.innerHTML; },
    copyText(text) { navigator.clipboard.writeText(text).then(() => {
        // Optional: Show a toast or feedback
        console.log('Copied to clipboard');
    }); }
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
            body: JSON.stringify({ message, use_rag: useRag })
        });
        return response.json();
    }
};

// ── NexaChat ──
const NexaChat = {
    isSending: false,
    pendingImage: null,
    webSearchMode: false,

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

    newChat() {
        const container = NexaUI.elements.chatMessages;
        if (container) { container.querySelectorAll('.msg-wrap').forEach(w => w.remove()); NexaUI.showWelcome(); }
        if (NexaUI.elements.chatInput) { NexaUI.elements.chatInput.value = ''; NexaUI.elements.chatInput.style.height = 'auto'; }
    },

    async clearChat() {
        if (!confirm('Clear all chat history? This cannot be undone.')) return;
        try {
            const res = await fetch(CLEAR_CONVERSATIONS_URL, { method: 'POST', headers: { 'X-CSRFToken': CSRF_TOKEN } });
            if (res.ok || res.redirected) {
                const container = NexaUI.elements.chatMessages;
                if (container) { container.querySelectorAll('.msg-wrap').forEach(w => w.remove()); NexaUI.showWelcome(); }
            }
        } catch(e) { console.error(e); }
    },

    async send(message) {
        if (this.isSending) return;
        const msg = message || NexaUI.elements.chatInput.value.trim();
        if (!msg && !this.pendingImage) return;
        this.isSending = true;
        NexaUI.hideWelcome();
        NexaUI.showLoading();
        if (NexaUI.elements.sendBtn) NexaUI.elements.sendBtn.disabled = true;
        if (!message && NexaUI.elements.chatInput) { NexaUI.elements.chatInput.value = ''; NexaUI.elements.chatInput.style.height = 'auto'; }
        this.closeAttachMenu();
        try {
            if (this.pendingImage) {
                this.addUserMessage(msg, this.pendingImage);
                await this.sendImageStreaming(msg, this.pendingImage);
                this.clearImage();
            } else if (this.webSearchMode) {
                this.addUserMessage('🌐 ' + msg);
                const data = await this.sendToWebSearch(msg);
                if (data.success) await this.addAIMessage(data.response, data.timestamp);
                else alert('Error: ' + (data.error || 'Web search failed'));
                this.clearWebSearch();
            } else {
                this.addUserMessage(msg);
                await NexaChat.sendStreaming(msg, NexaUI.elements.useRag?.checked ?? true);
            }
        } catch(error) {
            console.error(error);
            alert('Failed to connect to server.');
        } finally {
            this.isSending = false;
            NexaUI.hideLoading();
            if (NexaUI.elements.sendBtn) NexaUI.elements.sendBtn.disabled = false;
            NexaUI.scrollToBottom();
        }
    },

    async sendImageStreaming(message, imageFile) {
        const msgId = 'ai-msg-' + Date.now();
        const html = `
            <div class="msg-wrap" id="wrap-${msgId}">
                <div class="msg msg-ai">
                    <div class="msg-body">
                        <div class="msg-text board-render" id="${msgId}">
                            <div class="loading-indicator active">
                                <div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div>
                            </div>
                        </div>
                        <div class="msg-actions" id="actions-${msgId}" style="display:none">
                            <button class="msg-action-btn" onclick="NexaVoice.speak(this.closest('.msg-wrap').dataset.plain)" title="Listen">
                                <i data-feather="volume-2" style="width:14px;height:14px"></i>
                            </button>
                            <button class="msg-action-btn" onclick="NexaUI.copyText(this.closest('.msg-wrap').dataset.plain)" title="Copy">
                                <i data-feather="copy" style="width:14px;height:14px"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>`;
        NexaUI.elements.chatMessages.insertAdjacentHTML('beforeend', html);
        if (window.feather) feather.replace();
        NexaUI.scrollToBottom();
        const el = document.getElementById(msgId);
        const wrap = document.getElementById('wrap-' + msgId);
        let fullText = '';
        
        try {
            wrap.querySelector('.msg-ai').classList.add('streaming');
            const formData = new FormData();
            formData.append('message', message || 'Analyze this image');
            formData.append('image', imageFile);
            formData.append('csrfmiddlewaretoken', NexaAI.csrfToken);

            const res = await fetch(CHAT_IMAGE_URL, {
                method: 'POST',
                body: formData
            });

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
                        if (payload.error) { el.innerHTML = '<span style="color:#ef4444">Error: ' + payload.error + '</span>'; return; }
                        if (payload.done) break;
                        if (payload.token) {
                            fullText += payload.token;
                            el.innerHTML = NexaChat.renderBoardHTML(fullText) + '<span class="stream-cursor"></span>';
                            NexaUI.scrollToBottom();
                        }
                    } catch(e) {}
                }
            }
            wrap.querySelector('.msg-ai').classList.remove('streaming');
            el.innerHTML = NexaChat.renderBoardHTML(fullText);
            if (wrap) wrap.dataset.plain = fullText;
            document.getElementById('actions-' + msgId).style.display = '';
        } catch(e) {
            if(wrap) wrap.querySelector('.msg-ai').classList.remove('streaming');
            if(el) el.innerHTML = '<span style="color:#ef4444">Connection error. Please try again.</span>';
        }
    },

    async sendToWebSearch(message) {
        const response = await fetch(WEB_SEARCH_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': NexaAI.csrfToken },
            body: JSON.stringify({ message })
        });
        return response.json();
    },

    async sendStreaming(message, useRag = true) {
        const msgId = 'ai-msg-' + Date.now();
        const html = `
            <div class="msg-wrap" id="wrap-${msgId}">
                <div class="msg msg-ai">
                    <div class="msg-body">
                        <div class="msg-text board-render" id="${msgId}">
                            <div class="loading-indicator active">
                                <div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div>
                            </div>
                        </div>
                        <div class="msg-actions" id="actions-${msgId}" style="display:none">
                            <button class="msg-action-btn" onclick="NexaVoice.speak(this.closest('.msg-wrap').dataset.plain)" title="Listen">
                                <i data-feather="volume-2" style="width:14px;height:14px"></i>
                            </button>
                            <button class="msg-action-btn" onclick="NexaUI.copyText(this.closest('.msg-wrap').dataset.plain)" title="Copy">
                                <i data-feather="copy" style="width:14px;height:14px"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>`;
        NexaUI.elements.chatMessages.insertAdjacentHTML('beforeend', html);
        if (window.feather) feather.replace();
        NexaUI.scrollToBottom();
        const el = document.getElementById(msgId);
        const wrap = document.getElementById('wrap-' + msgId);
        let fullText = '';
        try {
            wrap.querySelector('.msg-ai').classList.add('streaming');
            const res = await fetch(NexaAI.streamUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': NexaAI.csrfToken },
                body: JSON.stringify({ message, use_rag: useRag })
            });
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
                        if (payload.error) { el.innerHTML = '<span style="color:#ef4444">Error: ' + payload.error + '</span>'; return; }
                        if (payload.done) break;
                        if (payload.token) {
                            fullText += payload.token;
                            el.innerHTML = NexaChat.renderBoardHTML(fullText) + '<span class="stream-cursor"></span>';
                            NexaUI.scrollToBottom();
                        }
                    } catch(e) {}
                }
            }
            wrap.querySelector('.msg-ai').classList.remove('streaming');
        } catch(e) {
            wrap.querySelector('.msg-ai').classList.remove('streaming');
            console.warn('Streaming failed, falling back to AJAX:', e);
            try {
                const res2 = await fetch(NexaAI.ajaxUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': NexaAI.csrfToken },
                    body: JSON.stringify({ message, use_rag: useRag })
                });
                const data = await res2.json();
                if (data.success) {
                    fullText = data.response;
                } else {
                    el.innerHTML = '<span style="color:#ef4444">Error: ' + (data.error || 'Request failed') + '</span>';
                    return;
                }
            } catch(e2) {
                el.innerHTML = '<span style="color:#ef4444">Connection error. Please try again.</span>';
                return;
            }
        }
        if (!fullText) {
            try {
                const res3 = await fetch(NexaAI.ajaxUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': NexaAI.csrfToken },
                    body: JSON.stringify({ message, use_rag: useRag })
                });
                const data = await res3.json();
                fullText = data.success ? data.response : ('Error: ' + (data.error || 'No response'));
            } catch(e3) {
                fullText = 'Connection error. Please try again.';
            }
        }
        el.innerHTML = NexaChat.renderBoardHTML(fullText);
        if (wrap) wrap.dataset.plain = fullText;
        document.getElementById('actions-' + msgId).style.display = '';
        NexaUI.scrollToBottom();
    },

    addUserMessage(text, imageFile) {
        const imgHtml = imageFile ? `<img src="${URL.createObjectURL(imageFile)}" style="max-width:180px;border-radius:8px;margin-top:6px;display:block;">` : '';
        const html = `
            <div class="msg-wrap">
                <div class="msg msg-user">
                    <div class="msg-body"><div class="msg-text">${NexaUI.escapeHtml(text)}${imgHtml}</div></div>
                </div>
            </div>`;
        NexaUI.elements.chatMessages.insertAdjacentHTML('beforeend', html);
    },

    async addAIMessage(text, timestamp) {
        const msgId = 'ai-msg-' + Date.now();
        const html = `
            <div class="msg-wrap" id="wrap-${msgId}">
                <div class="msg msg-ai">
                    <div class="msg-body">
                        <div class="msg-text board-render" id="${msgId}"></div>
                        <div class="msg-actions">
                            <button class="msg-action-btn" onclick="NexaVoice.speak(this.closest('.msg-wrap').dataset.plain)" title="Listen">
                                <i data-feather="volume-2" style="width:14px;height:14px"></i>
                            </button>
                            <button class="msg-action-btn" onclick="NexaUI.copyText(this.closest('.msg-wrap').dataset.plain)" title="Copy">
                                <i data-feather="copy" style="width:14px;height:14px"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>`;
        NexaUI.elements.chatMessages.insertAdjacentHTML('beforeend', html);
        if (window.feather) feather.replace();
        const el = document.getElementById(msgId);
        const wrap = document.getElementById('wrap-' + msgId);
        el.innerHTML = NexaChat.renderBoardHTML(text);
        if (wrap) wrap.dataset.plain = text;
        NexaUI.scrollToBottom();
    },

    renderBoardHTML(raw) {
        if (!raw) return '';
        var text = raw;
        text = text.replace(/\\\(/g, '$').replace(/\\\)/g, '$');
        text = text.replace(/\\\[/g, '$$').replace(/\\\]/g, '$$');
        text = text.replace(/(^|\n)\$([^$\n]+)\$(\n|$)/g, function(_, pre, m, post) {
            return (pre || '\n') + '$$' + m + '$$' + (post || '\n');
        });
        var mathStore = [];
        text = text.replace(/\$\$([\s\S]+?)\$\$/g, function(_, m) {
            var i = mathStore.length;
            mathStore.push({ display: true, src: m.trim() });
            return '\n\nNEXAMATH_D_' + i + '_END\n\n';
        });
        text = text.replace(/\$([^$\n]+?)\$/g, function(_, m) {
            var i = mathStore.length;
            mathStore.push({ display: false, src: m.trim() });
            return 'NEXAMATH_I_' + i + '_END';
        });
        var html = '';
        if (typeof marked !== 'undefined') {
            marked.setOptions({ breaks: true, gfm: true });
            html = marked.parse(text);
        } else {
            html = '<p>' + text.replace(/\n\n+/g, '</p><p>').replace(/\n/g, '<br>') + '</p>';
        }
        html = html.replace(/<p>\s*NEXAMATH_D_(\d+)_END\s*<\/p>/g, function(_, i) {
            return NexaChat._katex(mathStore[parseInt(i)]);
        });
        html = html.replace(/NEXAMATH_D_(\d+)_END/g, function(_, i) {
            return NexaChat._katex(mathStore[parseInt(i)]);
        });
        html = html.replace(/NEXAMATH_I_(\d+)_END/g, function(_, i) {
            return NexaChat._katex(mathStore[parseInt(i)]);
        });
        return html;
    },

    _katex(m) {
        if (typeof katex === 'undefined') {
            return m.display ? '<div class="br-math-display">$$' + m.src + '$$</div>' : '$' + m.src + '$';
        }
        try {
            var out = katex.renderToString(m.src, { displayMode: m.display, throwOnError: false });
            return m.display ? '<div class="br-math-display">' + out + '</div>' : out;
        } catch(e) {
            return m.display ? '<div class="br-math-display">$$' + m.src + '$$</div>' : '$' + m.src + '$';
        }
    }
};

// ── NexaVoice ──
const NexaVoice = {
    overlay: null, status: null, userText: null, aiText: null,
    recognition: null, interruptRecognition: null,
    synthesis: window.speechSynthesis, currentAudio: null,
    isListening: false, isProcessing: false, isActive: false,
    isSpeaking: false,
    webSearchTriggers: /\b(search|look up|google|find out|what is happening|latest|current|today|news|who is|where is|when did|wikipedia|weather|price|stock|score)\b/i,

    init() {
        this.overlay = document.getElementById('voice-overlay');
        this.status = document.getElementById('voice-status');
        this.userText = document.getElementById('voice-user-text');
        this.aiText = document.getElementById('voice-ai-text');
        this.micBtn = document.getElementById('voice-start-btn');
        this.setupRecognition();
        this.setupInterruptRecognition();
    },

    setupRecognition() {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) return;
        this.recognition = new SR();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        this.recognition.onstart = () => { this.isListening = true; this.updateStatus('Listening...', 'listening'); };
        this.recognition.onresult = (event) => {
            let final = '', interim = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) final += event.results[i][0].transcript;
                else interim += event.results[i][0].transcript;
            }
            if (interim && this.userText) this.userText.textContent = interim;
            if (final) { if (this.userText) this.userText.textContent = final; this.handleTranscript(final); }
        };
        this.recognition.onerror = (event) => { this.isListening = false; };
        this.recognition.onend = () => { this.isListening = false; if (this.isActive && !this.isProcessing && !this.isSpeaking) setTimeout(() => this.startListening(), 500); };
    },

    setupInterruptRecognition() {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) return;
        this.interruptRecognition = new SR();
        this.interruptRecognition.continuous = true;
        this.interruptRecognition.interimResults = true;
        this.interruptRecognition.lang = 'en-US';
        this.interruptRecognition.onresult = (event) => {
            if (!this.isSpeaking) return;
            let hasResult = false;
            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i][0].transcript.trim().length > 1) { hasResult = true; break; }
            }
            if (hasResult) this._handleInterrupt();
        };
        this.interruptRecognition.onend = () => { if (this.isSpeaking && this.isActive) { try { this.interruptRecognition.start(); } catch(e) {} } };
    },

    _handleInterrupt() {
        if (!this.isSpeaking) return;
        this.stopSpeaking();
        this.updateStatus('Interrupted — listening...', 'listening');
        setTimeout(() => { if (this.isActive) this.startListening(); }, 300);
    },

    startListening() { if (!this.recognition || this.isListening || this.isProcessing) return; try { this.recognition.start(); } catch(e) {} },
    stopListening() { if (!this.recognition) return; try { this.recognition.stop(); } catch(e) {} this.isListening = false; },
    open() {
        if (!this.overlay) this.init();
        this.isActive = true; this.overlay.classList.add('active');
        if (this.userText) this.userText.textContent = '';
        if (this.aiText) this.aiText.textContent = '';
        this.updateStatus('Listening...', 'listening');
        this.startListening();
    },
    close() {
        this.isActive = false; this.stopListening(); this.stopSpeaking();
        if (this.overlay) this.overlay.classList.remove('active');
    },
    updateStatus(text, state) {
        if (this.status) this.status.textContent = text;
        if (this.micBtn) this.micBtn.classList.toggle('listening', state === 'listening');
    },

    async processMessage(message) {
        if (this.isProcessing || !message.trim()) return;
        this.isProcessing = true; this.stopListening(); this.updateStatus('Thinking...', 'thinking');
        try {
            let data;
            if (this.webSearchTriggers.test(message)) {
                const res = await fetch(WEB_SEARCH_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
                    body: JSON.stringify({ message })
                });
                data = await res.json();
            } else {
                data = await NexaAI.sendToAI(message, true);
            }
            if (data.success) {
                this.updateStatus('Speaking...', 'speaking');
                if (this.aiText) this.aiText.textContent = '';
                await this.speak(data.response);
            }
        } finally { this.isProcessing = false; if (this.isActive) { this.updateStatus('Listening...', 'listening'); setTimeout(() => this.startListening(), 500); } }
    },

    speak(text) {
        return new Promise(async (resolve) => {
            if (!text) { resolve(); return; }
            this.isSpeaking = true;
            if (this.interruptRecognition) { try { this.interruptRecognition.start(); } catch(e) {} }
            const onDone = () => { this.isSpeaking = false; try { if (this.interruptRecognition) this.interruptRecognition.stop(); } catch(e) {} resolve(); };
            try {
                const response = await fetch(TTS_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
                    body: JSON.stringify({ text: text.substring(0, 2000) })
                });
                const data = await response.json();
                if (data.audio_url) {
                    const audio = new Audio(data.audio_url);
                    this.currentAudio = audio;
                    audio.onended = onDone;
                    audio.onerror = onDone;
                    audio.play().catch(onDone);
                } else { await this.speakWithBrowserTTS(text); onDone(); }
            } catch(e) { await this.speakWithBrowserTTS(text); onDone(); }
        });
    },

    speakWithBrowserTTS(text) {
        return new Promise((resolve) => {
            if (!text || !this.synthesis) { resolve(); return; }
            this.synthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.onend = resolve;
            utterance.onerror = resolve;
            this.synthesis.speak(utterance);
        });
    },

    stopSpeaking() {
        this.isSpeaking = false;
        if (this.synthesis) this.synthesis.cancel();
        if (this.currentAudio) this.currentAudio.pause();
        try { if (this.interruptRecognition) this.interruptRecognition.stop(); } catch(e) {}
    },
    toggleInput() { NexaVoice.open(); }
};

// ── NexaCamera ──
const NexaCamera = {
    stream: null,
    capturedBlob: null,
    open() { document.getElementById('camera-modal').classList.add('open'); },
    close() {
        this.stop();
        document.getElementById('camera-modal').classList.remove('open');
        this.capturedBlob = null;
    },
    async start() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
            const feed = document.getElementById('camFeed');
            feed.srcObject = this.stream;
            feed.style.display = 'block';
            document.getElementById('camIdleMsg').style.display = 'none';
            document.getElementById('camStartBtn').style.display = 'none';
            document.getElementById('camSnapBtn').style.display = '';
        } catch(e) { alert('Camera access denied'); }
    },
    snap() {
        const feed = document.getElementById('camFeed');
        const canvas = document.getElementById('camCanvas');
        canvas.width = feed.videoWidth; canvas.height = feed.videoHeight;
        canvas.getContext('2d').drawImage(feed, 0, 0);
        canvas.toBlob(blob => {
            this.capturedBlob = blob;
            const captured = document.getElementById('camCaptured');
            captured.src = URL.createObjectURL(blob);
            captured.style.display = 'block';
            feed.style.display = 'none';
            document.getElementById('camSnapBtn').style.display = 'none';
            document.getElementById('camRetakeBtn').style.display = '';
            document.getElementById('camSendBtn').style.display = '';
        }, 'image/jpeg', 0.9);
        this.stop();
    },
    retake() {
        this.capturedBlob = null;
        document.getElementById('camCaptured').style.display = 'none';
        this.start();
    },
    usePhoto() {
        if (!this.capturedBlob) return;
        const file = new File([this.capturedBlob], 'camera-photo.jpg', { type: 'image/jpeg' });
        NexaChat.pendingImage = file;
        const thumb = document.getElementById('image-preview-thumb');
        const strip = document.getElementById('image-preview-strip');
        if (thumb) thumb.src = URL.createObjectURL(file);
        if (strip) strip.style.display = 'flex';
        this.close();
    },
    stop() { if (this.stream) { this.stream.getTracks().forEach(t => t.stop()); this.stream = null; } }
};

// Init
document.addEventListener('DOMContentLoaded', () => {
    NexaUI.init();
    NexaVoice.init();
    document.querySelectorAll('.history-wrap').forEach(wrap => {
        const tmpl = wrap.querySelector('template.history-raw');
        const el = wrap.querySelector('.board-render');
        if (tmpl && el) {
            const raw = tmpl.innerHTML;
            el.innerHTML = NexaChat.renderBoardHTML(raw);
            wrap.dataset.plain = raw;
        }
    });
    NexaUI.scrollToBottom();
});
