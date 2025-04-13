from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Response
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
        subprocess.run(["ffmpeg", "-i", input_path, "-y", "-q:a", "0", "-map", "a", output_path], check=True) # Adicionei o -y para sobrescrever arquivos existentes
        with open(output_path, "rb") as mp3_file:
            mp3_data = mp3_file.read()

        return Response(content=mp3_data, media_type="audio/mpeg") # Retorna o binário do MP3 como resposta

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Erro ao converter com FFmpeg: {e}")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Arquivo MP3 não encontrado após a conversão")
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)
