/**
 * Onlink OS - Unified Core Module (v1.0.0)
 * Total Restoration with VDE Improvements
 */

let gameState = null;
let openWindows = {};
let zIndexCounter = 1000;
let startMenuOpen = false;
let mapInstance = null;
let mapMarkers = {};
let currentRemoteIp = null;
let currentBounceChain = [];
let lastMapNodes = [];
let bouncePolyline = null;
let mapSelectedNode = null;
let dragTarget = null, dragOffX = 0, dragOffY = 0;
let audioCtx = null;
let borderLayer = null; // Phase 23: GeoJSON borders
let activeNPCLines = []; // Phase 23: Visible blips

function setBackground(src) {
    const desktop = document.getElementById('desktop');
    if (!desktop) return;
    if (!src) {
        desktop.style.backgroundImage = 'none';
        desktop.style.backgroundColor = '#000';
    } else {
        desktop.style.backgroundImage = `linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('assets/wallpapers/${src}')`;
        desktop.style.backgroundSize = 'cover';
        desktop.style.backgroundPosition = 'center';
    }
}
const MusicManager = {
    player: null, currentId: null, volume: 0.2,
    tracks: { 'default': 'serenity', 'tense': 'mystique', 'action': 'A94FINAL', 'death': 'symphonic' },
    async init() {
        if (this.player) return true;
        if (typeof ChiptuneJsPlayer === 'undefined' || typeof libopenmpt === 'undefined') {
            console.warn("OS: Music Engine components not found.");
            return false;
        }
        if (libopenmpt.calledRun === false) {
            await new Promise(r => { const check = setInterval(() => { if (libopenmpt.calledRun) { clearInterval(check); r(); } }, 100); });
        }
        try {
            this.player = new ChiptuneJsPlayer(new ChiptuneJsConfig(-1));
            console.log("OS: Music Engine Initialized (Agnostic)");
            return true;
        } catch(e) { console.error("OS: Music Engine failure", e); return false; }
    },
    async play(id) {
        if (this.currentId === id) return;
        const ready = await this.init(); if (!ready) return;
        const baseName = this.tracks[id]; if (!baseName) return;
        this.stop(); this.currentId = id;
        const extensions = ['.s3m', '.xm', '.mod', '.it', '.uni'];
        for (const ext of extensions) {
            const src = `assets/music/${baseName}${ext}`;
            try {
                const response = await fetch(src, { method: 'HEAD' });
                if (response.ok) {
                    this.player.load(src, (buffer) => {
                        if (this.currentId === id && this.player) this.player.play(buffer);
                    });
                    console.log(`OS: Playing Tracker Scroll: ${src}`);
                    break;
                }
            } catch(e) {}
        }
    },
    stop() { if (this.player) { try { this.player.stop(); } catch(e) {} this.currentId = null; } },
    setVolume(v) { this.volume = v; }
};

// =========================================================================
// Initialization & Login
// =========================================================================
async function initLogin() {
    console.log("OS: Initializing Login Screen...");
    const userList = document.getElementById('user-list');
    const nameInput = document.getElementById('login-name');
    const codeInput = document.getElementById('login-code');
    const proceedBtn = document.getElementById('login-proceed');
    const newBtn = document.getElementById('login-new-user');
    const retireBtn = document.getElementById('login-retire');

    const refreshUserList = async () => {
        if (!userList) return [];
        userList.innerHTML = '<div style="color:var(--text-dim); padding:8px; font-style:italic;">Querying Uplink database...</div>';
        try {
            if (!window.eel || !window.eel.list_profiles) {
                userList.innerHTML = '<div style="color:var(--orange); padding:8px;">Awaiting Uplink Bridge...</div>';
                return [];
            }
            const profiles = await eel.list_profiles()();
            console.log("OS: Profiles received", profiles);
            if (!Array.isArray(profiles) || profiles.length === 0) {
                userList.innerHTML = '<div style="color:var(--text-dim); padding:8px; font-style:italic;">No profiles found</div>';
                return [];
            }
            userList.innerHTML = profiles.map(p => `<div class="user-name" style="cursor:pointer; padding:2px 5px;">${p}</div>`).join('');
            userList.querySelectorAll('.user-name').forEach(el => {
                el.onclick = () => {
                    const name = el.textContent.trim();
                    nameInput.value = name;
                    if (name === "TESTER") codeInput.value = "TESTER";
                    else codeInput.value = "";
                    codeInput.focus();
                };
            });
            return profiles;
        } catch (e) {
            console.error("OS: refreshUserList failed", e);
            userList.innerHTML = '<div style="color:var(--red); padding:8px;">CONNECTION ERROR</div>';
            return [];
        }
    };

    let currentProfiles = [];
    window.globalRefreshUserList = async () => { currentProfiles = await refreshUserList(); };

    // Wait for bridge then refresh
    let bridgeReady = false;
    for (let i = 0; i < 100; i++) {
        if (window.eel && window.eel.list_profiles) {
            bridgeReady = true;
            break;
        }
        await new Promise(r => setTimeout(r, 100));
    }

    if (bridgeReady) {
        currentProfiles = await refreshUserList();
    } else {
        console.error("OS: Eel bridge failed after 10s!");
        if (userList) userList.innerHTML = '<div style="color:var(--red); padding:8px;">BRIDGE TIMEOUT</div>';
    }

    if (proceedBtn) {
        proceedBtn.onclick = async () => {
            const name = nameInput.value.trim();
            const password = codeInput.value.trim();
            if (!name || !password) return alert("Credentials required.");
            
            // Activate audio on user gesture
            if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            if (audioCtx.state === 'suspended') audioCtx.resume();
            
            MusicManager.init().then(() => {
                if (MusicManager.player && MusicManager.player.context) {
                    if (MusicManager.player.context.state === 'suspended') {
                        MusicManager.player.context.resume();
                    }
                }
                MusicManager.play('default');
            });
            try {
                if (currentProfiles.includes(name)) {
                    const res = await eel.load_player_profile(name, password)();
                    if (res.success) await initOS();
                    else alert(res.error || "Invalid Authorization Code.");
                } else {
                    const res = await eel.set_player_profile(name, name, password)();
                    if (res.success) await initOS();
                    else alert("Profile creation failed.");
                }
            } catch (e) { console.error("OS: Login RPC failure", e); }
        };
    }
    if (newBtn) newBtn.onclick = () => { nameInput.value = ""; codeInput.value = ""; nameInput.focus(); };
    if (retireBtn) {
        retireBtn.onclick = async () => {
            const name = nameInput.value.trim();
            if (!name || !currentProfiles.includes(name)) return alert("Select an agent to retire.");
            if (confirm(`PERMANENTLY DELETE profile ${name}? This cannot be undone.`)) {
                await eel.delete_player_profile(name)();
                currentProfiles = await refreshUserList();
                nameInput.value = ""; codeInput.value = "";
            }
        };
    }
}

async function initOS() {
    const login = document.getElementById('login-screen');
    if (login) login.style.display = 'none';
    try {
        gameState = await eel.get_game_state()();
        updateHUD(); buildStartMenu();
        await setSpeed(1);
    } catch (e) { console.error("OS: Boot failure", e); }
}

window.setSpeed = setSpeed;

function updateHUD() {
    if (!gameState || !gameState.clock || !gameState.player) return;
    const el = (id) => document.getElementById(id);
    if (el('clock-display')) el('clock-display').textContent = gameState.clock.full_str || '00:00:00';
    
    // Financial HUD
    if (el('player-balance')) {
        const bal = el('player-balance');
        bal.textContent = gameState.player.balance_str || '0c';
        // Pulse red/orange if hot ratio is high
        if (gameState._hot_ratio > 0.1) {
            bal.style.color = "var(--orange)";
            bal.style.textShadow = "0 0 5px var(--red)";
        } else {
            bal.style.color = "var(--green)";
            bal.style.textShadow = "none";
        }
    }

    if (el('player-handle')) el('player-handle').textContent = gameState.player.handle;
    if (el('taskbar-clock')) el('taskbar-clock').textContent = gameState.clock.time_str || '00:00:00';
    
    // Neuromancer & Credit HUD
    if (el('neuromancer-display')) {
        let text = gameState.player.neuromancer_str || '';
        if (gameState.player.credit_score !== undefined) {
            text += ` | CS:${gameState.player.credit_score}`;
        }
        el('neuromancer-display').textContent = text;
    }

    if (el('connection-status')) el('connection-status').textContent = `LOCAL: ${gameState.player.localhost_ip || '127.0.0.1'}`;
}

async function setSpeed(speed) { await eel.set_speed(speed)(); }

async function buildStartMenu() {
    const appsContainer = document.getElementById('start-apps');
    if (appsContainer) appsContainer.innerHTML = '';
    try {
        const availableApps = await eel.list_apps()();
        const categories = {};
        availableApps.forEach(app => {
            if (!categories[app.category]) categories[app.category] = [];
            categories[app.category].push(app);
        });
        const categoryLabels = { network: 'NETWORK', system: 'SYSTEM', finance: 'FINANCE', tools: 'TOOLS' };
        for (const [cat, apps] of Object.entries(categories)) {
            const section = document.createElement('div');
            section.className = 'start-section';
            section.innerHTML = `<div class="start-section-title">${categoryLabels[cat] || cat.toUpperCase()}</div>`;
            const container = document.createElement('div');
            container.id = `start-${cat}-items`;
            apps.forEach(app => {
                const item = document.createElement('div');
                item.className = 'start-item';
                item.innerHTML = `<div class="start-icon">${app.icon}</div><span>${app.name}</span>`;
                item.onclick = (e) => { e.stopPropagation(); openApp(app.app_id); closeStartMenu(); };
                container.appendChild(item);
            });
            section.appendChild(container);
            if (appsContainer) appsContainer.appendChild(section);
        }
    } catch (e) { console.error("OS: Start Menu Build Failed", e); }
}

