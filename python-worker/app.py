from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import List
import logging
import os
import tempfile
from extract_text import fetch_and_extract
from audio import tts
from video import assemble_video, get_run_id


# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(title="AI Reels Worker")

class ExtractRequest(BaseModel):
    urls: List[str]

class ExtractResponse(BaseModel):
    items: List[dict]  # [{url, text}]

class FormatRequest(BaseModel):
    text: str

class FormatResponse(BaseModel):
    peter: list[str]
    stewie: list[str]

class GenerateAudioRequest(BaseModel):
    peter: list[str]
    stewie: list[str]

class GenerateAudioResponse(BaseModel):
    audio: bytes


@app.post("/extract", response_model=ExtractResponse)
def extract(req: ExtractRequest):
    logger.info(f"Requesting to extract: {req.urls}")
    out = []
    seen = set()
    for url in req.urls[:6]:  # cap to 3–6 sources for speed
        if url in seen: 
            continue
        seen.add(url)
        text = fetch_and_extract(url)
        if text:
            out.append({"url": url, "text": text})
    return {"items": out}

@app.post("/format-script", response_model=FormatResponse)
def format_script(req: FormatRequest):
    print(req.text)
    """
    Peter: Hey, Stewie, have you seen this new Visual Studio 2026? They say it’s AI-native now—like, it practically thinks for you!

    Stewie: Oh, Peter, if by “thinks” you mean it’s embedded with AI that smartly detects typos, suggests file names, and even renders Mermaid charts, then yes, it’s practically your own tiny coding genius in a box.
    """
    peter = []
    stewie = []
    for line in req.text.split("\n"):
        if line.startswith("Peter:"):
            peter.append(line.split(":")[1].strip())
        elif line.startswith("Stewie:"):
            stewie.append(line.split(":")[1].strip())
    return {"peter": peter, "stewie": stewie}


@app.post("/generate-audio", response_model=GenerateAudioResponse)
def generate_audio(req: GenerateAudioRequest):
    audio, timings = tts(req.peter, req.stewie)
    # Note: timings are not returned in this endpoint, but could be added to response model if needed
    return Response(content=audio, media_type="audio/wav")


@app.post("/generate-video")
def generate_video(req: GenerateAudioRequest):
    """
    Generate a video with PNG overlays based on speaker timings.
    Returns the final video file as MP4.
    """
    logger.info("Generating video with speaker overlays")
    # with open("/app/final-videos/final-20251112165521.mp4", "rb") as f:
    #     video_bytes = f.read()
    #     video_filename = "final-20251112165521.mp4"
    # return Response(
    #         content=video_bytes,
    #         media_type="video/mp4",
    #         headers={"Content-Disposition": f'attachment; filename="{video_filename}"'}
    #     )
    
    # Generate audio with timing information
    audio_bytes, timings = tts(req.peter, req.stewie)
    
    # Create temporary directory for audio file
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save audio to temporary WAV file
        audio_path = os.path.join(temp_dir, "dialogue.wav")
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        
        # Generate output video path
        video_filename = f"final-{get_run_id()}.mp4"
        video_path = os.path.join(temp_dir, video_filename)
        
        # Assemble video with PNG overlays
        assemble_video(
            dialogue_wav_path=audio_path,
            bg_folder="/app/background-videos",
            out_path=video_path,
            speaker_timings=timings,
            pngs_folder="/app/pngs",
        )
        
        # Read the generated video file
        with open(video_path, "rb") as f:
            video_bytes = f.read()
        
        logger.info(f"Video generated successfully: {video_filename}")
        
        # Return video as response
        return Response(
            content=video_bytes,
            media_type="video/mp4",
            headers={"Content-Disposition": f'attachment; filename="{video_filename}"'}
        )