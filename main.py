from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import subprocess
import uuid
import os

app = FastAPI()

# ROTA RAIZ (ESSA É A CORREÇÃO DO 502)
@app.get("/")
def root():
    return {"status": "online", "message": "API de video para mp3 funcionando"}

# ROTA DE PROCESSAMENTO
@app.post("/process")
async def process_video(file: UploadFile = File(...)):
    temp_id = str(uuid.uuid4())
    input_path = f"/tmp/{temp_id}.mp4"
    output_path = f"/tmp/{temp_id}.mp3"

    with open(input_path, "wb") as f:
        f.write(await file.read())

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vn",
        "-acodec", "libmp3lame",
        "-ab", "128k",
        output_path
    ]

    subprocess.run(cmd, check=True)

    return FileResponse(
        output_path,
        media_type="audio/mpeg",
        filename="audio.mp3"
    )
