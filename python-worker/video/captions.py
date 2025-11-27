"""
Caption chunking and rendering logic.
"""
from moviepy import TextClip
from typing import List, Optional
from .utils import get_speaker_at_time
from .title import check_text_wraps
from .effects import add_landing_effect


class CaptionChunk:
    """Represents a chunk of words to be displayed as a caption."""
    def __init__(
        self,
        words: List[str],
        start_time: float,
        end_time: float,
        speaker: Optional[str] = None
    ):
        self.words = words
        self.start_time = start_time
        self.end_time = end_time
        self.speaker = speaker


def chunk_words(
    word_alignments: list[tuple[str, float, float]],
    speaker_timings: list[tuple[str, float, float]],
    font_path: str,
    font_size: int,
    text_width: int,
    stroke_width: int
) -> List[CaptionChunk]:
    """
    Group words into chunks based on wrapping and speaker changes.
    
    Args:
        word_alignments: List of (word, start_time, end_time) tuples
        speaker_timings: List of (speaker, start_time, end_time) tuples
        font_path: Path to font file
        font_size: Font size in pixels
        text_width: Maximum text width
        stroke_width: Stroke width for text
        
    Returns:
        List of CaptionChunk objects
    """
    chunks = []
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
                chunks.append(CaptionChunk(
                    current_chunk_words,
                    chunk_start_time,
                    chunk_end_time,
                    current_chunk_speaker
                ))
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
        wraps = check_text_wraps(
            test_text, font_path, font_size, text_width, stroke_width, 'center'
        )
        
        if wraps and current_chunk_words:
            # Adding this word causes wrapping, so finalize current chunk without this word
            chunks.append(CaptionChunk(
                current_chunk_words,
                chunk_start_time,
                chunk_end_time,
                current_chunk_speaker
            ))
            
            # Start new chunk with this word
            current_chunk_words = [word]
            chunk_start_time = start_time
            chunk_end_time = end_time
            current_chunk_speaker = word_speaker
        else:
            # Word fits, add it to current chunk
            current_chunk_words.append(word)
            chunk_end_time = end_time
    
    # Create chunk for remaining words if any
    if current_chunk_words:
        chunks.append(CaptionChunk(
            current_chunk_words,
            chunk_start_time,
            chunk_end_time,
            current_chunk_speaker
        ))
    
    return chunks


def create_caption_clip(
    chunk: CaptionChunk,
    font_path: str,
    font_size: int = 90,
    font_color: str = 'yellow',
    stroke_color: str = 'black',
    stroke_width: int = 2,
    text_width: int = 960
) -> TextClip:
    """
    Create a text clip from a caption chunk.
    
    Args:
        chunk: CaptionChunk to render
        font_path: Path to font file
        font_size: Default font size
        font_color: Text color
        stroke_color: Stroke color
        stroke_width: Stroke width
        text_width: Maximum text width
        
    Returns:
        TextClip configured for caption display
    """
    if not chunk.words:
        return None
    
    chunk_text = " ".join(chunk.words).upper()
    
    # If single word, shrink font until it fits
    if len(chunk.words) == 1:
        adjusted_font_size = font_size
        while adjusted_font_size >= 20:
            if not check_text_wraps(
                chunk_text, font_path, adjusted_font_size, text_width,
                stroke_width, 'center'
            ):
                break  # Fits on one line
            adjusted_font_size -= 15
        adjusted_font_size = max(adjusted_font_size, 20)
    else:
        # Multiple words - use default font size
        adjusted_font_size = font_size

    txt_clip = TextClip(
        text=chunk_text,
        font=font_path,
        duration=chunk.end_time - chunk.start_time,
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


def create_caption_clips(
    word_alignments: list[tuple[str, float, float]],
    speaker_timings: list[tuple[str, float, float]],
    font_path: str,
    font_size: int = 90,
    font_color: str = 'yellow',
    stroke_color: str = 'black',
    stroke_width: int = 2,
    text_width: int = 960,
    start_offset: float = -0.1
) -> List[TextClip]:
    """
    Create all caption clips from word alignments.
    
    Args:
        word_alignments: List of (word, start_time, end_time) tuples
        speaker_timings: List of (speaker, start_time, end_time) tuples
        font_path: Path to font file
        font_size: Font size in pixels
        font_color: Text color
        stroke_color: Stroke color
        stroke_width: Stroke width
        text_width: Maximum text width
        start_offset: Offset to apply to start times (default -0.1)
        
    Returns:
        List of TextClip objects for captions
    """
    # Chunk words based on wrapping and speaker changes
    chunks = chunk_words(
        word_alignments, speaker_timings, font_path,
        font_size, text_width, stroke_width
    )
    
    # Create clips from chunks
    text_clips_with_timing = []
    for chunk in chunks:
        txt_clip = create_caption_clip(
            chunk, font_path, font_size, font_color,
            stroke_color, stroke_width, text_width
        )
        if txt_clip:
            text_clips_with_timing.append((txt_clip, chunk.start_time))
    
    # Apply start_time offset to text clips
    text_clips = [
        clip.with_start(start_time + start_offset)
        for clip, start_time in text_clips_with_timing
    ]
    
    return text_clips

