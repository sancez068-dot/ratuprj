from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, HTMLResponse
import uvicorn
import asyncio
from typing import List, Set

app = FastAPI()

# ---------- ВИДЕО ----------
latest_frame = None

@app.post("/upload")
async def upload_frame(frame: UploadFile = File(...)):
    global latest_frame
    contents = await frame.read()
    latest_frame = contents
    return {"status": "ok"}

@app.get("/stream")
async def stream():
    async def generate():
        while True:
            if latest_frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_frame + b'\r\n')
            await asyncio.sleep(0.1)
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")

# ---------- АУДИО РЕТРАНСЛЯЦИЯ ----------
audio_connections: List[WebSocket] = []

@app.websocket("/ws/audio")
async def websocket_audio(websocket: WebSocket):
    await websocket.accept()
    audio_connections.append(websocket)
    print(f"[WS Audio] Клиент подключен, всего: {len(audio_connections)}")
    try:
        while True:
            data = await websocket.receive_bytes()
            # Рассылаем всем, кроме отправителя
            for conn in audio_connections:
                if conn != websocket:
                    try:
                        await conn.send_bytes(data)
                    except:
                        pass
    except WebSocketDisconnect:
        if websocket in audio_connections:
            audio_connections.remove(websocket)
        print(f"[WS Audio] Клиент отключен, всего: {len(audio_connections)}")

# ---------- УПРАВЛЕНИЕ ----------
control_connections: Set[WebSocket] = set()

@app.websocket("/ws/control")
async def websocket_control(websocket: WebSocket):
    await websocket.accept()
    control_connections.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for conn in control_connections:
                if conn != websocket:
                    try:
                        await conn.send_text(data)
                    except:
                        pass
    except WebSocketDisconnect:
        control_connections.remove(websocket)

# ---------- ВЕБ-СТРАНИЦА (исправленный код) ----------
@app.get("/", response_class=HTMLResponse)
async def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Screen + Audio</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { margin: 0; background: #111; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; font-family: sans-serif; }
            #video { max-width: 100%; max-height: 60vh; border: 2px solid #333; }
            .controls { margin-top: 20px; display: flex; gap: 15px; flex-wrap: wrap; justify-content: center; }
            .btn { padding: 10px 25px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; transition: 0.2s; }
            .btn.mic { background: #4CAF50; color: white; }
            .btn.system { background: #2196F3; color: white; }
            .btn.both { background: #FF9800; color: white; }
            .btn.start { background: #9C27B0; color: white; }
            .btn.active { box-shadow: 0 0 15px #fff; }
            #status { color: #aaa; margin-top: 10px; font-family: monospace; }
            #audio-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: #555; margin-left: 10px; }
            #audio-indicator.active { background: #0f0; box-shadow: 0 0 10px #0f0; }
        </style>
    </head>
    <body>
        <img id="video" src="/stream" alt="Stream">
        <div class="controls">
            <button id="startBtn" class="btn start">▶ Запустить звук</button>
            <button id="micBtn" class="btn mic">🎤 Микрофон</button>
            <button id="systemBtn" class="btn system">🔉 Системный</button>
            <button id="bothBtn" class="btn both">🎧 Микрофон+Системный</button>
        </div>
        <div id="status">🔊 Audio: waiting for start... <span id="audio-indicator"></span></div>

        <script>
        (function() {
            const statusDiv = document.getElementById('status');
            const indicator = document.getElementById('audio-indicator');
            const log = (msg) => {
                console.log('[Audio]', msg);
                statusDiv.textContent = '🔊 ' + msg;
            };

            // ---- Управляющий WebSocket ----
            const controlWs = new WebSocket(`wss://${window.location.host}/ws/control`);
            controlWs.onopen = () => log('Control connected');
            controlWs.onclose = () => log('Control disconnected');

            function sendMode(mode) {
                controlWs.send(JSON.stringify({ mode }));
                document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
                const btn = document.getElementById(mode + 'Btn');
                if (btn) btn.classList.add('active');
            }

            document.getElementById('micBtn').onclick = () => sendMode('mic');
            document.getElementById('systemBtn').onclick = () => sendMode('system');
            document.getElementById('bothBtn').onclick = () => sendMode('both');

            // ---- Аудио WebSocket (безопасный) ----
            const audioWs = new WebSocket(`wss://${window.location.host}/ws/audio`);
            audioWs.binaryType = 'arraybuffer';
            let audioCtx = null;
            let nextStartTime = 0;

            audioWs.onopen = () => log('Audio WS connected');
            audioWs.onclose = () => log('Audio WS closed');
            audioWs.onerror = (e) => log('Audio WS error: ' + e);

            // Кнопка запуска звука
            document.getElementById('startBtn').onclick = async () => {
                try {
                    if (!audioCtx) {
                        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                        log('AudioContext created, state=' + audioCtx.state);
                        nextStartTime = audioCtx.currentTime;
                    }
                    if (audioCtx.state === 'suspended') {
                        await audioCtx.resume();
                        log('AudioContext resumed, state=' + audioCtx.state);
                    } else {
                        log('AudioContext already running, state=' + audioCtx.state);
                    }
                } catch (e) {
                    log('Error starting AudioContext: ' + e.message);
                }
            };

            // Обработка входящего аудио
            const sampleRate = 16000;
            audioWs.onmessage = (event) => {
                if (!audioCtx || audioCtx.state !== 'running') {
                    log('Audio data received but context not running');
                    return;
                }
                try {
                    const data = new Int16Array(event.data);
                    if (data.length === 0) return;
                    // Мигаем индикатором
                    indicator.classList.add('active');
                    setTimeout(() => indicator.classList.remove('active'), 100);

                    const audioBuffer = audioCtx.createBuffer(1, data.length, sampleRate);
                    const channelData = audioBuffer.getChannelData(0);
                    for (let i = 0; i < data.length; i++) {
                        channelData[i] = data[i] / 32768.0;
                    }
                    const source = audioCtx.createBufferSource();
                    source.buffer = audioBuffer;
                    source.connect(audioCtx.destination);
                    if (nextStartTime < audioCtx.currentTime) nextStartTime = audioCtx.currentTime;
                    source.start(nextStartTime);
                    nextStartTime += audioBuffer.duration;
                    log('Audio chunk played (' + data.length + ' samples)');
                } catch (e) {
                    log('Error playing audio: ' + e.message);
                }
            };
        })();
        </script>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)