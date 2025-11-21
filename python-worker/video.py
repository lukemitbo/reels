import random
import os
import json
from glob import glob
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip, TextClip
from moviepy import vfx, afx
from datetime import datetime
from typing import Optional
def get_run_id() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")

def ease_out_cubic(x: float) -> float:
    return 1 - (1 - x) ** 3

def get_speaker_at_time(speaker_timings: list[tuple[str, float, float]], time: float) -> Optional[str]:
    """
    Determine which speaker is speaking at a given time.
    Returns the speaker name if found, None otherwise.
    """
    for speaker, start, end in speaker_timings:
        if start <= time < end:
            return speaker
    return None

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

def add_landing_effect(clip, landing_dur=0.25, base_y='center'):
    """
    Adds a zoom-in + fade-in effect at the start of the clip.
    - No vertical movement.
    - Scale goes from 0.9 -> 1.0 over `landing_dur`.
    """

    # 1) Fix the position (no time-based movement)
    animated = clip.with_position(('center', base_y))

    # 2) Animate scale (zoom) over the first `landing_dur` seconds
    def scale_fn(t):
        # t is local to the clip (0 at clip.start)
        if t < 0:
            return 0.75
        if t > landing_dur:
            return 1.0
        alpha = ease_out_cubic(t / landing_dur)  # 0 -> 1 smoothly
        return 0.75 + 0.25 * alpha  # zoom from 75% to 100%

    animated = animated.with_effects([vfx.Resize(lambda t: scale_fn(t))])

    # 3) Fade in over the same time
    #animated = animated.with_effects([vfx.FadeIn(landing_dur)])

    return animated


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
    font_path: Optional[str] = None,
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
    if word_alignments:
        video_width = 1080
        video_height = 1920

        # Caption styling
        font_size = 90
        font_color = 'yellow'
        stroke_color = 'black'
        stroke_width = 2

        # Set default font path if not provided
        if font_path is None:
            font_path = "/app/fonts/SuperMalibu-Wp77v.ttf"

        text_clips_with_timing = []
        text_width = 960

        def create_text_clip(chunk_words, start_time, end_time):
            """Helper function to create a text clip from words, ensuring single line."""
            if not chunk_words:
                return None
            
            chunk_text = " ".join(chunk_words).upper()
            
            # If single word, shrink font until it fits
            if len(chunk_words) == 1:
                adjusted_font_size = font_size
                while adjusted_font_size >= 20:
                    if not _check_text_wraps(chunk_text, font_path,
                                             adjusted_font_size, text_width,
                                             stroke_width, 'center'):
                        break  # Fits on one line
                    adjusted_font_size -= 15
                adjusted_font_size = max(adjusted_font_size, 20)
            else:
                # Multiple words - use default font size
                adjusted_font_size = font_size
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
            txt_clip = TextClip(
                text=chunk_text,
                font=font_path,
                duration=end_time - start_time,
                color=font_color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                method='caption',
                font_size=adjusted_font_size,
                size=(text_width, 1800),  # Single line, auto height
                text_align='center'
            )
            
            txt_clip = txt_clip.with_position(('center', 'center'))
            txt_clip = add_landing_effect(txt_clip, 0.15)
            return txt_clip

        # Group words into chunks, checking for wrapping after each word
        current_chunk_words = []
        chunk_start_time = None
        chunk_end_time = None
        current_chunk_speaker = None

        for word, start_time, end_time in word_alignments:
            # Determine which speaker is speaking for this word
            word_speaker = None
            if speaker_timings:
                word_speaker = get_speaker_at_time(speaker_timings, start_time)
            
            # Check if speaker changed
            speaker_changed = False
            if current_chunk_words:
                if current_chunk_speaker is not None and word_speaker != current_chunk_speaker:
                    speaker_changed = True
                elif current_chunk_speaker is None and word_speaker is not None:
                    speaker_changed = True
            
            # If speaker changed, finalize current chunk first
            if speaker_changed:
                if current_chunk_words:
                    txt_clip = create_text_clip(current_chunk_words, chunk_start_time, chunk_end_time)
                    if txt_clip:
                        text_clips_with_timing.append((txt_clip, chunk_start_time))
                # Start new chunk
                current_chunk_words = []
                chunk_start_time = start_time
                chunk_end_time = end_time
                current_chunk_speaker = word_speaker
            
            # Initialize chunk if empty
            if not current_chunk_words:
                chunk_start_time = start_time
                chunk_end_time = end_time
                current_chunk_speaker = word_speaker
            
            # Test if adding this word causes wrapping
            test_words = current_chunk_words + [word]
            test_text = " ".join(test_words).upper()
            
            # Check if adding this word causes wrapping
            wraps = _check_text_wraps(test_text, font_path, font_size, text_width, stroke_width, 'center')
            
            if wraps and current_chunk_words:
                # Adding this word causes wrapping, so finalize current chunk without this word
                txt_clip = create_text_clip(current_chunk_words, chunk_start_time, chunk_end_time)
                if txt_clip:
                    text_clips_with_timing.append((txt_clip, chunk_start_time))
                
                # Start new chunk with this word
                current_chunk_words = [word]
                chunk_start_time = start_time
                chunk_end_time = end_time
                current_chunk_speaker = word_speaker
            else:
                # Word fits, add it to current chunk
                current_chunk_words.append(word)
                chunk_end_time = end_time
        
        # Create clip for remaining chunk if any
        if current_chunk_words:
            txt_clip = create_text_clip(current_chunk_words, chunk_start_time, chunk_end_time)
            if txt_clip:
                text_clips_with_timing.append((txt_clip, chunk_start_time))

        # Apply start_time to text clips
        text_clips = [
            clip.with_start(start_time - 0.1)
            for clip, start_time in text_clips_with_timing
        ]

    # Composite all clips together based on what we have
    if word_alignments:
        # Composite base + PNG overlays (if any) + text clips
        final = CompositeVideoClip([base_clip] + overlay_clips + text_clips)
    elif speaker_timings and pngs_folder:
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
    # Get the script directory and construct paths relative to reels root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    reels_root = os.path.dirname(script_dir)  # Go up from python-worker to reels
    
    # Load speaker timings
    speaker_timings_path = os.path.join(reels_root, "data", "out", "20251120233319_speaker_timings.json")
    with open(speaker_timings_path, 'r') as f:
        speaker_timings_data = json.load(f)
    speaker_timings = [(item["speaker"], item["start"], item["end"]) for item in speaker_timings_data]
    
    # Load word alignments
    word_alignments_path = os.path.join(reels_root, "data", "out", "20251120233319_word_alignments.json")
    with open(word_alignments_path, 'r') as f:
        word_alignments_data = json.load(f)
    word_alignments = [(item["word"], item["start"], item["end"]) for item in word_alignments_data]
    
    # Paths
    dialogue_wav_path = os.path.join(reels_root, "data", "out", "20251120233319.wav")
    bg_folder = os.path.join(script_dir, "background-videos")
    out_path = os.path.join(script_dir, "final-videos", f"final-{get_run_id()}.mp4")
    pngs_folder = os.path.join(script_dir, "pngs")
    font_path = os.path.join(script_dir, "fonts", "SuperMalibu-Wp77v.ttf")
    assemble_video(
        dialogue_wav_path=dialogue_wav_path,
        bg_folder=bg_folder,
        out_path=out_path,
        speaker_timings=speaker_timings,
        pngs_folder=pngs_folder,
        word_alignments=word_alignments,
        font_path=font_path,
    )
