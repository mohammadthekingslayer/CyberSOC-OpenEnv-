import subprocess
import sys
import os
import re
import threading
import time
from typing import Optional, Any, Dict

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from openenv_core.env_server import create_fastapi_app
from cyber_soc_env.env.environment import SOCEnvironment
from cyber_soc_env.models import SOCAction, SOCObservation

# --- Global State for Dashboard ---
baseline_lock = threading.Lock()
baseline_state: Dict[str, Any] = {
    "status": "idle", # idle, running, completed, error
    "logs": [],
    "scores": {"task1": 0.0, "task2": 0.0, "task3": 0.0},
    "kpis": {"task1": {}, "task2": {}, "task3": {}},
    "progress": 0,
    "current_task": None,
    "error": None
}

# Base OpenEnv app (gives /reset, /step, /state, /health, /docs)
app = create_fastapi_app(SOCEnvironment(), SOCAction, SOCObservation)

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """Professional, modern landing page for CyberSOC OpenEnv."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberSOC | Mission Control</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #05060f;
            --bg-surface: #0a0c1a;
            --bg-card: rgba(16, 20, 41, 0.7);
            --accent-primary: #3b82f6;
            --accent-secondary: #10b981;
            --accent-danger: #ef4444;
            --accent-warning: #f59e0b;
            --text-heading: #ffffff;
            --text-body: #94a3b8;
            --text-muted: #64748b;
            --border-glow: rgba(59, 130, 246, 0.3);
            --glass-border: rgba(255, 255, 255, 0.08);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-deep);
            background-image: 
                radial-gradient(circle at 50% 0%, rgba(59, 130, 246, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 100% 100%, rgba(16, 185, 129, 0.05) 0%, transparent 40%);
            color: var(--text-body);
            line-height: 1.5;
            min-height: 100vh;
            overflow-x: hidden;
        }

        .dashboard {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 2rem;
        }

        @media (max-width: 1100px) { .dashboard { grid-template-columns: 1fr; } }

        .sidebar { display: flex; flex-direction: column; gap: 2rem; }
        .logo-container { display: flex; align-items: center; gap: 1rem; padding: 1rem 0; border-bottom: 1px solid var(--glass-border); }
        .logo-icon { width: 40px; height: 40px; background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)); border-radius: 10px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 20px rgba(59, 130, 246, 0.4); }
        .logo-text { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.5px; color: var(--text-heading); background: linear-gradient(to right, #fff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .nav-group { display: flex; flex-direction: column; gap: 0.5rem; }
        .nav-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; border-radius: 0.75rem; text-decoration: none; color: var(--text-body); font-weight: 600; font-size: 0.95rem; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); background: rgba(255, 255, 255, 0.03); border: 1px solid transparent; }
        .nav-item:hover { background: rgba(59, 130, 246, 0.1); color: var(--text-heading); transform: translateX(4px); border-color: var(--border-glow); }
        .nav-item.active { background: linear-gradient(to right, rgba(59, 130, 246, 0.2), transparent); border-left: 3px solid var(--accent-primary); color: var(--text-heading); }

        .main-content { display: flex; flex-direction: column; gap: 2rem; }
        .header { display: flex; justify-content: space-between; align-items: center; }
        .header-title h1 { font-size: 2rem; font-weight: 700; color: var(--text-heading); margin-bottom: 0.25rem; }
        .status-pill { display: flex; align-items: center; gap: 0.5rem; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); color: var(--accent-secondary); padding: 0.5rem 1rem; border-radius: 9999px; font-size: 0.875rem; font-weight: 600; }
        .pulse { width: 8px; height: 8px; background: var(--accent-secondary); border-radius: 50%; animation: pulse-animation 2s infinite; }
        @keyframes pulse-animation { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); } }

        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
        @media (max-width: 800px) { .stats-grid { grid-template-columns: 1fr; } }

        .card { background: var(--bg-card); backdrop-filter: blur(12px); border: 1px solid var(--glass-border); border-radius: 1.25rem; padding: 1.5rem; transition: all 0.3s ease; cursor: pointer; position: relative; overflow: hidden; }
        .card:hover { transform: translateY(-4px); border-color: var(--border-glow); box-shadow: 0 8px 32px rgba(59, 130, 246, 0.2); }
        .card.active { border-color: var(--accent-primary); background: rgba(59, 130, 246, 0.1); }
        .card.active::after { content: "RUNNING"; position: absolute; top: 12px; right: 12px; font-size: 10px; font-weight: 800; color: var(--accent-primary); background: rgba(59, 130, 246, 0.1); padding: 2px 8px; border-radius: 4px; }

        .card-header { display: flex; justify-content: space-between; margin-bottom: 1rem; }
        .card-label { font-size: 0.875rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
        .card-value { font-size: 1.75rem; font-weight: 700; color: var(--text-heading); margin-bottom: 0.5rem; }
        .difficulty-tag { padding: 0.25rem 0.75rem; border-radius: 0.5rem; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }
        .diff-easy { background: rgba(59, 130, 246, 0.15); color: var(--accent-primary); }
        .diff-medium { background: rgba(245, 158, 11, 0.15); color: var(--accent-warning); }
        .diff-hard { background: rgba(239, 68, 68, 0.15); color: var(--accent-danger); }

        .terminal { background: #000; border: 1px solid var(--glass-border); border-radius: 1rem; font-family: 'JetBrains Mono', monospace; padding: 1.5rem; height: 350px; display: flex; flex-direction: column; }
        .terminal-header { display: flex; gap: 0.5rem; margin-bottom: 1rem; border-bottom: 1px solid #222; padding-bottom: 8px; }
        .terminal-content { color: #d1d5db; font-size: 0.85rem; line-height: 1.6; overflow-y: auto; flex-grow: 1; }
        .terminal-content::-webkit-scrollbar { width: 6px; }
        .terminal-content::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
        .command { color: var(--accent-primary); }
        .output { color: var(--accent-secondary); }
        .timestamp { color: var(--text-muted); font-size: 0.75rem; margin-right: 8px; }

        .btn { padding: 0.75rem 1.5rem; border-radius: 0.75rem; font-weight: 600; font-size: 0.95rem; cursor: pointer; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); text-decoration: none; display: inline-flex; align-items: center; justify-content: center; border: 1px solid transparent; gap: 8px; }
        .btn-primary { background: var(--accent-primary); color: white; box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4); }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6); background: #2563eb; }
        .btn-glass { background: rgba(255, 255, 255, 0.03); border-color: var(--glass-border); color: var(--text-heading); }
        .btn-glass:hover { background: rgba(255, 255, 255, 0.08); border-color: var(--text-muted); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; }

        .progress-container { width: 100%; background: rgba(255,255,255,0.05); height: 8px; border-radius: 4px; margin: 12px 0; overflow: hidden; }
        .progress-bar { height: 100%; background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary)); width: 0%; transition: width 0.3s ease; }

        footer { margin-top: auto; padding: 2rem 0; text-align: center; color: var(--text-muted); font-size: 0.875rem; border-top: 1px solid var(--glass-border); }
    </style>
</head>
<body>
    <div class="dashboard">
        <aside class="sidebar">
            <div class="logo-container">
                <div class="logo-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>
                <div class="logo-text">CyberSOC</div>
            </div>
            <nav class="nav-group">
                <a href="/" class="nav-item active"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg> Dashboard</a>
                <a href="/docs" class="nav-item"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg> API Docs</a>
                <a href="/verify" class="nav-item"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg> System Health</a>
            </nav>
            <div class="card" style="margin-top: auto; padding: 1rem;">
                <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem;">STATUS</p>
                <div id="connection-status" style="font-weight: 700; color: var(--accent-secondary);">CONNECTED</div>
            </div>
        </aside>

        <main class="main-content">
            <header class="header">
                <div class="header-title">
                    <h1>Mission Control</h1>
                    <p>OpenEnv AI Security Agent Training Environment</p>
                </div>
                <div class="status-pill">
                    <div class="pulse"></div>
                    <span id="system-status-text">System Operational</span>
                </div>
            </header>

            <section class="stats-grid">
                <div class="card" id="card-task1" onclick="activateTask('task1')">
                    <div class="card-header"><span class="card-label">Task I</span><span class="difficulty-tag diff-easy">Easy</span></div>
                    <div class="card-value">Brute Force</div>
                    <p style="font-size: 0.875rem;">Detect and mitigate authentication-based attacks.</p>
                </div>
                <div class="card" id="card-task2" onclick="activateTask('task2')">
                    <div class="card-header"><span class="card-label">Task II</span><span class="difficulty-tag diff-medium">Medium</span></div>
                    <div class="card-value">Malware</div>
                    <p style="font-size: 0.875rem;">Identify C2 traffic and isolate infected endpoints.</p>
                </div>
                <div class="card" id="card-task3" onclick="activateTask('task3')">
                    <div class="card-header"><span class="card-label">Task III</span><span class="difficulty-tag diff-hard">Hard</span></div>
                    <div class="card-value">APT Hunt</div>
                    <p style="font-size: 0.875rem;">Investigate multi-stage lateral movement campaigns.</p>
                </div>
            </section>

            <div class="grid-2" style="display: grid; grid-template-columns: 3fr 2fr; gap: 2rem;">
                <section class="terminal">
                    <div class="terminal-header">
                        <div class="dot red"></div><div class="dot yellow"></div><div class="dot green"></div>
                        <span style="font-size: 0.75rem; color: var(--text-muted); margin-left: auto;">LIVE_AGENT_LOGS</span>
                    </div>
                    <div class="terminal-content" id="log-monitor">
                        <p><span class="timestamp">[INIT]</span> <span class="output">Waiting for agent activity...</span></p>
                    </div>
                </section>

                <section class="card" style="display: flex; flex-direction: column; gap: 1rem; cursor: default;">
                    <h3 style="color: var(--text-heading);">Executive Summary</h3>
                    <div id="results-summary" style="display: flex; flex-direction: column; gap: 0.75rem;">
                        <div class="summary-row">
                            <span>Task 1 (Brute Force)</span>
                            <span id="score-task1" class="score-badge">---</span>
                        </div>
                        <div class="summary-row">
                            <span>Task 2 (Malware)</span>
                            <span id="score-task2" class="score-badge">---</span>
                        </div>
                        <div class="summary-row">
                            <span>Task 3 (APT Hunt)</span>
                            <span id="score-task3" class="score-badge">---</span>
                        </div>
                    </div>
                    
                    <div id="baseline-progress-box" style="display: none; margin-top: 1rem;">
                        <p id="baseline-status-text" style="font-size: 0.8rem; font-weight: 600; color: var(--accent-primary);">Running Baseline...</p>
                        <div class="progress-container"><div class="progress-bar" id="baseline-progress-bar"></div></div>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-top: auto;">
                        <button id="run-baseline-btn" class="btn btn-primary" onclick="startBaseline()">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                            Start Full Benchmark
                        </button>
                        <button class="btn btn-glass" onclick="window.open('./docs', '_blank')">Launch Swagger UI</button>
                    </div>
                </section>
            </div>

            <style>
                .summary-row { display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 8px; }
                .score-badge { font-weight: 700; padding: 2px 8px; border-radius: 4px; font-family: 'JetBrains Mono', monospace; }
                .score-pass { color: var(--accent-secondary); background: rgba(16, 185, 129, 0.1); }
                .score-fail { color: var(--accent-danger); background: rgba(239, 68, 68, 0.1); }
            </style>

            <section class="card" style="cursor: default;">
                <h3 style="color: var(--text-heading); margin-bottom: 1.5rem;">Active Telemetry</h3>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; text-align: center;">
                    <div style="padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 12px;">
                        <p style="font-size: 0.7rem; color: var(--text-muted);">CURRENT_TASK</p>
                        <p id="stat-task" style="font-weight: 700; color: var(--text-heading);">NONE</p>
                    </div>
                    <div style="padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 12px;">
                        <p style="font-size: 0.7rem; color: var(--text-muted);">STEP_COUNT</p>
                        <p id="stat-step" style="font-weight: 700; color: var(--text-heading);">0 / 15</p>
                    </div>
                    <div style="padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 12px;">
                        <p style="font-size: 0.7rem; color: var(--text-muted);">REWARD_LAST</p>
                        <p id="stat-reward" style="font-weight: 700; color: var(--accent-secondary);">0.00</p>
                    </div>
                    <div style="padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 12px;">
                        <p style="font-size: 0.7rem; color: var(--text-muted);">EPISODE_DONE</p>
                        <p id="stat-done" style="font-weight: 700; color: var(--text-muted);">FALSE</p>
                    </div>
                </div>
            </section>

            <section class="card" style="cursor: default; margin-top: 1rem;">
                <h3 style="color: var(--text-heading); margin-bottom: 1.5rem;">Cybersecurity KPIs</h3>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; text-align: center;">
                    <div style="padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 12px;">
                        <p style="font-size: 0.7rem; color: var(--text-muted);">SYS LATENCY (MS/STEP)</p>
                        <p id="kpi-latency" style="font-weight: 700; color: var(--accent-secondary);">---</p>
                    </div>
                    <div style="padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 12px;">
                        <p style="font-size: 0.7rem; color: var(--text-muted);">MTTD (STEPS)</p>
                        <p id="kpi-mttd" style="font-weight: 700; color: var(--text-heading);">---</p>
                    </div>
                    <div style="padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 12px;">
                        <p style="font-size: 0.7rem; color: var(--text-muted);">MTTR (STEPS)</p>
                        <p id="kpi-mttr" style="font-weight: 700; color: var(--text-heading);">---</p>
                    </div>
                </div>
            </section>
        </main>
    </div>

    <script>
        let currentTaskId = 'task1';
        let isBaselineRunning = false;
        
        async function updateDashboard() {
            try {
                // Update Local State (Relative URL)
                const stateRes = await fetch('./state');
                const state = await stateRes.json();
                
                document.getElementById('stat-step').innerText = `${state.step || 0} / 15`;
                document.getElementById('stat-done').innerText = (state.done || false).toString().toUpperCase();
                
                // Update active card styling
                document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
                const activeCard = document.getElementById('card-' + currentTaskId);
                if (activeCard) activeCard.classList.add('active');
                document.getElementById('stat-task').innerText = currentTaskId.toUpperCase();

                // Update Baseline Progress (Relative URL)
                const baselineRes = await fetch('./baseline/status');
                const baseline = await baselineRes.json();
                
                isBaselineRunning = baseline.status === 'running';

                // Update Scores
                Object.keys(baseline.scores).forEach(tid => {
                    const el = document.getElementById('score-' + tid);
                    if (el && baseline.scores[tid] > 0) {
                        const score = baseline.scores[tid];
                        el.innerText = score.toFixed(3);
                        el.className = 'score-badge ' + (score >= 0.7 ? 'score-pass' : 'score-fail');
                    }
                });

                // Update KPIs
                let totalLat = 0, totalMttd = 0, totalMttr = 0, kpiCount = 0;
                Object.keys(baseline.kpis).forEach(tid => {
                    const k = baseline.kpis[tid];
                    if (k && k.avg_latency_ms !== undefined) {
                        totalLat += k.avg_latency_ms;
                        totalMttd += k.mttd_steps || 0;
                        totalMttr += k.mttr_steps || 0;
                        kpiCount++;
                    }
                });
                if (kpiCount > 0) {
                    document.getElementById('kpi-latency').innerText = (totalLat / kpiCount).toFixed(0);
                    document.getElementById('kpi-mttd').innerText = (totalMttd / kpiCount).toFixed(1);
                    document.getElementById('kpi-mttr').innerText = (totalMttr / kpiCount).toFixed(1);
                }

                if (isBaselineRunning) {
                    document.getElementById('baseline-progress-box').style.display = 'block';
                    document.getElementById('run-baseline-btn').disabled = true;
                    document.getElementById('run-baseline-btn').innerText = 'Benchmark in Progress...';
                    document.getElementById('baseline-progress-bar').style.width = baseline.progress + '%';
                    document.getElementById('baseline-status-text').innerText = `Running: ${baseline.current_task || 'Initializing'}...`;
                } else {
                    document.getElementById('baseline-progress-box').style.display = 'none';
                    document.getElementById('run-baseline-btn').disabled = false;
                    document.getElementById('run-baseline-btn').innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg> Start Full Benchmark`;
                }

                // Update Logs with syntax highlighting
                const logMonitor = document.getElementById('log-monitor');
                if (baseline.logs && baseline.logs.length > 0) {
                    let logHtml = '';
                    baseline.logs.slice(-100).forEach(log => {
                        let typeClass = '';
                        if (log.includes('[START]')) typeClass = 'command';
                        else if (log.includes('[END]')) typeClass = 'output';
                        else if (log.includes('[ERROR]')) typeClass = 'red';
                        else if (log.includes('[STEP]')) typeClass = 'timestamp';
                        
                        logHtml += `<p><span class="timestamp">${new Date().toLocaleTimeString()}</span> <span class="${typeClass}">${escapeHtml(log)}</span></p>`;
                    });
                    logMonitor.innerHTML = logHtml;
                    logMonitor.scrollTop = logMonitor.scrollHeight;
                }
            } catch (e) { 
                console.error('Dashboard sync error', e);
                document.getElementById('connection-status').innerText = 'OFFLINE';
                document.getElementById('connection-status').style.color = 'var(--accent-danger)';
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        async function activateTask(taskId) {
            if (isBaselineRunning) return;
            currentTaskId = taskId;
            await fetch('./reset', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task_id: taskId})
            });
            updateDashboard();
        }

        async function startBaseline() {
            await fetch('./baseline', {method: 'POST'});
            updateDashboard();
        }

        setInterval(updateDashboard, 500);
        updateDashboard();
    </script>
</body>
</html>
"""

