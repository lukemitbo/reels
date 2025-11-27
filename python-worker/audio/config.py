"""
Audio processing configuration constants.
"""
import os
import logging

logger = logging.getLogger(__name__)

# Audio format constants
TARGET_SR = 44100  # Target sample rate
TARGET_CH = 1  # Mono channel
PAUSE_MS = 200  # Pause duration between speaker turns in milliseconds

# ElevenLabs API configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    logger.warning("ELEVENLABS_API_KEY not found in environment variables")

# Voice configurations
VOICE_CONFIGS = {
    "peter": {
        "voice_id": "pAeXHISBaG8rZIK5jvK7",
        "model_id": "eleven_multilingual_v2",
        "speed_multiplier": 1.2,
    },
    "stewie": {
        "voice_id": "CIu3R8tbZv2ufv9B4Hwe",
        "model_id": "eleven_multilingual_v2",
        "speed_multiplier": 1.2,
    }
}

