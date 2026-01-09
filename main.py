import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse

app = FastAPI(title="video-to-audio-splitter", version="1.0.0")


@app.get("/")
def root():
    # Isso evita o 502 quando você abre o link no navegador
    return {"status": "ok", "service": "video-to-audio-splitter"}


@app.get("/health")
def health():
    return {"ok": True}


def _run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "ffmpeg failed")


@app.post("/process")
async def process_video(file: UploadFile = File(...)):
    """
    Recebe um vídeo e retorna um ZIP contendo 1 arquivo MP3 (audio.mp3).
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo inválido (sem nome).")

    # pasta temporária segura
    workdir = Path(tempfile.mkdtemp(prefix="v2a_"))
    try:
        input_path = workdir / f"input{Path(file.filename).suffix.lower() or '.mp4'}"
        mp3_path = workdir / "audio.mp3"
        zip_path = workdir / "audio.zip"

        # salva upload em disco
        with input_path.open("wb") as f:
            content = await file.read()
            f.write(content)

        # ffmpeg: extrai áudio como MP3
        # -vn: remove vídeo
        # -b:a 128k: qualidade boa e tamanho baixo (pode mudar depois)
        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-vn",
            "-acodec", "libmp3lame",
            "-b:a", "128k",
            str(mp3_path),
        ]

        try:
            _run(cmd)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro no ffmpeg: {str(e)}")

        if not mp3_path.exists() or mp3_path.stat().st_size == 0:
            raise HTTPException(status_code=500, detail="MP3 não foi gerado.")

        # cria ZIP com o MP3 (porque você disse que ZIP estava funcionando melhor)
        shutil.make_archive(str(zip_path.with_suffix("")), "zip", root_dir=str(workdir), base_dir="audio.mp3")

        if not zip_path.exists():
            raise HTTPException(status_code=500, detail="ZIP não foi gerado.")

        # devolve o ZIP
        return FileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename="audio.zip",
        )

    finally:
        # limpeza (Railway é stateless, melhor limpar)
        try:
            shutil.rmtree(workdir, ignore_errors=True)
        except Exception:
            pass
