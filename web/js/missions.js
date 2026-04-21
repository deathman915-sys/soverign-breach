/**
 * Onlink OS - Mission BBS Module
 * Full mission UI: Available missions, Active missions, Complete button
 */

let currentMissions = [];
let currentActiveMissions = [];
let currentMissionTab = 'available';

async function refreshMissions() {
    if (currentMissionTab === 'active') {
        await refreshActiveMissions();
    } else {
        await refreshAvailableMissions();
    }
}

async function refreshAvailableMissions() {
    const missions = await eel.get_missions()();
    console.log("Missions loaded:", missions.length, missions);
    currentMissions = missions;
    const container = document.getElementById('available-missions');
    if (!container) return;

    if (missions.length === 0) {
        container.innerHTML = `<div style="color:var(--cyan); text-align:center; margin-top:50px;">
            <div style="font-size:14px; font-weight:bold; margin-bottom:10px;">NO CONTRACTS AVAILABLE</div>
            <div style="font-size:11px; color:#666;">New missions are generated periodically.</div>
            <div style="font-size:11px; color:#666;">Check back later or increase your Uplink Rating.</div>
        </div>`;
        return;
    }

    container.innerHTML = missions.map(m => `
        <div style="border:1px solid var(--p-blue); margin-bottom:15px; padding:15px; background:rgba(0,170,255,0.05); position:relative;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span style="color:var(--yellow); font-weight:bold;">${m.employer.toUpperCase()}</span>
                <span style="color:var(--green)">${m.payment.toLocaleString()}c ${m.is_negotiated ? '<span style="color:var(--cyan); font-size:9px;">(negotiated)</span>' : ''}</span>
            </div>
            <div style="font-size:12px; font-weight:bold; margin-bottom:10px;">MISSION ${m.id}: ${missionTypeToTitle(m.type)}</div>
            <div style="font-size:11px; color:#aaa; margin-bottom:15px; line-height:1.4;">${m.description}</div>
            <div style="display:flex; gap:10px; flex-wrap:wrap;">
                <button class="menu-btn" style="flex:1; min-width:120px;" onclick="acceptMission(${m.id})">ACCEPT MISSION</button>
                <button class="menu-btn" style="flex:1; min-width:120px;" onclick="previewTarget('${m.target_ip}')">LOCATE TARGET</button>
                ${!m.is_negotiated ? `<button class="menu-btn" style="flex:1; min-width:120px; background:var(--d-blue);" onclick="negotiateMission(${m.id})">CONTACT EMPLOYER</button>` : ''}
            </div>
        </div>
    `).join('');
}

async function refreshActiveMissions() {
    const missions = await eel.get_active_missions()();
    currentActiveMissions = missions;
    const container = document.getElementById('active-missions');
    if (!container) return;

    if (missions.length === 0) {
        container.innerHTML = `<div style="color:#444; text-align:center; margin-top:50px;">NO ACTIVE MISSIONS</div>`;
        return;
    }

    container.innerHTML = missions.map(m => {
        const timeStr = formatTicks(m.ticks_left);
        return `
        <div style="border:1px solid var(--orange); margin-bottom:15px; padding:15px; background:rgba(255,170,0,0.05); position:relative;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span style="color:var(--yellow); font-weight:bold;">${m.employer.toUpperCase()}</span>
                <span style="color:var(--green)">${m.payment.toLocaleString()}c ${m.is_negotiated ? '<span style="color:var(--cyan); font-size:9px;">(negotiated)</span>' : ''}</span>
            </div>
            <div style="font-size:12px; font-weight:bold; margin-bottom:10px;">MISSION ${m.id}: ${missionTypeToTitle(m.type)}</div>
            <div style="font-size:11px; color:#aaa; margin-bottom:10px; line-height:1.4;">${m.description}</div>
            <div style="display:flex; gap:15px; margin-bottom:15px; font-size:10px;">
                <span style="color:var(--cyan);">TARGET: ${m.target_ip}</span>
                <span style="color:var(--orange);">TIME LEFT: ${timeStr}</span>
            </div>
            <div style="display:flex; gap:10px; flex-wrap:wrap;">
                <button class="menu-btn" style="flex:1; min-width:120px; background:var(--green); color:#000;" onclick="completeMission(${m.id})">COMPLETE MISSION</button>
                <button class="menu-btn" style="flex:1; min-width:120px;" onclick="previewTarget('${m.target_ip}')">LOCATE TARGET</button>
            </div>
        </div>`;
    }).join('');
}

function formatTicks(ticks) {
    if (ticks === null || ticks === undefined) return 'N/A';
    const totalSeconds = Math.floor(ticks);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
}

function switchMissionTab(tab) {
    currentMissionTab = tab;
    document.querySelectorAll('.mission-tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-btn-' + tab).classList.add('active');
    
    document.getElementById('available-missions').classList.toggle('hidden', tab !== 'available');
    document.getElementById('active-missions').classList.toggle('hidden', tab !== 'active');
    
    refreshMissions();
}

function missionTypeToTitle(type) {
    const titles = {
        0: 'STEAL FILE',
        1: 'DELETE DATA',
        2: 'CHANGE ACADEMIC RECORDS',
        3: 'CHANGE CRIMINAL RECORDS',
        4: 'CHANGE SOCIAL SECURITY',
        5: 'CHANGE MEDICAL RECORDS',
        6: 'TRACE USER',
        7: 'FRAME USER',
        8: 'REMOVE COMPUTER',
        9: 'SPECIAL',
    };
    return titles[type] || 'UNKNOWN';
}

async function acceptMission(id) {
    const res = await eel.accept_mission(id)();
    if (res.success) {
        switchMissionTab('active');
    } else {
        alert(`Failed to accept mission: ${res.error}`);
    }
}

async function completeMission(id) {
    const res = await eel.complete_mission(id)();
    if (res.success) {
        alert(`Mission completed! Payment: ${res.payment}c, Rating +${res.rating_gain}`);
        refreshMissions();
        if (typeof refreshOS === 'function') refreshOS();
    } else {
        alert(`Cannot complete: ${res.error}`);
    }
}

async function previewTarget(ip) {
    if (typeof focusMapNode === 'function') focusMapNode(ip);
    alert("TARGET IP: " + ip + " - Check Map for locator pulse.");
}

async function negotiateMission(id) {
    const mission = currentMissions.find(m => m.id === id);
    if (!mission) return;
    
    const confirm = window.confirm(`Employer ${mission.employer} is willing to negotiate. Ask for 10% more payment?`);
    if (!confirm) return;
    
    const res = await eel.negotiate_mission(id, 0.1)();
    if (res.success) {
        alert(`Negotiation successful! New payment: ${res.new_payment}c`);
        refreshMissions();
    } else {
        alert(`Negotiation failed: ${res.msg}`);
    }
}