function toggleStartMenu() {
    startMenuOpen = !startMenuOpen;
    const menu = document.getElementById('start-menu');
    if (menu) { if (startMenuOpen) buildStartMenu(); menu.classList.toggle('open', startMenuOpen); }
}

function closeStartMenu() { startMenuOpen = false; const menu = document.getElementById('start-menu'); if (menu) menu.classList.remove('open'); }

document.addEventListener('click', (e) => {
    const menu = document.getElementById('start-menu'), btn = document.getElementById('start-btn');
    if (startMenuOpen && menu && !menu.contains(e.target) && e.target !== btn) closeStartMenu();
});

async function openApp(appId) {
    if (openWindows[appId]) {
        if (openWindows[appId].isMinimized) restoreApp(appId);
        else focusWindow(appId);
        return;
    }
    try {
        const allApps = await eel.list_apps()();
        const appDef = allApps.find(a => a.app_id === appId);
        if (!appDef) return showNotification("Software not available.", "warning");

        const appData = await eel.open_app(appId)();
        if (!appData || appData.error) { showNotification(appData ? appData.error : "No data from app", "critical"); return; }

        const container = document.getElementById('windows-container');
        const win = document.createElement('div');
        win.className = 'app-window open';
        win.id = `window-${appId}`;

        // Phase 24: High-Fidelity Workspace Scaling
        if (appId === 'map') {
            // Map defaults to full screen
            win.style.width = '100%';
            win.style.height = 'calc(100% - 66px)'; // HUD(30) + Taskbar(36)
            win.style.top = '30px';
            win.style.left = '0px';
            win.classList.add('maximized');
        } else {
            win.style.width = appDef.window_size[0] + 'px';
            win.style.height = appDef.window_size[1] + 'px';
            win.style.top = (40 + Object.keys(openWindows).length * 30) + 'px';
            win.style.left = (180 + Object.keys(openWindows).length * 30) + 'px';
        }
        win.style.zIndex = ++zIndexCounter;

        win.innerHTML = `
            <div class="title-bar" onmousedown="startDrag(event, document.getElementById('window-${appId}'))">
                <span>${appDef.name}</span>
                <div class="win-controls">
                    <button class="win-btn" onclick="toggleMaximize('${appId}')">□</button>
                    <button class="win-btn" onclick="minimizeApp('${appId}')">_</button>
                    <button class="win-btn win-close" onclick="closeApp('${appId}')">X</button>
                </div>
            </div>
            <div class="window-content" id="content-${appId}"></div>
            <div class="resize-handle" onmousedown="startResize(event, '${appId}')"></div>
        `;

        container.appendChild(win);
        openWindows[appId] = { el: win, appData, isMinimized: false };
        win.onmousedown = () => focusWindow(appId);
        
        // Ensure new window is focused
        focusWindow(appId);
        
        renderApp(appId, appData);
    } catch (e) { console.error("OS: openApp failure", e); }
}

function minimizeApp(appId) {
    const win = openWindows[appId];
    if (!win) return;
    win.isMinimized = true;
    win.el.classList.add('minimized');
    updateTaskbar();
}

function restoreApp(appId) {
    const win = openWindows[appId];
    if (!win) return;
    win.isMinimized = false;
    win.el.classList.remove('minimized');
    focusWindow(appId);
}

function toggleMaximize(appId) {
    const win = openWindows[appId];
    if (!win) return;
    
    if (win.el.classList.contains('maximized')) {
        // Restore
        win.el.classList.remove('maximized');
        win.el.style.width = win.oldWidth || '600px';
        win.el.style.height = win.oldHeight || '400px';
        win.el.style.top = win.oldTop || '100px';
        win.el.style.left = win.oldLeft || '200px';
    } else {
        // Maximize
        win.oldWidth = win.el.style.width;
        win.oldHeight = win.el.style.height;
        win.oldTop = win.el.style.top;
        win.oldLeft = win.el.style.left;
        
        win.el.classList.add('maximized');
        win.el.style.width = '100%';
        win.el.style.height = 'calc(100% - 66px)'; // HUD(30) + Taskbar(36)
        win.el.style.top = '30px';
        win.el.style.left = '0px';
    }
    
    if (appId === 'map' && mapInstance) {
        setTimeout(() => mapInstance.invalidateSize(), 200);
    }
}

function closeApp(appId) {
    const win = openWindows[appId];
    if (!win) return;
    if (appId === 'map' && mapInstance) { mapInstance.remove(); mapInstance = null; mapMarkers = {}; }
    win.el.remove();
    delete openWindows[appId];
    updateTaskbar();
}

function focusWindow(appId) {
    const win = openWindows[appId];
    if (!win) return;
    if (win.isMinimized) { restoreApp(appId); return; }
    
    // Remove active class from all, add to this one
    Object.values(openWindows).forEach(w => w.el.classList.remove('active'));
    win.el.classList.add('active');
    
    win.el.style.zIndex = ++zIndexCounter;
    updateTaskbar();
}

