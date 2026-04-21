/**
 * Onlink OS - Remote Interface Module
 * Refactored from remote_prototype.html for unified OS integration.
 */

let remoteState = null;
let selectedTool = null;
let knownUsernames = ["admin", "readwrite", "guest", "root"];
let currentUserIndex = 0;

function cycleUsername() {
    currentUserIndex = (currentUserIndex + 1) % knownUsernames.length;
    document.getElementById('username-target').innerText = knownUsernames[currentUserIndex];
}

async function refreshRemote() {
    if (!currentRemoteIp) return;
    remoteState = await eel.get_remote_state(currentRemoteIp)();
    if (!remoteState || remoteState.error) {
        console.error("Remote error:", remoteState?.error);
        return;
    }

    // Update Header
    document.getElementById('srv-name').innerText = remoteState.server.name.toUpperCase();
    document.getElementById('srv-ip').innerText = remoteState.server.ip;

    // Security Bars (Simplified mapping)
    document.getElementById('bar-proxy').style.width = remoteState.server.security.proxy.active ? '100%' : '0%';
    document.getElementById('bar-firewall').style.width = remoteState.server.security.firewall.active ? '100%' : '0%';
    document.getElementById('bar-monitor').style.width = remoteState.server.security.monitor.active ? '100%' : '0%';

    // Tool List (RAM)
    document.getElementById('tool-list').innerHTML = remoteState.local_ram.map(t => `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:5px; border-bottom:1px solid #222; cursor:pointer; font-size:11px; color:${t.active?'#fff':'#666'}; background:${t.active?'#000044':'transparent'}" 
             onclick="handleToolClick('${t.id}')">
            <div>
                <span style="color:${t.active?'var(--green)':'#444'}">[${t.active?'RAM':'VFS'}]</span> 
                ${t.name.toUpperCase()} v1.0
            </div>
            <div style="font-size:9px; color:#888;">${t.size || 1} GQ</div>
        </div>`).join('');

    // Files Grid (Simplified: mock blocks if not provided)
    const grid = document.getElementById('vfs-grid');
    if (grid) {
        const blockStates = new Array(120).fill({type:'free', id:null});
        remoteState.server.files.forEach((f, idx) => {
            // Mock block assignment if f.blocks is missing
            const blocks = f.blocks || [idx * 2, idx * 2 + 1];
            blocks.forEach(b => { if(b < 120) blockStates[b] = {type:f.type, id:f.id}; });
        });

        grid.innerHTML = blockStates.map((b,i) => {
            const task = remoteState.tasks.find(t => t.target_id === b.id);
            return `<div class="vfs-block ${b.type} ${task?'cracking':''}" onclick="applyTool('file','${b.id}')">
                ${task?`<div class='progress-overlay' style='width:${task.progress}%'></div>`:''}
            </div>`;
        }).join('');
    }

    // Logs
    const logList = document.getElementById('log-list');
    if (logList) {
        logList.innerHTML = remoteState.server.logs.map((l,i) => {
            const task = remoteState.tasks.find(t => t.target_id === i.toString());
            return `<div class="log-row ${l.type} ${task?'cracking':''}" onclick="applyTool('log',${i})">
                <span>${l.time}</span><span>${l.from}</span><span>${l.action}</span>
                ${task?`<div class='progress-overlay' style='width:${task.progress}%'></div>`:''}
            </div>`;
        }).join('');
    }

    // Login View
    const loginContainer = document.getElementById('login-container');
    const crackTask = remoteState.tasks.find(t => t.target_id === 'password');
    if (remoteState.server.is_unlocked) {
        loginContainer.innerHTML = `<h3 style="color:var(--green)">SYSTEM ACCESS GRANTED</h3><div style="font-size:12px; color:var(--cyan); margin-top:10px;">Security clearance recognized.</div>`;
        document.getElementById('tab-files').classList.add('unlocked');
        document.getElementById('tab-logs').classList.add('unlocked');
    } else if (crackTask) {
        document.getElementById('crack-progress').classList.remove('hidden');
        document.getElementById('crack-progress').innerText = `CRACKING: ${Math.round(crackTask.progress * 100)}%`;
        document.getElementById('password-target').innerText = Math.random().toString(36).substring(7).toUpperCase();
    } else {
        document.getElementById('crack-progress').classList.add('hidden');
        document.getElementById('password-target').innerText = "********";
        document.getElementById('password-target').onclick = () => applyTool('password', knownUsernames[currentUserIndex]);
    }

    // Links View
    const linksTab = document.getElementById('tab-links');
    const linksList = document.getElementById('links-list');
    if (remoteState.server.links && remoteState.server.links.length > 0) {
        linksTab.classList.remove('hidden');
        linksTab.classList.add('unlocked');
        linksList.innerHTML = remoteState.server.links.map(l => `
            <div style="display:flex; justify-content:space-between; align-items:center; padding:8px; border:1px solid #222; background:#050505; font-size:11px;">
                <div>
                    <b style="color:var(--cyan)">${l.name.toUpperCase()}</b><br>
                    <span style="font-size:10px; color:#666;">${l.ip}</span>
                </div>
                <button class="menu-btn" style="padding:2px 10px; font-size:10px;" onclick="addLink('${l.ip}')">ADD</button>
            </div>
        `).join('');
    } else {
        linksTab.classList.add('hidden');
    }

    // Console View
    const consoleTab = document.getElementById('tab-console');
    if (remoteState.server.has_console && remoteState.server.is_unlocked) {
        consoleTab.classList.remove('hidden');
        consoleTab.classList.add('unlocked');
    } else {
        consoleTab.classList.add('hidden');
    }

    // Trace Logic
    if (remoteState.trace_active && remoteState.show_trace_warning) {
        document.getElementById('trace-container').classList.remove('hidden');
        document.getElementById('trace-fill').style.width = remoteState.trace_progress + '%';
    } else {
        document.getElementById('trace-container').classList.add('hidden');
    }
}

