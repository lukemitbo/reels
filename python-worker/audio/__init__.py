"""
Audio processing module for text-to-speech generation and word alignment.
"""
import os
import tempfile
from audio.tts import generate_audio_for_speaker
from audio.processing import combine_to_wav_with_timings
from audio.alignment import align_with_whisperx


def tts(
    script: list[tuple[str, str]]  # (speaker, text)
) -> tuple[bytes, list[tuple[str, float, float]], list[tuple[str, float, float]]]:
    """
    Generate audio from text lines and return both audio bytes, speaker timing information, 
    and word-level alignments.
    
    Args:
        script: List of (speaker, text) tuples where speaker is 'Peter' or 'Stewie'
        
    Returns:
        Tuple of (audio_bytes, speaker_timings, word_alignments) where:
        - audio_bytes: Combined WAV audio bytes
        - speaker_timings: List of (speaker, start_time, end_time) tuples
        - word_alignments: List of (word, start_time, end_time) tuples
    """
    audio_segments: list[bytes] = []
    speakers: list[str] = []

    # Build combined transcript for WhisperX alignment
    transcript_parts: list[str] = []

    for speaker, text in script:
        audio, normalized_speaker = generate_audio_for_speaker(text, speaker)
        audio_segments.append(audio)
        speakers.append(normalized_speaker)
        transcript_parts.append(text)
    
    # Combine all text lines into a single transcript
    combined_transcript = " ".join(transcript_parts)

    # Combine audio segments with timing information
    combined_wav, timings = combine_to_wav_with_timings(audio_segments, speakers)

    # Use WhisperX to get word-level alignments
    # Save WAV to temporary file for WhisperX
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_wav.write(combined_wav)
        temp_wav_path = temp_wav.name

    try:
        # Run WhisperX alignment
        word_alignments = align_with_whisperx(temp_wav_path, combined_transcript)
    finally:
        # Clean up temporary file
        if os.path.exists(temp_wav_path):
            os.unlink(temp_wav_path)

    return combined_wav, timings, word_alignments


__all__ = ['tts']

