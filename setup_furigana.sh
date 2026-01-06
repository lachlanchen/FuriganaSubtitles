#!/bin/bash

echo "🚀 Setting up Furigana Subtitle Burner"

# Install Python packages
echo "📦 Installing Python packages..."
pip install opencv-python Pillow "numpy>=1.21.0,<2.0.0"

# Try to install fugashi and unidic (most accurate)
echo "🎌 Installing Japanese text processing libraries..."
pip install fugashi unidic

# Download unidic data
echo "📚 Downloading unidic dictionary data..."
python -c "import unidic; unidic.download()" 2>/dev/null || echo "⚠️  unidic download failed, will try pykakasi fallback"

# Install pykakasi as fallback
echo "🔄 Installing pykakasi as fallback..."
pip install pykakasi

# Test the installation
echo "🧪 Testing the installation..."
python test_furigana.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "📖 Usage:"
echo "  1. Test furigana generation: python test_furigana.py"
echo "  2. Process all videos: python process_furigana_videos.py"
echo "  3. Process single video: python process_furigana_videos.py video.mp4 subtitle.srt output.mp4"
echo ""
echo "📁 Your current video structure:"
ls -la video_*/
