from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Response
import shutil, os, uuid, subprocess
from dotenv import load_dotenv
from typing import Tuple

load_dotenv()

app = FastAPI()

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))
API_TOKEN = os.getenv("API_TOKEN", "token-default")

async def convert_to_mp3_and_extract_frame(input_path: str) -> Tuple[bytes, bytes]:
    """Converts the video to MP3 and extracts the first frame as JPEG."""
    output_mp3_path = input_path.replace(".mp4", ".mp3")
    output_jpeg_path = input_path.replace(".mp4", ".jpg")

    try:
        # Convert to MP3
        subprocess.run(
            ["ffmpeg", "-i", input_path, "-y", "-q:a", "0", "-map", "a", output_mp3_path],
            check=True,
            capture_output=True,  # Capture stdout and stderr for debugging
            text=True  # Ensure output is treated as text
        )

        # Extract the first frame as JPEG
        subprocess.run(
            ["ffmpeg", "-i", input_path, "-y", "-ss", "00:00:00", "-vframes", "1", output_jpeg_path],
            check=True,
            capture_output=True,  # Capture stdout and stderr for debugging
            text=True  # Ensure output is treated as text
        )

        # Read the MP3 file
        with open(output_mp3_path, "rb") as mp3_file:
            mp3_data = mp3_file.read()

        # Read the JPEG file
        with open(output_jpeg_path, "rb") as jpeg_file:
            jpeg_data = jpeg_file.read()

        return mp3_data, jpeg_data

    except subprocess.CalledProcessError as e:
        # Log stdout and stderr for better error diagnosis
        print(f"FFmpeg error: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"Erro ao converter com FFmpeg: {e}")
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        raise HTTPException(status_code=500, detail=f"Arquivo não encontrado após a conversão/extração: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {e}")
    finally:
        # Clean up input and output files (only if they exist)
        for file_path in [input_path, output_mp3_path, output_jpeg_path]:
            if os.path.exists(file_path):
                os.remove(file_path)


@app.post("/convert")
async def convert_to_mp3(file: UploadFile = File(...), authorization: str = Header(None)):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Token inválido")

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Arquivo maior que {MAX_FILE_SIZE_MB}MB")

    input_path = f"/tmp/{uuid.uuid4()}.mp4"

    with open(input_path, "wb") as f:
        f.write(contents)

    try:
        mp3_data, jpeg_data = await convert_to_mp3_and_extract_frame(input_path)

        # Return both MP3 and JPEG data
        return {
            "mp3": Response(content=mp3_data, media_type="audio/mpeg"),
            "jpeg": Response(content=jpeg_data, media_type="image/jpeg"),
        }

    except HTTPException as e:
        raise e  # Re-raise HTTPExceptions
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {e}")
