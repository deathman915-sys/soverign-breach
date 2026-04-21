/**
 * Onlink OS - Agent Rankings Module
 */
async function refreshRankings() {
    const rankings = await eel.get_rankings()();
    const container = document.getElementById('rankings-list');
    if (!container) return;

    if (rankings.length === 0) {
        container.innerHTML = `<div style="color:#444; text-align:center; margin-top:50px;">NO RANKINGS DATA</div>`;
        return;
    }

    container.innerHTML = `
        <table style="width:100%; font-size:11px; border-collapse:collapse;">
            <tr style="color:#666; border-bottom:1px solid #333;">
                <th style="text-align:left; padding:5px;">#</th>
                <th style="text-align:left; padding:5px;">Agent</th>
                <th style="text-align:right; padding:5px;">Rating</th>
            </tr>
            ${rankings.map((r, i) => `
                <tr style="border-bottom:1px solid #1a1a1a; ${r.is_player ? 'background:rgba(0,170,255,0.1);' : ''}">
                    <td style="padding:5px; color:${i < 3 ? 'var(--yellow)' : '#666'};">${i + 1}</td>
                    <td style="padding:5px; color:${r.is_player ? 'var(--cyan)' : '#aaa'};">${r.name} ${r.is_player ? '(YOU)' : ''}</td>
                    <td style="padding:5px; text-align:right; color:var(--green);">${r.rating}</td>
                </tr>
            `).join('')}
        </table>
    `;
}
