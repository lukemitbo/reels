"""
Main video assembly logic.
"""
from moviepy import AudioFileClip, CompositeVideoClip
from .background import prepare_background_clip
from .title import create_title_clip
from .overlays import create_overlay_clips
from .captions import create_caption_clips


def assemble_video(
    dialogue_wav_path: str,
    bg_folder: str,
    out_path: str,
    speaker_timings: list[tuple[str, float, float]],
    pngs_folder: str,
    word_alignments: list[tuple[str, float, float]],
    font_path: str,
    title: str,
    fps: int = 30,
    bitrate: str = "6M",
    video_width: int = 1080,
    video_height: int = 1920,
):
    """
    Assemble a complete video with background, title, overlays, and captions.
    
    Args:
        dialogue_wav_path: Path to dialogue audio file
        bg_folder: Folder containing background videos
        out_path: Output path for final video
        speaker_timings: List of (speaker, start_time, end_time) tuples
        pngs_folder: Folder containing PNG overlay images
        word_alignments: List of (word, start_time, end_time) tuples
        font_path: Path to font file
        title: Title text to display
        fps: Frames per second (default 30)
        bitrate: Video bitrate (default "6M")
        video_width: Video width in pixels (default 1080)
        video_height: Video height in pixels (default 1920)
    """
    # Load audio
    voice = AudioFileClip(dialogue_wav_path)
    audio_duration = voice.duration

    # Prepare background clip
    bg, bg_v = prepare_background_clip(
        bg_folder, audio_duration, video_width, video_height
    )
    
    # Create base clip with audio
    base_clip = bg_v.subclipped(0, audio_duration).with_audio(voice)

    # Create title clip
    title_clip = create_title_clip(
        title=title,
        font_path=font_path,
        audio_duration=audio_duration
    )

    # Create overlay clips
    overlay_clips = create_overlay_clips(
        speaker_timings=speaker_timings,
        pngs_folder=pngs_folder,
        video_width=video_width,
        video_height=video_height
    )

    # Create caption clips
    text_clips = create_caption_clips(
        word_alignments=word_alignments,
        speaker_timings=speaker_timings,
        font_path=font_path
    )

    # Composite all clips together
    final = CompositeVideoClip(
        [base_clip, title_clip] + overlay_clips + text_clips
    )

    # Write MP4 (H.264 + AAC)
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
    title_clip.close()
    for clip in overlay_clips:
        clip.close()
    for clip in text_clips:
        clip.close()

