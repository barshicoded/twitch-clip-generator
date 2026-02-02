#!/usr/bin/env python3
"""
Twitch Clip Generator
Converts Twitch VODs/Livestreams into short-form videos with subtitles
"""

import os
import sys
import json
import time
import argparse
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import whisper
import numpy as np

# Optional imports with fallbacks
try:
    from twitchAPI.twitch import Twitch
    from twitchAPI.helper import first
    HAS_TWITCH_API = True
except ImportError:
    HAS_TWITCH_API = False
    print("Warning: twitchAPI not installed. VOD features limited.")

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("Warning: OpenCV not installed. Visual processing limited.")


class TwitchClipGenerator:
    """Main class for generating clips from Twitch streams"""
    
    def __init__(self, client_id: Optional[str] = None, 
                 client_secret: Optional[str] = None,
                 output_dir: str = "./clips"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize Whisper for transcription (tiny = less memory)
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model("tiny")
        
        # Initialize Twitch API if credentials provided
        self.twitch = None
        if HAS_TWITCH_API and client_id and client_secret:
            self._init_twitch(client_id, client_secret)
    
    def _init_twitch(self, client_id: str, client_secret: str):
        """Initialize Twitch API connection"""
        try:
            self.twitch = Twitch(client_id, client_secret)
            self.twitch.authenticate_app([])
            print("✓ Twitch API connected")
        except Exception as e:
            print(f"✗ Twitch API failed: {e}")
            self.twitch = None
    
    def download_vod(self, vod_url: str, output_path: str) -> bool:
        """Download video from Twitch or YouTube using yt-dlp"""
        platform = "YouTube" if "youtube.com" in vod_url or "youtu.be" in vod_url else "Twitch"
        print(f"Downloading {platform} video: {vod_url}")
        
        cmd = [
            "yt-dlp",
            "--format", "bestvideo[height<=1080]+bestaudio/best",
            "--output", output_path,
            "--merge-output-format", "mp4",
            vod_url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"✓ Downloaded to {output_path}")
                return True
            else:
                print(f"✗ Download failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print("✗ Download timed out")
            return False
        except Exception as e:
            print(f"✗ Download error: {e}")
            return False
    
    def transcribe_audio(self, video_path: str) -> Dict:
        """Extract and transcribe audio from video"""
        print("Transcribing audio...")
        
        # Extract audio to temp file
        audio_path = video_path.replace('.mp4', '_audio.wav')
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-y",
            audio_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                audio_path,
                language="en",
                verbose=False
            )
            
            # Clean up audio file
            os.remove(audio_path)
            
            print(f"✓ Transcribed {len(result['segments'])} segments")
            return result
            
        except Exception as e:
            print(f"✗ Transcription failed: {e}")
            return {"segments": [], "text": ""}
    
    def find_viral_moments(self, transcript: Dict, 
                          min_duration: int = 15,
                          max_duration: int = 60) -> List[Dict]:
        """Identify viral/clip-worthy moments from transcript"""
        print("Analyzing for viral moments...")
        
        segments = transcript.get("segments", [])
        if not segments:
            return []
        
        moments = []
        
        # Method 1: High-energy phrases (exclamations, caps, etc.)
        energy_words = ["wow", "omg", "insane", "crazy", "no way", "let's go", 
                       "pog", "holy", "what", "unbelievable", "clutch"]
        
        for i, seg in enumerate(segments):
            text = seg.get("text", "").lower()
            
            # Check for energy indicators
            energy_score = sum(1 for word in energy_words if word in text)
            
            # Check for exclamations
            if "!" in seg.get("text", ""):
                energy_score += 2
            
            # Check for laughter
            if any(laugh in text for laugh in ["haha", "lol", "lmao"]):
                energy_score += 1
            
            if energy_score >= 2:
                moments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "energy_score": energy_score,
                    "reason": "high_energy"
                })
        
        # Method 2: Find gaps in speech (reaction moments)
        for i in range(len(segments) - 1):
            current_end = segments[i]["end"]
            next_start = segments[i + 1]["start"]
            gap = next_start - current_end
            
            # 1-3 second gaps often indicate reactions
            if 1.0 <= gap <= 3.0:
                moments.append({
                    "start": current_end,
                    "end": next_start,
                    "text": "[reaction moment]",
                    "energy_score": 1,
                    "reason": "reaction_gap"
                })
        
        # Method 3: Combine nearby moments into clips
        clips = []
        used_indices = set()
        
        for moment in sorted(moments, key=lambda x: x["energy_score"], reverse=True):
            if len(clips) >= 5:  # Max 5 clips
                break
            
            start = moment["start"]
            end = moment["end"]
            
            # Extend duration to meet minimum
            if end - start < min_duration:
                # Try to extend equally on both sides
                extend = (min_duration - (end - start)) / 2
                start = max(0, start - extend)
                end = min(segments[-1]["end"] if segments else end + 30, end + extend)
            
            # Cap at max duration
            if end - start > max_duration:
                end = start + max_duration
            
            # Check for overlap with existing clips
            overlap = False
            for clip in clips:
                if not (end < clip["start"] or start > clip["end"]):
                    overlap = True
                    break
            
            if not overlap:
                # Get full transcript for this clip
                clip_segments = [
                    s for s in segments 
                    if start <= s["start"] <= end or start <= s["end"] <= end
                ]
                clip_text = " ".join([s["text"] for s in clip_segments])
                
                clips.append({
                    "start": start,
                    "end": end,
                    "duration": end - start,
                    "text": clip_text.strip(),
                    "segments": clip_segments,
                    "reason": moment["reason"]
                })
        
        print(f"✓ Found {len(clips)} clip-worthy moments")
        return clips
    
    def create_vertical_video(self, input_path: str, output_path: str,
                              start_time: float, end_time: float,
                              subtitle_segments: List[Dict],
                              add_subtitles: bool = True) -> bool:
        """Create 9:16 vertical video clip with subtitles"""
        
        duration = end_time - start_time
        print(f"Creating clip ({duration:.1f}s): {start_time:.1f} - {end_time:.1f}")
        
        # Extract subtitle text file for ffmpeg
        if add_subtitles and subtitle_segments:
            subtitle_path = output_path.replace('.mp4', '.srt')
            self._create_srt(subtitle_segments, subtitle_path, start_time)
        else:
            subtitle_path = None
        
        # Build ffmpeg command for vertical video
        # Strategy: Scale to 1080 width, crop/pad to 9:16 (1080x1920)
        vf_filter = (
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"
        )
        
        if subtitle_path and add_subtitles:
            # Add subtitle burn-in
            vf_filter += (
                ",subtitles='" + subtitle_path.replace(':', '\\:') + "':"
                "force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,"
                "OutlineColour=&H00000000,OutlineThickness=2,Alignment=2'"
            )
        
        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", input_path,
            "-vf", vf_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            print(f"✓ Created clip: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Clip creation failed: {e}")
            return False
        finally:
            # Clean up subtitle file
            if subtitle_path and os.path.exists(subtitle_path):
                os.remove(subtitle_path)
    
    def _create_srt(self, segments: List[Dict], output_path: str, 
                   offset: float = 0):
        """Create SRT subtitle file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(segments, 1):
                start = seg["start"] - offset
                end = seg["end"] - offset
                text = seg["text"].strip()
                
                if start < 0 or not text:
                    continue
                
                f.write(f"{i}\n")
                f.write(f"{self._format_time(start)} --> {self._format_time(end)}\n")
                f.write(f"{text}\n\n")
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to SRT time format"""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int(td.microseconds / 1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def process_vod(self, vod_url: str, 
                   clip_duration: Tuple[int, int] = (15, 60),
                   max_clips: int = 5) -> List[str]:
        """Full pipeline: download VOD, analyze, create clips"""
        
        print(f"\n{'='*50}")
        print(f"Processing: {vod_url}")
        print(f"{'='*50}\n")
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download VOD
            video_path = os.path.join(temp_dir, "vod.mp4")
            if not self.download_vod(vod_url, video_path):
                return []
            
            # Get video info
            duration = self._get_video_duration(video_path)
            print(f"Video duration: {duration:.1f}s ({duration/60:.1f}m)")
            
            # For long videos, analyze a sample (first 30 min)
            if duration > 1800:
                print("Video long - analyzing first 30 minutes...")
                sample_path = self._extract_sample(video_path, temp_dir, 1800)
                if sample_path:
                    transcript = self.transcribe_audio(sample_path)
                else:
                    transcript = self.transcribe_audio(video_path)
            else:
                transcript = self.transcribe_audio(video_path)
            
            if not transcript.get("segments"):
                print("✗ No transcription available")
                return []
            
            # Find viral moments
            clips = self.find_viral_moments(
                transcript,
                min_duration=clip_duration[0],
                max_duration=clip_duration[1]
            )
            
            if not clips:
                print("✗ No clip-worthy moments found")
                return []
            
            # Create output clips
            output_files = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for i, clip in enumerate(clips[:max_clips], 1):
                output_path = self.output_dir / f"clip_{timestamp}_{i}.mp4"
                
                success = self.create_vertical_video(
                    video_path,
                    str(output_path),
                    clip["start"],
                    clip["end"],
                    clip["segments"],
                    add_subtitles=True
                )
                
                if success:
                    output_files.append(str(output_path))
                    
                    # Save metadata
                    meta_path = output_path.with_suffix('.json')
                    with open(meta_path, 'w') as f:
                        json.dump({
                            "source": vod_url,
                            "start_time": clip["start"],
                            "end_time": clip["end"],
                            "duration": clip["duration"],
                            "transcript": clip["text"],
                            "reason": clip["reason"]
                        }, f, indent=2)
            
            return output_files
    
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds"""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except:
            return 0
    
    def _extract_sample(self, video_path: str, temp_dir: str, 
                       duration: int) -> Optional[str]:
        """Extract sample from beginning of video"""
        sample_path = os.path.join(temp_dir, "sample.mp4")
        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-t", str(duration),
            "-c", "copy",
            sample_path
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return sample_path
        except:
            return None


def main():
    parser = argparse.ArgumentParser(
        description="Generate short-form clips from Twitch VODs"
    )
    parser.add_argument("url", help="Twitch VOD URL")
    parser.add_argument("-o", "--output", default="./clips", 
                       help="Output directory")
    parser.add_argument("-n", "--num-clips", type=int, default=5,
                       help="Maximum clips to generate")
    parser.add_argument("--min-duration", type=int, default=15,
                       help="Minimum clip duration (seconds)")
    parser.add_argument("--max-duration", type=int, default=60,
                       help="Maximum clip duration (seconds)")
    parser.add_argument("--client-id", help="Twitch API Client ID")
    parser.add_argument("--client-secret", help="Twitch API Client Secret")
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = TwitchClipGenerator(
        client_id=args.client_id,
        client_secret=args.client_secret,
        output_dir=args.output
    )
    
    # Process VOD
    clips = generator.process_vod(
        args.url,
        clip_duration=(args.min_duration, args.max_duration),
        max_clips=args.num_clips
    )
    
    if clips:
        print(f"\n{'='*50}")
        print(f"✓ Generated {len(clips)} clips:")
        for clip in clips:
            print(f"  - {clip}")
        print(f"{'='*50}")
    else:
        print("\n✗ No clips generated")
        sys.exit(1)


if __name__ == "__main__":
    main()
