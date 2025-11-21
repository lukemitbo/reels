import random
import os
from glob import glob
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, TextClip
from moviepy import vfx, afx
from datetime import datetime
from typing import Optional
def get_run_id() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")

def _check_text_wraps(text, font_path, font_size, width, stroke_width, text_align):
    """
    Check if text wraps to multiple lines when rendered with given parameters.
    Returns True if text wraps, False if it fits on one line.
    """
    # Create temporary TextClip to check if text wraps
    temp_clip = TextClip(
        text=text,
        font=font_path,
        font_size=font_size,
        method='caption',
        size=(width, None),
        text_align=text_align,
        stroke_width=stroke_width
    )
    # Check if text contains newline (wrapped)
    wraps = "\n" in temp_clip.text
    temp_clip.close()  # Cleanup
    return wraps

def make_vertical(bg_clip: VideoFileClip, target_w=1080, target_h=1920) -> VideoFileClip:
    """
    Scale & crop a source video to 9:16 without letterboxing.
    """
    # First, scale to ensure height >= target_h
    scaled = bg_clip.with_effects([vfx.Resize(height=target_h)])

    # If width is still < target_w, scale by width instead
    if scaled.w < target_w:
        scaled = bg_clip.with_effects([vfx.Resize(width=target_w)])
    # Center-crop to exact 1080x1920
    x_center = scaled.w / 2
    y_center = scaled.h / 2
    x1 = x_center - target_w / 2
    y1 = y_center - target_h / 2
    x2 = x_center + target_w / 2
    y2 = y_center + target_h / 2
    cropped = scaled.with_effects([vfx.Crop(x1=x1, y1=y1, x2=x2, y2=y2)])
    return cropped


