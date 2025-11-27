"""
ElevenLabs client initialization.
"""
from elevenlabs.client import ElevenLabs
from audio.config import ELEVENLABS_API_KEY

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

