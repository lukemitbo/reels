FROM python:3.11-slim

# System deps: ffmpeg, fonts, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg ca-certificates curl git fonts-dejavu-core libsndfile1 \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app code (not just a few files)
COPY . .

# Ensure required dirs exist
RUN mkdir -p audios final-videos background-videos fonts

# MoviePy / imageio use system ffmpeg
ENV IMAGEIO_FFMPEG_EXE=ffmpeg

EXPOSE 8000

# Default: run the FastAPI app (good for dev / n8n)
# For scheduled jobs we will override this CMD to `python main.py`.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
