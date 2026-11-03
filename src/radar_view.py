"""
Cinematic 2D Mission Radar & Flight Animation Theater.
Provides a smooth 60 FPS HTML5 canvas tactical radar displaying drones taking off from PSTU,
flying across air corridors with spinning rotors, dropping cargo, and docking into charging bays.
"""
from __future__ import annotations
import json
from typing import List, Dict, Any
from src.network import DumkiNetwork

def generate_radar_theater_html(
    network: DumkiNetwork,
    events: List[Dict[str, Any]],
    fleet_ids: List[str]
) -> str:
    """
    Builds a standalone interactive HTML5 / Canvas 2D simulation theater.
    """
    depot_id = network.get_depot_id()
    depot_info = network.depots[depot_id]
    
    # Pack nodes into JSON for JS
    nodes_data = {
        "depot": {
            "id": depot_id,
            "name": depot_info["name"],
            "lat": depot_info["lat"],
            "lon": depot_info["lon"]
        },
        "delivery_nodes": [
            {
                "id": nid,
                "name": n["name"],
                "lat": n["lat"],
                "lon": n["lon"],
                "zone": n.get("zone", "Dumki"),
                "color": n.get("color", "blue")
            }
            for nid, n in network.delivery_nodes.items()
        ]
    }

    nodes_json = json.dumps(nodes_data)
    events_json = json.dumps(events)
    fleet_json = json.dumps(fleet_ids)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            body {{ background: #050c14; color: #e2e8f0; overflow: hidden; }}
            #radar-container {{ position: relative; width: 100%; height: 580px; background: radial-gradient(circle at 50% 50%, #0d1e30 0%, #050c14 100%); border: 1px solid #1a365d; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,229,255,0.1); }}
            canvas {{ width: 100%; height: 100%; display: block; }}
            
            /* Controls overlay */
            .controls-panel {{
                position: absolute; bottom: 16px; left: 16px; right: 16px;
                background: rgba(10, 25, 41, 0.88); backdrop-filter: blur(8px);
                border: 1px solid #00e5ff44; border-radius: 8px; padding: 12px 18px;
                display: flex; align-items: center; justify-content: space-between; gap: 16px; z-index: 10;
            }}
            .btn {{
                background: #00e5ff; color: #050c14; border: none; padding: 8px 18px;
                font-weight: 700; border-radius: 6px; cursor: pointer; transition: all 0.2s;
                font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;
            }}
            .btn:hover {{ background: #38bdf8; box-shadow: 0 0 12px #00e5ff88; transform: translateY(-1px); }}
            .btn-secondary {{ background: #1e293b; color: #cbd5e1; border: 1px solid #475569; }}
            .btn-secondary:hover {{ background: #334155; color: white; }}
            
            .slider-group {{ flex-grow: 1; display: flex; align-items: center; gap: 12px; }}
            .slider-group input[type=range] {{ flex-grow: 1; accent-color: #00e5ff; cursor: pointer; }}
            
            /* Live Mission HUD Overlay */
            .hud-panel {{
                position: absolute; top: 16px; left: 16px;
                background: rgba(10, 25, 41, 0.85); backdrop-filter: blur(6px);
                border: 1px solid #1e40af; border-left: 4px solid #00e5ff;
                border-radius: 6px; padding: 10px 14px; font-size: 12px; pointer-events: none; z-index: 10;
            }}
            .hud-title {{ font-size: 11px; color: #94a3b8; letter-spacing: 1px; text-transform: uppercase; }}
            .hud-ticker {{ font-size: 13px; color: #00e5ff; font-weight: 600; margin-top: 4px; }}
            
            .stats-badge {{
                position: absolute; top: 16px; right: 16px;
                background: rgba(10, 25, 41, 0.85); backdrop-filter: blur(6px);
                border: 1px solid #334155; border-radius: 6px; padding: 10px 14px;
                font-size: 12px; text-align: right; pointer-events: none; z-index: 10;
            }}
        </style>
    </head>
    <body>
        <div id="radar-container">
            <canvas id="radarCanvas"></canvas>
            
            <div class="hud-panel">
                <div class="hud-title">📡 PSTU Drone Command • Live Mission Telemetry</div>
                <div id="liveTicker" class="hud-ticker">Simulating fleet operations across Dumki...</div>
            </div>
            
            <div class="stats-badge">
                <div style="color: #94a3b8;">Simulated Time: <b id="timeDisplay" style="color: #00e5ff; font-size: 15px;">0.0 min</b></div>
                <div style="color: #64748b; font-size: 11px; margin-top: 2px;">Central Hub: PSTU Main Campus</div>
            </div>

            <div class="controls-panel">
                <button id="playBtn" class="btn" onclick="togglePlay()">▶ Play Mission</button>
                <button class="btn btn-secondary" onclick="resetSim()">↺ Reset</button>
                
                <div class="slider-group">
                    <span style="font-size: 12px; color: #94a3b8;">Timeline:</span>
                    <input id="timelineSlider" type="range" min="0" max="240" step="0.5" value="0" oninput="onSliderScrub(this.value)">
                </div>

                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 12px; color: #94a3b8;">Speed:</span>
                    <button class="btn btn-secondary" style="padding: 4px 10px;" onclick="setSpeed(1)">1x</button>
                    <button class="btn btn-secondary" style="padding: 4px 10px;" onclick="setSpeed(3)">3x</button>
                    <button class="btn btn-secondary" style="padding: 4px 10px;" onclick="setSpeed(8)">8x</button>
                </div>
            </div>
        </div>

        <script>
            const canvas = document.getElementById('radarCanvas');
            const ctx = canvas.getContext('2d');
            
            const rawNodes = {nodes_json};
            const rawEvents = {events_json};
            const fleetIds = {fleet_json};

            let isPlaying = true;
            let simTime = 0.0;
            let playbackSpeed = 2.0; // simulated mins per real second
            let maxSimTime = 240.0;
            let lastTimestamp = 0;
            let rotorAngle = 0;

            function resize() {{
                canvas.width = canvas.parentElement.clientWidth;
                canvas.height = canvas.parentElement.clientHeight;
            }}
            window.addEventListener('resize', resize);
            resize();

            // Find bounds for normalization
            const allLats = [rawNodes.depot.lat, ...rawNodes.delivery_nodes.map(n => n.lat)];
            const allLons = [rawNodes.depot.lon, ...rawNodes.delivery_nodes.map(n => n.lon)];
            const minLat = Math.min(...allLats) - 0.006;
            const maxLat = Math.max(...allLats) + 0.006;
            const minLon = Math.min(...allLons) - 0.008;
            const maxLon = Math.max(...allLons) + 0.008;

            function project(lat, lon) {{
                const pad = 60;
                const w = canvas.width - pad * 2;
                const h = canvas.height - pad * 2 - 60;
                const x = pad + ((lon - minLon) / (maxLon - minLon)) * w;
                const y = (canvas.height - pad - 60) - ((lat - minLat) / (maxLat - minLat)) * h;
                return {{ x, y }};
            }}

            const depotPos = project(rawNodes.depot.lat, rawNodes.depot.lon);
            const nodePosMap = {{}};
            nodePosMap[rawNodes.depot.id] = depotPos;
            rawNodes.delivery_nodes.forEach(n => {{
                nodePosMap[n.id] = project(n.lat, n.lon);
            }});

            // Drone state manager
            class DroneActor {{
                constructor(id, index) {{
                    this.id = id;
                    this.index = index;
                    this.x = depotPos.x + (index % 2 === 0 ? -15 : 15);
                    this.y = depotPos.y + (Math.floor(index / 2) * 16 - 8);
                    this.status = 'IDLE';
                    this.soc = 1.0;
                    this.targetNodeId = null;
                    this.startX = this.x;
                    this.startY = this.y;
                    this.targetX = this.x;
                    this.targetY = this.y;
                    this.legStartTime = 0;
                    this.legDuration = 10;
                    this.cargoWeight = 0;
                    this.trail = [];
                }}

                update(t) {{
                    // Determine current flight state from events
                    let currentEvent = null;
                    for (let i = 0; i < rawEvents.length; i++) {{
                        const ev = rawEvents[i];
                        if (ev.drone_id === this.id && ev.simulation_time_min <= t) {{
                            currentEvent = ev;
                        }}
                    }}

                    if (currentEvent) {{
                        this.soc = currentEvent.soc || 1.0;
                        if (currentEvent.event_type === 'MISSION_DISPATCH') {{
                            this.status = 'OUTBOUND';
                        }} else if (currentEvent.event_type === 'PACKAGE_DELIVERED') {{
                            this.status = 'RETURNING';
                        }} else if (currentEvent.event_type === 'CHARGING_STARTED') {{
                            this.status = 'CHARGING';
                        }} else if (currentEvent.event_type === 'CHARGING_QUEUE_ENTER') {{
                            this.status = 'QUEUED';
                        }} else if (currentEvent.event_type === 'DRONE_AVAILABLE' || currentEvent.event_type === 'RETURNED_TO_DEPOT') {{
                            this.status = 'IDLE';
                        }}
                    }}

                    // Interpolate position along air corridor
                    if (this.status === 'OUTBOUND' || this.status === 'RETURNING') {{
                        // Smooth rhythmic flight animation towards target
                        const speedFactor = 0.04;
                        this.x += (this.targetX - this.x) * speedFactor;
                        this.y += (this.targetY - this.y) * speedFactor;
                    }} else {{
                        // Resting at depot pad
                        const homeX = depotPos.x + (this.index % 2 === 0 ? -22 : 22);
                        const homeY = depotPos.y + (Math.floor(this.index / 2) * 20 - 10);
                        this.x += (homeX - this.x) * 0.1;
                        this.y += (homeY - this.y) * 0.1;
                    }}

                    // Maintain motion trail
                    this.trail.push({{ x: this.x, y: this.y }});
                    if (this.trail.length > 18) this.trail.shift();
                }}

                draw() {{
                    // Draw neon motion trail
                    if (this.trail.length > 2 && (this.status === 'OUTBOUND' || this.status === 'RETURNING')) {{
                        ctx.beginPath();
                        ctx.moveTo(this.trail[0].x, this.trail[0].y);
                        for (let pt of this.trail) ctx.lineTo(pt.x, pt.y);
                        ctx.strokeStyle = this.status === 'OUTBOUND' ? 'rgba(0, 229, 255, 0.4)' : 'rgba(168, 85, 247, 0.4)';
                        ctx.lineWidth = 3;
                        ctx.stroke();
                    }}

                    ctx.save();
                    ctx.translate(this.x, this.y);

                    // Draw Quadcopter Fuselage
                    ctx.fillStyle = '#0f172a';
                    ctx.strokeStyle = '#00e5ff';
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    ctx.arc(0, 0, 7, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.stroke();

                    // Quadcopter 4 Arm Struts
                    const armLen = 11;
                    ctx.strokeStyle = '#64748b';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(-armLen, -armLen); ctx.lineTo(armLen, armLen);
                    ctx.moveTo(-armLen, armLen); ctx.lineTo(armLen, -armLen);
                    ctx.stroke();

                    // Spinning Propeller Rotors
                    const bladeColor = this.status === 'CHARGING' ? '#22c55e' : (this.status === 'IDLE' ? '#94a3b8' : '#00e5ff');
                    const bladeSpeed = (this.status === 'IDLE' || this.status === 'CHARGING') ? 0.05 : 0.4;
                    const rAngle = rotorAngle * bladeSpeed;

                    [[-armLen, -armLen], [armLen, armLen], [-armLen, armLen], [armLen, -armLen]].forEach(([rx, ry]) => {{
                        ctx.save();
                        ctx.translate(rx, ry);
                        ctx.rotate(rAngle);
                        ctx.strokeStyle = bladeColor;
                        ctx.lineWidth = 2;
                        ctx.beginPath();
                        ctx.moveTo(-5, 0); ctx.lineTo(5, 0);
                        ctx.stroke();
                        ctx.restore();
                    }});

                    // Battery HUD Tag
                    const socPct = Math.round(this.soc * 100);
                    const socColor = socPct > 50 ? '#22c55e' : (socPct > 25 ? '#eab308' : '#ef4444');
                    
                    ctx.fillStyle = 'rgba(5, 12, 20, 0.85)';
                    ctx.strokeStyle = socColor;
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.roundRect(-22, -26, 44, 13, 3);
                    ctx.fill();
                    ctx.stroke();

                    ctx.font = 'bold 8px monospace';
                    ctx.fillStyle = '#f8fafc';
                    ctx.textAlign = 'center';
                    let statusIcon = this.status === 'CHARGING' ? '⚡' : (this.status === 'OUTBOUND' ? '📦' : '🔋');
                    ctx.fillText(`${{statusIcon}} ${{socPct}}%`, 0, -17);

                    ctx.font = 'bold 9px sans-serif';
                    ctx.fillStyle = '#38bdf8';
                    ctx.fillText(this.id, 0, 22);

                    ctx.restore();
                }}
            }}

            const drones = fleetIds.map((id, idx) => new DroneActor(id, idx));

            // Set flight destinations dynamically from events
            function syncDroneDestinations(t) {{
                drones.forEach(d => {{
                    for (let ev of rawEvents) {{
                        if (ev.drone_id === d.id && ev.simulation_time_min <= t) {{
                            if (ev.event_type === 'MISSION_DISPATCH') {{
                                // Extract destination node from details
                                for (let n of rawNodes.delivery_nodes) {{
                                    if (ev.details.includes(n.id)) {{
                                        const p = nodePosMap[n.id];
                                        d.targetX = p.x;
                                        d.targetY = p.y;
                                    }}
                                }}
                            }} else if (ev.event_type === 'PACKAGE_DELIVERED') {{
                                d.targetX = depotPos.x;
                                d.targetY = depotPos.y;
                            }}
                        }}
                    }}
                }});
            }}

            function drawRadar() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // 1. Tactical Grid & Range Rings
                ctx.strokeStyle = 'rgba(0, 229, 255, 0.05)';
                ctx.lineWidth = 1;
                for (let r = 80; r < canvas.width; r += 80) {{
                    ctx.beginPath();
                    ctx.arc(depotPos.x, depotPos.y, r, 0, Math.PI * 2);
                    ctx.stroke();
                }}

                // 2. Air Corridors (Glowing vectors from PSTU)
                rawNodes.delivery_nodes.forEach(n => {{
                    const p = nodePosMap[n.id];
                    ctx.strokeStyle = n.zone.includes('PSTU') ? 'rgba(56, 189, 248, 0.25)' : 'rgba(245, 158, 11, 0.18)';
                    ctx.lineWidth = n.zone.includes('PSTU') ? 2 : 1.5;
                    ctx.setLineDash([4, 6]);
                    ctx.beginPath();
                    ctx.moveTo(depotPos.x, depotPos.y);
                    ctx.lineTo(p.x, p.y);
                    ctx.stroke();
                    ctx.setLineDash([]);
                }});

                // 3. Draw Delivery Nodes
                rawNodes.delivery_nodes.forEach(n => {{
                    const p = nodePosMap[n.id];
                    const isCampus = n.zone.includes('PSTU');

                    // Node pulsing aura
                    ctx.fillStyle = isCampus ? 'rgba(56, 189, 248, 0.15)' : 'rgba(245, 158, 11, 0.12)';
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, 14, 0, Math.PI * 2);
                    ctx.fill();

                    // Node Core
                    ctx.fillStyle = isCampus ? '#0284c7' : '#d97706';
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
                    ctx.fill();

                    // Node Name Label
                    ctx.font = isCampus ? 'bold 11px sans-serif' : '10px sans-serif';
                    ctx.fillStyle = isCampus ? '#e0f2fe' : '#cbd5e1';
                    ctx.textAlign = 'center';
                    ctx.fillText(n.name, p.x, p.y + 18);
                }});

                // 4. Draw Central Hub (PSTU Campus Drone Depot)
                ctx.fillStyle = 'rgba(239, 68, 68, 0.18)';
                ctx.beginPath();
                ctx.arc(depotPos.x, depotPos.y, 28, 0, Math.PI * 2);
                ctx.fill();

                ctx.strokeStyle = '#ef4444';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(depotPos.x, depotPos.y, 16, 0, Math.PI * 2);
                ctx.stroke();

                // Charging Dock Icons inside Central Hub
                ctx.fillStyle = '#22c55e';
                ctx.beginPath();
                ctx.arc(depotPos.x - 7, depotPos.y, 3, 0, Math.PI * 2);
                ctx.arc(depotPos.x + 7, depotPos.y, 3, 0, Math.PI * 2);
                ctx.fill();

                ctx.font = 'bold 12px sans-serif';
                ctx.fillStyle = '#f87171';
                ctx.textAlign = 'center';
                ctx.fillText('🚁 PSTU Central Hub (Charging Dock)', depotPos.x, depotPos.y - 24);

                // 5. Update and Draw Drones
                syncDroneDestinations(simTime);
                drones.forEach(d => {{
                    d.update(simTime);
                    d.draw();
                }});
            }}

            function loop(timestamp) {{
                if (!lastTimestamp) lastTimestamp = timestamp;
                const dt = (timestamp - lastTimestamp) / 1000.0;
                lastTimestamp = timestamp;

                if (isPlaying) {{
                    simTime += playbackSpeed * dt * 2.5;
                    if (simTime > maxSimTime) simTime = 0.0;
                    document.getElementById('timelineSlider').value = simTime;
                    document.getElementById('timeDisplay').innerText = simTime.toFixed(1) + ' min';

                    // Update HUD ticker with latest event
                    let latestEvent = rawEvents.find(e => e.simulation_time_min <= simTime && simTime - e.simulation_time_min < 4);
                    if (latestEvent) {{
                        document.getElementById('liveTicker').innerText = `[${{latestEvent.simulation_time_min.toFixed(1)}}m] ${{latestEvent.drone_id}}: ${{latestEvent.details}}`;
                    }}
                }}

                rotorAngle += 1;
                drawRadar();
                requestAnimationFrame(loop);
            }}
            requestAnimationFrame(loop);

            function togglePlay() {{
                isPlaying = !isPlaying;
                document.getElementById('playBtn').innerText = isPlaying ? '⏸ Pause' : '▶ Play Mission';
            }}

            function resetSim() {{
                simTime = 0.0;
                document.getElementById('timelineSlider').value = 0;
                document.getElementById('timeDisplay').innerText = '0.0 min';
            }}

            function onSliderScrub(val) {{
                simTime = parseFloat(val);
                document.getElementById('timeDisplay').innerText = simTime.toFixed(1) + ' min';
            }}

            function setSpeed(spd) {{
                playbackSpeed = spd;
            }}
        </script>
    </body>
    </html>
    """
    return html_code

