#!/usr/bin/env python3
"""
Batch process multiple Twitch VODs
"""

import sys
import json
from pathlib import Path
from clip_generator import TwitchClipGenerator


def process_vod_list(vod_file: str, output_dir: str = "./clips"):
    """Process multiple VODs from a JSON file"""
    
    # Load VOD list
    with open(vod_file, 'r') as f:
        vods = json.load(f)
    
    # Initialize generator
    generator = TwitchClipGenerator(output_dir=output_dir)
    
    all_clips = []
    
    for vod in vods:
        url = vod.get("url")
        name = vod.get("name", "unnamed")
        
        print(f"\n{'='*60}")
        print(f"Processing: {name}")
        print(f"URL: {url}")
        print(f"{'='*60}\n")
        
        try:
            clips = generator.process_vod(
                url,
                clip_duration=(vod.get("min_duration", 15), 
                              vod.get("max_duration", 60)),
                max_clips=vod.get("max_clips", 5)
            )
            
            all_clips.extend(clips)
            
        except Exception as e:
            print(f"Error processing {name}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"Batch complete! Generated {len(all_clips)} total clips")
    print(f"{'='*60}\n")
    
    return all_clips


if __name__ == "__main__":
    # Example usage:
    # python batch_process.py vods.json
    
    if len(sys.argv) < 2:
        print("Usage: python batch_process.py <vods.json>")
        print("\nvods.json format:")
        print(json.dumps([
            {
                "url": "https://www.twitch.tv/videos/123456",
                "name": "Stream 1",
                "min_duration": 15,
                "max_duration": 45,
                "max_clips": 3
            },
            {
                "url": "https://www.twitch.tv/videos/789012",
                "name": "Stream 2",
                "min_duration": 20,
                "max_duration": 60,
                "max_clips": 5
            }
        ], indent=2))
        sys.exit(1)
    
    vods_file = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "./clips"
    
    process_vod_list(vods_file, output)
