// Mobile Interactions for Study Materials

// Toggle Quick Actions Panel
function toggleQuickActions() {
    const panel = document.querySelector('.quick-actions-mobile');
    const backdrop = document.querySelector('.quick-actions-backdrop');
    const fab = document.querySelector('.quick-actions-fab');
    
    if (panel && backdrop) {
        const isOpen = panel.classList.toggle('open');
        backdrop.classList.toggle('open');
        
        if (fab) {
            fab.classList.toggle('active');
        }
    }
}

// Close quick actions on backdrop click
document.addEventListener('DOMContentLoaded', function() {
    const backdrop = document.querySelector('.quick-actions-backdrop');
    if (backdrop) {
        backdrop.addEventListener('click', toggleQuickActions);
    }
    
    // Close on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const panel = document.querySelector('.quick-actions-mobile');
            const backdrop = document.querySelector('.quick-actions-backdrop');
            if (panel && panel.classList.contains('open')) {
                panel.classList.remove('open');
                backdrop.classList.remove('open');
            }
        }
    });
    
    // Fix sidebar overlay pointer events
    const sidebarOverlay = document.querySelector('.sidebar-overlay');
    if (sidebarOverlay) {
        // Ensure overlay only blocks when sidebar is open
        const sidebar = document.querySelector('.sidebar');
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'class') {
                    const isOpen = sidebar.classList.contains('open');
                    if (isOpen) {
                        sidebarOverlay.style.pointerEvents = 'auto';
                        sidebarOverlay.style.opacity = '1';
                    } else {
                        sidebarOverlay.style.pointerEvents = 'none';
                        sidebarOverlay.style.opacity = '0';
                    }
                }
            });
        });
        
        if (sidebar) {
            observer.observe(sidebar, { attributes: true });
        }
    }
    
    // Add pulse animation to FAB on first load
    setTimeout(function() {
        const fab = document.querySelector('.quick-actions-fab');
        if (fab && window.innerWidth <= 992) {
            fab.classList.add('pulse');
            setTimeout(function() {
                fab.classList.remove('pulse');
            }, 500);
        }
    }, 1000);
    
    // Prevent body scroll when quick actions panel is open
    const quickActionsPanel = document.querySelector('.quick-actions-mobile');
    if (quickActionsPanel) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'class') {
                    if (quickActionsPanel.classList.contains('open')) {
                        document.body.style.overflow = 'hidden';
                    } else {
                        document.body.style.overflow = '';
                    }
                }
            });
        });
        
        observer.observe(quickActionsPanel, { attributes: true });
    }
});

// Toggle mobile menu (if not already defined)
if (typeof toggleMobileMenu === 'undefined') {
    function toggleMobileMenu() {
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.querySelector('.sidebar-overlay');
        
        if (sidebar && overlay) {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('open');
        }
    }
}

// Handle material card clicks on mobile
function handleMaterialCardClick(materialId) {
    if (window.innerWidth <= 768) {
        // On mobile, navigate to detail page
        window.location.href = `/materials/${materialId}/`;
    }
}

// Prevent zoom on double-tap for iOS
let lastTouchEnd = 0;
document.addEventListener('touchend', function(event) {
    const now = Date.now();
    if (now - lastTouchEnd <= 300) {
        event.preventDefault();
    }
    lastTouchEnd = now;
}, false);

// Add touch feedback to buttons
document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.btn, .toolbar-btn, .ai-quick-btn, .quick-actions-fab');
    
    buttons.forEach(function(button) {
        button.addEventListener('touchstart', function() {
            this.style.opacity = '0.7';
        });
        
        button.addEventListener('touchend', function() {
            this.style.opacity = '1';
        });
        
        button.addEventListener('touchcancel', function() {
            this.style.opacity = '1';
        });
    });
});

// Smooth scroll for mobile
if (window.innerWidth <= 768) {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}
