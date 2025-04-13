from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Header
from fastapi.responses import FileResponse
import os
import uuid
import subprocess

app = FastAPI()

MAX_UPLOAD_SIZE_MB = 50  # Limite de upload em MB
AUTH_TOKEN = "seu-token-seguro-aqui"

@app.middleware("http")
async def check_authorization_and_size(request: Request, call_next):
    # Autenticação por token
    auth = request.headers.get("authorization")
    if auth != f"Bearer {AUTH_TOKEN}":
        raise HTTPException(status_code=401, detail="Token inválido")

    # Verifica Content-Length para limitar tamanho do upload
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Arquivo excede o tamanho máximo permitido (50MB)")

    return await call_next(request)

@app.post("/extract-audio")
async def extract_audio(file: UploadFile = File(...)):
    input_filename = f"/tmp/{uuid.uuid4()}.mp4"
    output_filename = input_filename.replace(".mp4", ".mp3")

    # Salva vídeo temporariamente
    with open(input_filename, "wb") as f:
        f.write(await file.read())

    try:
        # Extrai áudio com ffmpeg
        subprocess.run([
            "ffmpeg", "-i", input_filename, "-vn",
            "-ar", "44100", "-ac", "2", "-b:a", "192k", output_filename
        ], check=True)
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="Erro ao extrair áudio com ffmpeg")

    return FileResponse(output_filename, media_type="audio/mpeg", filename="output.mp3")
