#!/usr/bin/env python3
"""
Test furigana generation and rendering
"""

from furigana_subtitle_burner import FuriganaGenerator, FuriganaRenderer, SRTParser
from PIL import Image
import os

def test_furigana_generation():
    """Test furigana generation with sample text"""
    generator = FuriganaGenerator()
    
    # Test samples from your SRT
    test_texts = [
        "おはようございます。",
        "今日は空が晴れていて、",
        "朝は気持ちをリセットするのにちょうどいい時間ですね。",
        "あなたの朝も穏やかでありますように"
    ]
    
    print("=== Testing Furigana Generation ===")
    for text in test_texts:
        print(f"\nOriginal: {text}")
        furigana_chars = generator.generate_furigana(text)
        
        result = ""
        for char_info in furigana_chars:
            if char_info.furigana:
                result += f"{char_info.char}({char_info.furigana})"
            else:
                result += char_info.char
        print(f"Furigana: {result}")

def test_rendering():
    """Test rendering furigana to image"""
    generator = FuriganaGenerator()
    renderer = FuriganaRenderer(main_font_size=48, furigana_font_size=24)
    
    test_text = "今日は空が晴れていて、空気が気持ちいいです。"
    
    print(f"\n=== Testing Rendering ===")
    print(f"Text: {test_text}")
    
    # Generate furigana
    furigana_chars = generator.generate_furigana(test_text)
    
    # Measure text
    width, height = renderer.measure_text_with_furigana(furigana_chars)
    print(f"Measured size: {width}x{height}")
    
    # Add padding
    img_width = width + 100
    img_height = height + 100
    
    # Render
    img = renderer.render_text_with_furigana(
        furigana_chars, img_width, img_height
    )
    
    # Save test image
    output_path = "test_furigana_output.png"
    img.save(output_path)
    print(f"Test image saved to: {output_path}")

def test_srt_parsing(srt_path: str):
    """Test SRT parsing"""
    if not os.path.exists(srt_path):
        print(f"SRT file not found: {srt_path}")
        return
    
    print(f"\n=== Testing SRT Parsing: {srt_path} ===")
    
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    segments = SRTParser.parse_srt(content)
    print(f"Found {len(segments)} segments")
    
    # Show first few segments
    for i, segment in enumerate(segments[:3]):
        print(f"\nSegment {i+1}:")
        print(f"  Time: {segment.start_time:.3f} -> {segment.end_time:.3f}")
        print(f"  Text: {segment.text}")

def main():
    """Run all tests"""
    print("🧪 Testing Furigana Subtitle System")
    
    # Test furigana generation
    test_furigana_generation()
    
    # Test rendering
    test_rendering()
    
    # Test SRT parsing with actual file - search for any SRT files
    import glob
    srt_files = glob.glob("video_*/*.srt")
    
    if srt_files:
        test_srt_parsing(srt_files[0])
    else:
        print("\n=== No SRT files found ===")
        print("Place video directories with SRT files in the current directory to test parsing.")
    
    print("\n✅ Tests completed! Check test_furigana_output.png to see rendered furigana.")

if __name__ == "__main__":
    main()
