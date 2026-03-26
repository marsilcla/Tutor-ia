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
<meta name="theme-color" content="#0d0d0d">
<link rel="manifest" href="/manifest.json">
<link rel="apple-touch-icon" href="/icon-192.png">
<title>Alex · English Coach</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  :root { --green: #00e676; --red: #ff5252; --purple: #7c4dff; --bg: #0d0d0d; --card: #1a1a1a; }

  body {
    background: var(--bg);
    color: #fff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    height: 100dvh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  #header {
    padding: 18px 20px 14px;
    border-bottom: 1px solid #1e1e1e;
    flex-shrink: 0;
  }
  #header h1 { font-size: 1.05em; font-weight: 700; color: var(--green); letter-spacing: 0.3px; }
  #header p  { font-size: 0.72em; color: #555; margin-top: 3px; }

  #chat {
    flex: 1;
    overflow-y: auto;
    padding: 16px 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    -webkit-overflow-scrolling: touch;
  }

  .bubble {
    max-width: 84%;
    padding: 11px 15px;
    border-radius: 18px;
    line-height: 1.55;
    font-size: 0.93em;
    word-break: break-word;
  }
  .bubble.user  { background: #252525; align-self: flex-end; border-bottom-right-radius: 4px; color: #ddd; }
  .bubble.alex  { background: #0a2e18; align-self: flex-start; border-bottom-left-radius: 4px; color: #d4f5e3; border: 1px solid #00e67618; }
  .bubble.hint  { align-self: center; color: #383838; font-size: 0.75em; font-style: italic; background: transparent; }

  #bottom {
    flex-shrink: 0;
    padding: 14px 20px 28px;
    border-top: 1px solid #1e1e1e;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    background: var(--bg);
  }

  #status {
    font-size: 0.72em;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    height: 16px;
    color: #444;
    transition: color 0.2s;
  }
  #status.listening { color: var(--red); }
  #status.thinking  { color: var(--green); }
  #status.speaking  { color: var(--purple); }

  #micBtn {
    width: 72px; height: 72px;
    border-radius: 50%; border: none;
    background: var(--green);
    font-size: 28px;
    cursor: pointer;
    box-shadow: 0 0 28px rgba(0,230,118,0.2);
    transition: transform 0.15s, background 0.25s, box-shadow 0.25s;
    -webkit-tap-highlight-color: transparent;
    outline: none;
  }
  #micBtn:active { transform: scale(0.90); }
  #micBtn.listening { background: var(--red); box-shadow: 0 0 28px rgba(255,82,82,0.3); animation: pulse 1.1s ease-in-out infinite; }
  #micBtn.speaking  { background: var(--purple); box-shadow: 0 0 28px rgba(124,77,255,0.3); animation: pulse 2s ease-in-out infinite; }
  #micBtn.off       { background: #2a2a2a; box-shadow: none; cursor: default; }

  @keyframes pulse {
    0%, 100% { transform: scale(1); }
    50%       { transform: scale(1.07); }
  }

  #hint { font-size: 0.7em; color: #333; }
</style>
</head>
<body>

<div id="header">
  <h1>Alex · English Coach</h1>
  <p>Habla en español o en inglés — te respondo en inglés</p>
</div>

<div id="chat">
  <div class="bubble hint">Toca el micro para empezar la conversación</div>
</div>

<div id="bottom">
  <div id="status">TOCA PARA EMPEZAR</div>
  <button id="micBtn" aria-label="Micrófono">🎤</button>
  <div id="hint">Di "ciérrate" para terminar</div>
</div>

<script>
const btn      = document.getElementById('micBtn');
const statusEl = document.getElementById('status');
const chat     = document.getElementById('chat');

let autoListen = false;
let speaking   = false;
let voices     = [];

// ── Voices ──────────────────────────────────────────────────
function loadVoices() { voices = window.speechSynthesis.getVoices(); }
loadVoices();
window.speechSynthesis.onvoiceschanged = loadVoices;

function bestEnglishVoice() {
  return voices.find(v => v.lang === 'en-US' && /google/i.test(v.name))
    || voices.find(v => v.lang === 'en-US')
    || voices.find(v => v.lang.startsWith('en'))
    || (voices[0] || null);
}

// ── Chat bubbles ─────────────────────────────────────────────
function addBubble(text, type) {
  const el = document.createElement('div');
  el.className = 'bubble ' + type;
  el.textContent = text;
  chat.appendChild(el);
  requestAnimationFrame(() => { chat.scrollTop = chat.scrollHeight; });
}

function setStatus(text, cls) {
  statusEl.textContent = text;
  statusEl.className   = cls || '';
}