function startResize(e, appId) {
    e.preventDefault();
    e.stopPropagation();
    const win = openWindows[appId].el;
    const startX = e.clientX;
    const startY = e.clientY;
    const startWidth = parseInt(win.style.width);
    const startHeight = parseInt(win.style.height);

    const onMouseMove = (moveEvt) => {
        const newWidth = Math.max(300, startWidth + (moveEvt.clientX - startX));
        const newHeight = Math.max(200, startHeight + (moveEvt.clientY - startY));
        win.style.width = newWidth + 'px';
        win.style.height = newHeight + 'px';
        
        // Special case for map
        if (appId === 'map' && mapInstance) {
            mapInstance.invalidateSize();
        }
    };

    const onMouseUp = () => {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
}

// Phase 24: Global Logic Export
window.openApp = openApp;
window.toggleMaximize = toggleMaximize;
window.minimizeApp = minimizeApp;
window.restoreApp = restoreApp;
window.closeApp = closeApp;
window.startDrag = startDrag;
window.startResize = startResize;
window.winAction = winAction;

async function updateTaskbar() {
    const container = document.getElementById('taskbar-buttons');
    if (!container) return;
    try {
        const allApps = await eel.list_apps()();
        container.innerHTML = Object.keys(openWindows).map(appId => {
            const appDef = allApps.find(a => a.app_id === appId);
            const win = openWindows[appId];
            const isTop = !win.isMinimized && parseInt(win.el.style.zIndex) === zIndexCounter;
            return `<button class="taskbar-btn ${isTop ? 'active' : ''}" 
                onclick="winAction('${appId}')" style="${win.isMinimized ? 'opacity:0.5;' : ''}">${appDef ? appDef.icon : '?'} ${appDef ? appDef.name : appId}</button>`;
        }).join('');
    } catch (e) { console.error("OS: updateTaskbar failure", e); }
}

function winAction(appId) {
    const win = openWindows[appId];
    if (!win) return;
    if (win.isMinimized) restoreApp(appId);
    else if (parseInt(win.el.style.zIndex) === zIndexCounter) minimizeApp(appId);
    else focusWindow(appId);
}

function startDrag(e, win) {
    dragTarget = win;
    dragOffX = e.clientX - win.offsetLeft;
    dragOffY = e.clientY - win.offsetTop;
    win.style.zIndex = ++zIndexCounter;
    updateTaskbar();
}

document.addEventListener('mousemove', e => {
    if (dragTarget) {
        dragTarget.style.left = (e.clientX - dragOffX) + 'px';
        dragTarget.style.top = (e.clientY - dragOffY) + 'px';
    }
});

document.addEventListener('mouseup', () => {
    if (dragTarget) {
        const el = dragTarget, snapDist = 40, w = window.innerWidth, h = window.innerHeight, rect = el.getBoundingClientRect();
        if (rect.left < snapDist) el.style.left = '0px';
        if (rect.top < 30 + snapDist) el.style.top = '30px';
        if (w - rect.right < snapDist) el.style.left = (w - rect.width) + 'px';
        if (h - rect.bottom < 36 + snapDist) el.style.top = (h - 36 - rect.height) + 'px';
        dragTarget = null;
    }
});

function showDesktopMenu(e) {
    if (e.target.id !== 'desktop' && e.target.id !== 'windows-container') return;
    e.preventDefault();
    const menu = document.getElementById('desktop-menu');
    if (!menu) return;
    menu.style.left = e.clientX + 'px';
    menu.style.top = e.clientY + 'px';
    menu.classList.remove('hidden');

    const items = menu.querySelector('div[style="padding:4px 0;"]');
    if (items && !items.innerHTML.includes('WALLPAPER')) {
        items.innerHTML += `
            <div style="border-top:1px solid #111; margin:4px 0;"></div>
            <div class="start-header" style="padding:4px 8px; font-size:8px;">WALLPAPER</div>
            <div class="start-item" style="padding:4px 8px;" onclick="setBackground('default.jpg')">DEFAULT</div>
            <div class="start-item" style="padding:4px 8px;" onclick="setBackground('tactical.jpg')">TACTICAL</div>
            <div class="start-item" style="padding:4px 8px;" onclick="setBackground(null)">PURE VOID</div>
        `;
    }
}

function closeDesktopMenu() { const menu = document.getElementById('desktop-menu'); if (menu) menu.classList.add('hidden'); }
function closeAllWindows() { Object.keys(openWindows).forEach(appId => closeApp(appId)); closeDesktopMenu(); }
function resetWorkspace() { closeAllWindows(); openApp('map'); openApp('tasks'); }
document.addEventListener('mousedown', (e) => { const dmenu = document.getElementById('desktop-menu'); if (dmenu && !dmenu.contains(e.target)) closeDesktopMenu(); });

async function refreshApp(appId) {
    if (!openWindows[appId]) return;
    try {
        const appData = await eel.open_app(appId)();
        if (appData && !appData.error) {
            openWindows[appId].appData = appData;
            renderApp(appId, appData);
        }
    } catch (e) { console.error(`OS: refreshApp(${appId}) failure`, e); }
}

function interactWithIP(ip) {
    if (!ip) return;
    if (gameState && ip === gameState.player.localhost_ip) return showNotification("Localhost connection ignored.", "info");
    showNotification(`Node Identified: ${ip}`, "info");
    if (openWindows['map']) {
        focusWindow('map');
        if (typeof focusMapNode === 'function') focusMapNode(ip);
    }
}

function renderApp(appId, data) {
    const container = document.getElementById(`content-${appId}`); if (!container) return;
    switch (appId) {
        case 'map': renderMap(container, data); break;
        case 'remote': renderRemote(container, data); break;
        case 'tasks': renderTasks(container, data); break;
        case 'missions': renderMissions(container, data); break;
        case 'finance': renderFinance(container, data); break;
        case 'messages': renderMessages(container, data); break;
        case 'hardware': renderHardware(container, data); break;
        case 'store': renderStore(container, data); break;
        case 'news': renderNews(container, data); break;
        case 'rankings': renderRankings(container, data); break;
        case 'logistics': renderLogistics(container, data); break;
        case 'company': renderCompany(container, data); break;
        case 'terminal': renderTerminal(container, data); break;
        case 'memory_banks': renderMemoryBanks(container, data); break;
        case 'tutorial': renderTutorial(container, data); break;
    }
}

function renderFileServerScreen(el, s) {
    const files = s.files || [];
    el.innerHTML = `<div style="padding:15px; overflow-y:auto; height:100%;"><div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">FILE SERVER</div>${files.map(f => `<div style="border:1px solid #222; padding:8px; margin-bottom:4px; display:flex; justify-content:space-between; align-items:center;"><div><span style="color:#fff;">${f.name}</span> <span style="color:var(--text-dim); font-size:9px;">(${f.size}GQ)</span></div><div style="display:flex; gap:4px;"><button class="menu-btn" style="font-size:9px;" onclick="serverCopyFile('${f.name}')">COPY</button><button class="menu-btn" style="font-size:9px; background:#300; color:#a55;" onclick="serverDeleteFile('${f.name}')">DEL</button></div></div>`).join('') || '<div style="color:#333; text-align:center;">No files</div>'}</div>`;
}

function renderLinksScreen(el, s) {
    const links = s.links || [];
    el.innerHTML = `<div style="padding:15px;"><div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">LINKS</div>${links.map(l => `<div style="color:var(--cyan); cursor:pointer; margin-bottom:4px; font-size:11px;" onclick="interactWithIP('${l.ip || l}')">${l.name || l.ip || l}</div>`).join('') || '<div style="color:#333; text-align:center;">Empty</div>'}</div>`;
}

function renderPasswordScreen(el, s) {
    el.innerHTML = `<div style="padding:40px; text-align:center;"><div style="color:var(--red); font-weight:bold;">PASSWORD REQUIRED</div><div style="color:var(--text-dim); font-size:9px; margin-top:10px;">${s.hint || ''}</div></div>`;
}

function renderConsoleScreen(el, s) {
    el.innerHTML = `<div style="padding:15px; background:#000; height:100%; font-family:monospace; color:var(--green);">${s.cwd || '~'}</div>`;
}

function renderTasks(el, data) {
    const tasks = data.tasks || [];
    el.innerHTML = `<div style="padding:15px; height:100%; display:flex; flex-direction:column; background:rgba(0,10,20,0.6);">
            <div style="color:var(--cyan); font-weight:bold; margin-bottom:15px;">CPU TASK SCHEDULER</div><div style="flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:8px;">
                ${tasks.map(t => `<div style="border:1px solid #222; padding:10px; background:rgba(0,0,0,0.5); position:relative;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:5px;"><div style="color:#fff; font-weight:bold; font-size:11px;">${t.tool || t.name}</div><div style="color:var(--orange); font-family:monospace; font-size:11px;">${(t.progress*100).toFixed(0)}%</div></div>
                        <div style="background:#111; height:2px; width:100%;"><div style="width:${t.progress*100}%; height:100%; background:var(--orange);"></div></div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;"><span style="color:var(--text-dim); font-size:8px;">TARGET: ${t.target || 'N/A'}</span><button class="menu-btn" style="font-size:7px; background:#300; border-color:#500; color:#a55;" onclick="stopTask(${t.id})">TERMINATE</button></div></div>`).join('') || '<div style="color:#333; text-align:center; padding-top:40px;">CPU IDLE</div>'}
            </div></div>`;
}

function renderMemoryBanks(el, data) {
    const files = data.files || [];
    el.innerHTML = `<div style="padding:15px; height:100%; display:flex; flex-direction:column; background:rgba(0,5,10,0.8);"><div style="color:var(--cyan); font-weight:bold; margin-bottom:15px; display:flex; justify-content:space-between; align-items:center;"><span>VFS MEMORY BANKS</span><span style="font-size:9px; color:var(--text-dim);">${files.length} FILES</span></div><div style="flex:1; overflow-y:auto;"><div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap:15px; padding:10px;">${files.map(f => `<div class="vfs-icon" style="display:flex; flex-direction:column; align-items:center; gap:5px; cursor:pointer;" onclick="toggleTool('${f.id}')" oncontextmenu="event.preventDefault(); deleteVFSFile('${f.name}')"><div style="width:40px; height:40px; background:${f.loaded ? 'var(--cyan)' : '#111'}; border:1px solid ${f.loaded ? '#fff' : 'var(--p-blue)'}; display:flex; align-items:center; justify-content:center; font-size:18px; color:${f.loaded ? '#000' : '#444'}; box-shadow:${f.loaded ? '0 0 10px var(--cyan)' : 'none'};">${f.name.endsWith('.exe') ? 'EXE' : 'DAT'}</div><div style="font-size:8px; color:${f.loaded ? '#fff' : '#888'}; text-align:center; word-break:break-all; max-width:80px;">${f.name}<br>v${f.version}</div></div>`).join('')}</div></div><div style="border-top:1px solid #111; padding-top:10px; margin-top:10px; font-size:8px; color:var(--text-dim);">LEFT CLICK: LOAD/UNLOAD | RIGHT CLICK: DELETE</div></div>`;
}

async function toggleTool(id) { try { const res = await eel.toggle_tool(id)(); if (res.success) refreshApp('memory_banks'); } catch (e) {} }
async function deleteVFSFile(name) { if (!confirm(`Delete ${name}?`)) return; try { const res = await eel.delete_vfs_file(name)(); if (res.success) { showNotification(`Deleted ${name}`, "info"); refreshApp('memory_banks'); } else showNotification(res.error || "Failed", "critical"); } catch (e) {} }

function renderMap(el, data) {
    if (mapInstance) { mapInstance.remove(); mapInstance = null; mapMarkers = {}; }
    el.innerHTML = `<div style="display:grid; grid-template-columns: 1fr 200px; height:100%;"><div id="map-app-container" style="width:100%;height:100%;"></div><div style="background:rgba(0,10,20,0.9); border-left:1px solid #111; padding:10px; display:flex; flex-direction:column;"><div style="color:var(--cyan); font-weight:bold; font-size:9px; margin-bottom:10px;">NETWORK SEARCH</div><input id="map-search" type="text" placeholder="IP/Name..." style="width:100%; background:#000; border:1px solid #222; color:#fff; padding:4px; font-size:10px; outline:none;" oninput="searchMap(this.value)" /><div id="map-node-list" style="flex:1; overflow-y:auto; font-size:9px; margin-top:10px;"></div><div style="border-top:1px solid #111; padding-top:10px; margin-top:10px;"><div style="color:var(--yellow); font-size:9px; margin-bottom:5px;">SELECTED NODE</div><div id="map-selected-info" style="color:var(--text-dim); font-size:9px; margin-bottom:8px;">None</div><button id="map-connect-btn" class="menu-btn" style="width:100%; margin-bottom:5px; display:none;" onclick="mapConnectSelected()">CONNECT</button><button id="map-clear-chain-btn" class="menu-btn" style="width:100%; background:#300; color:#a55; display:none;" onclick="mapClearChain()">CLEAR CHAIN</button></div></div></div>`;
    setTimeout(() => initMapApp(data || {nodes: []}), 100);
}

function searchMap(query) { const list = document.getElementById('map-node-list'); if (!list || !lastMapNodes) return; const q = query.toLowerCase(); const filtered = lastMapNodes.filter(n => n.name.toLowerCase().includes(q) || n.ip.includes(q)); list.innerHTML = filtered.map(n => `<div class="user-name" style="padding:4px; border-bottom:1px solid #111; cursor:pointer;" onclick="focusMapNode('${n.ip}')">${n.name}<br><span style="color:var(--text-dim);">${n.ip}</span></div>`).join(''); }
function focusMapNode(ip) { const m = mapMarkers[ip]; if (m && mapInstance) { mapInstance.setView(m.getLatLng(), 4); m.openTooltip(); } }
async function mapConnectSelected() { if (!mapSelectedNode) return; currentRemoteIp = mapSelectedNode; const res = await eel.attempt_connect(mapSelectedNode)(); if (res.success) { showNotification("Connected", "info"); openApp('remote'); } else showNotification("Failed", "critical"); }
async function mapClearChain() { currentBounceChain = []; await eel.toggle_bounce('__clear__')(); updateMapVisuals(); }

function updateMapVisuals() {
    lastMapNodes.forEach(n => {
        const m = mapMarkers[n.ip]; if (!m) return;
        const inChain = currentBounceChain.includes(n.ip);
        const isSelected = mapSelectedNode === n.ip;
        m.setStyle({ color: isSelected ? '#fff' : (inChain ? '#ffaa00' : (n.type===1 ? '#00aaff' : '#0000ff')), fillColor: isSelected ? '#fff' : (inChain ? '#ffaa00' : (n.type===1 ? '#00aaff' : '#0000ff')), radius: n.type===1 ? 6 : (isSelected ? 5 : 3), weight: isSelected ? 2 : 1 });
    });
    drawBounceLines(lastMapNodes);
    const info = document.getElementById('map-selected-info'), connBtn = document.getElementById('map-connect-btn'), clearBtn = document.getElementById('map-clear-chain-btn');
    if (info) info.textContent = mapSelectedNode ? mapSelectedNode : 'None';
    if (connBtn) connBtn.style.display = mapSelectedNode ? 'block' : 'none';
    if (clearBtn) clearBtn.style.display = currentBounceChain.length > 0 ? 'block' : 'none';
}

async function initMapApp(data) {
    try { currentBounceChain = await eel.get_bounce_chain()(); } catch(e) { currentBounceChain = []; }
    lastMapNodes = data.nodes || []; mapSelectedNode = null;
    try {
        const container = document.getElementById('map-app-container'); if (!container) return;
        mapInstance = L.map('map-app-container', { center:[30,0], zoom:2, attributionControl:false, maxBounds: [[-85, -280], [85, 280]], maxBoundsViscosity: 1.0 });
        
        // Phase 24: Resilient Geometry
        const resizeObserver = new ResizeObserver(() => {
            if (mapInstance) mapInstance.invalidateSize();
        });
        resizeObserver.observe(container);

        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { 
            noWrap: true, // RESTORE SINGULARITY: No horizontal world repeats
            bounds: [[-85, -180], [85, 180]]
        }).addTo(mapInstance);
        
        lastMapNodes.forEach(n => {
            if (!n.x || !n.y) return;
            const marker = L.circleMarker([n.y, n.x], { radius:n.type===1?6:3, color:currentBounceChain.includes(n.ip)?'#ffaa00':(n.type===1?'#00aaff':'#0000ff'), fillColor:currentBounceChain.includes(n.ip)?'#ffaa00':(n.type===1?'#00aaff':'#0000ff'), fillOpacity:0.8 }).addTo(mapInstance);
            marker.bindTooltip(n.name.toUpperCase()+"<br>"+n.ip, { className:'hacker-tooltip', direction:'top' });
            marker.on('click', async () => { mapSelectedNode = n.ip; currentBounceChain = await eel.toggle_bounce(n.ip)(); updateMapVisuals(); });
            marker.on('dblclick', async (e) => { L.DomEvent.stopPropagation(e); currentRemoteIp = n.ip; const res = await eel.attempt_connect(n.ip)(); if (res.success) { showNotification("Connected to " + n.ip, "info"); openApp('remote'); } else showNotification("Failed", "critical"); });
            mapMarkers[n.ip] = marker;
        });
        drawBounceLines(lastMapNodes); updateMapVisuals();
    } catch(e) { console.error("OS: initMapApp failed:", e); }
}

