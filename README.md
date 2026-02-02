# 🎬 Clip Generator

Convert Twitch VODs and YouTube videos into viral short-form videos (9:16) with auto-generated subtitles.

## ✨ Features

- **Auto-download** Twitch VODs and YouTube videos via URL
- **AI-powered** highlight detection using Whisper transcription
- **Smart clipping** based on:
  - High-energy phrases ("OMG", "Let's go!", etc.)
  - Exclamation intensity
  - Chat reaction gaps
  - Laughter detection
- **Auto-subtitles** burned into video
- **Vertical format** (1080x1920) ready for TikTok/Reels/Shorts
- **Batch processing** - generates multiple clips per VOD

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Clone/navigate to project
cd projects/twitch-clip-generator

# Install requirements
pip install -r requirements.txt

# Install ffmpeg (system dependency)
# Ubuntu/Debian:
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg

# Windows:
# Download from https://ffmpeg.org/download.html
```

### 2. Run the Tool

```bash
# Twitch VOD
python clip_generator.py "https://www.twitch.tv/videos/123456789"

# YouTube video
python clip_generator.py "https://www.youtube.com/watch?v=AbCdEfGhIjK"

# Custom settings
python clip_generator.py "https://www.twitch.tv/videos/123456789" \
    --num-clips 3 \
    --min-duration 20 \
    --max-duration 45 \
    --output ./my_clips
```

## 📋 Usage Examples

### Generate 5 clips (default)
```bash
python clip_generator.py "https://www.twitch.tv/videos/123456789"
```

### Generate shorter, punchier clips
```bash
python clip_generator.py "URL" \
    --min-duration 10 \
    --max-duration 25 \
    --num-clips 8
```

### Process with Twitch API (for better metadata)
```bash
python clip_generator.py "URL" \
    --client-id YOUR_CLIENT_ID \
    --client-secret YOUR_CLIENT_SECRET
```

## 🎯 How It Works

1. **Download** - Uses yt-dlp to grab the VOD
2. **Transcribe** - Whisper AI converts speech to text with timestamps
3. **Analyze** - Finds high-energy moments:
   - Exclamations ("!" heavy)
   - Energy words ("OMG", "Let's go", "Pog", etc.)
   - Laughter detection
   - Reaction gaps
4. **Clip** - Extracts best moments, extends to meet duration requirements
5. **Format** - Converts to 9:16 vertical with centered video + black bars
6. **Subtitle** - Burns subtitles directly into video

## 📁 Output Structure

```
clips/
├── clip_20260202_143022_1.mp4    # Video file
├── clip_20260202_143022_1.json   # Metadata (timestamps, transcript)
├── clip_20260202_143022_2.mp4
├── clip_20260202_143022_2.json
└── ...
```

## ⚙️ Advanced Configuration

Edit the script to customize:

### Energy Words
```python
energy_words = ["wow", "omg", "insane", "crazy", "no way", "let's go", 
                "pog", "holy", "what", "unbelievable", "clutch"]
```

### Visual Style
```python
# In create_vertical_video(), modify vf_filter:
vf_filter = (
    "scale=1080:1920:force_original_aspect_ratio=decrease,"
    "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"  # Change 'black' to color
)
```

### Subtitle Style
```python
# Font, size, colors in the subtitles filter:
"FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,"
"OutlineColour=&H00000000,OutlineThickness=2"
```

## 🔄 Live Stream Support

**Current status:** VOD processing only

**For live streams**, you have options:

### Option 1: Record then Process
Use a tool like `streamlink` to record live streams, then process the file:

```bash
# Record live stream
streamlink --record stream.mp4 "https://twitch.tv/channel" best

# Process recording
python clip_generator.py "file://stream.mp4"
```

### Option 2: Real-time (Future)
Live clipping requires continuous audio buffering and real-time transcription - 
more complex. This tool is designed for post-stream editing.

## 🎨 Customization Ideas

### Add Background Gameplay
Instead of black bars, use blurred/zoomed gameplay as background:

```python
# Modify ffmpeg filter in create_vertical_video()
vf_filter = (
    "split[original][copy];"
    "[copy]scale=1080:1920:force_original_aspect_ratio=increase,blur=10[bg];"
    "[original]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
    "[bg][fg]overlay=(W-w)/2:(H-h)/2"
)
```

### Add B-roll/Chat Overlay
Extract chat comments during clip moments and overlay them.

### Different Aspect Ratios
Change from 9:16 to 4:5 (Instagram) or 1:1 (square):

```python
# 4:5 ratio (1080x1350)
vf_filter = "scale=1080:1350:force_original_aspect_ratio=decrease,pad=1080:1350:(ow-iw)/2:(oh-ih)/2:black"
```

## 🐛 Troubleshooting

### "ffmpeg not found"
Install ffmpeg on your system (not via pip)

### "No clip-worthy moments found"
- Stream might be too quiet/monotone
- Try lowering energy threshold in code
- Check that audio track exists

### "Transcription failed"
- Video might have no/corrupted audio
- Try shorter video sample
- Check disk space

### Subtitles not showing
- Ensure video has clear speech
- Check that subtitle file is created in temp

## 📝 Todo / Future Features

- [ ] Live stream real-time processing
- [ ] Chat reaction integration (high chat activity = clip moment)
- [ ] Auto-thumbnail generation
- [ ] Caption styling templates (meme text, etc.)
- [ ] Batch VOD processing from playlist
- [ ] Face detection (center on speaker)
- [ ] Music/sound effect detection
- [ ] Export directly to TikTok/YouTube APIs

## 📜 License

MIT - Use for your content!

## 🙏 Credits

- [OpenAI Whisper](https://github.com/openai/whisper) for transcription
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for downloading
- FFmpeg for video magic
