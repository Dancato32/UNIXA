/**
 * NEXA AI - Unified Model Selection & State Management
 * Persists the user's selected model and handles the picker UI.
 */

const NexaModel = {
    storageKey: 'clutch_selected_model',
    defaultModel: 'openai/gpt-4o-mini',
    
    get current() {
        return localStorage.getItem(this.storageKey) || this.defaultModel;
    },
    
    set(modelId) {
        localStorage.setItem(this.storageKey, modelId);
        this.updateUI(modelId);
        // Dispatch global event for other listeners
        window.dispatchEvent(new CustomEvent('nexaModelChanged', { detail: modelId }));
    },
    
    updateUI(modelId) {
        // Update model badge if it exists in the topbar
        const badge = document.getElementById('model-badge-name');
        if (badge && window.__CLUTCH_MODELS__) {
            const found = window.__CLUTCH_MODELS__.find(m => m.id === modelId);
            if (found) badge.textContent = found.name;
        }
        
        // Highlight active option in picker
        document.querySelectorAll('.model-option').forEach(el => {
            el.classList.toggle('active', el.getAttribute('data-model-id') === modelId);
        });
    }
};

const ModelPicker = {
    loaded: false,
    isOpen: false,
    async load(modelsUrl) {
        if (this.loaded) return;
        try {
            const res = await fetch(modelsUrl);
            const data = await res.json();
            window.__CLUTCH_MODELS__ = data.models;
            this.render(data.models);
            this.loaded = true;
            NexaModel.updateUI(NexaModel.current);
        } catch(e) { console.error('Failed to load models', e); }
    },
    render(models) {
        const container = document.getElementById('model-picker-list');
        if (!container) return;
        
        const groups = {};
        models.forEach(m => {
            if (!groups[m.provider]) groups[m.provider] = [];
            groups[m.provider].push(m);
        });
        
        let html = '';
        for (const [provider, items] of Object.entries(groups)) {
            html += `<div class="provider-group">
                <div class="provider-label provider-${provider}">${provider}</div>`;
            items.forEach(m => {
                html += `<div class="model-option" data-model-id="${m.id}" onclick="ModelPicker.select('${m.id}')">
                    <div class="model-option-left">
                        <span class="model-option-name">${m.name}</span>
                        <span class="model-option-id">${m.id}</span>
                    </div>
                    <span class="model-badge badge-${m.badge}">${m.badge}</span>
                </div>`;
            });
            html += '</div>';
        }
        container.innerHTML = html;
    },
    toggle() {
        if (!this.isOpen) this.open(); else this.close();
    },
    open() {
        document.getElementById('model-picker-overlay').classList.add('open');
        document.getElementById('model-picker-panel').style.display = 'block';
        this.isOpen = true;
        NexaModel.updateUI(NexaModel.current);
    },
    close() {
        const overlay = document.getElementById('model-picker-overlay');
        const panel = document.getElementById('model-picker-panel');
        if (overlay) overlay.classList.remove('open');
        if (panel) panel.style.display = 'none';
        this.isOpen = false;
    },
    select(modelId) {
        NexaModel.set(modelId);
        const models = window.__CLUTCH_MODELS__ || [];
        const found = models.find(m => m.id === modelId);
        if (found) {
            this.showToast('✓ Switched to ' + found.name);
        }
        this.close();
    },
    showToast(msg) {
        const toast = document.createElement('div');
        toast.style.cssText = 'position:fixed;bottom:100px;left:50%;transform:translateX(-50%);background:rgba(15,23,42,0.95);border:1px solid rgba(59,130,246,0.3);color:#fff;padding:10px 20px;border-radius:20px;font-size:13px;font-weight:700;z-index:9999;animation:pickerIn 0.3s ease;pointer-events:none;';
        toast.textContent = msg;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2500);
    }
};