function drawBounceLines(nodes) { if (bouncePolyline) mapInstance.removeLayer(bouncePolyline); if (currentBounceChain.length < 2) return; const latlngs = currentBounceChain.map(ip => { const n = nodes.find(node => node.ip === ip); return n ? [n.y, n.x] : null; }).filter(ll => ll !== null); bouncePolyline = L.polyline(latlngs, { color:'#ffaa00', weight:1, dashArray:'4, 6', opacity:0.6 }).addTo(mapInstance); }

function renderRemote(el, data) {
    const chainStr = currentBounceChain.length > 0 ? currentBounceChain.join(' > ') : 'Direct';
    el.innerHTML = `<div style="display:grid; grid-template-columns: 220px 1fr; height:100%; font-size:10px; background:#000; overflow:hidden;"><div style="padding:12px; border-right:1px solid #111; display:flex; flex-direction:column; background:rgba(0,10,20,0.4);"><div style="margin-bottom:15px;"><div style="color:var(--cyan); font-weight:bold; font-size:9px; margin-bottom:5px;">TARGET NODE</div><input id="remote-ip-input" type="text" placeholder="0.0.0.0" value="${currentRemoteIp || ''}" style="width:100%; background:#000; border:1px solid #222; color:#fff; padding:6px; font-family:monospace; outline:none;" /><div style="display:grid; grid-template-columns: 1fr 1fr; gap:4px; margin-top:6px;"><button class="menu-btn" onclick="remoteConnect()">CONNECT</button><button class="menu-btn" onclick="remoteDisconnect()" style="background:#300; color:#a55;">DROP</button></div></div><div style="margin-bottom:15px; border-top:1px solid #111; padding-top:10px;"><div style="color:var(--yellow); font-size:9px; margin-bottom:8px; font-weight:bold;">SECURITY STACK</div><div id="stack-container" style="display:flex; flex-direction:column; gap:6px;">${['proxy','firewall','monitor','encrypter'].map(s => `<div><div style="display:flex; justify-content:space-between; margin-bottom:2px; font-size:8px;"><span style="text-transform:uppercase;">${s}</span><span id="txt-${s}" style="color:var(--text-dim);">INACTIVE</span></div><div style="background:#050505; height:3px; border:1px solid #111;"><div id="bar-${s}" style="width:0%; height:100%; background:var(--cyan);"></div></div></div>`).join('')}</div></div><div id="remote-route" style="font-size:8px; color:var(--text-dim); margin-top:auto;">ROUTE: ${chainStr}</div></div><div style="display:flex; flex-direction:column; background:#020408;"><div id="remote-header" style="padding:10px 15px; border-bottom:1px solid #111; display:flex; justify-content:space-between; align-items:center; background:#050505;"><div><div id="srv-name" style="color:var(--cyan); font-weight:bold; font-size:12px;">NOT CONNECTED</div><div id="srv-ip" style="color:var(--text-dim); font-size:9px;">0.0.0.0</div></div><div id="trace-indicator-remote" class="hidden" style="text-align:right; min-width:120px;"><div style="color:var(--red); font-weight:bold; font-size:8px; margin-bottom:2px;">TRACE DETECTED</div><div style="background:#200; height:4px; width:100%;"><div id="trace-fill-remote" style="width:0%; height:100%; background:var(--red);"></div></div></div></div><div id="remote-content" style="flex:1; overflow:auto;"></div></div></div>`;
    if (currentRemoteIp) refreshRemote();
}

async function remoteConnect() { const ip = document.getElementById('remote-ip-input').value; if(!ip) return; const res = await eel.attempt_connect(ip)(); if (res.success) { currentRemoteIp = ip; refreshRemote(); } else showNotification("Failed: " + res.error, "critical"); }
async function remoteDisconnect() { await eel.disconnect()(); currentRemoteIp = null; refreshApp('remote'); }

async function refreshRemote() {
    if (!currentRemoteIp) return;
    try {
        const data = await eel.get_remote_state(currentRemoteIp)(); const content = document.getElementById('remote-content'); if (!content) return;
        document.getElementById('srv-name').textContent = data.server.name; document.getElementById('srv-ip').textContent = data.server.ip;
        const sec = data.server.security; ['proxy','firewall','monitor','encrypter'].forEach(s => updateSecurityStackBar(s, sec[s]));
        const trace = document.getElementById('trace-indicator-remote'); if (trace) { if (data.trace_active) { trace.classList.remove('hidden'); document.getElementById('trace-fill-remote').style.width = data.trace_progress + '%'; } else trace.classList.add('hidden'); }
        const s = data.current_screen; if (s) { if (s.html) content.innerHTML = s.html; else switch(s.type) { case 'menu': renderMenuScreen(content, s); break; case 'file_server': renderFileServerScreen(content, s); break; case 'logs': renderLogScreen(content, s); break; case 'bbs': renderBBSScreen(content, s); break; case 'links': renderLinksScreen(content, s); break; case 'academic': renderRecordScreen(content, s, "ACADEMIC", "cyan"); break; case 'criminal': renderRecordScreen(content, s, "CRIMINAL", "red"); break; case 'social_security': renderRecordScreen(content, s, "SOCSEC", "green"); break; case 'medical': renderRecordScreen(content, s, "MEDICAL", "orange"); break; case 'password': renderPasswordScreen(content, s); break; case 'console': renderConsoleScreen(content, s); break; } }
    } catch (e) { console.error("OS: refreshRemote failure", e); }
}

