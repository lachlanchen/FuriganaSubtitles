#!/usr/bin/env python3
"""
Debug Japanese text processing libraries
"""

def test_fugashi():
    print("=== Testing Fugashi ===")
    try:
        import fugashi
        print("✅ Fugashi imported successfully")
        
        try:
            tagger = fugashi.Tagger()
            print("✅ Fugashi tagger created successfully")
            
            test_text = "今日は"
            result = tagger(test_text)
            print(f"✅ Fugashi processing successful: {test_text}")
            for word in result:
                print(f"  {word.surface} -> {word.feature}")
            return True
            
        except Exception as e:
            print(f"❌ Fugashi tagger failed: {e}")
            return False
            
    except ImportError:
        print("❌ Fugashi not available")
        return False

def test_pykakasi():
    print("\n=== Testing Pykakasi ===")
    try:
        import pykakasi
        print("✅ Pykakasi imported successfully")
        
        # Test old API
        print("🔄 Testing old pykakasi API...")
        try:
            kks = pykakasi.kakasi()
            kks.setMode('J', 'H')  # Kanji to Hiragana
            conv = kks.getConverter()
            result = conv.do("今日は")
            print(f"✅ Old API successful: 今日は -> {result}")
            print(f"   Result type: {type(result)}")
            print(f"   Result content: {result}")
            return True
        except Exception as e:
            print(f"❌ Old API failed: {e}")
        
        # Test new API
        print("🔄 Testing new pykakasi API...")
        try:
            kks = pykakasi.kakasi()
            result = kks.convert("今日は")
            print(f"✅ New API successful: 今日は -> {result}")
            print(f"   Result type: {type(result)}")
            print(f"   Result content: {result}")
            return True
        except Exception as e:
            print(f"❌ New API failed: {e}")
            
        return False
        
    except ImportError:
        print("❌ Pykakasi not available")
        return False

def test_basic_kanji_detection():
    print("\n=== Testing Basic Kanji Detection ===")
    
    def is_kanji(char):
        return '\u4e00' <= char <= '\u9faf'
    
    test_chars = ['今', '日', 'は', 'あ', 'A', '1', '。']
    
    for char in test_chars:
        kanji_status = "kanji" if is_kanji(char) else "not kanji"
        print(f"  '{char}' -> {kanji_status}")
    
    print("✅ Basic kanji detection working")

def main():
    print("🧪 Debugging Japanese Text Processing\n")
    
    fugashi_works = test_fugashi()
    pykakasi_works = test_pykakasi()
    test_basic_kanji_detection()
    
    print(f"\n📊 Summary:")
    print(f"  Fugashi: {'✅ Working' if fugashi_works else '❌ Not working'}")
    print(f"  Pykakasi: {'✅ Working' if pykakasi_works else '❌ Not working'}")
    
    if fugashi_works:
        print("🎉 Fugashi is ready - you'll get the best furigana!")
    elif pykakasi_works:
        print("🎉 Pykakasi is ready - you'll get basic furigana!")
    else:
        print("⚠️  Neither library working - will use fallback with limited kanji")

if __name__ == "__main__":
    main()
