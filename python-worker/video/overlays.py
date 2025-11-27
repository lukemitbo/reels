"""
PNG overlay handling for speaker images.
"""
import os
from moviepy import ImageClip, VideoFileClip
from moviepy import vfx
from typing import List


def create_overlay_clips(
    speaker_timings: list[tuple[str, float, float]],
    pngs_folder: str,
    video_width: int,
    video_height: int,
    target_png_height_ratio: float = 0.4
) -> List[ImageClip]:
    """
    Create overlay clips for speaker PNG images based on timing.
    
    Args:
        speaker_timings: List of (speaker, start_time, end_time) tuples
        pngs_folder: Folder containing PNG images
        video_width: Video width in pixels
        video_height: Video height in pixels
        target_png_height_ratio: Ratio of video height for PNG height (default 0.4)
        
    Returns:
        List of ImageClip objects for overlays
    """
    overlay_clips = []
    target_png_height = int(video_height * target_png_height_ratio)

    # Load PNG images
    peter_png_path = os.path.join(pngs_folder, "Peter_Griffin.png")
    stewie_png_path = os.path.join(pngs_folder, "Stewie_Griffin.png")

    if not os.path.exists(peter_png_path):
        raise FileNotFoundError(f"Peter PNG not found at {peter_png_path}")
    if not os.path.exists(stewie_png_path):
        raise FileNotFoundError(f"Stewie PNG not found at {stewie_png_path}")

    # Get original image dimensions to calculate proportional scaling
    peter_img = ImageClip(peter_png_path)
    stewie_img = ImageClip(stewie_png_path)

    # Calculate scale factors based on target height
    peter_scale = target_png_height / peter_img.h
    stewie_scale = target_png_height / stewie_img.h

    # Calculate proportional widths
    peter_width = int(peter_img.w * peter_scale)
    peter_height = target_png_height
    stewie_width = int(stewie_img.w * stewie_scale)
    stewie_height = target_png_height

    # Close temporary clips used for dimension checking
    peter_img.close()
    stewie_img.close()

    # Create overlay clips for each timing segment
    for speaker, start_time, end_time in speaker_timings:
        # Determine which PNG to use, dimensions, and position
        if speaker == "peter":
            png_path = peter_png_path
            png_width = peter_width
            png_height = peter_height
            x_pos = 0  # bottom-left
        elif speaker == "stewie":
            png_path = stewie_png_path
            png_width = stewie_width
            png_height = stewie_height
            x_pos = video_width - png_width  # bottom-right
        else:
            continue  # Skip unknown speakers

        y_pos = video_height - png_height  # bottom alignment for both

        # Create ImageClip for this segment
        img_clip = ImageClip(png_path, duration=end_time - start_time)
        img_clip = img_clip.with_effects([vfx.Resize((png_width, png_height))])
        img_clip = img_clip.with_start(start_time)
        img_clip = img_clip.with_position((x_pos, y_pos))

        overlay_clips.append(img_clip)

    return overlay_clips