function updateSecurityStackBar(id, data) { 
    const bar = document.getElementById(`bar-${id}`), txt = document.getElementById(`txt-${id}`); 
    if (!bar || !txt) return; 
    if (data.active) { 
        txt.textContent = "LVL " + data.level; 
        txt.style.color = "var(--green)"; 
        bar.style.width = "100%"; 
        bar.style.background = "var(--cyan)";
    } else if (data.bypassed) {
        txt.textContent = "BYPASSED";
        txt.style.color = "var(--orange)";
        bar.style.width = "100%";
        bar.style.background = "var(--orange)";
    } else { 
        txt.textContent = "INACTIVE"; 
        txt.style.color = "#444"; 
        bar.style.width = "0%"; 
    } 
}
function renderMenuScreen(el, s) { 
    el.innerHTML = `
        <div style="padding:40px 20px; display:flex; flex-direction:column; align-items:center;">
            <div style="width:100%; max-width:600px; display:flex; flex-direction:column; gap:8px;">
                ${s.options.map(o => `<button class="menu-btn" style="text-align:left; padding:10px 15px; font-size:11px; letter-spacing:1px;" onclick="remoteNavigate(${o.screen_type})">${o.name.toUpperCase()}</button>`).join('')}
            </div>
        </div>`; 
}
async function remoteNavigate(type) { await eel.navigate_screen(currentRemoteIp, type)(); refreshRemote(); }
function renderLogScreen(el, s) { 
    el.innerHTML = `
        <div style="padding:20px; display:flex; flex-direction:column; align-items:center;">
            <div style="width:100%; max-width:800px;">
                <div style="color:var(--yellow); font-weight:bold; margin-bottom:15px; font-size:10px; letter-spacing:1px; border-bottom:1px solid #111; padding-bottom:5px;">ACCESS LOGS</div>
                ${s.logs.map(log_entry => `<div style="display:flex; justify-content:space-between; font-family:monospace; font-size:9px; border-bottom:1px solid #111; padding:6px 0;"><span style="color:var(--red);">${log_entry.subject}</span><span style="color:var(--cyan); cursor:pointer;" onclick="interactWithIP('${log_entry.from}')">${log_entry.from}</span><span style="color:var(--text-dim);">${log_entry.time}</span></div>`).join('') || '<div style="color:var(--text-dim); text-align:center; padding:20px;">No entries found.</div>'}
            </div>
        </div>`; 
}
function renderRecordScreen(el, s, title, theme) { 
    const records = s.recordbank || []; 
    el.innerHTML = `
        <div style="padding:15px; display:grid; grid-template-columns: 240px 1fr; gap:15px; height:100%;">
            <div style="border-right:1px solid #111; overflow-y:auto; background:rgba(0,0,0,0.2); padding-right:10px;">
                <div style="color:var(--${theme}); font-weight:bold; margin-bottom:10px; font-size:10px; letter-spacing:1px;">${title} DATABASE</div>
                ${records.map((r, i) => `<div class="user-name" style="padding:6px 8px; border-bottom:1px solid #111; cursor:pointer; font-size:11px;" onclick="viewRecord(${i}, '${theme}')">${r.name.toUpperCase()}</div>`).join('')}
            </div>
            <div id="record-detail" style="padding:20px; color:var(--text-dim); display:flex; flex-direction:column; align-items:center;">
                <div style="margin-top:100px; color:#333; letter-spacing:2px; font-size:10px;">SELECT RECORD FOR ANALYSIS</div>
            </div>
        </div>`; 
}
function viewRecord(idx, theme) {
    const records = window._recordData || [], r = records[idx], detail = document.getElementById('record-detail'); if (!r || !detail) return;
    detail.innerHTML = `<div style="display:flex; gap:15px; border-bottom:1px solid #111; padding-bottom:15px; margin-bottom:15px;"><div style="width:100px; height:120px; border:2px solid var(--${theme}); overflow:hidden;"><img src="https://i.pravatar.cc/150?img=${r.photo_index || 1}" style="width:100%; height:100%; object-fit:cover; filter:grayscale(100%);" /></div><div><div style="color:var(--${theme}); font-size:14px; font-weight:bold;">${r.name.toUpperCase()}</div></div></div><div style="display:flex; flex-direction:column; gap:8px;">${Object.entries(r.fields).map(([k,v]) => `<div style="display:flex; align-items:center; gap:10px;"><div style="min-width:120px;"><div style="color:var(--text-dim); text-transform:uppercase; font-size:8px;">${k}</div></div><div style="flex:1; color:#ccc; font-size:10px; background:#050505; padding:4px 6px; border:1px solid #222;">${v}</div><button class="menu-btn" style="font-size:8px; padding:2px 6px; white-space:nowrap;" onclick="alterField('${r.name}', '${k}', '${theme}')">ALTER</button></div>`).join('')}</div>`;
}

function alterField(recordName, fieldName, theme) {
    const records = window._recordData || [], r = records.find(rec => rec.name === recordName); if (!r) return;
    const newVal = prompt(`New value for ${fieldName}:`, r.fields[fieldName] || ''); if (newVal !== null) { eel.alter_record(currentRemoteIp, recordName, fieldName, newVal)().then(res => { if (res.success) { showNotification("Updated", "info"); refreshRemote(); } else showNotification("Failed", "critical"); }); }
}

async function renderFinance(el, data) { 
    try {
        const html = await eel.get_finance_html()();
        el.innerHTML = html;
    } catch (e) {
        el.innerHTML = `<div style="color:var(--red); padding:20px; text-align:center;">RENDER ERROR: ${e.message}</div>`;
    }
}
function renderHardware(el, data) {
    const heatPct = Math.min(100, ((data.heat || 0) / (data.max_heat || 90)) * 100).toFixed(1);
    const powerPct = data.psu_capacity > 0 ? ((data.power_draw / data.psu_capacity) * 100).toFixed(1) : 0;
    const tasks = data.tasks || [], vfsMap = data.vfs_map || [];
    const ramUsed = (data.ram_used || 0), ramTotal = (data.memory_gq || 8);
    const ramPct = ((ramUsed / ramTotal) * 100).toFixed(1);
    const storageUsed = (data.storage_used || 0), storageTotal = (data.storage_gq || 24);
    const storagePct = ((storageUsed / storageTotal) * 100).toFixed(1);

    el.innerHTML = `<div style="padding:15px; display:grid; grid-template-columns: 200px 1fr; gap:15px; height:100%;"><div style="border-right:1px solid #111;"><div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">${data.name || 'GATEWAY'}</div>${data.is_melted ? '<div style="color:var(--red); font-weight:bold;">MELTDOWN</div>' : `
        <div style="font-size:8px; color:var(--text-dim); margin-bottom:2px;">THERMALS: ${data.heat.toFixed(1)}°C</div><div style="background:#111; height:4px; margin-bottom:6px;"><div style="width:${heatPct}%; height:100%; background:var(--orange);"></div></div>
        <div style="font-size:8px; color:var(--text-dim); margin-bottom:2px;">POWER: ${data.power_draw.toFixed(1)}W</div><div style="background:#111; height:4px; margin-bottom:6px;"><div style="width:${powerPct}%; height:100%; background:var(--green);"></div></div>
        <div style="font-size:8px; color:var(--text-dim); margin-bottom:2px;">ACTIVE RAM: ${ramUsed}/${ramTotal}GQ</div><div style="background:#111; height:4px; margin-bottom:6px;"><div style="width:${ramPct}%; height:100%; background:var(--cyan);"></div></div>
        <div style="font-size:8px; color:var(--text-dim); margin-bottom:2px;">VFS STORAGE: ${storageUsed}/${storageTotal}GQ</div><div style="background:#111; height:4px; margin-bottom:6px;"><div style="width:${storagePct}%; height:100%; background:var(--p-blue);"></div></div>
        <div style="font-size:9px; color:var(--yellow); margin-bottom:4px; margin-top:10px;">VFS FRAGMENTATION</div><div style="display:grid; grid-template-columns: repeat(8,1fr); gap:1px; background:#050505; padding:2px;">${vfsMap.map(o => `<div style="height:8px; background:${o ? 'var(--p-blue)' : '#111'};"></div>`).join('')}</div>`}</div>
        <div><div style="color:var(--yellow); font-weight:bold; margin-bottom:8px;">PROCESSOR STACK</div>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:5px; margin-bottom:15px;">${data.cpus ? data.cpus.map(c => `<div style="border:1px solid #222; padding:4px; background:rgba(0,0,0,0.4);"><div style="color:#fff; font-size:9px;">SLOT ${c.id}</div><div style="color:var(--cyan); font-size:10px; font-weight:bold;">${c.speed}GHz</div></div>`).join('') : ''}</div>
        <div style="color:var(--yellow); font-weight:bold; margin-bottom:8px;">ACTIVE PROCESSES</div>${(tasks.length > 0 ? tasks : [{tool: 'System Idle', progress: 0}]).map(t => `<div style="padding:4px; font-size:9px; display:flex; justify-content:space-between;"><span style="color:#fff;">${t.tool || t.tool_name || '?'}</span><span style="color:var(--orange);">${((t.progress || 0) * 100).toFixed(0)}%</span></div>`).join('')}</div></div>`;
}

