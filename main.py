from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import uuid
import subprocess
import shutil

app = FastAPI()

# Healthcheck (resolve o "Application failed to respond" do Railway)
@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/process")
async def process_video(file: UploadFile = File(...)):
    workdir = f"/tmp/{uuid.uuid4()}"
    os.makedirs(workdir, exist_ok=True)

    in_path = os.path.join(workdir, file.filename or "input.mp4")
    out_path = os.path.join(workdir, "audio.mp3")

    # salva upload
    content = await file.read()
    with open(in_path, "wb") as f:
        f.write(content)

    # garante ffmpeg
    if not shutil.which("ffmpeg"):
        raise HTTPException(status_code=500, detail="ffmpeg não está instalado no servidor")

    # extrai áudio inteiro em MP3
    cmd = [
        "ffmpeg",
        "-y",
        "-i", in_path,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-b:a", "64k",
        out_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"ffmpeg erro: {result.stderr[-1000:]}")

    return FileResponse(out_path, media_type="audio/mpeg", filename="audio.mp3")
