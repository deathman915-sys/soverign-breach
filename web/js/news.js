/**
 * Onlink OS - News Module
 */

async function refreshNews() {
    const news = await eel.get_news()();
    const container = document.getElementById('news-list');
    if (!container) return;

    if (news.length === 0) {
        container.innerHTML = `<div style="color:#444; text-align:center; margin-top:50px;">NO RECENT NEWS DATA</div>`;
        return;
    }

    container.innerHTML = news.map(n => `
        <div style="border:1px solid #222; margin-bottom:15px; padding:15px; background:rgba(0,170,255,0.02);">
            <div style="color:var(--orange); font-weight:bold; font-size:14px; margin-bottom:5px;">${n.headline.toUpperCase()}</div>
            <div style="font-size:10px; color:var(--cyan); margin-bottom:10px;">FILED: ${n.date}</div>
            <div style="font-size:12px; color:#ccc; line-height:1.4;">${n.body}</div>
        </div>
    `).join('');
}
