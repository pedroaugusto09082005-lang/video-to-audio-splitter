import os
import uuid
import subprocess
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/process")
async def process_video(file: UploadFile = File(...)):
    # aceita vídeo ou áudio como entrada
    ext = (file.filename or "").split(".")[-1].lower() if file.filename else "mp4"
    if ext not in {"mp4", "mov", "m4a", "mp3", "wav", "aac", "webm", "mkv"}:
        # não trava por causa disso, só tenta mesmo assim
        ext = "mp4"

    tmp_dir = "/tmp"
    job_id = str(uuid.uuid4())
    input_path = f"{tmp_dir}/{job_id}.{ext}"
    output_path = f"{tmp_dir}/{job_id}.mp3"

    try:
        # salva arquivo recebido
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Arquivo vazio.")
        with open(input_path, "wb") as f:
            f.write(content)

        # converte para UM mp3 só (mono, 16k) -> leve e bom pra transcrição
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-b:a", "64k",
            output_path,
        ]

        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0 or not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail=f"Falha no ffmpeg: {proc.stderr[-800:]}")

        return FileResponse(
            output_path,
            media_type="audio/mpeg",
            filename="audio.mp3"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # limpeza básica
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
        except:
            pass