let spawnedWidgets = {};

async function handleToolClick(id) {
    const tool = remoteState.local_ram.find(t => t.id === id);
    if (!tool) return;
    
    if (!tool.active) {
        await eel.toggle_tool(id)();
        refreshRemote();
        return;
    }

    if (!spawnedWidgets[tool.id]) {
        spawnWidget(tool);
    }
}

function spawnWidget(tool) {
    const container = document.getElementById('task-widgets-container');
    if (!container) return;
    const widgetId = 'widget-' + tool.id;
    
    const widget = document.createElement('div');
    widget.className = 'window tool-widget';
    widget.id = widgetId;
    widget.style.position = 'absolute';
    widget.style.width = '200px';
    widget.style.top = (Math.random() * 200 + 100) + 'px';
    widget.style.left = (Math.random() * 200 + 100) + 'px';
    widget.style.zIndex = 1600;
    
    widget.innerHTML = `
        <div class="title-bar" style="background:var(--d-blue); border-bottom:1px solid var(--p-blue); padding:5px 10px; font-size:11px; font-weight:bold; display:flex; justify-content:space-between; align-items:center; cursor:move;">
            ${tool.name.toUpperCase()} v1.0
            <button class="win-close" style="background:none; border:1px solid #444; color:#888; cursor:pointer; padding:0 5px; font-size:10px;" onclick="closeWidget('${tool.id}')">X</button>
        </div>
        <div class="window-content" style="padding:10px; background:rgba(0,0,0,0.9); border:1px solid var(--p-blue); border-top:none;">
            <div class="status-text" style="font-size:10px; color:var(--cyan); margin-bottom:5px;">STATUS: IDLE</div>
            <button class="menu-btn target-btn" style="width:100%; margin-bottom:5px; background:var(--d-blue); border:1px solid var(--p-blue); color:var(--cyan); padding:5px; cursor:pointer; font-family:inherit; font-size:11px; font-weight:bold;" onclick="activateTargeting('${tool.id}')">TARGET</button>
            <div class="progress-bar-container" style="height:10px; border:1px solid #333; background:#111; display:none;">
                <div class="progress-fill" style="height:100%; width:0%; background:var(--orange);"></div>
            </div>
        </div>
    `;
    
    container.appendChild(widget);
    
    const titleBar = widget.querySelector('.title-bar');
    titleBar.onmousedown = (e) => {
        let mx = e.clientX, my = e.clientY;
        document.onmousemove = (ev) => {
            let x = mx - ev.clientX, y = my - ev.clientY;
            mx = ev.clientX; my = ev.clientY;
            widget.style.top = (widget.offsetTop - y) + "px";
            widget.style.left = (widget.offsetLeft - x) + "px";
        };
        document.onmouseup = () => { document.onmousemove = null; };
    };
    
    spawnedWidgets[tool.id] = tool;
}

function closeWidget(id) {
    const w = document.getElementById('widget-' + id);
    if (w) w.remove();
    delete spawnedWidgets[id];
}

