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
                overflow: hidden; /* Evita scrolls raros en el móvil */
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
            };

            // Mantiene el micro encendido si falla
            recognition.onerror = () => {
                btn.classList.remove('listening');
                status.innerText = "INTÉNTALO DE NUEVO";
            };
        </script>
    </body>
    </html>
    """
