"""
Title text rendering and formatting.
"""
from moviepy import TextClip


def check_text_wraps(
    text: str,
    font_path: str,
    font_size: int,
    width: int,
    stroke_width: int,
    text_align: str
) -> bool:
    """
    Check if text wraps to multiple lines when rendered with given parameters.
    
    Args:
        text: Text to check
        font_path: Path to font file
        font_size: Font size in pixels
        width: Text width constraint
        stroke_width: Stroke width for text
        text_align: Text alignment ('center', 'left', 'right')
        
    Returns:
        True if text wraps, False if it fits on one line.
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


def format_title_text(
    title: str,
    font_path: str,
    font_size: int,
    text_width: int,
    stroke_width: int
) -> str:
    """
    Format title text with word-boundary wrapping.
    
    Args:
        title: Title text to format
        font_path: Path to font file
        font_size: Font size in pixels
        text_width: Maximum text width
        stroke_width: Stroke width for text
        
    Returns:
        Formatted title text with newlines at word boundaries
    """
    title_words = title.upper().split()
    built_text = ""
    
    for word in title_words:
        # Try adding this word
        test_text = built_text + (" " if built_text else "") + word
        
        # Create temporary clip to check if it wraps
        temp_clip = TextClip(
            text=test_text,
            font=font_path,
            font_size=font_size,
            method='caption',
            size=(text_width, None),
            text_align='center',
            stroke_width=stroke_width
        )
        
        # Check if text wraps and where the newline occurs
        rendered_text = temp_clip.text
        temp_clip.close()
        
        # If text wraps, check if newline is in the middle of the current word
        if "\n" in rendered_text:
            # Split into lines
            lines = rendered_text.split("\n")
            last_line = lines[-1].strip()
            
            # Check if the word appears complete at the end of the last line
            if last_line.endswith(word):
                # Word fits completely at the end of new line, add it normally
                built_text = test_text
            else:
                # Word is likely split - put newline before it to force word boundary
                if built_text and not built_text.endswith("\n"):
                    built_text = built_text.rstrip(" ")
                built_text = built_text + ("\n" if not built_text.endswith("\n") else "") + word
        else:
            # No wrapping, add word normally
            built_text = test_text
    
    return built_text


def create_title_clip(
    title: str,
    font_path: str,
    audio_duration: float,
    font_size: int = 70,
    font_color: str = 'white',
    stroke_color: str = 'black',
    stroke_width: int = 3,
    text_width: int = 1000,
    max_duration: float = 15.0
) -> TextClip:
    """
    Create a title text clip for the video.
    
    Args:
        title: Title text
        font_path: Path to font file
        audio_duration: Duration of audio in seconds
        font_size: Font size in pixels
        font_color: Text color
        stroke_color: Stroke color
        stroke_width: Stroke width
        text_width: Maximum text width
        max_duration: Maximum duration to show title
        
    Returns:
        TextClip configured for title display
    """
    title_duration = min(max_duration, audio_duration)
    
    # Format title with word-boundary wrapping
    formatted_title = format_title_text(
        title, font_path, font_size, text_width, stroke_width
    )
    
    # Create title text clip
    title_clip = TextClip(
        text=formatted_title,
        font=font_path,
        duration=title_duration,
        color=font_color,
        stroke_color=stroke_color,
        stroke_width=stroke_width,
        method='caption',
        font_size=font_size,
        size=(text_width, 750),
        text_align='center'
    )
    
    # Center horizontally, position near top
    title_clip = title_clip.with_position(('center', 'top'))
    
    return title_clip

