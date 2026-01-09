import os
import uuid
import shutil
import subprocess
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse

app = FastAPI()

@app.post("/process")
async def process_video(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    workdir = f"/tmp/{job_id}"
    os.makedirs(workdir, exist_ok=True)

    input_path = f"{workdir}/{file.filename}"

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    output_pattern = f"{workdir}/part_%03d.mp3"

    command = [
        "ffmpeg",
        "-i", input_path,
        "-vn",
        "-acodec", "libmp3lame",
        "-f", "segment",
        "-segment_time", "300",
        output_pattern
    ]

    subprocess.run(command, check=True)

    zip_path = f"/tmp/{job_id}.zip"
    shutil.make_archive(zip_path.replace(".zip", ""), "zip", workdir)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="audio_parts.zip"
    )
