from fastapi import FastAPI, UploadFile, File
import subprocess
import os
import uuid

app = FastAPI()

@app.post("/process")
async def process_video(file: UploadFile = File(...)):
    uid = str(uuid.uuid4())
    input_path = f"/tmp/{uid}.mp4"
    output_dir = f"/tmp/{uid}"
    os.makedirs(output_dir, exist_ok=True)

    with open(input_path, "wb") as f:
        f.write(await file.read())

    command = [
        "ffmpeg",
        "-i", input_path,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-f", "segment",
        "-segment_time", "600",
        f"{output_dir}/part_%03d.mp3"
    ]

    subprocess.run(command, check=True)

    files = sorted(os.listdir(output_dir))
    return {
        "parts": files
    }
