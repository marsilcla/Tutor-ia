import os
import json
import google.generativeai as genai
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

MEMORIA_FILE = "memoria_estudiantes.json"


def cargar():
    return json.load(open(MEMORIA_FILE, encoding="utf-8")) if os.path.exists(MEMORIA_FILE) else {}


def guardar(d):
    json.dump(d, open(MEMORIA_FILE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


memoria = cargar()


class Mensaje(BaseModel):
    usuario_id: str
    texto: str


@app.get("/ping")
async def ping():
    return {"status": "alive"}


@app.post("/conversar")
async def conversar(msg: Mensaje):
    uid = msg.usuario_id
    if uid not in memoria:
        memoria[uid] = {"h": []}

    hist = memoria[uid]["h"][-6:]
    ctx = "\n".join(f"User: {h['u']}\nAlex: {h['a']}" for h in hist)

    prompt = f"""You are Alex, a native English speaker who is a natural, friendly conversation partner helping a Spanish speaker learn English by just... talking.

YOUR VOICE: Warm, relaxed, real. Like a friend — not a teacher. Short sentences. Natural rhythm. Never robotic.

WHEN THE STUDENT SPEAKS IN ENGLISH:
→ Reply naturally, keep the conversation flowing
→ If they made a grammar or vocabulary mistake, weave the correct form into your reply naturally without making a big deal of it
→ Example: "Yeah totally — you'd say 'I went' there, not 'I go'. Anyway, so what happened next?"

WHEN THE STUDENT SPEAKS IN SPANISH:
→ Light up — show them the English equivalent right away
→ Use it in a real sentence, something casual
→ Invite them to try saying it in English
→ Example: "Oh nice! So in English: 'I'm exhausted.' Like — 'I'm exhausted, I need a coffee.' Now you say it!"

RULES:
- Max 2–3 sentences per reply. Keep the pace fast and natural.
- Always end with something that pulls them back into the conversation.
- Never say "Great job!" or "Well done!" — that sounds like a teacher. Just talk.
- If student says "ciérrate", "close", "goodbye", "bye", "adiós", "hasta luego" or any farewell → give a warm short goodbye, then on the very last line write exactly: SHUTDOWN

{f"Recent:{chr(10)}{ctx}" if ctx else ""}

Student: "{msg.texto}"
Alex:"""

    r = model.generate_content(prompt)
    text = r.text.strip()
    shutdown = "SHUTDOWN" in text
    clean = text.replace("SHUTDOWN", "").strip()

    memoria[uid]["h"] = (hist + [{"u": msg.texto, "a": clean}])[-20:]
    guardar(memoria)

    return {"respuesta": clean, "shutdown": shutdown}


@app.get("/", response_class=HTMLResponse)
async def home():
    return """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Alex Coach">
<meta name="theme-color" content="#0e0e16">
<link rel="manifest" href="/manifest.json">
<link rel="apple-touch-icon" href="/icon-192.png">
<title>Alex · English Coach</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
:root{
  --bg:#0e0e16; --card:#16161f;
  --green:#00e676; --red:#ff5252; --purple:#9c6dff; --blue:#448aff;
  --dim:#44445a;
}
html,body{
  width:100%;height:100%;background:var(--bg);color:#fff;
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Segoe UI",Roboto,sans-serif;
  overflow:hidden;user-select:none;
}

/* ═══════════════════ SPLASH ═══════════════════ */
#splash{
  position:fixed;inset:0;background:var(--bg);
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:14px;z-index:999;
  transition:opacity 0.7s ease,transform 0.7s ease;
}
#splash.out{opacity:0;transform:scale(1.06);pointer-events:none}

.sp-orb{
  position:relative;width:130px;height:130px;
  display:flex;align-items:center;justify-content:center;
}
.sp-ring{
  position:absolute;border-radius:50%;
  border:1.5px solid var(--green);
  animation:sp-expand 2.4s ease-in-out infinite;
}
.sp-ring:nth-child(1){width:130px;height:130px;animation-delay:0s;opacity:.06}
.sp-ring:nth-child(2){width:100px;height:100px;animation-delay:.5s;opacity:.10}
.sp-ring:nth-child(3){width:70px;height:70px;animation-delay:1s;opacity:.18}
@keyframes sp-expand{
  0%,100%{transform:scale(.92);opacity:.08}
  50%{transform:scale(1.08);opacity:.22}
}
.sp-core{
  width:72px;height:72px;border-radius:50%;
  background:conic-gradient(from 0deg,#00c853,#00e676,#69f0ae,#00e676,#00c853);
  display:flex;align-items:center;justify-content:center;
  font-size:32px;font-weight:900;color:#000;letter-spacing:-1px;
  animation:sp-spin 4s linear infinite;
  box-shadow:0 0 36px rgba(0,230,118,.45);
}
@keyframes sp-spin{from{filter:hue-rotate(0deg)}to{filter:hue-rotate(30deg)}}
.sp-name{font-size:30px;font-weight:900;letter-spacing:8px;color:#fff}
.sp-tag{font-size:11px;color:var(--dim);letter-spacing:3.5px;text-transform:uppercase}
.sp-conn{font-size:11px;color:var(--green);letter-spacing:2px;margin-top:6px}
.sp-conn::after{content:'';animation:dot3 1.4s steps(3,end) infinite}
@keyframes dot3{0%{content:'.'}33%{content:'..'}66%{content:'...'}}

/* ═══════════════════ APP ═══════════════════ */
#app{
  width:100%;height:100dvh;
  display:flex;flex-direction:column;align-items:center;
  padding:0 24px;
  opacity:0;transition:opacity 0.7s ease;
}
#app.on{opacity:1}

/* Top bar */
#topbar{
  width:100%;padding:18px 0 10px;
  display:flex;align-items:center;justify-content:space-between;
  flex-shrink:0;
}
.tb-left{display:flex;flex-direction:column}
.tb-name{font-size:13px;font-weight:800;letter-spacing:4px;color:var(--green)}
.tb-sub{font-size:10px;color:var(--dim);letter-spacing:2px;margin-top:2px}
.tb-live{
  display:flex;align-items:center;gap:6px;
  font-size:10px;color:var(--dim);letter-spacing:1px;
}
.live-dot{
  width:7px;height:7px;border-radius:50%;background:var(--green);
  box-shadow:0 0 8px var(--green);
  animation:blink 2.5s ease-in-out infinite;
}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.25}}

/* Avatar zone */
#av-zone{
  flex:1;display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  gap:0;
}

/* Orbital rings */
#av-wrap{
  position:relative;width:220px;height:220px;
  display:flex;align-items:center;justify-content:center;
}
.ring{
  position:absolute;border-radius:50%;
  border:1px solid var(--green);
  transition:all .4s ease;
}
#rA{width:220px;height:220px;opacity:.05}
#rB{width:172px;height:172px;opacity:.08}
#rC{width:128px;height:128px;opacity:.13}

/* Core face */
#face{
  position:relative;
  width:96px;height:96px;border-radius:50%;
  background:linear-gradient(145deg,#0c241a,#112e1e);
  border:2px solid var(--green);
  box-shadow:0 0 32px rgba(0,230,118,.18);
  display:flex;align-items:center;justify-content:center;
  transition:all .4s ease;
  overflow:hidden;
}

/* Letter A — idle */
#face-letter{
  font-size:42px;font-weight:900;color:var(--green);
  transition:opacity .25s;
}

/* Wave bars — speaking */
#face-wave{
  position:absolute;
  display:flex;align-items:center;gap:4px;
  opacity:0;transition:opacity .25s;
}
.wb{width:4px;border-radius:3px;background:var(--purple);
    animation:wb 0.55s ease-in-out infinite alternate}
.wb:nth-child(1){height:10px;animation-delay:.0s}
.wb:nth-child(2){height:22px;animation-delay:.1s}
.wb:nth-child(3){height:34px;animation-delay:.2s}
.wb:nth-child(4){height:22px;animation-delay:.3s}
.wb:nth-child(5){height:10px;animation-delay:.4s}
@keyframes wb{from{transform:scaleY(.35)}to{transform:scaleY(1.2)}}

/* Think dots — thinking */
#face-think{
  position:absolute;
  display:none;align-items:center;gap:6px;
}
.td{width:8px;height:8px;border-radius:50%;background:var(--blue);
    animation:td .9s ease-in-out infinite}
.td:nth-child(1){animation-delay:0s}
.td:nth-child(2){animation-delay:.18s}
.td:nth-child(3){animation-delay:.36s}
@keyframes td{0%,100%{transform:translateY(0);opacity:.35}50%{transform:translateY(-7px);opacity:1}}

/* ── State: listen ── */
.s-listen #rA{border-color:var(--red);opacity:.12;animation:pulse-ring 1.1s ease-out infinite}
.s-listen #rB{border-color:var(--red);opacity:.20;animation:pulse-ring 1.1s ease-out .25s infinite}
.s-listen #rC{border-color:var(--red);opacity:.35;animation:pulse-ring 1.1s ease-out .5s infinite}
.s-listen #face{border-color:var(--red);box-shadow:0 0 40px rgba(255,82,82,.35);
  background:linear-gradient(145deg,#1f0a0a,#2e1212)}
.s-listen #face-letter{color:var(--red)}
@keyframes pulse-ring{0%{transform:scale(1)}100%{transform:scale(1.08);opacity:0}}

/* ── State: think ── */
.s-think #face{border-color:var(--blue);box-shadow:0 0 40px rgba(68,138,255,.35);
  background:linear-gradient(145deg,#0a1020,#101828);
  animation:spin-glow 1.8s linear infinite}
.s-think #face-letter{color:var(--blue);opacity:0}
.s-think #face-think{display:flex}
@keyframes spin-glow{
  0%  {box-shadow:0 0 30px rgba(68,138,255,.3)}
  50% {box-shadow:0 0 60px rgba(68,138,255,.55)}
  100%{box-shadow:0 0 30px rgba(68,138,255,.3)}
}

/* ── State: speak ── */
.s-speak #face{border-color:var(--purple);box-shadow:0 0 50px rgba(156,109,255,.4);
  background:linear-gradient(145deg,#150a22,#1c1030);
  animation:speak-breathe 1.6s ease-in-out infinite}
.s-speak #face-letter{opacity:0}
.s-speak #face-wave{opacity:1}
@keyframes speak-breathe{
  0%,100%{transform:scale(1)}50%{transform:scale(1.04)}
}

/* Name + role */
#av-name{margin-top:22px;font-size:24px;font-weight:900;letter-spacing:6px;color:#fff}
#av-role{font-size:10px;color:var(--dim);letter-spacing:3px;margin-top:5px}
#av-status{
  margin-top:14px;font-size:10px;font-weight:700;
  letter-spacing:2.5px;text-transform:uppercase;color:var(--dim);
  height:14px;transition:color .3s;
}
.s-listen #av-status{color:var(--red)}
.s-think  #av-status{color:var(--blue)}
.s-speak  #av-status{color:var(--purple)}

/* Exchange bubbles */
#exchange{
  width:100%;max-width:360px;margin-top:20px;
  display:flex;flex-direction:column;gap:8px;
  min-height:56px;
}
.bbl{
  padding:9px 14px;border-radius:14px;
  font-size:13px;line-height:1.5;max-width:86%;
  animation:fadin .3s ease;
}
.bbl.alex{
  background:#16162a;border-left:3px solid var(--purple);
  align-self:flex-start;color:#ccc;
}
.bbl.user{
  background:#0e2018;border-right:3px solid var(--green);
  align-self:flex-end;color:#c8f5dc;text-align:right;
}
@keyframes fadin{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}

/* Bottom */
#bottom{
  flex-shrink:0;padding:16px 0 44px;
  display:flex;flex-direction:column;align-items:center;gap:10px;
  width:100%;
}
#micBtn{
  width:70px;height:70px;border-radius:50%;border:none;
  background:var(--green);cursor:pointer;outline:none;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 0 28px rgba(0,230,118,.3);
  transition:all .2s;
}
#micBtn:active{transform:scale(.87)}
#micBtn.listening{background:var(--red);box-shadow:0 0 28px rgba(255,82,82,.45)}
#micBtn.speaking {background:var(--purple);box-shadow:0 0 28px rgba(156,109,255,.45)}
#micBtn.off{background:#1e1e30;box-shadow:none;cursor:default}
#hint{font-size:10px;color:#2a2a40;letter-spacing:1.5px}
</style>
</head>
<body>

<!-- ══ SPLASH ══════════════════════════════════ -->
<div id="splash">
  <div class="sp-orb">
    <div class="sp-ring"></div>
    <div class="sp-ring"></div>
    <div class="sp-ring"></div>
    <div class="sp-core">A</div>
  </div>
  <div class="sp-name">ALEX</div>
  <div class="sp-tag">English Coach · AI</div>
  <div class="sp-conn">despertando a Alex<span></span></div>
</div>

<!-- ══ APP ═════════════════════════════════════ -->
<div id="app">

  <div id="topbar">
    <div class="tb-left">
      <div class="tb-name">ALEX</div>
      <div class="tb-sub">ENGLISH COACH</div>
    </div>
    <div class="tb-live">
      <div class="live-dot"></div>
      <span>EN VIVO</span>
    </div>
  </div>

  <div id="av-zone">

    <div id="av-wrap">
      <div class="ring" id="rA"></div>
      <div class="ring" id="rB"></div>
      <div class="ring" id="rC"></div>
      <div id="face">
        <span id="face-letter">A</span>
        <div id="face-wave">
          <div class="wb"></div><div class="wb"></div><div class="wb"></div>
          <div class="wb"></div><div class="wb"></div>
        </div>
        <div id="face-think">
          <div class="td"></div><div class="td"></div><div class="td"></div>
        </div>
      </div>
    </div>

    <div id="av-name">ALEX</div>
    <div id="av-role">ENGLISH COACH · AI</div>
    <div id="av-status">Toca para empezar</div>

    <div id="exchange"></div>

  </div>

  <div id="bottom">
    <button id="micBtn" aria-label="Micrófono">
      <svg width="30" height="30" viewBox="0 0 24 24" fill="white">
        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
        <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
      </svg>
    </button>
    <div id="hint">Di "ciérrate" para terminar</div>
  </div>

</div>

<script>
const splash   = document.getElementById('splash');
const appEl    = document.getElementById('app');
const statusEl = document.getElementById('av-status');
const exchange = document.getElementById('exchange');
const btn      = document.getElementById('micBtn');
const hint     = document.getElementById('hint');

// ── State ────────────────────────────────────
const ST = {idle:'',listen:'s-listen',think:'s-think',speak:'s-speak'};
const ST_LABEL = {
  idle:'Toca para empezar',
  listen:'Te escucho...',
  think:'Pensando...',
  speak:'Hablando...'
};
function setState(s){
  appEl.className = s==='idle' ? 'on' : 'on '+ST[s];
  statusEl.textContent = ST_LABEL[s];
}

// ── Exchange display ──────────────────────────
function showExchange(user, alex){
  exchange.innerHTML='';
  if(alex){
    const d=document.createElement('div');
    d.className='bbl alex'; d.textContent=alex;
    exchange.appendChild(d);
  }
  if(user){
    const d=document.createElement('div');
    d.className='bbl user'; d.textContent=user;
    exchange.appendChild(d);
  }
}

// ── Voices ───────────────────────────────────
let voices=[];
function loadVoices(){ voices=window.speechSynthesis.getVoices(); }
loadVoices();
window.speechSynthesis.onvoiceschanged=loadVoices;
function bestVoice(){
  return voices.find(v=>v.lang==='en-US' && /google/i.test(v.name))
    || voices.find(v=>v.lang==='en-US')
    || voices.find(v=>v.lang.startsWith('en'))
    || null;
}

// ── TTS ──────────────────────────────────────
let speaking=false;
function speak(text, cb){
  window.speechSynthesis.cancel();
  speaking=true; setState('speak');
  btn.className='speaking';
  const u=new SpeechSynthesisUtterance(text);
  u.voice=bestVoice(); u.lang='en-US'; u.rate=0.93; u.pitch=1.02;
  const done=()=>{ speaking=false; if(cb) cb(); };
  u.onend=done; u.onerror=done;
  // Chrome keep-alive
  const ka=setInterval(()=>{ if(!speaking) clearInterval(ka); else window.speechSynthesis.pause()||window.speechSynthesis.resume(); },9000);
  window.speechSynthesis.speak(u);
}

// ── ASR ──────────────────────────────────────
const SpeechRec=window.SpeechRecognition||window.webkitSpeechRecognition;
const rec=new SpeechRec();
rec.lang='es-ES'; rec.continuous=false; rec.interimResults=false;

let autoListen=false;
const FAREWELL=/ci[eé]rrate|cierra|close|goodbye|bye|adi[oó]s|hasta luego|fin|termina/i;

function startListening(){
  if(speaking||btn.classList.contains('off')) return;
  try{
    rec.start(); setState('listen'); btn.className='listening';
    navigator.vibrate&&navigator.vibrate(25);
  }catch(e){}
}

rec.onresult=async e=>{
  const text=e.results[0][0].transcript.trim();
  if(!text){ if(autoListen) startListening(); return; }
  setState('think'); btn.className='';
  showExchange(text,null);

  if(FAREWELL.test(text)){
    const bye="See you! Keep practising — you're doing great. Bye!";
    showExchange(text,bye); speak(bye,shutdown); return;
  }

  try{
    const res=await fetch('/conversar',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({usuario_id:'user',texto:text})
    });
    const data=await res.json();
    showExchange(text,data.respuesta);
    if(data.shutdown) speak(data.respuesta,shutdown);
    else speak(data.respuesta,()=>{ if(autoListen) startListening(); });
  }catch{
    setState('idle'); btn.className='';
    if(autoListen) setTimeout(startListening,2500);
  }
};

rec.onend=()=>{
  if(speaking||btn.classList.contains('off')) return;
  btn.className='';
  if(autoListen){ setState('listen'); setTimeout(startListening,150); }
  else setState('idle');
};

rec.onerror=ev=>{
  btn.className='';
  if(ev.error==='no-speech'||ev.error==='aborted'){
    if(autoListen) setTimeout(startListening,300); return;
  }
  setState('idle');
  if(autoListen) setTimeout(startListening,2500);
};

// ── Shutdown ──────────────────────────────────
function shutdown(){
  autoListen=false;
  btn.className='off'; setState('idle');
  statusEl.textContent='¡Hasta luego! 👋';
  hint.style.display='none';
}

// ── First tap ─────────────────────────────────
btn.onclick=()=>{
  if(btn.classList.contains('off')) return;
  if(!autoListen){ autoListen=true; hint.style.display='none'; }
  startListening();
};

// ── Keep-alive (13 min ping) ──────────────────
setInterval(()=>fetch('/ping').catch(()=>{}), 13*60*1000);

// ── Splash → App ─────────────────────────────
async function waitForServer(){
  let tries=0;
  while(tries<25){
    try{
      const ctrl=new AbortController();
      const t=setTimeout(()=>ctrl.abort(),4500);
      const r=await fetch('/ping',{signal:ctrl.signal});
      clearTimeout(t);
      if(r.ok) break;
    }catch(e){}
    await new Promise(r=>setTimeout(r,2200));
    tries++;
  }
  splash.classList.add('out');
  appEl.classList.add('on');
  setTimeout(()=>{ splash.style.display='none'; },800);
}

// ── Service Worker ────────────────────────────
if('serviceWorker' in navigator){
  navigator.serviceWorker.register('/sw.js').catch(()=>{});
}

waitForServer();
</script>
</body>
</html>"""


@app.get("/manifest.json")
async def manifest():
    return JSONResponse({
        "name": "Alex · English Coach",
        "short_name": "Alex",
        "description": "Aprende inglés conversando con Alex, tu coach nativo",
        "start_url": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#0e0e16",
        "theme_color": "#00e676",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
        ]
    })


@app.get("/sw.js")
async def service_worker():
    js = """
const CACHE='alex-v2';
self.addEventListener('install',e=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil(clients.claim()));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET') return;
  e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));
});
"""
    return Response(content=js, media_type="application/javascript")


@app.get("/icon-{size}.png")
async def icon(size: str):
    s = size.replace(".png", "").split("x")[0]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{s}" height="{s}" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="90" fill="#0e0e16"/>
  <circle cx="256" cy="256" r="210" fill="#00e676" opacity="0.06"/>
  <circle cx="256" cy="256" r="170" fill="#00e676" opacity="0.08"/>
  <circle cx="256" cy="256" r="130" fill="#00e676" opacity="0.12"/>
  <circle cx="256" cy="256" r="96" fill="#0c241a" stroke="#00e676" stroke-width="6"/>
  <text x="256" y="320" font-size="196" text-anchor="middle"
    font-family="-apple-system,BlinkMacSystemFont,Roboto,sans-serif"
    font-weight="900" fill="#00e676">A</text>
</svg>"""
    return Response(
        content=svg.encode(),
        media_type="image/svg+xml",
        headers={"Content-Type": "image/svg+xml"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("orquestador_base:app", host="0.0.0.0", port=8000, reload=True)
