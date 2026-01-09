from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import os
import subprocess
import tempfile
import uuid

app = FastAPI(title="Video to MP3", version="1.0.0")


@app.get("/")
def home():
    return {"status": "ok", "message": "API online. Use POST /process com form-data file"}


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/process")
async def process_video(file: UploadFile = File(...)):
    # Aceita qualquer vídeo, mas valida que veio algo
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Envie um arquivo no campo 'file'")

    workdir = tempfile.mkdtemp(prefix="job_")
    input_path = os.path.join(workdir, f"input_{uuid.uuid4().hex}_{file.filename}")
    output_path = os.path.join(workdir, "output.mp3")

    # salva upload no disco
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Converte para MP3 (tamanho bom e qualidade boa)
    # 128k = ~3MB em 3 minutos (aprox). Se quiser mais qualidade, muda para 192k.
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vn",
        "-acodec", "libmp3lame",
        "-b:a", "128k",
        "-ar", "44100",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Erro no ffmpeg: {result.stderr[-800:]}"
            )
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="ffmpeg não encontrado no container")

    return FileResponse(
        output_path,
        media_type="audio/mpeg",
        filename="audio.mp3"
    )
