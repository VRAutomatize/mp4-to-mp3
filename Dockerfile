FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY .env /app/.env

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
