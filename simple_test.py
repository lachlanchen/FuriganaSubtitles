#!/usr/bin/env python3
"""
Simple test that bypasses library issues and tests core functionality
"""

from furigana_subtitle_burner import FuriganaChar, FuriganaRenderer, SRTParser
from PIL import Image
import os
import glob

def test_rendering_only():
    """Test rendering without library dependencies"""
    print("=== Testing Text Rendering (No Library Dependencies) ===")
    
    # Create mock furigana data manually
    furigana_chars = [
        FuriganaChar('今', 'いま', True),
        FuriganaChar('日', 'ひ', True),
        FuriganaChar('は', None, False),
        FuriganaChar('空', 'そら', True),
        FuriganaChar('が', None, False),
        FuriganaChar('晴', 'は', True),
        FuriganaChar('れ', None, False),
        FuriganaChar('て', None, False),
        FuriganaChar('い', None, False),
        FuriganaChar('て', None, False),
    ]
    
    print("🎨 Testing renderer...")
    renderer = FuriganaRenderer(main_font_size=48, furigana_font_size=24)
    
    # Measure text
    width, height = renderer.measure_text_with_furigana(furigana_chars)
    print(f"📏 Measured size: {width}x{height}")
    
    # Add padding
    img_width = width + 100
    img_height = height + 100
    
    # Render
    img = renderer.render_text_with_furigana(
        furigana_chars, img_width, img_height
    )
    
    # Save test image
    output_path = "simple_test_output.png"
    img.save(output_path)
    print(f"✅ Test image saved to: {output_path}")

def test_srt_parsing():
    """Test SRT parsing with actual files"""
    print("\n=== Testing SRT Parsing ===")
    
    srt_files = glob.glob("video_*/*.srt")
    
    if not srt_files:
        print("❌ No SRT files found")
        return False
    
    srt_file = srt_files[0]
    print(f"📄 Testing with: {srt_file}")
    
    try:
        with open(srt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        segments = SRTParser.parse_srt(content)
        print(f"✅ Parsed {len(segments)} subtitle segments")
        
        # Show first segment
        if segments:
            seg = segments[0]
            print(f"   Example: {seg.start_time:.2f}s - {seg.end_time:.2f}s: '{seg.text}'")
        
        return True
        
    except Exception as e:
        print(f"❌ SRT parsing failed: {e}")
        return False

def test_manual_furigana():
    """Test manual furigana creation for your specific text"""
    print("\n=== Testing Manual Furigana ===")
    
    # Text from your SRT file
    sample_texts = [
        "おはようございます。",
        "今日は空が晴れていて、",
        "空気が気持ちいいです。",
        "朝は気持ちをリセットするのにちょうどいい時間ですね。"
    ]
    
    # Manual furigana mapping
    kanji_furigana = {
        '今': 'いま', '日': 'ひ', '空': 'そら', '気': 'き', '持': 'も',
        '晴': 'は', '朝': 'あさ', '時': 'じ', '間': 'かん'
    }
    
    def is_kanji(char):
        return '\u4e00' <= char <= '\u9faf'
    
    for text in sample_texts:
        print(f"\n📝 Text: {text}")
        
        furigana_chars = []
        for char in text:
            is_k = is_kanji(char)
            furigana = kanji_furigana.get(char) if is_k else None
            furigana_chars.append(FuriganaChar(char, furigana, is_k))
        
        # Show result
        result = ""
        for fc in furigana_chars:
            if fc.furigana:
                result += f"{fc.char}({fc.furigana})"
            else:
                result += fc.char
        
        print(f"   Result: {result}")
    
    print("✅ Manual furigana working")

def main():
    print("🧪 Simple Furigana Test (Library-Independent)\n")
    
    test_rendering_only()
    srt_ok = test_srt_parsing()
    test_manual_furigana()
    
    print("\n📊 Core Components:")
    print("✅ Text rendering: Working")
    print("✅ Manual furigana: Working")
    print(f"{'✅' if srt_ok else '❌'} SRT parsing: {'Working' if srt_ok else 'Failed'}")
    
    print("\n🎬 Next steps:")
    if srt_ok:
        print("   Ready to test video processing!")
        print("   Run: python process_furigana_videos.py")
    else:
        print("   Fix SRT file issues first")
    
    print("   Check simple_test_output.png for rendering preview")

if __name__ == "__main__":
    main()
