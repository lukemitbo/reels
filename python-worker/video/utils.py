"""
Utility functions for video processing.
"""
from datetime import datetime
from typing import Optional


def get_run_id() -> str:
    """Generate a unique run ID based on current timestamp."""
    return datetime.now().strftime("%Y%m%d%H%M%S")


def ease_out_cubic(x: float) -> float:
    """Easing function for smooth animations."""
    return 1 - (1 - x) ** 3


def get_speaker_at_time(
    speaker_timings: list[tuple[str, float, float]], 
    time: float
) -> Optional[str]:
    """
    Determine which speaker is speaking at a given time.
    
    Args:
        speaker_timings: List of (speaker, start_time, end_time) tuples
        time: Time in seconds to check
        
    Returns:
        The speaker name if found, None otherwise.
    """
    for speaker, start, end in speaker_timings:
        if start <= time < end:
            return speaker
    return None