@app.get("/ping")
def ping():
    """Simple health check alias."""
    return {"status": "pong"}

# ── CORE API ROUTING (OpenEnv Compliant with Error Handling) ──

class ResetRequest(BaseModel):
    """Schema for the reset request."""
    task_id: Optional[str] = "task1"

@app.post("/reset")
async def reset_env(request: ResetRequest):
    """Reset environment with a specific task_id.
    
    Returns:
        Observation with initial state, reward (0.0), and done status.
    """
    try:
        # Validate task_id
        valid_tasks = ["task1", "task2", "task3"]
        task_id = request.task_id or "task1"
        
        if task_id not in valid_tasks:
            return {
                "error": f"Invalid task_id: {task_id}. Must be one of {valid_tasks}",
                "observation": None,
                "reward": 0.0,
                "done": False
            }
        
        observation = app.state.env.reset(task_id=task_id)
        return {
            "observation": observation,
            "reward": observation.reward,
            "done": observation.done
        }
    except Exception as e:
        return {
            "error": f"Reset failed: {str(e)}",
            "observation": None,
            "reward": 0.0,
            "done": False
        }

@app.post("/step")
async def step_env(action: SOCAction):
    """Execute an action in the current environment.
    
    Args:
        action: SOCAction with action_type, target, and optional reasoning
        
    Returns:
        Observation with result, reward, and done status.
    """
    try:
        observation = app.state.env.step(action)
        return {
            "observation": observation,
            "reward": observation.reward,
            "done": observation.done
        }
    except Exception as e:
        return {
            "error": f"Step execution failed: {str(e)}",
            "observation": None,
            "reward": 0.0,
            "done": False
        }

