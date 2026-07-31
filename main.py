from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, HTMLResponse
import uvicorn
import asyncio

app = FastAPI()

# Последний полученный кадр (байты JPEG)
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
            await asyncio.sleep(0.1)  # 10 fps максимум
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/", response_class=HTMLResponse)
async def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Screen Stream</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { margin: 0; background: #111; display: flex; justify-content: center; align-items: center; height: 100vh; }
            img { max-width: 100%; max-height: 100vh; border: 2px solid #333; }
        </style>
    </head>
    <body>
        <img src="/stream" alt="Stream">
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)