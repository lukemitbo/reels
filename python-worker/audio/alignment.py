"""
Word-level alignment using WhisperX.
"""
import whisperx
import torchaudio
import logging

logger = logging.getLogger(__name__)


def align_with_whisperx(
    audio_path: str, 
    transcript: str,
    language: str = "en",
    device: str = "cpu"
) -> list[tuple[str, float, float]]:
    """
    Use WhisperX forced alignment to get word-level timestamps.
    
    Args:
        audio_path: Path to audio file
        transcript: Full transcript text
        language: Language code (default "en")
        device: Device to run alignment on (default "cpu")
        
    Returns:
        List of (word, start_time, end_time) tuples
    """
    # Load audio
    audio = whisperx.load_audio(audio_path)

    # Get audio duration
    info = torchaudio.info(audio_path)
    duration = info.num_frames / float(info.sample_rate)

    # Create a single segment spanning the entire audio duration
    segments = [{
        "start": 0.0,
        "end": duration,
        "text": transcript
    }]

    # Load alignment model
    align_model, metadata = whisperx.load_align_model(
        language_code=language, device=device
    )

    # Run alignment
    aligned = whisperx.align(
        segments,
        align_model,
        metadata,
        audio,
        device,
        return_char_alignments=False
    )

    # Extract words from all segments and convert to tuple format
    word_alignments = []
    segments = aligned["segments"]
    for i, segment in enumerate(segments):
        words = segment["words"]
        for j, w in enumerate(words):
            # Determine start
            if "start" in w:
                start = w["start"]
            else:
                if j > 0 and "end" in words[j-1]:
                    start = words[j-1]["end"] + 0.01
                else:
                    start = None  # fallback

            # Determine end
            if "end" in w:
                end = w["end"]
            else:
                if j < len(words) - 1 and "start" in words[j+1]:
                    end = words[j+1]["start"]
                else:
                    end = None  # fallback            

            if start and end:
                word_alignments.append((w["word"], start, end))

    logger.info(
        f"WhisperX generated {len(word_alignments)} word alignments "
        f"from {len(aligned['segments'])} segments"
    )

    return word_alignments

