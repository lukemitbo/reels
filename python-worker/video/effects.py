"""
Video effects and animations.
"""
from moviepy import VideoClip
from moviepy import vfx
from .utils import ease_out_cubic


def add_landing_effect(
    clip: VideoClip,
    landing_dur: float = 0.25,
    base_y: str = 'center'
) -> VideoClip:
    """
    Adds a zoom-in + fade-in effect at the start of the clip.
    - No vertical movement.
    - Scale goes from 0.75 -> 1.0 over `landing_dur`.
    
    Args:
        clip: Video clip to animate
        landing_dur: Duration of landing animation in seconds
        base_y: Vertical position ('center', 'top', 'bottom', or pixel value)
        
    Returns:
        Animated clip with landing effect
    """
    # Fix the position (no time-based movement)
    animated = clip.with_position(('center', base_y))

    # Animate scale (zoom) over the first `landing_dur` seconds
    def scale_fn(t):
        # t is local to the clip (0 at clip.start)
        if t < 0:
            return 0.75
        if t > landing_dur:
            return 1.0
        alpha = ease_out_cubic(t / landing_dur)  # 0 -> 1 smoothly
        return 0.75 + 0.25 * alpha  # zoom from 75% to 100%

    animated = animated.with_effects([vfx.Resize(lambda t: scale_fn(t))])

    return animated