function activateTargeting(id) {
    const tool = spawnedWidgets[id];
    if (!tool) return;
    selectedTool = tool;
    const cursor = document.getElementById('tool-cursor');
    cursor.innerText = "TARGET: " + selectedTool.name.toUpperCase();
    cursor.classList.remove('hidden');
}

function handleTaskUpdates(tasks) {
    if (!remoteState) return;
    
    const crackTask = tasks.find(t => t.extra && t.extra.target_id === 'password');
    if (crackTask && !remoteState.server.is_unlocked) {
        document.getElementById('crack-progress').classList.remove('hidden');
        document.getElementById('crack-progress').innerText = 'CRACKING: ' + Math.round(crackTask.progress * 100) + '%';
    }

    Object.values(spawnedWidgets).forEach(tool => {
        const widget = document.getElementById('widget-' + tool.id);
        if (!widget) return;
        
        const task = tasks.find(t => t.tool_name === tool.name);
        const statusDiv = widget.querySelector('.status-text');
        const progContainer = widget.querySelector('.progress-bar-container');
        const progFill = widget.querySelector('.progress-fill');
        const targetBtn = widget.querySelector('.target-btn');
        
        if (task) {
            statusDiv.innerText = "STATUS: ACTIVE";
            targetBtn.style.display = "none";
            progContainer.style.display = "block";
            progFill.style.width = (task.progress * 100) + "%";
        } else {
            statusDiv.innerText = "STATUS: IDLE";
            targetBtn.style.display = "block";
            progContainer.style.display = "none";
            progFill.style.width = "0%";
        }
    });
}

async function applyTool(type, id) {
    if (!selectedTool) return;
    const res = await eel.execute_hack(currentRemoteIp, selectedTool.name, type, id.toString())();
    if (res.msg) console.log("Hack response:", res.msg);
    selectedTool = null; 
    document.getElementById('tool-cursor').classList.add('hidden'); 
    refreshRemote();
}

async function toggleSecurity(sec_type) {
    // Only allow manual bypass if system is unlocked (admin access)
    if (!remoteState || !remoteState.server.is_unlocked) {
        alert("Admin access required to modify security subsystems.");
        return;
    }
    const res = await eel.toggle_remote_security(currentRemoteIp, sec_type)();
    if (!res.success) {
        alert("Failed: " + res.error);
    } else {
        refreshRemote();
    }
}

function switchRemoteView(view) {
    if (!remoteState.server.is_unlocked && view !== 'login' && view !== 'links') return;
    document.querySelectorAll('.view-content > div').forEach(v => v.classList.add('hidden'));
    document.querySelectorAll('.view-tab').forEach(t => t.classList.remove('active'));
    document.getElementById('view-' + view).classList.remove('hidden');
    document.getElementById('tab-' + view).classList.add('active');
    if (view === 'console') {
        clearConsole();
        // Focus input
        const input = document.getElementById('console-input');
        if (input) input.focus();
    }
}

async function addLink(ip) {
    const res = await eel.save_ip(ip)();
    if (res.success) {
        alert(res.msg);
        if (typeof syncMap === 'function') syncMap();
    } else {
        alert(res.msg);
    }
}

// Console functions
let consoleHistory = {};

async function sendConsoleCommand() {
    const input = document.getElementById('console-input');
    if (!input || !currentRemoteIp) return;
    const cmd = input.value.trim();
    if (!cmd) return;
    input.value = '';
    
    // Append command to output
    appendConsoleOutput(`> ${cmd}`);
    
    // Send to backend
    const res = await eel.console_command(currentRemoteIp, cmd)();
    if (res.output) {
        res.output.forEach(line => appendConsoleOutput(line));
    }
    if (res.cwd !== undefined) {
        // Update prompt maybe?
    }
}

function appendConsoleOutput(text) {
    const output = document.getElementById('console-output');
    if (!output) return;
    const line = document.createElement('div');
    line.textContent = text;
    output.appendChild(line);
    output.scrollTop = output.scrollHeight;
}

function clearConsole() {
    const output = document.getElementById('console-output');
    if (output) output.innerHTML = '';
}

// Global Mouse Listeners for Tool Targeting
window.addEventListener('mousedown', e => { 
    if(e.button === 2 && selectedTool) { 
        selectedTool = null; 
        document.getElementById('tool-cursor').classList.add('hidden'); 
        refreshRemote(); 
    } 
});

window.addEventListener('mousemove', e => { 
    if(selectedTool) { 
        const c = document.getElementById('tool-cursor'); 
        c.style.left = (e.clientX + 15) + "px"; 
        c.style.top = (e.clientY + 15) + "px"; 
    } 
});
