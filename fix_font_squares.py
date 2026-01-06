#!/usr/bin/env python3
"""
Quick fix for square boxes instead of Japanese text
"""

import os
import subprocess
import sys

def quick_font_fix():
    """Quick fix for Japanese font issues"""
    print("🔧 Quick fix for Japanese font squares\n")
    
    # First, check what we have
    print("1️⃣ Checking current font situation...")
    
    from PIL import Image, ImageDraw, ImageFont
    
    # Test with default font
    try:
        img = Image.new('RGB', (200, 100), 'white')
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((10, 10), "今日は", font=font, fill='black')
        img.save("test_default.png")
        print("✅ Default font test saved as test_default.png")
    except Exception as e:
        print(f"❌ Default font test failed: {e}")
    
    # Check if we're on Linux and can install fonts easily
    if os.path.exists("/etc/debian_version"):
        print("\n2️⃣ Installing Japanese fonts (Debian/Ubuntu)...")
        try:
            result = subprocess.run([
                "sudo", "apt-get", "install", "-y", 
                "fonts-noto-cjk", "fonts-takao-gothic"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✅ Japanese fonts installed successfully!")
                
                # Update font cache
                subprocess.run(["fc-cache", "-f"], capture_output=True)
                print("✅ Font cache updated")
                
            else:
                print("⚠️  Package installation failed, trying manual download...")
                manual_download()
                
        except subprocess.TimeoutExpired:
            print("⏰ Installation timed out, trying manual download...")
            manual_download()
        except Exception as e:
            print(f"⚠️  Package installation failed: {e}")
            manual_download()
    
    elif os.path.exists("/etc/redhat-release"):
        print("\n2️⃣ Installing Japanese fonts (RedHat/CentOS/Fedora)...")
        try:
            # Try dnf first, then yum
            for cmd in [["dnf", "install", "-y"], ["yum", "install", "-y"]]:
                try:
                    result = subprocess.run(cmd + ["google-noto-cjk-fonts"], 
                                          capture_output=True, text=True, timeout=120)
                    if result.returncode == 0:
                        print("✅ Japanese fonts installed successfully!")
                        break
                except:
                    continue
            else:
                manual_download()
        except Exception as e:
            print(f"⚠️  Package installation failed: {e}")
            manual_download()
    
    else:
        print("\n2️⃣ Manual font download...")
        manual_download()
    
    # Test again
    print("\n3️⃣ Testing fonts after installation...")
    test_fonts_after_install()

def manual_download():
    """Manually download Japanese fonts"""
    print("📥 Downloading Japanese font manually...")
    
    import urllib.request
    
    # Create user fonts directory
    font_dir = os.path.expanduser("~/.local/share/fonts")
    os.makedirs(font_dir, exist_ok=True)
    
    # Download a smaller Japanese font
    font_url = "https://fonts.gstatic.com/ea/notosansjapanese/v6/NotoSansJP-Regular.otf"
    font_path = os.path.join(font_dir, "NotoSansJP-Regular.otf")
    
    try:
        if not os.path.exists(font_path):
            print(f"📥 Downloading to {font_path}...")
            urllib.request.urlretrieve(font_url, font_path)
        
        print(f"✅ Font available at: {font_path}")
        
        # Update font cache
        try:
            subprocess.run(["fc-cache", "-f", font_dir], capture_output=True)
            print("✅ Font cache updated")
        except:
            print("⚠️  Could not update font cache")
        
        return font_path
        
    except Exception as e:
        print(f"❌ Manual download failed: {e}")
        return None

def test_fonts_after_install():
    """Test font rendering after installation"""
    from PIL import Image, ImageDraw, ImageFont
    
    # Find Japanese fonts
    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf",
        os.path.expanduser("~/.local/share/fonts/NotoSansJP-Regular.otf"),
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
    ]
    
    working_font = None
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, 48)
                
                # Test rendering
                img = Image.new('RGB', (300, 100), 'white')
                draw = ImageDraw.Draw(img)
                draw.text((10, 10), "今日は空が晴れ", font=font, fill='black')
                
                test_file = f"test_{os.path.basename(font_path)}.png"
                img.save(test_file)
                
                print(f"✅ Font works: {font_path}")
                print(f"   Test image: {test_file}")
                working_font = font_path
                break
                
            except Exception as e:
                print(f"❌ Font failed: {font_path} - {e}")
    
    if working_font:
        print(f"\n🎉 SUCCESS! Working Japanese font found: {working_font}")
        print("\n📝 Your furigana subtitle burner should now work!")
        print("   Run: python standalone_furigana_burner.py")
    else:
        print("\n❌ No working Japanese fonts found")
        print("\n🔧 Manual steps:")
        print("1. Install fonts manually: sudo apt install fonts-noto-cjk")
        print("2. Or download from: https://fonts.google.com/noto/specimen/Noto+Sans+JP")
        print("3. Place in ~/.local/share/fonts/")
        print("4. Run: fc-cache -f")

def main():
    """Main function"""
    print("🆘 Font Squares Fix Tool")
    print("=" * 50)
    
    quick_font_fix()
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print("- Check the test_*.png files")
    print("- If you see Japanese characters (not squares), fonts are working!")
    print("- If still squares, try rebooting and running again")

if __name__ == "__main__":
    main()
