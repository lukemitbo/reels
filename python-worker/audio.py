import io
from pydub import AudioSegment, effects
from elevenlabs.client import ElevenLabs
import os
import logging

logger = logging.getLogger(__name__)

TARGET_SR = 44100
TARGET_CH = 1  # mono
PAUSE_MS = 200  # between turns

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    logger.warning("ELEVENLABS_API_KEY not found in environment variables")

client = ElevenLabs(
    api_key=ELEVENLABS_API_KEY
)

def generate_audio_from_text_stewie(text: str) -> bytes:
    audio = client.text_to_speech.convert(
        text=text,
        voice_id="CIu3R8tbZv2ufv9B4Hwe",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    mp3_bytes = b"".join(list(audio))
    return mp3_bytes

def generate_audio_from_text_peter(text: str) -> bytes:
    audio = client.text_to_speech.convert(
        text=text,
        voice_id="pAeXHISBaG8rZIK5jvK7",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    mp3_bytes = b"".join(list(audio))
    return mp3_bytes


def segment_from_mp3_bytes(mp3_bytes: bytes) -> AudioSegment:
    buf = io.BytesIO(mp3_bytes)
    seg = AudioSegment.from_file(buf, format="mp3")
    # Normalize format for editing
    seg = seg.set_frame_rate(TARGET_SR).set_channels(TARGET_CH)
    # Optional: loudness normalization so voices match
    seg = effects.normalize(seg)
    return seg

def combine_to_wav(audio_segments_mp3: list[bytes]) -> bytes:
    """
    Takes a list of MP3 byte blobs, converts each to a normalized WAV segment,
    concatenates with small pauses, and returns PCM WAV bytes.
    """
    combined = AudioSegment.silent(duration=0, frame_rate=TARGET_SR)
    for i, mp3_bytes in enumerate(audio_segments_mp3):
        seg = segment_from_mp3_bytes(mp3_bytes)
        combined += seg
        if i != len(audio_segments_mp3) - 1:
            combined += AudioSegment.silent(duration=PAUSE_MS, frame_rate=TARGET_SR)

    out = io.BytesIO()
    combined.export(out, format="wav")  # 16-bit PCM
    return out.getvalue()

def combine_to_wav_with_timings(audio_segments_mp3: list[bytes], speakers: list[str]) -> tuple[bytes, list[tuple[str, float, float]]]:
    """
    Takes a list of MP3 byte blobs and speaker names, converts each to a normalized WAV segment,
    concatenates with small pauses, and returns PCM WAV bytes along with timing data.
    Returns: (wav_bytes, timing_data) where timing_data is list of (speaker, start_time, end_time) tuples.
    """
    combined = AudioSegment.silent(duration=0, frame_rate=TARGET_SR)
    timings: list[tuple[str, float, float]] = []
    current_time = 0.0
    
    for i, (mp3_bytes, speaker) in enumerate(zip(audio_segments_mp3, speakers)):
        seg = segment_from_mp3_bytes(mp3_bytes)
        seg_duration_seconds = len(seg) / 1000.0  # pydub duration is in milliseconds
        
        # Record timing for this segment
        start_time = current_time
        end_time = current_time + seg_duration_seconds
        timings.append((speaker, start_time, end_time))
        
        combined += seg
        current_time = end_time
        
        # Add pause if not last segment
        if i != len(audio_segments_mp3) - 1:
            pause_duration_seconds = PAUSE_MS / 1000.0
            combined += AudioSegment.silent(duration=PAUSE_MS, frame_rate=TARGET_SR)
            current_time += pause_duration_seconds

    out = io.BytesIO()
    combined.export(out, format="wav")  # 16-bit PCM
    return out.getvalue(), timings

def tts(peter_lines: list[str], stewie_lines: list[str]) -> tuple[bytes, list[tuple[str, float, float]]]:
    """
    Generate audio from text lines and return both audio bytes and timing information.
    Returns: (audio_bytes, timing_data) where timing_data is list of (speaker, start_time, end_time) tuples.
    """
    audio_segments: list[bytes] = []
    speakers: list[str] = []
    
    for peter_line, stewie_line in zip(peter_lines, stewie_lines):
        # get mp3 bytes for each line
        peter_audio = generate_audio_from_text_peter(peter_line) 
        stewie_audio = generate_audio_from_text_stewie(stewie_line)
        audio_segments.extend([peter_audio, stewie_audio])
        speakers.extend(["peter", "stewie"])
    
    combined_wav, timings = combine_to_wav_with_timings(audio_segments, speakers)
    return combined_wav, timings