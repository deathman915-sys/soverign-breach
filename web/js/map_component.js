/**
 * Onlink-Clone: High-Fidelity Map Component (Ultra-Polished)
 */

class WorldMap {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        
        this.nodes = [];
        this.bounceChain = [];
        this.hoveredNode = null;
        this.pulse = 0;

        this.onNodeClick = options.onNodeClick || (() => {});
        this._initEvents();
        
        // Start animation loop for pulsing nodes
        this._animate();
    }

    setNodes(nodes) {
        this.nodes = nodes;
        this.draw();
    }

    setBounceChain(chain) {
        this.bounceChain = chain;
        this.draw();
    }

    _initEvents() {
        this.canvas.addEventListener('click', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const pos = { x: e.clientX - rect.left, y: e.clientY - rect.top };
            const node = this._hitTest(pos);
            if (node) this.onNodeClick(node);
        });

        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const pos = { x: e.clientX - rect.left, y: e.clientY - rect.top };
            const node = this._hitTest(pos);
            if (this.hoveredNode !== node) {
                this.hoveredNode = node;
            }
        });
    }

    _animate() {
        this.pulse = (Math.sin(Date.now() / 300) + 1) / 2; // 0 to 1
        this.draw();
        requestAnimationFrame(() => this._animate());
    }

    _hitTest(pos) {
        const { mapW, mapH, offsetX, offsetY } = this._getLayout();
        for (const n of this.nodes) {
            const nx = offsetX + (n.x / 600) * mapW;
            const ny = offsetY + (n.y / 300) * mapH;
            if (Math.hypot(pos.x - nx, pos.y - ny) < 12) return n;
        }
        return null;
    }

    _getLayout() {
        const rect = this.canvas.getBoundingClientRect();
        const w = rect.width;
        const h = rect.height;
        
        // World is roughly 2:1 aspect ratio
        let mapW = w;
        let mapH = w / 2;
        if (mapH > h) {
            mapH = h;
            mapW = h * 2;
        }
        
        return {
            w, h,
            mapW, mapH,
            offsetX: (w - mapW) / 2,
            offsetY: (h - mapH) / 2
        };
    }

    draw() {
        const dpr = window.devicePixelRatio || 1;
        const { w, h, mapW, mapH, offsetX, offsetY } = this._getLayout();
        if (w === 0) return;

        this.canvas.width = w * dpr;
        this.canvas.height = h * dpr;
        this.ctx.scale(dpr, dpr);

        // 1. Background
        this.ctx.fillStyle = '#000';
        this.ctx.fillRect(0, 0, w, h);

        // 2. Global Grid
        this.ctx.strokeStyle = 'rgba(0, 100, 255, 0.05)';
        this.ctx.lineWidth = 0.5;
        const step = mapW / 20;
        for(let x = offsetX; x <= offsetX + mapW; x += step) {
            this.ctx.beginPath(); this.ctx.moveTo(x, offsetY); this.ctx.lineTo(x, offsetY + mapH); this.ctx.stroke();
        }
        for(let y = offsetY; y <= offsetY + mapH; y += step) {
            this.ctx.beginPath(); this.ctx.moveTo(offsetX, y); this.ctx.lineTo(offsetX + mapW, y); this.ctx.stroke();
        }

        // 3. Continents
        const mapData = window.WORLD_MAP_DATA;
        if (mapData) {
            this.ctx.strokeStyle = '#0044aa';
            this.ctx.fillStyle = 'rgba(0, 20, 80, 0.4)';
            this.ctx.lineWidth = 1.5;
            
            const sx = mapW / 1000;
            const sy = mapH / 1000;

            for (const name in mapData) {
                const shape = mapData[name];
                this.ctx.beginPath();
                shape.forEach(([x, y], i) => {
                    const px = offsetX + x * sx;
                    const py = offsetY + y * sy;
                    if(i === 0) this.ctx.moveTo(px, py);
                    else this.ctx.lineTo(px, py);
                });
                this.ctx.closePath();
                this.ctx.fill();
                this.ctx.stroke();
            }
        }

        // 4. Background Backbone Links (Subtle)
        this.ctx.strokeStyle = 'rgba(0, 80, 255, 0.15)';
        this.ctx.lineWidth = 1;
        for (let i = 0; i < this.nodes.length; i++) {
            for (let j = i + 1; j < this.nodes.length; j++) {
                const n1 = this.nodes[i], n2 = this.nodes[j];
                this.ctx.beginPath();
                this.ctx.moveTo(offsetX + (n1.x/600)*mapW, offsetY + (n1.y/300)*mapH);
                this.ctx.lineTo(offsetX + (n2.x/600)*mapW, offsetY + (n2.y/300)*mapH);
                this.ctx.stroke();
            }
        }

        // 5. Bounce Chain (Dashed White)
        if (this.bounceChain.length > 1) {
            this.ctx.strokeStyle = '#fff';
            this.ctx.setLineDash([4, 4]);
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.bounceChain.forEach((ip, i) => {
                const n = this.nodes.find(node => node.ip === ip);
                if (n) {
                    const nx = offsetX + (n.x / 600) * mapW;
                    const ny = offsetY + (n.y / 300) * mapH;
                    if (i === 0) this.ctx.moveTo(nx, ny);
                    else this.ctx.lineTo(nx, ny);
                }
            });
            this.ctx.stroke();
            this.ctx.setLineDash([]);
        }

        // 6. Nodes
        this.nodes.forEach(n => {
            const nx = offsetX + (n.x / 600) * mapW;
            const ny = offsetY + (n.y / 300) * mapH;
            const isLocal = n.ip === "127.0.0.1";
            const inChain = this.bounceChain.includes(n.ip);
            const isHovered = this.hoveredNode && this.hoveredNode.ip === n.ip;

            // Pulsing effect for interactive nodes
            let baseSize = 4;
            if (isLocal || inChain) baseSize += this.pulse * 2;

            this.ctx.beginPath();
            this.ctx.arc(nx, ny, isHovered ? 7 : baseSize, 0, Math.PI * 2);
            
            let color = '#00aaff';
            if (isLocal) color = '#00ff00';
            if (inChain && !isLocal) color = '#ffffff';
            if (isHovered) color = '#66ccff';

            this.ctx.fillStyle = color;
            this.ctx.shadowBlur = isHovered || isLocal ? 12 : 5;
            this.ctx.shadowColor = color;
            this.ctx.fill();
            this.ctx.shadowBlur = 0;

            // Labels
            if (isHovered || isLocal) {
                this.ctx.fillStyle = '#fff';
                this.ctx.font = 'bold 10px Consolas';
                this.ctx.fillText(n.name.toUpperCase(), nx + 12, ny + 3);
            }
        });
    }
}
