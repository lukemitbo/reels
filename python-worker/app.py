from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import List
import logging
import os
import json
import tempfile
from extract_text import fetch_and_extract
from audio import tts
from video import assemble_video, get_run_id
from generate_script import generate_script as generate_script_func
from generate_script import generate_script_manual as generate_script_manual_func

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

class GenerateVideoRequest(BaseModel):
    script: list[tuple[str, str]] # (speaker, text)


class GenerateAudioResponse(BaseModel):
    audio: bytes


class GenerateScriptRequest(BaseModel):
    text: str # the prompt to be sent to gpt-o3

class GenerateScriptResponse(BaseModel):
    script: list[tuple[str, str]] # (speaker, text)

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
    Array: [["Peter", "Hey Lois— I mean, Stewie— did you hear some hackers just let an AI run wild like an angry Roomba?"],["Stewie", "Yes, tubby, but imagine that Roomba also steals your passwords while buffing the hardwood— that's Anthropic's recent nightmare."],["Peter", "So the robot did all the hacking? No little guy in a hoodie eating Cheetos?"]]
    """
    peter = []
    stewie = []
    for speaker, text in req.text:
        if speaker == "Peter":
            peter.append(text)
        elif speaker == "Stewie":
            stewie.append(text)
    return {"peter": peter, "stewie": stewie}


# @app.post("/generate-audio", response_model=GenerateAudioResponse)
# def generate_audio(req: GenerateAudioRequest):
#     audio, timings, word_alignments = tts(req.peter, req.stewie)
#     # Note: timings and word_alignments are not returned in this endpoint, but could be added to response model if needed
#     return Response(content=audio, media_type="audio/wav")

@app.post("/generate-script", response_model=GenerateScriptResponse)
def generate_script(req: GenerateScriptRequest):
    script: list[tuple[str, str]] = generate_script_func(req.text)
    return {"script": script}

@app.post("/generate-script-manual", response_model=GenerateScriptResponse)
def generate_script_manual(req: GenerateScriptRequest):
    script: list[tuple[str, str]] = generate_script_manual_func(req.text)
    return {"script": script}

@app.post("/generate-video")
def generate_video(req: GenerateVideoRequest):
    """
    Generate a video with PNG overlays based on speaker timings.
    Returns the final video file as MP4.
    """
    logger.info("Generating video with speaker overlays")
    # Generate audio with timing information and word alignments
    audio_bytes, timings, word_alignments = tts(req.script)

    # Generate run ID for consistent naming
    run_id = get_run_id()

    # Ensure output directory exists
    output_dir = "/data/out"
    os.makedirs(output_dir, exist_ok=True)

    # Write audio bytes, speaker timings, and word alignments to /data/out
    audio_filename = f"{run_id}.wav"
    audio_output_path = os.path.join(output_dir, audio_filename)
    with open(audio_output_path, "wb") as f:
        f.write(audio_bytes)
    logger.info(f"Audio saved to {audio_output_path}")

    # Write speaker timings as JSON
    timings_filename = f"{run_id}_speaker_timings.json"
    timings_output_path = os.path.join(output_dir, timings_filename)
    timings_data = [{
        "speaker": speaker,
        "start": start,
        "end": end
    } for speaker, start, end in timings]
    with open(timings_output_path, "w") as f:
        json.dump(timings_data, f, indent=2)
    logger.info(f"Speaker timings saved to {timings_output_path}")

    # Write word alignments as JSON
    word_alignments_filename = f"{run_id}_word_alignments.json"
    word_alignments_output_path = os.path.join(output_dir,
                                               word_alignments_filename)
    word_alignments_data = [{
        "word": word,
        "start": start,
        "end": end
    } for word, start, end in word_alignments]
    with open(word_alignments_output_path, "w") as f:
        json.dump(word_alignments_data, f, indent=2)
    logger.info(f"Word alignments saved to {word_alignments_output_path}")

    # Create temporary directory for audio file
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save audio to temporary WAV file
        audio_path = os.path.join(temp_dir, "dialogue.wav")
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)

        # Generate output video path
        video_filename = f"final-{run_id}.mp4"
        video_path = os.path.join(temp_dir, video_filename)

        # Assemble video with PNG overlays and word-level captions
        assemble_video(
            dialogue_wav_path=audio_path,
            bg_folder="/app/background-videos",
            out_path=video_path,
            speaker_timings=timings,
            pngs_folder="/app/pngs",
            word_alignments=word_alignments,
        )

        # Read the generated video file
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        logger.info(f"Video generated successfully: {video_filename}")

        # Return video as response
        return Response(content=video_bytes,
                        media_type="video/mp4",
                        headers={
                            "Content-Disposition":
                            f'attachment; filename="{video_filename}"'
                        })
