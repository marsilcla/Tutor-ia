import os
import json
import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

API_KEY = os.getenv("GOOGLE_API_KEY")

# --- AUTODESCUBRIMIENTO DE MODELO ---
MODELO_ACTIVO = None

async def obtener_modelo_real():
    url_lista = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url_lista)
            modelos = r.json().get('models', [])
            candidatos = [m['name'] for m in modelos if 'generateContent' in m.get('supportedGenerationMethods', [])]
            for target in ["1.5-flash", "1.5-pro", "gemini-pro"]:
                for m in candidatos:
                    if target in m:
                        print(f"✅ MODELO DETECTADO Y ACTIVO: {m}")
                        return m
            return candidatos[0] if candidatos else None
        except Exception as e:
            print(f"❌ Error al listar modelos: {e}")
            return None

@app.on_event("startup")
async def startup_event():
    global MODELO_ACTIVO
    MODELO_ACTIVO = await obtener_modelo_real()

# --- MEMORIA ---
FICHERO_MEMORIA = "memoria_tutor.json"

def cargar_memoria():
    if os.path.exists(FICHERO_MEMORIA):
        try:
            with open(FICHERO_MEMORIA, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {}

def guardar_memoria(data):
    try:
        with open(FICHERO_MEMORIA, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)
    except: pass

memoria_global = cargar_memoria()

class Peticion(BaseModel):
    usuario_id: str
    intento_usuario: str

@app.post("/procesar_intento")
async def procesar(peticion: Peticion):
    if not MODELO_ACTIVO:
        return {"feedback": "Error crítico: Google no devuelve ningún modelo válido."}

    uid = peticion.usuario_id
    url = f"https://generativelanguage.googleapis.com/v1beta/{MODELO_ACTIVO}:generateContent?key={API_KEY}"
    
    prompt = {
        "contents": [{
            "parts": [{"text": f"Eres un tutor de inglés experto. Corrige de forma breve y natural, sin usar asteriscos ni lenguaje robótico: {peticion.intento_usuario}"}]
        }]
    }

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url, json=prompt, timeout=15.0)
            data = r.json()
            
            if r.status_code != 200:
                error_real = data.get('error', {}).get('message', f'Código HTTP {r.status_code}')
                return {"feedback": f"Error de Google: {error_real}"}
            
            respuesta_texto = data['candidates'][0]['content']['parts'][0]['text'].replace("*", "").strip()

            if uid not in memoria_global: memoria_global[uid] = {"puntos": 0, "historial": []}
            memoria_global[uid]["puntos"] += 1
            memoria_global[uid]["historial"].append(peticion.intento_usuario)
            guardar_memoria(memoria_global)

            return {
                "feedback": respuesta_texto,
                "sesiones": memoria_global[uid]["puntos"]
            }
        except Exception as e:
            return {"feedback": f"Fallo de servidor: {str(e)}", "sesiones": 0}

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="Tutor L3">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="theme-color" content="#0a0a0a">

        <title>Tutor Pro IA</title>
        <style>
            :root { --accent: #00e676; --bg: #0a0a0a; }
            body { 
                background: var(--bg); 
                color: white; 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                display: flex; 
                flex-direction: column; 
                align-items: center; 
                justify-content: center; 
                height: 100vh; 
                margin: 0;
                overflow: hidden;
            }
            .container { width: 90%; max-width: 400px; text-align: center; }
            .mic-btn { 
                background: var(--accent); 
                border: none; 
                width: 140px; 
                height: 140px; 
                border-radius: 50%; 
                font-size: 60px; 
                cursor: pointer; 
                box-shadow: 0 0 40px rgba(0,230,118,0.2); 
                transition: transform 0.2s;
                -webkit-tap-highlight-color: transparent;
            }
            .mic-btn:active { transform: scale(0.9); }
            .mic-btn.listening { background: #ff5252; box-shadow: 0 0 40px rgba(255,82,82,0.4); animation: pulse 1.5s infinite; }
            @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
            .card { background: #1a1a1a; padding: 25px; border-radius: 25px; margin-top: 30px; text-align: left; display: none; border-left: 6px solid var(--accent); }
            #status { height: 25px; color: var(--accent); margin-bottom: 15px; font-weight: bold; letter-spacing: 1px; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="container">
            <div id="status">LISTO PARA PRACTICAR</div>
            <button class="mic-btn" id="micBtn">🎤</button>
            <div id="resCard" class="card">
                <div style="font-size: 0.7em; color: var(--accent); font-weight: bold;">TUTOR IA</div>
                <p id="iaFeedback" style="margin-top: 10px; line-height: 1.6; font-size: 1.1em;"></p>
            </div>
        </div>

        <script>
            const btn = document.getElementById('micBtn');
            const status = document.getElementById('status');
            const iaFeedback = document.getElementById('iaFeedback');
            const resCard = document.getElementById('resCard');

            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'en-US';

            btn.onclick = () => {
                try {
                    recognition.start();
                    btn.classList.add('listening');
                    status.innerText = "TE ESCUCHO...";
                } catch(e) { console.log("Re-start prevent"); }
            };

            recognition.onresult = async (e) => {
                btn.classList.remove('listening');
                const text = e.results[0][0].transcript;
                status.innerText = "PENSANDO...";
                
                try {
                    const r = await fetch('/procesar_intento', {
                        method:'POST', headers:{'Content-Type':'application/json'},
                        body: JSON.stringify({usuario_id: "creus", intento_usuario: text})
                    });
                    const d = await r.json();
                    
                    iaFeedback.innerText = d.feedback;
                    resCard.style.display = 'block';
                    status.innerText = "LISTO";

                    const utterance = new SpeechSynthesisUtterance(d.feedback);
                    const voices = window.speechSynthesis.getVoices();
                    utterance.voice = voices.find(v => v.lang.includes('es') && v.name.includes('Google')) || voices[0];
                    utterance.rate = 0.95;
                    window.speechSynthesis.speak(utterance);
                } catch(err) {
                    status.innerText = "ERROR DE RED";
                }
            };

            recognition.onerror = () => {
                btn.classList.remove('listening');
                status.innerText = "INTÉNTALO DE NUEVO";
            };
        </script>
    </body>
    </html>
    """
