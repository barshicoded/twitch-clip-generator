"""
Configuration for Twitch Clip Generator
Edit these settings to customize your clips
"""

# Video Settings
VIDEO_SETTINGS = {
    "resolution": (1080, 1920),  # Width, Height (9:16)
    "fps": 60,
    "video_codec": "libx264",
    "audio_codec": "aac",
    "video_quality": 23,  # CRF value (lower = higher quality, larger file)
    "audio_bitrate": "128k",
}

# Clip Detection
CLIP_SETTINGS = {
    "min_duration": 15,  # Minimum clip length (seconds)
    "max_duration": 60,  # Maximum clip length (seconds)
    "max_clips": 5,      # Maximum clips per VOD
    "sample_duration": 1800,  # For long VODs, analyze first X seconds
}

# Energy Detection (what makes a moment "clip-worthy")
ENERGY_WORDS = [
    "wow", "omg", "oh my god", "holy", "what", "no way",
    "insane", "crazy", "wild", "nuts", "bonkers",
    "let's go", "pog", "poggers", "clutch", "sick",
    "unbelievable", "incredible", "amazing", "awesome",
    "destroyed", "wrecked", "demolished", "owned",
    "lmao", "haha", "lol", "dead", "dying",
    "wait", "hold up", "stop", "pause",
    "perfect", "clean", "smooth", "nasty"
]

# Laughter detection
LAUGHTER_PATTERNS = ["haha", "hehe", "lol", "lmao", "lmfao", "rofl"]

# Exclamation weight (how much "!" counts toward energy)
EXCLAMATION_WEIGHT = 2  # Points per exclamation mark

# Whisper Settings
WHISPER_SETTINGS = {
    "model": "base",  # tiny, base, small, medium, large (larger = more accurate, slower)
    "language": "en",  # Set to None for auto-detect
    "device": "cpu",   # "cuda" if you have GPU
}

# Subtitle Appearance
SUBTITLE_STYLE = {
    "font": "Arial",
    "size": 24,
    "color": "&H00FFFFFF",  # White (BBGGRR format)
    "outline_color": "&H00000000",  # Black
    "outline_thickness": 2,
    "alignment": 2,  # 2 = bottom center
    "margin_v": 50,  # Vertical margin from bottom
}

# Background (for vertical video bars)
BACKGROUND = {
    "color": "black",  # Can be hex color like "#1a1a1a" or "blur"
    "blur_intensity": 10,  # If using blur background
}

# Output Naming
OUTPUT_TEMPLATE = "clip_{timestamp}_{index}.mp4"
METADATA_TEMPLATE = "clip_{timestamp}_{index}.json"

# Processing
PROCESSING = {
    "temp_cleanup": True,  # Delete temp files after processing
    "keep_audio": False,   # Keep extracted audio files
    "parallel": False,     # Process multiple clips in parallel (experimental)
}
