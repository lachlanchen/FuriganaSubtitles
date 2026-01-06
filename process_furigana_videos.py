#!/usr/bin/env python3
"""
Process all videos in the furigana directory with furigana subtitles
"""

import os
import glob
from pathlib import Path
from furigana_subtitle_burner import FuriganaSubtitleBurner

def process_videos_in_directory(base_dir: str = "."):
    """Process all videos with their corresponding SRT files"""
    
    # Find all video directories
    video_dirs = [d for d in os.listdir(base_dir) 
                  if os.path.isdir(os.path.join(base_dir, d)) and d.startswith('video_')]
    
    if not video_dirs:
        print("No video directories found!")
        return
    
    print(f"Found {len(video_dirs)} video directories")
    
    # Create furigana burner
    burner = FuriganaSubtitleBurner(
        main_font_size=64,      # Larger for better visibility
        furigana_font_size=32   # Proportional furigana size
    )
    
    for video_dir in video_dirs:
        print(f"\n=== Processing {video_dir} ===")
        
        dir_path = os.path.join(base_dir, video_dir)
        
        # Find MP4 and SRT files
        mp4_files = glob.glob(os.path.join(dir_path, "*.MP4"))
        srt_files = glob.glob(os.path.join(dir_path, "*.srt"))
        
        if not mp4_files:
            print(f"No MP4 file found in {video_dir}")
            continue
        
        if not srt_files:
            print(f"No SRT file found in {video_dir}")
            continue
        
        video_file = mp4_files[0]
        srt_file = srt_files[0]
        
        # Create output filename
        output_file = os.path.join(dir_path, f"{video_dir}_furigana.mp4")
        
        print(f"Video: {video_file}")
        print(f"Subtitles: {srt_file}")
        print(f"Output: {output_file}")
        
        try:
            # Process the video
            burner.burn_subtitles(
                video_path=video_file,
                srt_path=srt_file,
                output_path=output_file,
                subtitle_position='bottom',
                margin=80  # More margin for better visibility
            )
            print(f"✅ Successfully processed {video_dir}")
            
        except Exception as e:
            print(f"❌ Error processing {video_dir}: {e}")
            continue
    
    print("\n🎉 All videos processed!")


def process_single_video(video_path: str, srt_path: str, output_path: str):
    """Process a single video file"""
    print(f"Processing single video: {video_path}")
    
    burner = FuriganaSubtitleBurner(
        main_font_size=64,
        furigana_font_size=32
    )
    
    try:
        burner.burn_subtitles(
            video_path=video_path,
            srt_path=srt_path,
            output_path=output_path,
            subtitle_position='bottom',
            margin=80
        )
        print(f"✅ Successfully created: {output_path}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # Process all videos in current directory
        process_videos_in_directory()
    elif len(sys.argv) == 4:
        # Process single video
        video_path, srt_path, output_path = sys.argv[1], sys.argv[2], sys.argv[3]
        process_single_video(video_path, srt_path, output_path)
    else:
        print("Usage:")
        print("  python process_furigana_videos.py                    # Process all videos in current dir")
        print("  python process_furigana_videos.py video.mp4 sub.srt output.mp4  # Process single video")
