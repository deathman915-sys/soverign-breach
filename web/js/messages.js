/**
 * Onlink OS - Messages/Email Module
 */
async function refreshMessages() {
    const messages = await eel.get_messages()();
    const container = document.getElementById('messages-list');
    if (!container) return;

    if (messages.length === 0) {
        container.innerHTML = `<div style="color:#444; text-align:center; margin-top:50px;">NO MESSAGES</div>`;
        return;
    }

    container.innerHTML = messages.reverse().map(m => `
        <div style="border:1px solid ${m.is_read ? '#333' : 'var(--p-blue)'}; margin-bottom:8px; padding:10px; background:${m.is_read ? 'transparent' : 'rgba(0,170,255,0.05)'}; cursor:pointer;" onclick="readMessage(${m.id})">
            <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
                <span style="color:${m.is_read ? '#666' : 'var(--cyan)'}; font-weight:bold; font-size:11px;">${m.from}</span>
                <span style="color:#444; font-size:9px;">Tick ${m.created_at_tick}</span>
            </div>
            <div style="color:${m.is_read ? '#888' : 'var(--yellow)'}; font-size:11px; font-weight:bold;">${m.subject}</div>
            ${!m.is_read ? '<div style="color:var(--green); font-size:9px;">[NEW]</div>' : ''}
        </div>
    `).join('');
}

async function readMessage(id) {
    await eel.mark_message_read(id)();
    refreshMessages();
    const messages = await eel.get_messages()();
    const msg = messages.find(m => m.id === id);
    if (msg) {
        alert(`From: ${msg.from}\nSubject: ${msg.subject}\n\n${msg.body}`);
    }
}
