from fastapi import FastAPI, File, UploadFile, HTTPException, Header
import shutil, os, uuid, subprocess
from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis do .env

app = FastAPI()

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))
API_TOKEN = os.getenv("API_TOKEN", "token-default")

@app.post("/convert")
async def convert_to_mp3(file: UploadFile = File(...), authorization: str = Header(None)):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Token inválido")

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Arquivo maior que {MAX_FILE_SIZE_MB}MB")

    input_path = f"/tmp/{uuid.uuid4()}.mp4"
    output_path = input_path.replace(".mp4", ".mp3")

    with open(input_path, "wb") as f:
        f.write(contents)

    try:
        subprocess.run(["ffmpeg", "-i", input_path, "-q:a", "0", "-map", "a", output_path], check=True)
        return {"message": "Convertido com sucesso", "file_path": output_path}
    except subprocess.CalledProcessError:
        raise HTTPException(status_code=500, detail="Erro ao converter com FFmpeg")
    finally:
        os.remove(input_path)
