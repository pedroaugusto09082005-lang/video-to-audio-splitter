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
    # cria pasta temporária
    workdir = f"/tmp/{uuid.uuid4()}"
    os.makedirs(workdir, exist_ok=True)

    # caminhos
    in_path = os.path.join(workdir, file.filename or "input.mp4")
    out_path = os.path.join(workdir, "audio.mp3")

    # salva upload
    with open(in_path, "wb") as f:
        f.write(await file.read())

    # garante que ffmpeg existe
    if not shutil.which("ffmpeg"):
        raise HTTPException(status_code=500, detail="ffmpeg não está instalado no servidor")

    # extrai áudio inteiro em MP3 (leve e bom pra transcrição)
    # 64k: tamanho baixo (bom), 16kHz mono: ótimo pra STT
    cmd = [
        "ffmpeg",
        "-y",
        "-i", in_path,
        "-vn",
        "-ac", "1",
