/**
 * OmniSearch v9.1 - Universal Command Palette & Navigation
 */

(function () {
    let omniIndex = { items: [] };
    let fuse = null;
    let isOpen = false;
    let selectedIndex = 0;
    let filteredItems = [];

    // Initialize UI
    const injectStyles = () => {
        const style = document.createElement('style');
        style.textContent = `
            #omni-overlay {
                position: fixed; inset: 0; background: rgba(2, 6, 23, 0.8);
                backdrop-filter: blur(8px); z-index: 9999; display: none;
                align-items: start; justify-content: center; padding-top: 10vh;
            }
            #omni-palette {
                width: 100%; max-width: 600px; background: #0f172a;
                border: 1px solid rgba(255,255,255,0.1); border-radius: 1.5rem;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                overflow: hidden; display: flex; flex-direction: column;
            }
            #omni-input {
                width: 100%; background: transparent; border: none;
                padding: 1.5rem; color: white; font-size: 1.1rem; outline: none;
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }
            #omni-results {
                max-height: 60vh; overflow-y: auto; padding: 0.5rem;
            }
            .omni-item {
                padding: 0.75rem 1rem; border-radius: 0.75rem; cursor: pointer;
                display: flex; justify-content: space-between; align-items: center;
                transition: all 0.2s;
            }
            .omni-item.selected { background: rgba(79, 70, 229, 0.2); border: 1px solid rgba(79, 70, 229, 0.3); }
            .omni-badge {
                font-size: 9px; font-weight: 800; text-transform: uppercase;
                padding: 2px 6px; border-radius: 4px; letter-spacing: 0.05em;
            }
            .badge-doc { background: rgba(16, 185, 129, 0.1); color: #10b981; }
            .badge-dictionary { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
            .badge-entity { background: rgba(99, 102, 241, 0.1); color: #6366f1; }
            .badge-command { background: rgba(244, 63, 94, 0.1); color: #f43f5e; }
        `;
        document.head.appendChild(style);
    };

    const createUI = () => {
        const overlay = document.createElement('div');
        overlay.id = 'omni-overlay';
        overlay.innerHTML = `
            <div id="omni-palette">
                <input type="text" id="omni-input" placeholder="Search Docs, Dictionary, Entities or Commands... (Esc to close)" autocomplete="off">
                <div id="omni-results"></div>
                <div style="padding: 0.75rem; font-size: 9px; color: #475569; text-transform: uppercase; border-top: 1px solid rgba(255,255,255,0.05); text-align: center; letter-spacing: 0.1em;">
                    ↑↓ navigate • Enter to go • Esc close
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        const input = document.getElementById('omni-input');
        input.addEventListener('input', (e) => updateResults(e.target.value));
        input.addEventListener('keydown', handleKeydown);
        overlay.addEventListener('click', (e) => { if (e.target === overlay) togglePalette(); });
    };

    const loadIndex = async () => {
        try {
            // Adjust path based on current window location
            const depth = window.location.pathname.split('/').filter(p => p).length;
            const prefix = window.location.pathname.includes('docs/') ? '../' : '';
            const res = await fetch(prefix + 'data/snapshots/omni_index.json');
            if (res.ok) {
                omniIndex = await res.json();
                filteredItems = omniIndex.items.slice(0, 10);
                renderResults();
            }
        } catch (e) { console.error("Failed to load Omni Index", e); }
    };

    const togglePalette = () => {
        const overlay = document.getElementById('omni-overlay');
        isOpen = !isOpen;
        overlay.style.display = isOpen ? 'flex' : 'none';
        if (isOpen) {
            document.getElementById('omni-input').focus();
            selectedIndex = 0;
            renderResults();
        }
    };

    const updateResults = (query) => {
        if (!query) {
            filteredItems = omniIndex.items.slice(0, 10);
        } else {
            const q = query.toLowerCase();
            filteredItems = omniIndex.items.filter(item =>
                item.title.toLowerCase().includes(q) ||
                item.subtitle.toLowerCase().includes(q) ||
                (item.tags && item.tags.some(t => t.toLowerCase().includes(q)))
            ).slice(0, 15);
        }
        selectedIndex = 0;
        renderResults();
    };

    const renderResults = () => {
        const container = document.getElementById('omni-results');
        container.innerHTML = filteredItems.map((item, i) => `
            <div class="omni-item ${i === selectedIndex ? 'selected' : ''}" onclick="window.omniNavigate(${i})">
                <div style="flex: 1">
                    <div style="font-weight: 700; color: #f8fafc; font-size: 14px">${item.title}</div>
                    <div style="font-size: 11px; color: #64748b">${item.subtitle}</div>
                </div>
                <div class="omni-badge badge-${item.kind}">${item.kind}</div>
            </div>
        `).join('') || '<div style="padding: 2rem; text-align: center; color: #475569">No results found.</div>';
    };

    window.omniNavigate = (index) => {
        const item = filteredItems[index];
        if (!item) return;

        let url = item.route.page;
        if (item.route.params) {
            const params = new URLSearchParams(item.route.params).toString();
            url += '?' + params;
        }

        // Correct path for pages in /docs
        if (!window.location.pathname.includes('docs/')) {
            // Already root, fine
        } else if (url.includes('docs/')) {
            url = url.replace('docs/', '');
        }

        window.location.href = url;
    };

    const handleKeydown = (e) => {
        if (e.key === 'ArrowDown') {
            selectedIndex = (selectedIndex + 1) % filteredItems.length;
            renderResults();
            e.preventDefault();
        } else if (e.key === 'ArrowUp') {
            selectedIndex = (selectedIndex - 1 + filteredItems.length) % filteredItems.length;
            renderResults();
            e.preventDefault();
        } else if (e.key === 'Enter') {
            window.omniNavigate(selectedIndex);
        } else if (e.key === 'Escape') {
            togglePalette();
        }
    };

    // Global Key Listener
    window.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            togglePalette();
        }
    });

    // Page Load Logic: Query Param Routing
    const handleQueryParams = () => {
        const params = new URLSearchParams(window.location.search);
        // Expose params to page global
        window.omniParams = Object.fromEntries(params.entries());
    };

    // Init
    document.addEventListener('DOMContentLoaded', () => {
        injectStyles();
        createUI();
        loadIndex();
        handleQueryParams();
    });

})();