function renderRankings(el, data) { const r = data.rankings || []; el.innerHTML = `<div style="padding:15px; height:100%; overflow-y:auto;"><div style="color:var(--cyan); font-weight:bold; margin-bottom:15px;">AGENT RANKINGS</div>${r.map((a, i) => `<div style="display:flex; justify-content:space-between; padding:6px; border-bottom:1px solid #111; ${a.is_player?'background:rgba(0,170,255,0.1);':''}"> <span style="color:${a.is_player?'var(--cyan)':'#888'}">${i+1}. ${a.name}</span><span style="color:var(--green);">${a.rating}</span></div>`).join('')}</div>`; }
function renderMessages(el, data) { const m = data.messages || []; el.innerHTML = `<div style="padding:15px; height:100%; overflow-y:auto;">${m.map(msg => `<div style="border:1px solid #222; padding:10px; margin-bottom:5px; cursor:pointer;"><div style="display:flex; justify-content:space-between; font-weight:bold;"><span>${msg.from}</span><span style="color:var(--text-dim);">Tick ${msg.created_at_tick}</span></div><div style="color:var(--yellow);">${msg.subject}</div></div>`).join('') || '<div style="color:var(--text-dim); text-align:center;">Inbox empty</div>'}</div>`; }
function renderLogistics(el, data) { const m = data.manifests || []; el.innerHTML = `<div style="padding:15px; height:100%; overflow-y:auto;"><div style="color:var(--yellow); font-weight:bold; margin-bottom:10px;">GLOBAL SHIPMENTS</div>${m.map(x => `<div style="border:1px solid #222; padding:10px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; background:rgba(0,10,20,0.3);"><div><div style="color:#fff; font-weight:bold;">${x.cargo}</div><div style="color:var(--text-dim); font-size:9px;">${x.origin} -> ${x.destination}</div><div style="color:var(--cyan); font-size:8px; margin-top:4px;">Carrier: ${x.carrier} | Sec: ${x.security.toFixed(1)}</div></div><div style="text-align:right;"><div style="color:var(--orange); font-weight:bold;">${(x.progress*100).toFixed(1)}%</div><div style="color:var(--text-dim); font-size:8px;">${x.vehicle_type}</div>${x.vehicle_ip ? `<button class="menu-btn" style="font-size:7px; padding:1px 4px; margin-top:4px;" onclick="interactWithIP('${x.vehicle_ip}')">HACK VEHICLE</button>` : ''}</div></div>`).join('') || '<div style="color:var(--text-dim); text-align:center; padding-top:20px;">No shipments currently tracked.</div>'}</div>`; }
function renderTerminal(el, data) { const prompt = (data && data.prompt) || 'terminal'; el.innerHTML = `<div style="padding:15px; font-family:monospace; height:100%; display:flex; flex-direction:column;"><div id="terminal-output" style="flex:1; overflow-y:auto; color:#aaa;">Welcome to Onlink Terminal.</div><div style="display:flex; margin-top:5px;"><span style="color:var(--green); margin-right:5px;">${prompt}</span><input id="terminal-input" style="flex:1; background:transparent; border:none; color:#fff; outline:none;" onkeydown="if(event.key==='Enter')execTerminalCmd()" autofocus /></div></div>`; }

function renderCompany(el, data) {
    if (!data.owned) { el.innerHTML = `<div style="padding:40px; text-align:center;"><div style="color:var(--yellow); font-weight:bold; font-size:14px; margin-bottom:15px;">CORPORATE REGISTRATION</div><input id="new-comp-name" placeholder="COMPANY NAME" style="background:#000; border:1px solid #0af; color:#fff; padding:8px; margin-bottom:15px; outline:none; text-align:center;" /><br><div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; max-width:300px; margin:0 auto;"><button class="menu-btn" onclick="foundCompany(3)">PMC</button><button class="menu-btn" onclick="foundCompany(2)">LOGISTICS</button></div><div style="color:var(--text-dim); font-size:9px; margin-top:15px;">Cost: 10,000c</div></div>`; return; }
    const squads = data.squads || [], vehicles = data.vehicles || [], manifests = data.manifests || [];
    el.innerHTML = `<div style="padding:15px; height:100%; display:flex; flex-direction:column; overflow-y:auto;"><div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:15px;"><div><div style="color:var(--cyan); font-weight:bold; font-size:16px;">${data.name}</div><div style="font-size:9px; color:var(--text-dim);">TYPE: ${data.type} | STOCK: ${data.stock_price.toFixed(2)}c</div></div><div style="text-align:right;"><div style="color:var(--green); font-weight:bold; font-size:14px;">${data.balance.toLocaleString()}c</div><div style="font-size:8px; color:var(--text-dim);">TREASURY</div></div></div>${data.type === 'PMC' ? `<div style="margin-bottom:20px;"><div style="color:var(--yellow); font-size:10px; font-weight:bold; margin-bottom:8px; border-bottom:1px solid #222; padding-bottom:4px;">TACTICAL SQUADS</div>${squads.map(s => `<div style="border:1px solid #222; padding:8px; margin-bottom:5px; background:rgba(255,0,0,0.05); display:flex; justify-content:space-between; align-items:center;"><div><div style="color:#fff; font-weight:bold;">${s.name}</div><div style="color:var(--text-dim); font-size:8px;">Combat: ${s.combat.toFixed(1)} | Loc: ${s.location}</div></div><div style="text-align:right;"><div style="color:var(--cyan); font-size:9px;">${s.status}</div></div></div>`).join('') || '<div style="color:var(--text-dim); font-size:9px; text-align:center;">No squads enlisted.</div>'}</div>` : ''}<div style="margin-bottom:20px;"><div style="color:var(--yellow); font-size:10px; font-weight:bold; margin-bottom:8px; border-bottom:1px solid #222; padding-bottom:4px;">ACTIVE FLEET</div><div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap:5px;">${vehicles.map(v => `<div style="border:1px solid #222; padding:5px; text-align:center; background:rgba(0,170,255,0.05);"><div style="color:#fff; font-size:9px; font-weight:bold;">${v.name}</div><div style="color:var(--text-dim); font-size:8px;">${v.type} | ${v.status}</div></div>`).join('') || '<div style="color:var(--text-dim); font-size:9px; grid-column: 1 / -1; text-align:center;">No active assets.</div>'}</div></div><div><div style="color:var(--yellow); font-size:10px; font-weight:bold; margin-bottom:8px; border-bottom:1px solid #222; padding-bottom:4px;">ACTIVE CONTRACTS</div>${manifests.map(m => `<div style="border:1px solid #222; padding:8px; margin-bottom:5px; display:flex; justify-content:space-between; align-items:center;"><div><div style="color:#fff; font-size:10px;">${m.cargo}</div><div style="color:var(--text-dim); font-size:8px;">${m.origin} -> ${m.destination}</div></div><div style="text-align:right;"><div style="color:var(--orange); font-size:10px; font-weight:bold;">${(m.progress*100).toFixed(1)}%</div></div></div>`).join('') || '<div style="color:var(--text-dim); font-size:9px; text-align:center;">No active contracts.</div>'}</div></div></div>`;
}

function renderBBSScreen(el, s) { const missions = s.missions || []; el.innerHTML = `<div style="padding:15px; overflow-y:auto; height:100%; background:rgba(0,10,20,0.4);"><div style="color:var(--cyan); font-weight:bold; margin-bottom:15px; border-bottom:1px solid #222; padding-bottom:5px;">PUBLIC MISSION BOARD</div>${missions.map(m => `<div style="border:1px solid #222; padding:12px; margin-bottom:8px; background:rgba(0,0,0,0.3); display:flex; justify-content:space-between; align-items:center;"><div><div style="color:#fff; font-size:11px; font-weight:bold; margin-bottom:3px;">${m.employer || m.type}</div><div style="color:var(--text-dim); font-size:9px; line-height:1.2;">${m.description || ''}</div><div style="color:var(--green); font-size:10px; margin-top:5px; font-family:monospace;">${m.payment.toLocaleString()} Credits</div></div><div style="display:flex; flex-direction:column; gap:4px;"><button class="menu-btn" style="font-size:9px;" onclick="serverAcceptMission(${m.id})">ACCEPT</button><button class="menu-btn" style="font-size:9px; background:#222;" onclick="serverNegotiateMission(${m.id})">NEGOTIATE</button></div></div>`).join('') || '<div style="color:#333; text-align:center; padding-top:20px;">No public contracts listed.</div>'}</div>`; }
function renderStore(el, data) {
    const software = data.software || [], gateways = data.gateways || [], addons = data.addons || [], balance = data.balance || 0;
    // For modular hardware, we'll use a placeholder for now or query a new catalog
    el.innerHTML = `<div style="padding:15px; height:100%; overflow-y:auto; background:rgba(0,10,20,0.5);"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; border-bottom:1px solid #222; padding-bottom:8px;"><div style="color:var(--cyan); font-weight:bold; font-size:14px;">HARDWARE & SOFTWARE STORE</div><div style="color:var(--green); font-size:12px; font-weight:bold;">${balance.toLocaleString()}c</div></div><div class="store-grid" style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
        <div>
            <div style="color:var(--yellow); font-size:10px; font-weight:bold; margin-bottom:10px;">SOFTWARE CATALOG</div>
            ${software.map(s => `<div style="border:1px solid #222; padding:8px; margin-bottom:5px; background:rgba(0,0,0,0.3); display:flex; justify-content:space-between; align-items:center;"><div><div style="color:#fff; font-size:10px;">${s.name} v${s.version}</div><div style="color:var(--text-dim); font-size:8px;">${s.size}GQ</div></div><button class="menu-btn" style="font-size:9px;" onclick="serverBuySoftware('${s.name}', ${s.version})">${s.price}c</button></div>`).join('')}
        </div>
        <div>
            <div style="color:var(--yellow); font-size:10px; font-weight:bold; margin-bottom:10px;">GATEWAY SYSTEMS</div>
            ${gateways.map(g => `<div style="border:1px solid #222; padding:8px; margin-bottom:5px; background:rgba(0,170,255,0.05); display:flex; justify-content:space-between; align-items:center;"><div style="color:#fff; font-size:10px;">${g.name}</div><button class="menu-btn" onclick="serverBuyGateway('${g.name}')">${g.price}c</button></div>`).join('')}
            <div style="color:var(--yellow); font-size:10px; font-weight:bold; margin-top:15px; margin-bottom:10px;">MODULAR UPGRADES</div>
            <div style="display:flex; gap:5px; margin-bottom:10px;">
                <button class="menu-btn" style="font-size:8px;" onclick="showHardwareCategory('cpu')">CPUs</button>
                <button class="menu-btn" style="font-size:8px;" onclick="showHardwareCategory('modem')">MODEMS</button>
                <button class="menu-btn" style="font-size:8px;" onclick="showHardwareCategory('memory')">MEMORY</button>
            </div>
            <div id="hardware-category-list"></div>
            <div style="color:var(--yellow); font-size:10px; font-weight:bold; margin-top:15px; margin-bottom:10px;">ADDONS</div>
            ${addons.map(a => `<div style="border:1px solid #222; padding:8px; margin-bottom:5px; background:rgba(255,170,0,0.05); display:flex; justify-content:space-between; align-items:center;"><div style="color:#fff; font-size:10px;">${a.name}</div><button class="menu-btn" onclick="serverBuyAddon('${a.name}')">${a.price}c</button></div>`).join('')}
        </div>
    </div></div>`;
}

