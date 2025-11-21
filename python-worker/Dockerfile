FROM python:3.11-slim

# 1) system deps:
# - ffmpeg: required by pydub/moviepy/whisperx
# - git & ca-certificates/curl: robustness for model downloads
# - fonts-dejavu: lets MoviePy TextClip render text without ImageMagick
# - libsndfile1: safer for torchaudio/soundfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg ca-certificates curl git fonts-dejavu-core libsndfile1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2) Python deps first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) App code
COPY app.py .
COPY audio.py .
COPY video.py .
COPY extract_text.py .

# 4) Media assets (background-videos and final-videos mounted as volumes)
COPY pngs/ ./pngs/
RUN mkdir -p audios final-videos background-videos fonts

# Optional: set env so MoviePy/imageio use system ffmpeg explicitly
ENV IMAGEIO_FFMPEG_EXE=ffmpeg

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
