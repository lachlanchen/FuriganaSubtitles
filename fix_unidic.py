#!/usr/bin/env python3
"""
Fix unidic installation for fugashi/MeCab
"""

import os
import subprocess
import sys

def fix_unidic():
    """Fix unidic installation"""
    print("🔧 Fixing unidic installation...")
    
    try:
        # Try to download unidic data properly
        print("📚 Downloading unidic dictionary...")
        result = subprocess.run([
            sys.executable, "-c", 
            "import unidic; unidic.download()"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Unidic download successful!")
        else:
            print(f"⚠️  Unidic download had issues: {result.stderr}")
            
        # Try alternative download method
        print("🔄 Trying alternative unidic download...")
        result2 = subprocess.run([
            sys.executable, "-c", 
            "import unidic; unidic.download_version('3.1.1')"
        ], capture_output=True, text=True, timeout=300)
        
        if result2.returncode == 0:
            print("✅ Alternative unidic download successful!")
        
    except subprocess.TimeoutExpired:
        print("⏰ Download timed out, but may have partially completed")
    except Exception as e:
        print(f"❌ Error during unidic download: {e}")
    
    # Test fugashi installation
    print("\n🧪 Testing fugashi...")
    try:
        import fugashi
        tagger = fugashi.Tagger()
        test_result = tagger("今日は")
        print("✅ Fugashi is working!")
        for word in test_result:
            print(f"  {word.surface} -> {word.feature}")
        return True
    except Exception as e:
        print(f"❌ Fugashi still not working: {e}")
        return False

def test_pykakasi():
    """Test pykakasi installation"""
    print("\n🧪 Testing pykakasi...")
    try:
        import pykakasi
        
        # Try old API
        try:
            kks = pykakasi.kakasi()
            kks.setMode('J', 'H')  # Kanji to Hiragana
            conv = kks.getConverter()
            result = conv.do("今日は")
            print(f"✅ Pykakasi (old API) working: 今日は -> {result}")
            return True
        except:
            pass
        
        # Try new API
        try:
            kks = pykakasi.kakasi()
            result = kks.convert("今日は")
            print(f"✅ Pykakasi (new API) working: 今日は -> {result}")
            return True
        except Exception as e:
            print(f"❌ Pykakasi not working: {e}")
            return False
            
    except ImportError:
        print("❌ Pykakasi not installed")
        return False

if __name__ == "__main__":
    print("🛠️  Fixing Japanese text processing...")
    
    fugashi_works = fix_unidic()
    pykakasi_works = test_pykakasi()
    
    if fugashi_works:
        print("\n✅ Fugashi is ready to use!")
    elif pykakasi_works:
        print("\n✅ Pykakasi is ready to use as fallback!")
    else:
        print("\n⚠️  Neither fugashi nor pykakasi is working properly")
        print("Installing simple fallback...")
        # We'll use the fallback method in the main code
    
    print("\n🚀 Ready to test!")
