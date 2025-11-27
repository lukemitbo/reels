"""
Background video processing and preparation.
"""
import random
import os
from glob import glob
from moviepy import VideoFileClip, AudioFileClip
from moviepy import vfx
from typing import Tuple


def make_vertical(
    bg_clip: VideoFileClip, 
    target_w: int = 1080, 
    target_h: int = 1920
) -> VideoFileClip:
    """
    Scale & crop a source video to 9:16 aspect ratio without letterboxing.
    
    Args:
        bg_clip: Source video clip
        target_w: Target width (default 1080)
        target_h: Target height (default 1920)
        
    Returns:
        Vertically formatted video clip
    """
    # First, scale to ensure height >= target_h
    scaled = bg_clip.with_effects([vfx.Resize(height=target_h)])

    # If width is still < target_w, scale by width instead
    if scaled.w < target_w:
        scaled = bg_clip.with_effects([vfx.Resize(width=target_w)])
    
    # Center-crop to exact target dimensions
    x_center = scaled.w / 2
    y_center = scaled.h / 2
    x1 = x_center - target_w / 2
    y1 = y_center - target_h / 2
    x2 = x_center + target_w / 2
    y2 = y_center + target_h / 2
    cropped = scaled.with_effects([vfx.Crop(x1=x1, y1=y1, x2=x2, y2=y2)])
    return cropped


def prepare_background_clip(
    bg_folder: str,
    audio_duration: float,
    target_w: int = 1080,
    target_h: int = 1920
) -> Tuple[VideoFileClip, VideoFileClip]:
    """
    Select and prepare a background video clip to match audio duration.
    
    Args:
        bg_folder: Folder containing background video files
        audio_duration: Duration of the audio in seconds
        target_w: Target width (default 1080)
        target_h: Target height (default 1920)
        
    Returns:
        Tuple of (base_clip_with_audio, background_clip)
    """
    # Pick a random background video
    choices = glob(os.path.join(bg_folder, "*.mp4"))
    if not choices:
        raise RuntimeError(f"No background MP4s found in {bg_folder}")
    bg_path = random.choice(choices)

    bg = VideoFileClip(bg_path).without_audio()

    # Make vertical 1080x1920
    bg_v = make_vertical(bg, target_w, target_h)

    # Select a random start point and trim to match audio length
    duration = audio_duration + 0.5  # small pad for video
    start_time = random.uniform(0, max(0, bg_v.duration - duration))
    bg_v = bg_v.subclipped(start_time)

    return bg, bg_v