async function showHardwareCategory(cat) {
    const list = document.getElementById('hardware-category-list'); if (!list) return;
    list.innerHTML = '<div style="color:var(--text-dim); font-size:9px;">Loading catalog...</div>';
    // This requires a new bridge to get individual hardware items from constants
    const items = await eel.get_hardware_upgrades(cat)();
    list.innerHTML = items.map(i => `<div style="border:1px solid #111; padding:6px; margin-bottom:3px; display:flex; justify-content:space-between; align-items:center; background:rgba(0,0,0,0.2);"><div style="color:#ccc; font-size:9px;">${i.name}</div><button class="menu-btn" style="font-size:8px;" onclick="serverBuyModular('${cat}', '${i.name}')">${i.price}c</button></div>`).join('');
}

async function serverBuyModular(type, model) {
    let res;
    if (type === 'cpu') res = await eel.buy_cpu(0, model)();
    else if (type === 'modem') res = await eel.buy_modem(model)();
    else if (type === 'memory') res = await eel.buy_memory(model)();
    
    showNotification(res.success ? `Upgraded ${type}` : (res.error || "Failed"), res.success ? "info" : "critical");
    if (res.success) { refreshApp('store'); refreshApp('hardware'); }
}

function renderMissions(el, data) { const available = (data.available || []).concat(data.active || []); el.innerHTML = `<div style="padding:15px; overflow-y:auto; height:100%; background:rgba(0,10,20,0.4);"><div style="color:var(--cyan); font-weight:bold; margin-bottom:15px; border-bottom:1px solid #222; padding-bottom:5px;">MISSION BOARD</div>${available.map(m => `<div style="border:1px solid #222; padding:10px; margin-bottom:5px; background:rgba(0,0,0,0.3);"><div style="color:#fff; font-size:11px;">${m.employer || m.type}: ${m.description || ''}</div><div style="color:var(--green); font-size:9px;">Payment: ${m.payment}c</div></div>`).join('') || '<div style="color:#333; text-align:center;">No missions available</div>'}</div>`; }
function renderNews(el, data) { const articles = data.news || []; el.innerHTML = `<div style="padding:15px; overflow-y:auto; height:100%; background:rgba(0,5,10,0.8);"><div style="color:var(--cyan); font-weight:bold; margin-bottom:10px;">NEWS FEED</div>${articles.map(a => `<div style="border:1px solid #222; padding:10px; margin-bottom:5px; background:rgba(0,0,0,0.4);"><div style="color:#fff; font-size:11px;">${a.headline}</div><div style="color:var(--text-dim); font-size:9px;">${a.date}</div></div>`).join('') || '<div style="color:#333; text-align:center;">No news</div>'}</div>`; }

function renderTutorial(el, data) {
    const steps = [ { title: "Welcome, Agent", text: "Welcome to Sovereign Breach. This tutorial will guide you through your first operation.<br><br>Objective: Discover a target, bounce your connection, and gain access.", action: "Click NEXT to begin." }, { title: "Phase 1: The Backbone", text: `Your journey starts at InterNIC. Open the <b>MAP</b>, locate <b>InterNIC</b> (${data.internic_ip}), and double-click to connect.`, action: "Connect to InterNIC." }, { title: "Phase 2: Discovery", text: "Navigate to the <b>LINKS</b> screen on InterNIC. Click a link to save its IP to your map.", action: "Open the LINKS screen." }, { title: "Phase 3: Stealth", text: "Use the <b>MAP</b> to click on nodes and add them as <b>hops</b> in your bounce chain. A dotted line should appear.", action: "Add a hop to your bounce chain." }, { title: "Phase 4: Breach", text: "Encounter a password? Load <b>Password Breaker</b> from <b>Memory Banks</b> into RAM, then click the password field.", action: "Start a Password Breaker task." }, { title: "Phase 5: Cleanup", text: "Every action leaves a trace. Load <b>Log Deleter</b>, go to <b>LOGS</b>, and wipe your entry.", action: "Start a Log Deleter task." }, { title: "Tutorial Complete", text: "Training complete. You can now delete <b>tutorial.exe</b> from your <b>Memory Banks</b>.<br><br>Good luck.", action: "Tutorial Finished." } ];
    let currentStep = 0; const updateUI = () => {
        const s = steps[currentStep]; el.innerHTML = `<div style="padding:20px; display:flex; flex-direction:column; height:100%;"><div style="color:var(--cyan); font-weight:bold; font-size:16px; margin-bottom:10px;">${s.title}</div><div style="color:#ccc; font-size:12px; line-height:1.5; flex:1;">${s.text}</div><div style="border-top:1px solid #222; padding-top:15px; margin-top:15px;"><div id="tutorial-action" style="color:var(--yellow); font-size:10px; margin-bottom:10px; font-family:monospace;">${s.action}</div><button id="tutorial-next" class="menu-btn" style="width:100%;" ${currentStep === 0 || currentStep === steps.length - 1 ? '' : 'disabled'}>NEXT STEP</button></div></div>`;
        document.getElementById('tutorial-next').onclick = () => { if (currentStep < steps.length - 1) { currentStep++; updateUI(); } else closeApp('tutorial'); };
    }; updateUI();
    const iv = setInterval(async () => { if (!document.getElementById('window-tutorial')) { clearInterval(iv); return; } if (currentStep === 0 || currentStep === steps.length - 1) return; try { const res = await eel.call_app_func('tutorial', 'verify_step', currentStep)(); if (res === true) { const btn = document.getElementById('tutorial-next'), act = document.getElementById('tutorial-action'); if (btn) btn.disabled = false; if (act) { act.style.color = "var(--green)"; act.innerText = "STEP COMPLETED!"; } } } catch (e) {} }, 1000);
}

async function serverBuySoftware(name, version) { const res = await eel.buy_software(name, version)(); showNotification(res.success ? `Purchased ${name}` : (res.error || "Failed"), res.success ? "info" : "critical"); if (res.success) { refreshApp('store'); refreshRemote(); } }
async function serverBuyGateway(name) { const res = await eel.buy_gateway(name)(); showNotification(res.success ? `Purchased ${name}` : (res.error || "Failed"), res.success ? "info" : "critical"); if (res.success) { refreshApp('store'); refreshRemote(); } }
async function serverBuyCooling(name) { const res = await eel.buy_cooling(name)(); showNotification(res.success ? `Purchased ${name}` : (res.error || "Failed"), res.success ? "info" : "critical"); if (res.success) { refreshApp('store'); refreshRemote(); } }
async function serverBuyPSU(name) { const res = await eel.buy_psu(name)(); showNotification(res.success ? `Purchased ${name}` : (res.error || "Failed"), res.success ? "info" : "critical"); if (res.success) { refreshApp('store'); refreshRemote(); } }
async function serverBuyAddon(name) { const res = await eel.buy_addon(name)(); showNotification(res.success ? `Purchased ${name}` : (res.error || "Failed"), res.success ? "info" : "critical"); if (res.success) { refreshApp('store'); refreshRemote(); } }

eel.expose(update_hud);
function update_hud(data) {
    if(!gameState) { 
        gameState = data; 
        MusicManager.play('default'); 
    } else { 
        gameState.clock = { ...data.clock }; 
        gameState.player = { ...data.player }; 
        if (!MusicManager.currentId) MusicManager.play('default');
    }
    const traceInd = document.getElementById('trace-indicator'), traceBar = document.getElementById('trace-bar-fill');
    if(traceInd && traceBar && data.trace) {
        if(data.trace.active) { 
            traceInd.classList.remove('hidden'); 
            traceBar.style.width = (data.trace.progress*100)+'%'; 
            MusicManager.play('tense'); 
        } else { 
            traceInd.classList.add('hidden'); 
            MusicManager.play('default'); 
        }
    }
    updateHUD();
}
eel.expose(update_tasks);
function update_tasks(tasks) { if (!gameState) return; ['hardware','remote','memory_banks','tasks'].forEach(id => { if(openWindows[id]) id==='remote'?refreshRemote():refreshApp(id); }); }

eel.expose(trigger_event);
function trigger_event(evt) {
    if (evt.type === 'npc_map_blip') {
        drawNPCBlip(evt.source_ip, evt.target_ip, evt.duration);
    } else if (evt.type === 'conflict_shift') {
        showNotification(evt.msg, "warning");
        refreshBorders();
    } else if(evt.type==="forensics_update") showNotification(`Investigator reached ${evt.node}`, "warning"); 
    else if(evt.type==="forensics_lost") showNotification("Trail broken", "info");
    else if(evt.type==="arrest") { showArrestOverlay(evt); MusicManager.play('death'); } 
    else if(evt.type==="disavowed") { showDisavowedOverlay(evt); MusicManager.play('death'); } 
    else if(evt.type==="profile_deleted") { alert("PROFILE DELETED"); location.reload(); }
    else if(evt.type==="released") { document.getElementById('arrest-overlay')?.remove(); showNotification("Released", "info"); MusicManager.play('default'); } 
    else if(evt.type==="disavow_countdown") showNotification(`DISAVOWED: ${evt.ticks_left} ticks`, "critical"); 
    else if(evt.type==="game_over") { alert("GAME OVER: " + evt.msg); location.reload(); }
}

