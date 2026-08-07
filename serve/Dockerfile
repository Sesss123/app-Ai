FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY serve/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY serve/ ./serve/
COPY data/processed/places.json ./data/processed/places.json
COPY models/ ./models/

WORKDIR /app/serve
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
