from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import shutil
import subprocess
import uuid

app = FastAPI(title="Video to Audio (single MP3)")

@app.get("/")
def home():
    return {"status": "ok", "hint": "Use POST /process with form-data field 'file' (video)"}

@app.post("/process")
async def process_video(file: UploadFile = File(...)):
    # valida
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo inválido")

    # cria pasta temporária
    job_id = str(uuid.uuid4())
    workdir = f"/tmp/{job_id}"
    os.makedirs(workdir, exist_ok=True)

    # salva o vídeo recebido
    input_path = os.path.join(workdir, file.filename)
    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # saída mp3 única
    output_path = os.path.join(workdir, "audio.mp3")

    # ffmpeg: extrai áudio inteiro (mono 16k, leve pra transcrição)
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-b:a", "64k",
        output_path
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"FFmpeg falhou: {proc.stderr[-1200:]}"
            )
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="FFmpeg não encontrado no container")

    # devolve o arquivo mp3 (download direto)
    return FileResponse(
        output_path,
        media_type="audio/mpeg",
        filename="audio.mp3"
    )