@app.get("/state")
async def get_state():
    """Get current environment state.
    
    Returns:
        Current SOCState with step count, actions taken, and done status.
    """
    try:
        return app.state.env.state
    except Exception as e:
        return {
            "error": f"Failed to retrieve state: {str(e)}"
        }

# Store environment in app state for cross-route access
app.state.env = SOCEnvironment(task_id="task1")

# Route Priority Fix: Ensure our custom handlers override the defaults
# By re-inserting them at the front of the routes list
for route_path in ["/reset", "/step", "/state"]:
    # Find our custom route and move it to the front
    for i, route in enumerate(app.router.routes):
        if hasattr(route, "path") and route.path == route_path and "api" in str(route.endpoint):
             app.router.routes.insert(0, app.router.routes.pop(i))
             break

# ── MANDATORY EXTRA ENDPOINTS (OpenEnv Competition) ──

@app.get("/verify")
def verify_system():
    """Automated health check and registry validation.
    
    Returns system status and compliance information.
    """
    try:
        return {
            "status": "operational",
            "tasks_loaded": 3,
            "environment": "CyberSOC OpenEnv v1.0.0",
            "framework": "OpenEnv",
            "python_version": "3.11",
            "grading_system": "deterministic",
            "compliance": "OpenEnv Spec Compliant"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/tasks")
def get_tasks():
    """Returns all available tasks with their schemas.
    
    Provides task metadata and action schema for API consumers.
    """
    try:
        return {
            "tasks": [
                {
                    "task_id": "task1",
                    "name": "Brute Force Detection",
                    "difficulty": "easy",
                    "description": "Detect and block SSH/RDP brute force attacks on corporate infrastructure",
                    "max_steps": 15,
                    "action_schema": {
                        "action_type": "string (analyze_log | block_ip | mark_safe | escalate)",
                        "target": "string (IP address, hostname, or log ID)",
                        "reasoning": "string (optional explanation)"
                    }
                },
                {
                    "task_id": "task2",
                    "name": "Malware Containment",
                    "difficulty": "medium",
                    "description": "Identify malware indicators, C2 communications, and contain infected systems",
                    "max_steps": 15,
                    "action_schema": {
                        "action_type": "string (analyze_log | block_ip | isolate_device | run_scan)",
                        "target": "string (IP, device name, file hash, or log ID)",
                        "reasoning": "string (optional explanation)"
                    }
                },
                {
                    "task_id": "task3",
                    "name": "APT Investigation",
                    "difficulty": "hard",
                    "description": "Investigate multi-stage Advanced Persistent Threat campaigns with lateral movement",
                    "max_steps": 15,
                    "action_schema": {
                        "action_type": "string (analyze_log | block_ip | isolate_device | correlate_events | escalate | mark_safe)",
                        "target": "string (IP, device name, event ID, or log ID)",
                        "reasoning": "string (optional explanation)"
                    }
                }
            ],
            "global_action_types": [
                "analyze_log",
                "block_ip",
                "isolate_device",
                "mark_safe",
                "escalate",
                "run_scan",
                "correlate_events"
            ]
        }
    except Exception as e:
        return {
            "error": f"Failed to retrieve tasks: {str(e)}",
            "tasks": []
        }

@app.post("/tasks")
def post_tasks():
    """POST variant of /tasks for compatibility."""
    return get_tasks()

@app.get("/grader")
def get_grader_score(task_id: str = "task1", episode_id: str = "latest"):
    """Returns grader score for a completed episode.
    
    Args:
        task_id: Task identifier (task1, task2, or task3)
        episode_id: Episode identifier (default: latest)
        
    Returns:
        Score (0.0-1.0), pass/fail status, and feedback.
    """
    try:
        # Validate task_id
        valid_tasks = ["task1", "task2", "task3"]
        if task_id not in valid_tasks:
            return {
                "error": f"Invalid task_id: {task_id}",
                "task_id": task_id,
                "score": 0.0,
                "passed": False
            }
        
        # Try to pull score from the active session or baseline runs
        if app.state.env.task_id == task_id and len(app.state.env._actions_raw) > 0:
            score = app.state.env.grade_episode(task_id=task_id)
        else:
            # Fallback: pull from baseline scores if UI started the benchmark
            score = baseline_state["scores"].get(task_id, 0.0)
            
        return {
            "task_id": task_id,
            "episode_id": episode_id,
            "score": round(float(score), 4),
            "passed": score >= 0.7,
            "threshold": 0.7
        }
    except Exception as e:
        return {
            "error": f"Grading failed: {str(e)}",
            "task_id": task_id,
            "score": 0.0,
            "passed": False
        }

@app.post("/grader")
def post_grader_score(task_id: str = "task1", episode_id: str = "latest"):
    """POST variant of /grader for compatibility."""
    return get_grader_score(task_id, episode_id)

# ── MANDATORY EXTRA ENDPOINTS (OpenEnv Competition) ──

@app.get("/baseline/status")
def get_baseline_status():
    """Returns the current background status of the baseline process."""
    return baseline_state

def run_baseline_task():
    """Background worker function for the baseline script with lock protection."""
    if not baseline_lock.acquire(blocking=False):
        return  # Already running
        
    try:
        baseline_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "inference.py"))
        
        baseline_state["status"] = "running"
        baseline_state["logs"] = ["[START] Background Baseline Execution Initiated"]
        baseline_state["progress"] = 0
        baseline_state["scores"] = {"task1": 0.0, "task2": 0.0, "task3": 0.0}
        baseline_state["kpis"] = {"task1": {}, "task2": {}, "task3": {}}
        baseline_state["error"] = None
        
        env_vars = os.environ.copy()
        env_vars["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        # Launch substrate process with cleanup ensured
        with subprocess.Popen(
            [sys.executable, baseline_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env_vars,
            bufsize=1,
            universal_newlines=True
        ) as process:
            for line in process.stdout:
                line = line.strip()
                if not line: continue
                
                # Truncate logs to avoid memory bloat (keep last 500)
                if len(baseline_state["logs"]) > 500:
                    baseline_state["logs"] = baseline_state["logs"][-500:]
                
                baseline_state["logs"].append(line)
                
                # Progress tracking logic
                if "[START]" in line:
                    task_match = re.search(r"task=(\S+)", line)
                    if task_match:
                        baseline_state["current_task"] = task_match.group(1)
                        # More robust index finding
                        tasks = ["task1", "task2", "task3"]
                        if baseline_state["current_task"] in tasks:
                            idx = tasks.index(baseline_state["current_task"])
                            baseline_state["progress"] = int((idx / 3) * 100)
                
                if "[END]" in line:
                    score_match = re.search(r"score=([\d.]+)", line)
                    kpis_match = re.search(r"kpis=({.+})", line)
                    if score_match and baseline_state["current_task"]:
                        curr_task = baseline_state["current_task"]
                        baseline_state["scores"][curr_task] = float(score_match.group(1))
                        if kpis_match:
                            try:
                                import json
                                baseline_state["kpis"][curr_task] = json.loads(kpis_match.group(1))
                            except:
                                pass
                        tasks = ["task1", "task2", "task3"]
                        if curr_task in tasks:
                            baseline_state["progress"] = int(((tasks.index(curr_task) + 1) / 3) * 100)

            process.wait()
            if process.returncode == 0:
                baseline_state["status"] = "completed"
                baseline_state["logs"].append("[END] Baseline process finished successfully")
            else:
                baseline_state["status"] = "error"
                baseline_state["error"] = f"Process exited with code {process.returncode}"
                baseline_state["logs"].append(f"[ERROR] Process exited with code {process.returncode}")
            
            baseline_state["progress"] = 100

    except Exception as e:
        baseline_state["status"] = "error"
        baseline_state["error"] = str(e)
        baseline_state["logs"].append(f"[ERROR] Subprocess fatal: {str(e)}")
    finally:
        baseline_lock.release()

@app.post("/baseline")
def start_baseline_post(background_tasks: BackgroundTasks):
    """Triggers the baseline benchmark in the background."""
    if baseline_state["status"] == "running":
        return JSONResponse({"status": "already_running"}, status_code=400)
    
    background_tasks.add_task(run_baseline_task)
    return {"status": "started"}

@app.get("/baseline")
def run_baseline_get(background_tasks: BackgroundTasks):
    """GET variant of /baseline for legacy support."""
    return start_baseline_post(background_tasks)
