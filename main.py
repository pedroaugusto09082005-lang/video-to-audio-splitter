import os
import subprocess
import tempfile
import zipfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="Video to Audio (MP3 ZIP)")

@app.get("/")
def health():
    return {"status": "ok", "message": "API online. Use POST /process com form-data file."}

@app.post("/process")
async def process_video(file: UploadFile = File(...)):
    # cria uma pasta temporária
    with tempfile.TemporaryDirectory() as tmpdir:
        # caminhos
        input_path = os.path.join(tmpdir, file.filename or "input.mp4")
        mp3_path = os.path.join(tmpdir, "audio.mp3")
        zip_path = os.path.join(tmpdir, "audio.zip")

        # salva o arquivo recebido
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Arquivo vazio.")
        with open(input_path, "wb") as f:
            f.write(content)

        # converte para MP3 (1 arquivo só)
        # 128k é um padrão bom (3 min ~ 3MB)
        cmd = [
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-vn",
            "-acodec", "libmp3lame",
            "-b:a", "128k",
            "-ar", "44100",
            "-ac", "2",
            mp3_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao executar ffmpeg: {str(e)}")

        if result.returncode != 0:
            # manda o log do ffmpeg pra você enxergar o erro
            raise HTTPException(
                status_code=500,
                detail=f"FFmpeg falhou.\nSTDERR:\n{result.stderr}"
            )

        # cria ZIP com o mp3 dentro
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(mp3_path, arcname="audio.mp3")

        # retorna o ZIP
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename="audio.zip"
        )
