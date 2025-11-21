import io
import tempfile
from pydub import AudioSegment, effects
from elevenlabs.client import ElevenLabs
import whisperx
import torchaudio
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
    # Speed up audio to 150% (1.5x speed)
    buf = io.BytesIO(mp3_bytes)
    seg = AudioSegment.from_file(buf, format="mp3")
    seg = seg.speedup(playback_speed=1.2)
    out = io.BytesIO()
    seg.export(out, format="mp3")
    return out.getvalue()

def generate_audio_from_text_peter(text: str) -> bytes:
    audio = client.text_to_speech.convert(
        text=text,
        voice_id="pAeXHISBaG8rZIK5jvK7",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    mp3_bytes = b"".join(list(audio))
    # Speed up audio to 150% (1.5x speed)
    buf = io.BytesIO(mp3_bytes)
    seg = AudioSegment.from_file(buf, format="mp3")
    seg = seg.speedup(playback_speed=1.2)
    out = io.BytesIO()
    seg.export(out, format="mp3")
    return out.getvalue()


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

def align_with_whisperx(audio_path: str, transcript: str) -> list[tuple[str, float, float]]:
    """
    Use WhisperX forced alignment to get word-level timestamps.
    Returns list of (word, start_time, end_time) tuples.
    """
    # Load audio
    audio = whisperx.load_audio(audio_path)

    # Get audio duration
    info = torchaudio.info(audio_path)
    duration = info.num_frames / float(info.sample_rate)

    # Hardcode language to English
    lang = "en"

    # Create a single segment spanning the entire audio duration
    segments = [{
        "start": 0.0,
        "end": duration,
        "text": transcript
    }]

    # Load English alignment model
    align_model, metadata = whisperx.load_align_model(
        language_code=lang, device="cpu"
    )

    # Run alignment
    aligned = whisperx.align(
        segments,
        align_model,
        metadata,
        audio,
        "cpu",
        return_char_alignments=False
    )

    # Extract words from all segments and convert to tuple format
    word_alignments = []
    for segment in aligned["segments"]:
        words = segment["words"]
        for w in words:
            word_alignments.append((w["word"], w["start"], w["end"]))

    logger.info(f"WhisperX generated {len(word_alignments)} word alignments from {len(aligned['segments'])} segments")

    return word_alignments


def tts(
    script: list[tuple[str, str]]  # (speaker, text)
) -> tuple[bytes, list[tuple[str, float, float]], list[tuple[str, float,
                                                             float]]]:
    """
    Generate audio from text lines and return both audio bytes, speaker timing information, and word-level alignments.
    Returns: (audio_bytes, speaker_timings, word_alignments) where:
        - speaker_timings is list of (speaker, start_time, end_time) tuples
        - word_alignments is list of (word, start_time, end_time) tuples
    """
    audio_segments: list[bytes] = []
    speakers: list[str] = []

    # Build combined transcript for WhisperX alignment
    transcript_parts: list[str] = []

    for speaker, text in script:
        if speaker == "Peter":
            peter_audio = generate_audio_from_text_peter(text)
            audio_segments.append(peter_audio)
            speakers.append("peter")
        elif speaker == "Stewie":
            stewie_audio = generate_audio_from_text_stewie(text)
            audio_segments.append(stewie_audio)
            speakers.append("stewie")
        transcript_parts.append(text)
    # Combine all text lines into a single transcript
    combined_transcript = " ".join(transcript_parts)

    combined_wav, timings = combine_to_wav_with_timings(
        audio_segments, speakers)

    # Use WhisperX to get word-level alignments
    # Save WAV to temporary file for WhisperX
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_wav.write(combined_wav)
        temp_wav_path = temp_wav.name

    # Run WhisperX alignment
    word_alignments = align_with_whisperx(temp_wav_path, combined_transcript)

    # Clean up temporary file
    if os.path.exists(temp_wav_path):
        os.unlink(temp_wav_path)

    return combined_wav, timings, word_alignments
