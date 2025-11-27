"""
Text-to-speech generation using ElevenLabs.
"""
import io
from pydub import AudioSegment
from audio.client import client
from audio.config import VOICE_CONFIGS


def generate_audio_from_text(text: str, voice_name: str) -> bytes:
    """
    Generate audio from text using the specified voice.
    
    Args:
        text: Text to convert to speech
        voice_name: Voice name ('peter' or 'stewie')
        
    Returns:
        MP3 audio bytes
        
    Raises:
        ValueError: If voice_name is not recognized
    """
    if voice_name not in VOICE_CONFIGS:
        raise ValueError(f"Unknown voice: {voice_name}. Must be one of {list(VOICE_CONFIGS.keys())}")
    
    voice_config = VOICE_CONFIGS[voice_name]
    
    # Generate audio using ElevenLabs
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_config["voice_id"],
        model_id=voice_config["model_id"],
        output_format="mp3_44100_128",
    )
    
    mp3_bytes = b"".join(list(audio))
    
    # Apply speed adjustment
    buf = io.BytesIO(mp3_bytes)
    seg = AudioSegment.from_file(buf, format="mp3")
    seg = seg.speedup(playback_speed=voice_config["speed_multiplier"])
    
    out = io.BytesIO()
    seg.export(out, format="mp3")
    return out.getvalue()


def generate_audio_for_speaker(text: str, speaker: str) -> tuple[bytes, str]:
    """
    Generate audio for a speaker and return normalized speaker name.
    
    Args:
        text: Text to convert to speech
        speaker: Speaker name ('Peter' or 'Stewie')
        
    Returns:
        Tuple of (audio_bytes, normalized_speaker_name)
        
    Raises:
        ValueError: If speaker is not recognized
    """
    speaker_lower = speaker.lower()
    
    if speaker_lower == "peter":
        audio = generate_audio_from_text(text, "peter")
        return audio, "peter"
    elif speaker_lower == "stewie":
        audio = generate_audio_from_text(text, "stewie")
        return audio, "stewie"
    else:
        raise ValueError(f"Unknown speaker: {speaker}. Must be 'Peter' or 'Stewie'")

