FROM python:3.11-slim

# System deps for lxml/ffmpeg (ffmpeg for video processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ffmpeg ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code and resources
COPY app.py .
COPY audio.py .
COPY video.py .
COPY extract_text.py .

# Copy necessary resources (PNGs and background videos)
COPY pngs/ ./pngs/
COPY background-videos/ ./background-videos/
COPY final-videos/ ./final-videos/

# Create directories for temporary files (if needed)
RUN mkdir -p audios final-videos

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

