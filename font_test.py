#!/usr/bin/env python3
"""
Test Japanese font rendering
"""

from PIL import Image, ImageDraw, ImageFont
import os

def find_japanese_fonts():
    """Find all available Japanese fonts"""
    print("🔍 Searching for Japanese fonts...")
    
    font_paths = [
        # macOS fonts
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/Hiragino Mincho ProN.otf",
        "/Library/Fonts/Arial Unicode MS.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        
        # Linux fonts
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        "/usr/share/fonts/truetype/fonts-japanese-mincho.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        
        # Windows fonts
        "/Windows/Fonts/msgothic.ttc",
        "/Windows/Fonts/msmincho.ttc",
        "/Windows/Fonts/meiryo.ttc",
        "/Windows/Fonts/arial.ttf",
        
        # Ubuntu/Debian specific
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf",
        "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf",
    ]
    
    found_fonts = []
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                # Test if font can be loaded
                test_font = ImageFont.truetype(font_path, 20)
                found_fonts.append(font_path)
                print(f"✅ Found: {font_path}")
            except Exception as e:
                print(f"❌ Failed to load: {font_path} - {e}")
    
    return found_fonts

def test_font_rendering(font_path=None):
    """Test rendering Japanese text with a specific font"""
    test_text = "今日は空が晴れて"
    
    print(f"\n🎨 Testing font rendering with: {font_path or 'default font'}")
    
    # Create image
    img = Image.new('RGB', (400, 200), 'white')
    draw = ImageDraw.Draw(img)
    
    try:
        if font_path and os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 48)
        else:
            font = ImageFont.load_default()
        
        # Draw Japanese text
        draw.text((20, 50), test_text, font=font, fill='black')
        
        # Draw English text for comparison
        draw.text((20, 120), "English test", font=font, fill='black')
        
        # Save test image
        output_name = "font_test.png"
        img.save(output_name)
        print(f"✅ Test image saved: {output_name}")
        print(f"   Check if Japanese characters are visible (not squares)")
        
        return True
        
    except Exception as e:
        print(f"❌ Font rendering failed: {e}")
        return False

def install_japanese_font():
    """Install a Japanese font"""
    print("\n📥 Installing Japanese font...")
    
    try:
        import urllib.request
        
        # Create fonts directory
        font_dir = os.path.expanduser("~/.local/share/fonts")
        os.makedirs(font_dir, exist_ok=True)
        
        # Download Noto Sans CJK JP
        font_url = "https://github.com/googlefonts/noto-cjk/releases/download/Sans2.004/02_NotoSansCJK-Regular.ttc"
        font_path = os.path.join(font_dir, "NotoSansCJK-Regular.ttc")
        
        if os.path.exists(font_path):
            print(f"✅ Font already exists: {font_path}")
            return font_path
        
        print("📥 Downloading Noto Sans CJK (this may take a moment)...")
        urllib.request.urlretrieve(font_url, font_path)
        
        # Update font cache on Linux
        try:
            import subprocess
            subprocess.run(['fc-cache', '-f'], check=False, capture_output=True)
            print("🔄 Updated font cache")
        except:
            pass
        
        print(f"✅ Downloaded font to: {font_path}")
        return font_path
        
    except Exception as e:
        print(f"❌ Font download failed: {e}")
        
        # Try alternative smaller font
        try:
            font_url = "https://fonts.gstatic.com/ea/notosansjapanese/v6/NotoSansJP-Regular.otf"
            font_path = os.path.join(font_dir, "NotoSansJP-Regular.otf")
            
            if not os.path.exists(font_path):
                print("📥 Downloading alternative font...")
                urllib.request.urlretrieve(font_url, font_path)
                print(f"✅ Downloaded alternative font: {font_path}")
                return font_path
            
        except Exception as e2:
            print(f"❌ Alternative font download failed: {e2}")
        
        return None

def main():
    """Main function"""
    print("🧪 Japanese Font Test\n")
    
    # Find existing fonts
    found_fonts = find_japanese_fonts()
    
    if found_fonts:
        print(f"\n✅ Found {len(found_fonts)} Japanese font(s)")
        # Test with the first found font
        test_font_rendering(found_fonts[0])
    else:
        print("\n❌ No Japanese fonts found")
        
        # Test with default font first
        print("Testing with default font:")
        test_font_rendering()
        
        # Try to install a font
        font_path = install_japanese_font()
        if font_path:
            print("\nTesting with downloaded font:")
            test_font_rendering(font_path)
    
    print("\n📋 Summary:")
    print("- Check font_test.png to see if Japanese characters render correctly")
    print("- If you see squares, the font doesn't support Japanese")
    print("- If you see Japanese characters, the font is working!")
    
    if found_fonts:
        print(f"\n📂 Available Japanese fonts:")
        for font in found_fonts[:3]:  # Show first 3
            print(f"   {font}")

if __name__ == "__main__":
    main()
