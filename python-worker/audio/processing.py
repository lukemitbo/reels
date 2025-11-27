"""
Audio processing: segmenting, combining, and formatting.
"""
import io
from pydub import AudioSegment, effects
from audio.config import TARGET_SR, TARGET_CH, PAUSE_MS


def segment_from_mp3_bytes(mp3_bytes: bytes) -> AudioSegment:
    """
    Convert MP3 bytes to a normalized AudioSegment.
    
    Args:
        mp3_bytes: MP3 audio bytes
        
    Returns:
        Normalized AudioSegment with target sample rate and channels
    """
    buf = io.BytesIO(mp3_bytes)
    seg = AudioSegment.from_file(buf, format="mp3")
    # Normalize format for editing
    seg = seg.set_frame_rate(TARGET_SR).set_channels(TARGET_CH)
    # Optional: loudness normalization so voices match
    seg = effects.normalize(seg)
    return seg


def combine_to_wav(audio_segments_mp3: list[bytes]) -> bytes:
    """
    Combine multiple MP3 audio segments into a single WAV file.
    
    Takes a list of MP3 byte blobs, converts each to a normalized WAV segment,
    concatenates with small pauses, and returns PCM WAV bytes.
    
    Args:
        audio_segments_mp3: List of MP3 audio byte blobs
        
    Returns:
        Combined WAV audio bytes
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


def combine_to_wav_with_timings(
    audio_segments_mp3: list[bytes], 
    speakers: list[str]
) -> tuple[bytes, list[tuple[str, float, float]]]:
    """
    Combine audio segments with speaker timing information.
    
    Takes a list of MP3 byte blobs and speaker names, converts each to a normalized WAV segment,
    concatenates with small pauses, and returns PCM WAV bytes along with timing data.
    
    Args:
        audio_segments_mp3: List of MP3 audio byte blobs
        speakers: List of speaker names corresponding to each segment
        
    Returns:
        Tuple of (wav_bytes, timing_data) where timing_data is list of 
        (speaker, start_time, end_time) tuples.
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