// ── Speech synthesis ─────────────────────────────────────────
function speak(text, onDone) {
  window.speechSynthesis.cancel();
  speaking = true;
  btn.classList.remove('listening');
  btn.classList.add('speaking');
  setStatus('HABLANDO...', 'speaking');

  const u   = new SpeechSynthesisUtterance(text);
  u.voice   = bestEnglishVoice();
  u.lang    = 'en-US';
  u.rate    = 0.93;
  u.pitch   = 1.0;
  u.volume  = 1.0;

  const finish = () => {
    speaking = false;
    btn.classList.remove('speaking');
    if (onDone) onDone();
  };
  u.onend  = finish;
  u.onerror = finish;

  // Chrome iOS workaround: keep synthesis alive
  const keepAlive = setInterval(() => { if (!speaking) clearInterval(keepAlive); }, 5000);

  window.speechSynthesis.speak(u);
}

// ── Speech recognition ────────────────────────────────────────
const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
const rec = new SpeechRec();
rec.lang            = 'es-ES';   // Bilingual: Gemini handles detection
rec.continuous      = false;
rec.interimResults  = false;
rec.maxAlternatives = 1;

const FAREWELL = /ci[eé]rrate|cierra|close|goodbye|good bye|bye|adi[oó]s|hasta luego|hasta mañana|fin|termina/i;

function startListening() {
  if (speaking || btn.classList.contains('off')) return;
  try {
    rec.start();
    btn.classList.add('listening');
    setStatus('TE ESCUCHO...', 'listening');
  } catch(e) { /* already running */ }
}

rec.onresult = async (e) => {
  const text = e.results[0][0].transcript.trim();
  if (!text) { if (autoListen) startListening(); return; }

  btn.classList.remove('listening');
  setStatus('PENSANDO...', 'thinking');
  addBubble(text, 'user');

  // Client-side farewell shortcut
  if (FAREWELL.test(text)) {
    const bye = "See you! Keep it up — every conversation counts. Bye!";
    addBubble(bye, 'alex');
    speak(bye, shutdown);
    return;
  }

  try {
    const res  = await fetch('/conversar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usuario_id: 'creus', texto: text })
    });
    const data = await res.json();
    addBubble(data.respuesta, 'alex');

    if (data.shutdown) {
      speak(data.respuesta, shutdown);
    } else {
      speak(data.respuesta, () => { if (autoListen) startListening(); });
    }
  } catch(err) {
    setStatus('ERROR — INTENTA DE NUEVO');
    btn.classList.remove('listening');
    if (autoListen) setTimeout(startListening, 2000);
  }
};

rec.onend = () => {
  if (speaking || btn.classList.contains('off')) return;
  btn.classList.remove('listening');
  if (autoListen) {
    setStatus('TE ESCUCHO...', 'listening');
    setTimeout(startListening, 150);
  } else {
    setStatus('TOCA PARA EMPEZAR');
  }
};

rec.onerror = (ev) => {
  btn.classList.remove('listening');
  if (ev.error === 'no-speech') {
    if (autoListen) setTimeout(startListening, 300);
    return;
  }
  if (ev.error === 'aborted') return;
  setStatus('INTÉNTALO DE NUEVO');
  if (autoListen) setTimeout(startListening, 2000);
};

// ── Shutdown ──────────────────────────────────────────────────
function shutdown() {
  autoListen = false;
  btn.classList.remove('listening', 'speaking');
  btn.classList.add('off');
  btn.textContent = '👋';
  setStatus('HASTA LUEGO');
  document.getElementById('hint').style.display = 'none';
}

// ── Start on first tap ────────────────────────────────────────
// Register service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}

btn.onclick = () => {
  if (btn.classList.contains('off')) return;
  if (!autoListen) {
    autoListen = true;
    const hint = chat.querySelector('.hint');
    if (hint) hint.remove();
    document.getElementById('hint').style.display = 'none';
  }
  startListening();
};
</script>
</body>
</html>"""


@app.get("/manifest.json")
async def manifest():
    return JSONResponse({
        "name": "Alex · English Coach",
        "short_name": "Alex Coach",
        "description": "Aprende inglés conversando con Alex, tu tutor nativo",
        "start_url": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#0d0d0d",
        "theme_color": "#00e676",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
        ]
    })


@app.get("/sw.js")
async def service_worker():
    js = """
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(clients.claim()));
self.addEventListener('fetch', e => e.respondWith(fetch(e.request).catch(() => new Response('Offline'))));
"""
    return Response(content=js, media_type="application/javascript")


@app.get("/icon-{size}.png")
async def icon(size: str):
    # SVG icon rendered as PNG via base64 embedded SVG
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size.split('x')[0] if 'x' in size else size}" height="{size.split('x')[0] if 'x' in size else size}" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="100" fill="#0d0d0d"/>
  <circle cx="256" cy="256" r="180" fill="#00e676" opacity="0.15"/>
  <text x="256" y="320" font-size="240" text-anchor="middle" font-family="Apple Color Emoji,Segoe UI Emoji,sans-serif">🎤</text>
</svg>"""
    return Response(content=svg.encode(), media_type="image/svg+xml",
                    headers={"Content-Disposition": f"inline; filename=icon-{size}.png"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("orquestador_base:app", host="0.0.0.0", port=8000, reload=True)