function showNotification(msg, type = "info") {
    const stack = document.getElementById('notif-stack'); if (!stack) return;
    const item = document.createElement('div'); item.className = `notif-item ${type}`;
    const icons = { info: 'i', warning: '!', critical: 'X' }; item.innerHTML = `<div class="notif-icon notif-${type}">${icons[type] || 'i'}</div><div class="notif-text">${msg}</div>`;
    stack.appendChild(item); setTimeout(() => item.classList.add('show'), 10);
    setTimeout(() => { item.classList.remove('show'); setTimeout(() => item.remove(), 400); }, 5000); playUISound(type === 'critical' ? 'alert' : 'notify');
}

function playUISound(type) {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (!audioCtx) return; const osc = audioCtx.createOscillator(), gain = audioCtx.createGain(), now = audioCtx.currentTime; osc.connect(gain); gain.connect(audioCtx.destination);
    if (type === 'click') { osc.type = 'sine'; osc.frequency.setValueAtTime(800, now); osc.frequency.exponentialRampToValueAtTime(100, now + 0.1); gain.gain.setValueAtTime(0.05, now); gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1); osc.start(now); osc.stop(now + 0.1); }
    else if (type === 'notify') { osc.type = 'triangle'; osc.frequency.setValueAtTime(440, now); osc.frequency.setValueAtTime(880, now + 0.1); gain.gain.setValueAtTime(0.03, now); gain.gain.exponentialRampToValueAtTime(0.01, now + 0.3); osc.start(now); osc.stop(now + 0.3); }
    else if (type === 'alert') { osc.type = 'sawtooth'; osc.frequency.setValueAtTime(100, now); osc.frequency.linearRampToValueAtTime(300, now + 0.2); gain.gain.setValueAtTime(0.03, now); gain.gain.linearRampToValueAtTime(0, now + 0.2); osc.start(now); osc.stop(now + 0.2); }
}

document.addEventListener('mousedown', (e) => { if (e.target.tagName === 'BUTTON' || e.target.classList.contains('start-item') || e.target.classList.contains('menu-btn')) playUISound('click'); });
document.addEventListener('keydown', async (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === 'Escape') { const topWinId = Object.keys(openWindows).sort((a, b) => parseInt(openWindows[b].el.style.zIndex) - parseInt(openWindows[a].el.style.zIndex))[0]; if (topWinId) closeApp(topWinId); }
    if (e.code === 'Space') { e.preventDefault(); const currentSpeed = gameState?.clock?.speed_multiplier || 1; await setSpeed(currentSpeed > 0 ? 0 : 1); showNotification(currentSpeed > 0 ? "Simulation Paused" : "Simulation Resumed", "info"); }
    if (e.key === 'Tab') { e.preventDefault(); const ids = Object.keys(openWindows).sort((a, b) => parseInt(openWindows[a].el.style.zIndex) - parseInt(openWindows[b].el.style.zIndex)); if (ids.length > 1) focusWindow(ids[0]); }
    if (e.altKey && e.key >= '1' && e.key <= '9') { const index = parseInt(e.key) - 1, ids = Object.keys(openWindows); if (ids[index]) focusWindow(ids[index]); }
});

function showArrestOverlay(evt) {
    const bailHtml = evt.bail_amount ? `<div style="color:var(--green); margin-top:10px;">Bail: ${evt.bail_amount}c <button onclick="payBailFromOverlay()" class="menu-btn" style="background:var(--green); color:#000; border:none; margin-left:5px;">PAY</button></div>` : '';
    const overlay = document.createElement('div'); overlay.id = 'arrest-overlay'; overlay.style.cssText = 'position:fixed; inset:0; background:rgba(0,0,0,0.95); z-index:10000; display:flex; flex-direction:column; align-items:center; justify-content:center; font-family:Consolas,monospace;';
    overlay.innerHTML = `<div style="max-width:500px; border:2px solid var(--red); padding:30px; background:#100; text-align:center;"><div style="color:var(--red); font-size:24px; font-weight:bold; margin-bottom:15px; text-shadow:0 0 10px var(--red);">ARRESTED</div><div style="color:#ccc; font-size:12px; margin-bottom:20px; line-height:1.6;"><div style="color:var(--orange); margin-bottom:10px;">OFFICIAL NOTICE OF ARREST</div><div>Reason: ${evt.reason || 'Investigation Complete'}</div><div>Jail Sentence: ${evt.jail_ticks || '?'} ticks</div><div>Balance Seized: ${evt.balance_remaining || 0}c remaining</div><div>Arrest Count: ${evt.arrest_count || 1}</div>${bailHtml}</div><button onclick="document.getElementById('arrest-overlay').remove()" class="menu-btn" style="background:var(--red); color:#fff; border:none; padding:8px 20px;">ACKNOWLEDGE</button></div>`;
    document.body.appendChild(overlay);
}

async function payBailFromOverlay() { try { const res = await eel.pay_bail()(); if (res.success) { showNotification(`Bail paid!`, "info"); document.getElementById('arrest-overlay')?.remove(); } else showNotification("Failed: " + (res.error || "unknown"), "critical"); } catch (e) {} }
function showDisavowedOverlay(evt) {
    const overlay = document.createElement('div'); overlay.id = 'disavowed-overlay'; overlay.style.cssText = 'position:fixed; inset:0; background:rgba(0,0,0,0.95); z-index:10000; display:flex; flex-direction:column; align-items:center; justify-content:center; font-family:Consolas,monospace;';
    overlay.innerHTML = `<div style="max-width:500px; border:2px solid var(--orange); padding:30px; background:#210; text-align:center;"><div style="color:var(--orange); font-size:24px; font-weight:bold; margin-bottom:15px; text-shadow:0 0 10px var(--orange);">DISAVOWED</div><div style="color:#ccc; font-size:12px; margin-bottom:20px; line-height:1.6;"><div style="color:var(--red); margin-bottom:10px;">PROFILE MARKED FOR DELETION</div><div>Reason: Multiple arrests</div></div><button onclick="document.getElementById('disavowed-overlay').remove(); location.reload();" class="menu-btn" style="background:var(--orange); color:#000; border:none; padding:8px 20px; font-weight:bold;">DELETE & RESTART</button></div>`;
    document.body.appendChild(overlay);
}

async function stopTask(id) { await eel.stop_task(id)(); refreshApp('tasks'); refreshApp('memory_banks'); }

async function applyTool(type, id) {
    if (!currentRemoteIp) return;
    // For now, we assume a selected tool or find the first active one
    const state = await eel.get_remote_state(currentRemoteIp)();
    const activeTool = state.local_ram.find(t => t.active);
    if (!activeTool) return showNotification("No active tool in RAM", "warning");

    const res = await eel.execute_hack(currentRemoteIp, activeTool.name, type, id.toString())();
    if (res.success) showNotification(`Executing ${activeTool.name}...`, "info");
    else showNotification(res.msg || "Hack failed", "critical");
    refreshRemote();
}

async function sendConsoleCmd() {
    const input = document.getElementById('console-input');
    const output = document.getElementById('console-output');
    if (!input || !currentRemoteIp) return;
    const cmd = input.value.trim();
    if (!cmd) return;
    input.value = '';
    const res = await eel.console_command(currentRemoteIp, cmd)();
    if (output) {
        output.innerHTML += `<div style="color:var(--green);">$ ${cmd}</div>`;
        if (res.output) res.output.forEach(line => { output.innerHTML += `<div>${line}</div>`; });
        if (res.error) output.innerHTML += `<div style="color:var(--red);">${res.error}</div>`;
        output.scrollTop = output.scrollHeight;
    }
}

async function serverAcceptMission(id) {
    const res = await eel.accept_mission(id)();
    if (res.success) { showNotification("Contract Accepted", "info"); refreshApp('missions'); refreshRemote(); }
    else showNotification(res.error || "Failed", "critical");
}

async function serverNegotiateMission(id) {
    const res = await eel.negotiate_mission(id)();
    if (res.success) { showNotification(`New Payment: ${res.new_payment}c`, "info"); refreshRemote(); }
    else showNotification(res.error || "Negotiation failed", "critical");
}

async function redirectTransportPrompt(manifestId) {
    const dest = prompt("Enter new destination IP or Name:");
    if (dest) {
        const res = await eel.redirect_transport(currentRemoteIp, manifestId, dest)();
        if (res.success) { showNotification("Shipment Redirected", "info"); refreshRemote(); }
        else showNotification(res.error || "Failed", "critical");
    }
}

async function sabotageTransportSecurity(manifestId) {
    const res = await eel.sabotage_transport(currentRemoteIp, manifestId)();
    if (res.success) { showNotification("Security Sabotaged", "info"); refreshRemote(); }
    else showNotification(res.error || "Failed", "critical");
}

async function foundCompany(type) {
 const name = document.getElementById('new-comp-name').value.trim(); if (name) { const res = await eel.found_company(name, type)(); if (res.success) { showNotification("Charter Granted", "info"); refreshApp('company'); } else alert(res.error); } }
async function execTerminalCmd() {
    const inp = document.getElementById('terminal-input'), out = document.getElementById('terminal-output'); const cmd = inp.value.trim(); inp.value = ''; out.innerHTML += `<div style="color:var(--green);">$ ${cmd}</div>`;
    if (cmd === 'ls') { const gs = await eel.get_game_state()(); out.innerHTML += `<div>${gs.vfs.join(' ')}</div>`; } else if (cmd === 'help') out.innerHTML += `<div>Commands: ls, clear, help</div>`; else if (cmd === 'clear') out.innerHTML = ''; out.scrollTop = out.scrollHeight;
}
window.onload = () => { initLogin(); };