def assemble_video(
    dialogue_wav_path: str,
    bg_folder: str,
    out_path: str,
    fps: int = 30,
    bitrate: str = "6M",
    speaker_timings: Optional[list[tuple[str, float, float]]] = None,
    pngs_folder: Optional[str] = None,
    word_alignments: Optional[list[tuple[str, float, float]]] = None,
):
    voice = AudioFileClip(dialogue_wav_path)
    audio_duration = voice.duration
    duration = audio_duration + 0.5  # small pad for video

    # Pick a random background loop you own
    choices = glob(os.path.join(bg_folder, "*.mp4"))
    if not choices:
        raise RuntimeError(f"No background MP4s found in {bg_folder}")
    bg_path = random.choice(choices)

    bg = VideoFileClip(bg_path).without_audio()

    # Make vertical 1080x1920 first (before looping to ensure proper frame timing)
    bg_v = make_vertical(bg, 1080, 1920)

    # Loop or cut to match audio length (with small pad)
    # vfx.Loop repeats the clip seamlessly to the requested duration
    # Ensure it starts from the beginning by explicitly trimming first
    #start_time = random.uniform(10, 900)
    start_time = random.uniform(0, bg_v.duration - duration)
    bg_v = bg_v.subclipped(start_time)  #, min(bg_v.duration, duration))
    # if bg_v.duration < duration:
    #     bg_v = bg_v.with_effects([vfx.Loop(duration=duration)])

    # Combine - use audio duration for final clip to avoid reading beyond audio file
    # Explicitly trim to ensure it starts at t=0 and has proper frame timing
    base_clip = bg_v.subclipped(0, audio_duration).with_audio(voice)

    # Add PNG overlays if timing data is provided
    overlay_clips = []
    text_clips = []
    if speaker_timings and pngs_folder:
        video_width = 1080
        video_height = 1920
        target_png_height = int(video_height * 0.4)  # 40% of video height

        # Load PNG images
        peter_png_path = os.path.join(pngs_folder, "Peter_Griffin.png")
        stewie_png_path = os.path.join(pngs_folder, "Stewie_Griffin.png")

        if not os.path.exists(peter_png_path):
            raise FileNotFoundError(f"Peter PNG not found at {peter_png_path}")
        if not os.path.exists(stewie_png_path):
            raise FileNotFoundError(
                f"Stewie PNG not found at {stewie_png_path}")

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
            img_clip = img_clip.with_effects(
                [vfx.Resize((png_width, png_height))])
            img_clip = img_clip.with_start(start_time)
            img_clip = img_clip.with_position((x_pos, y_pos))

            overlay_clips.append(img_clip)

    # Add word-level captions if word alignments are provided
    # if word_alignments:
    #     video_width = 1080
    #     video_height = 1920

    #     # Caption styling
    #     font_size = 90
    #     font_color = 'yellow'
    #     stroke_color = 'black'
    #     stroke_width = 2

    #     text_clips_with_timing = []
    #     font_path = "/app/fonts/SuperMalibu-Wp77v.ttf"
    #     text_width = 960

    #     for word, start_time, end_time in word_alignments:
    #         # Adjust font size if text wraps to multiple lines
    #         adjusted_font_size = font_size
    #         word_text = word.upper()

    #         # Check if text wraps and reduce font size until it fits on one line
    #         while adjusted_font_size >= 20:
    #             if not _check_text_wraps(word_text, font_path,
    #                                      adjusted_font_size, text_width,
    #                                      stroke_width, 'center'):
    #                 break  # Fits on one line
    #             adjusted_font_size -= 15

    #         # Ensure we don't go below minimum
    #         adjusted_font_size = max(adjusted_font_size, 20)

    #         # Create TextClip for each word with adjusted font size
    #         txt_clip = TextClip(
    #             text=word_text,
    #             font=font_path,
    #             duration=end_time - start_time,
    #             color=font_color,
    #             stroke_color=stroke_color,
    #             stroke_width=stroke_width,
    #             method='caption',
    #             font_size=adjusted_font_size,
    #             size=(text_width,
    #                   1800),  # Leave margins, auto height for wrapping
    #             text_align='center')

    #         # Set position - use 'center' for horizontal, fixed Y for vertical
    #         txt_clip = txt_clip.with_position(('center', 'center'))

    #         # Store clip with its start_time to apply in CompositeVideoClip
    #         text_clips_with_timing.append((txt_clip, start_time))

    #     # Apply start_time to text clips
    #     text_clips = [
    #         clip.with_start(start_time)
    #         for clip, start_time in text_clips_with_timing
    #     ]

    # # Composite all clips together based on what we have
    # if word_alignments:
    #     # Composite base + PNG overlays (if any) + text clips
    #     final = CompositeVideoClip([base_clip] + overlay_clips + text_clips)
    if speaker_timings and pngs_folder:
        # Composite base + PNG overlays
        final = CompositeVideoClip([base_clip] + overlay_clips)
    else:
        final = base_clip

    # Speed up video
    # final = final.with_effects([vfx.MultiplySpeed(1.3)])

    # Write MP4 (H.264 + AAC). Do the *only* lossy pass here.
    final.write_videofile(
        out_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        bitrate=bitrate,
        preset="medium",
        threads=4,
        write_logfile=False,
        ffmpeg_params=[
            "-movflags",
            "+faststart",  # better streaming/IG upload
            "-vsync",
            "cfr",  # constant frame rate to prevent frame freezing
        ],
    )

    # Cleanup
    voice.close()
    bg.close()
    bg_v.close()
    final.close()
    for clip in overlay_clips:
        clip.close()
    for clip in text_clips:
        clip.close()
if __name__ == "__main__":
    assemble_video(
        dialogue_wav_path="/app/audios/generate-audio.wav",
        bg_folder="/app/background-videos",
        out_path=f"/app/final-videos/final-{get_run_id()}.mp4",
        speaker_timings=[("peter", 0, 6), ("stewie", 7, 19), ("peter", 20, 30)],
        pngs_folder="/app/pngs",
    )
