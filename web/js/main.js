/**
 * Onlink OS - Remote View Module
 * Handles the remote terminal view when connected to a server.
 */

let currentRemoteIp = null;

async function loadRemoteView(ip) {
    currentRemoteIp = ip;
    const view = document.getElementById('remote-view');
    if (!view) return;

    try {
        const state = await eel.get_remote_state(ip)();
        if (state.error) {
            view.innerHTML = `<div style="color:var(--red); text-align:center; margin-top:50px;">${state.error}</div>`;
            return;
        }

        const server = state.server;
        view.innerHTML = `
            <div style="font-size:11px;">
                <div style="color:var(--cyan); font-weight:bold; margin-bottom:10px; font-size:13px;">${server.name}</div>
                <div style="color:#666; font-size:9px; margin-bottom:15px;">IP: ${ip} | Type: ${server.type} | Difficulty: ${server.difficulty}</div>
                
                ${server.security ? `
                <div style="margin-bottom:15px;">
                    <div style="color:var(--yellow); font-size:10px; margin-bottom:5px;">SECURITY</div>
                    <div class="security-stack">
                        <div>
                            <div style="font-size:9px; color:#666;">Proxy</div>
                            <div class="sec-bar"><div class="sec-fill ${server.security.proxy.active ? 'active-blue' : ''}" style="width:${server.security.proxy.level * 20}%"></div></div>
                        </div>
                        <div>
                            <div style="font-size:9px; color:#666;">Firewall</div>
                            <div class="sec-bar"><div class="sec-fill ${server.security.firewall.active ? 'active-red' : ''}" style="width:${server.security.firewall.level * 20}%"></div></div>
                        </div>
                        <div>
                            <div style="font-size:9px; color:#666;">Monitor</div>
                            <div class="sec-bar"><div class="sec-fill ${server.security.monitor.active ? 'active-green' : ''}" style="width:${server.security.monitor.level * 20}%"></div></div>
                        </div>
                    </div>
                </div>` : ''}

                ${server.files && server.files.length > 0 ? `
                <div style="margin-bottom:15px;">
                    <div style="color:var(--yellow); font-size:10px; margin-bottom:5px;">FILES</div>
                    ${server.files.map(f => `
                        <div style="display:flex; justify-content:space-between; padding:3px 0; border-bottom:1px solid #111; font-size:10px;">
                            <span style="color:var(--orange);">${f.name}</span>
                            <span style="color:#666;">${f.size} GQ</span>
                        </div>
                    `).join('')}
                </div>` : ''}

                ${server.logs && server.logs.length > 0 ? `
                <div style="margin-bottom:15px;">
                    <div style="color:var(--yellow); font-size:10px; margin-bottom:5px;">LOGS (${server.logs.length})</div>
                    ${server.logs.map(l => `
                        <div style="display:flex; justify-content:space-between; padding:3px 0; border-bottom:1px solid #111; font-size:10px;">
                            <span style="color:var(--red);">${l.subject}</span>
                            <span style="color:#666;">${l.date}</span>
                        </div>
                    `).join('')}
                </div>` : ''}

                ${server.has_console ? `
                <div style="margin-bottom:15px;">
                    <div style="color:var(--yellow); font-size:10px; margin-bottom:5px;">CONSOLE</div>
                    <div style="display:flex; gap:5px;">
                        <input id="console-input" type="text" placeholder="Command..." style="flex:1; background:#000; border:1px solid #333; color:white; padding:4px; font-family:inherit; font-size:10px;" onkeydown="if(event.key==='Enter')sendConsoleCmd()" />
                        <button class="menu-btn" style="font-size:9px;" onclick="sendConsoleCmd()">EXEC</button>
                    </div>
                    <div id="console-output" style="max-height:150px; overflow-y:auto; margin-top:5px; font-size:9px; color:#888;"></div>
                </div>` : ''}

                ${state.local_ram && state.local_ram.length > 0 ? `
                <div>
                    <div style="color:var(--yellow); font-size:10px; margin-bottom:5px;">LOCAL RAM</div>
                    ${state.local_ram.map(t => `
                        <div class="tool-chip ${t.active ? 'active' : ''}" onclick="toggleRemoteTool('${t.id}')" style="margin-bottom:4px;">
                            <div class="tool-indicator"></div>
                            ${t.name}
                        </div>
                    `).join('')}
                </div>` : ''}
            </div>
        `;
    } catch (e) {
        view.innerHTML = `<div style="color:var(--red); text-align:center; margin-top:50px;">Error loading remote: ${e.message}</div>`;
    }
}

async function sendConsoleCmd() {
    const input = document.getElementById('console-input');
    const output = document.getElementById('console-output');
    if (!input || !output || !currentRemoteIp) return;

    const cmd = input.value.trim();
    input.value = '';

    const res = await eel.console_command(currentRemoteIp, cmd)();
    output.innerHTML += `<div style="color:var(--green);">$ ${cmd}</div>`;
    if (res.output) res.output.forEach(line => { output.innerHTML += `<div>${line}</div>`; });
    if (res.error) output.innerHTML += `<div style="color:var(--red);">${res.error}</div>`;
    output.scrollTop = output.scrollHeight;
}

async function toggleRemoteTool(toolId) {
    await eel.toggle_tool(toolId)();
    if (currentRemoteIp) loadRemoteView(currentRemoteIp);
}
