#!/usr/bin/env python3
"""
Standalone Furigana Subtitle Burner
Burns Japanese subtitles with furigana onto video files
Complete single-file solution
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import re
import os
from dataclasses import dataclass
from typing import List, Tuple, Optional
import sys

# Try to import Japanese text processing libraries
try:
    import pykakasi
    KAKASI_AVAILABLE = True
except ImportError:
    KAKASI_AVAILABLE = False

try:
    import fugashi
    FUGASHI_AVAILABLE = True
except ImportError:
    FUGASHI_AVAILABLE = False


@dataclass
class SubtitleSegment:
    start_time: float
    end_time: float
    text: str


@dataclass
class FuriganaChar:
    char: str
    furigana: Optional[str]
    is_kanji: bool


class FuriganaGenerator:
    """Generate furigana for Japanese text"""
    
    def __init__(self):
        self.kakasi = None
        self.tagger = None
        
        # Try fugashi first
        if FUGASHI_AVAILABLE:
            try:
                self.tagger = fugashi.Tagger()
                print("✅ Using fugashi for furigana generation")
            except Exception as e:
                print(f"⚠️  Fugashi failed: {e}")
        
        # Try pykakasi as fallback
        if not self.tagger and KAKASI_AVAILABLE:
            try:
                kks = pykakasi.kakasi()
                kks.setMode('J', 'H')  # Kanji to Hiragana
                self.kakasi = kks.getConverter()
                print("✅ Using pykakasi for furigana generation")
            except Exception as e:
                print(f"⚠️  Pykakasi failed: {e}")
                try:
                    # Try new API
                    self.kakasi = pykakasi.kakasi()
                    print("✅ Using pykakasi (new API) for furigana generation")
                except Exception as e2:
                    print(f"⚠️  Pykakasi new API failed: {e2}")
        
        if not self.tagger and not self.kakasi:
            print("⚠️  Using fallback furigana generation (limited)")
    
    def generate_furigana(self, text: str) -> List[FuriganaChar]:
        """Generate furigana for Japanese text"""
        if self.tagger:
            return self._generate_with_fugashi(text)
        elif self.kakasi:
            return self._generate_with_kakasi(text)
        else:
            return self._generate_fallback(text)
    
    def _generate_with_fugashi(self, text: str) -> List[FuriganaChar]:
        """Generate furigana using fugashi"""
        result = []
        try:
            for word in self.tagger(text):
                if word.feature.reading and word.feature.reading != '*':
                    surface = word.surface
                    reading = self._katakana_to_hiragana(word.feature.reading)
                    
                    if len(surface) == 1 and self._is_kanji(surface):
                        result.append(FuriganaChar(surface, reading, True))
                    else:
                        distributed = self._distribute_furigana(surface, reading)
                        result.extend(distributed)
                else:
                    for char in word.surface:
                        result.append(FuriganaChar(char, None, self._is_kanji(char)))
        except Exception as e:
            print(f"Fugashi error: {e}")
            return self._generate_fallback(text)
        
        return result
    
    def _generate_with_kakasi(self, text: str) -> List[FuriganaChar]:
        """Generate furigana using pykakasi"""
        result = []
        try:
            if hasattr(self.kakasi, 'convert'):
                # New API
                conversion = self.kakasi.convert(text)
                if isinstance(conversion, list):
                    for item in conversion:
                        if isinstance(item, dict):
                            orig = item.get('orig', '')
                            hira = item.get('hira', item.get('hiragana', ''))
                            for char in orig:
                                is_kanji = self._is_kanji(char)
                                furigana = hira if is_kanji and hira != orig and len(orig) == 1 else None
                                result.append(FuriganaChar(char, furigana, is_kanji))
                        else:
                            for char in str(item):
                                result.append(FuriganaChar(char, None, self._is_kanji(char)))
                else:
                    # Handle string result
                    for char in text:
                        result.append(FuriganaChar(char, None, self._is_kanji(char)))
            
            elif hasattr(self.kakasi, 'do'):
                # Old API
                conversion = self.kakasi.do(text)
                if isinstance(conversion, str):
                    for i, char in enumerate(text):
                        is_kanji = self._is_kanji(char)
                        furigana = None
                        if is_kanji and i < len(conversion) and conversion[i] != char:
                            furigana = conversion[i]
                        result.append(FuriganaChar(char, furigana, is_kanji))
                else:
                    for char in text:
                        result.append(FuriganaChar(char, None, self._is_kanji(char)))
            
            else:
                # Manual processing
                for char in text:
                    is_kanji = self._is_kanji(char)
                    furigana = None
                    if is_kanji:
                        try:
                            char_result = self.kakasi.convert(char) if hasattr(self.kakasi, 'convert') else self.kakasi.do(char)
                            if isinstance(char_result, str) and char_result != char:
                                furigana = char_result
                            elif isinstance(char_result, list) and len(char_result) > 0:
                                item = char_result[0]
                                if isinstance(item, dict):
                                    furigana = item.get('hira', item.get('hiragana', ''))
                                    if furigana == char:
                                        furigana = None
                        except:
                            pass
                    result.append(FuriganaChar(char, furigana, is_kanji))
        
        except Exception as e:
            print(f"Pykakasi error: {e}")
            return self._generate_fallback(text)
        
        return result
    
    def _generate_fallback(self, text: str) -> List[FuriganaChar]:
        """Fallback furigana generation with common kanji"""
        kanji_to_furigana = {
            # Common kanji from your subtitle
            '今': 'いま', '日': 'ひ', '空': 'そら', '気': 'き', '持': 'も',
            '晴': 'は', '朝': 'あさ', '時': 'じ', '間': 'かん', '静': 'しず',
            '心': 'こころ', '落': 'お', '着': 'つ', '深': 'ふか', '呼': 'こ',
            '吸': 'きゅう', '外': 'そと', '鳥': 'とり', '声': 'こえ', '聞': 'き',
            '温': 'あたた', '入': 'い', '笑': 'わら', '穏': 'おだ'
        }
        
        result = []
        for char in text:
            is_kanji = self._is_kanji(char)
            furigana = kanji_to_furigana.get(char) if is_kanji else None
            result.append(FuriganaChar(char, furigana, is_kanji))
        
        return result
    
    def _distribute_furigana(self, surface: str, reading: str) -> List[FuriganaChar]:
        """Distribute furigana across characters"""
        result = []
        kanji_chars = [i for i, c in enumerate(surface) if self._is_kanji(c)]
        
        if not kanji_chars:
            for char in surface:
                result.append(FuriganaChar(char, None, False))
            return result
        
        reading_per_kanji = len(reading) // len(kanji_chars) if kanji_chars else 0
        
        for i, char in enumerate(surface):
            is_kanji = self._is_kanji(char)
            furigana = None
            
            if is_kanji and i in kanji_chars:
                kanji_idx = kanji_chars.index(i)
                start_idx = kanji_idx * reading_per_kanji
                end_idx = start_idx + reading_per_kanji
                if kanji_idx == len(kanji_chars) - 1:
                    end_idx = len(reading)
                furigana = reading[start_idx:end_idx]
            
            result.append(FuriganaChar(char, furigana, is_kanji))
        
        return result
    
    def _is_kanji(self, char: str) -> bool:
        """Check if character is kanji"""
        return '\u4e00' <= char <= '\u9faf'
    
    def _katakana_to_hiragana(self, text: str) -> str:
        """Convert katakana to hiragana"""
        result = ""
        for char in text:
            if '\u30a1' <= char <= '\u30f6':
                result += chr(ord(char) - 0x60)
            else:
                result += char
        return result


class FuriganaRenderer:
    """Render text with furigana using PIL"""
    
    def __init__(self, main_font_size: int = 48, furigana_font_size: int = 24):
        self.main_font_size = main_font_size
        self.furigana_font_size = furigana_font_size
        self.main_font = self._load_font(main_font_size)
        self.furigana_font = self._load_font(furigana_font_size)
        self.line_spacing = 1.2
        self.furigana_spacing = 0.3
    
    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Load Japanese font with fallback"""
        font_paths = [
            "/System/Library/Fonts/Hiragino Sans GB.ttc",  # macOS
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",  # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "/Windows/Fonts/msgothic.ttc",  # Windows
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Linux Noto
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except Exception:
                continue
        
        try:
            return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()
    
    def measure_text_with_furigana(self, furigana_chars: List[FuriganaChar]) -> Tuple[int, int]:
        """Measure total size needed for text with furigana"""
        if not furigana_chars:
            return 0, 0
        
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        total_width = 0
        max_height = 0
        
        for char_info in furigana_chars:
            char_bbox = temp_draw.textbbox((0, 0), char_info.char, font=self.main_font)
            char_width = char_bbox[2] - char_bbox[0]
            char_height = char_bbox[3] - char_bbox[1]
            
            furigana_width = 0
            if char_info.furigana:
                furigana_bbox = temp_draw.textbbox((0, 0), char_info.furigana, font=self.furigana_font)
                furigana_width = furigana_bbox[2] - furigana_bbox[0]
            
            total_width += max(char_width, furigana_width)
            
            total_height = char_height
            if char_info.furigana:
                total_height += self.furigana_font_size + int(self.furigana_font_size * self.furigana_spacing)
            
            max_height = max(max_height, total_height)
        
        return total_width, max_height
    
    def render_text_with_furigana(self, furigana_chars: List[FuriganaChar], 
                                 width: int, height: int) -> Image.Image:
        """Render text with furigana"""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        text_width, text_height = self.measure_text_with_furigana(furigana_chars)
        start_x = (width - text_width) // 2
        start_y = (height - text_height) // 2
        current_x = start_x
        
        for char_info in furigana_chars:
            char_bbox = draw.textbbox((0, 0), char_info.char, font=self.main_font)
            char_width = char_bbox[2] - char_bbox[0]
            char_height = char_bbox[3] - char_bbox[1]
            
            furigana_width = 0
            if char_info.furigana:
                furigana_bbox = draw.textbbox((0, 0), char_info.furigana, font=self.furigana_font)
                furigana_width = furigana_bbox[2] - furigana_bbox[0]
            
            column_width = max(char_width, furigana_width)
            char_x = current_x + (column_width - char_width) // 2
            char_y = start_y + (self.furigana_font_size + int(self.furigana_font_size * self.furigana_spacing))
            
            # Draw stroke
            stroke_width = 2
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx*dx + dy*dy <= stroke_width*stroke_width:
                        draw.text((char_x + dx, char_y + dy), char_info.char, 
                                font=self.main_font, fill=(0, 0, 0))
            
            # Draw main character
            draw.text((char_x, char_y), char_info.char, font=self.main_font, fill=(255, 255, 255))
            
            # Draw furigana
            if char_info.furigana:
                furigana_x = current_x + (column_width - furigana_width) // 2
                furigana_y = start_y
                
                # Draw furigana stroke
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        if dx*dx + dy*dy <= stroke_width*stroke_width:
                            draw.text((furigana_x + dx, furigana_y + dy), char_info.furigana,
                                    font=self.furigana_font, fill=(0, 0, 0))
                
                draw.text((furigana_x, furigana_y), char_info.furigana, 
                         font=self.furigana_font, fill=(255, 255, 255))
            
            current_x += column_width
        
        return img


class SRTParser:
    """Parse SRT subtitle files"""
    
    @staticmethod
    def parse_srt(srt_content: str) -> List[SubtitleSegment]:
        """Parse SRT content"""
        segments = []
        blocks = re.split(r'\n\s*\n', srt_content.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            timestamp_line = lines[1]
            match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', 
                           timestamp_line)
            
            if not match:
                continue
            
            start_time = (int(match.group(1)) * 3600 + 
                         int(match.group(2)) * 60 + 
                         int(match.group(3)) + 
                         int(match.group(4)) / 1000)
            
            end_time = (int(match.group(5)) * 3600 + 
                       int(match.group(6)) * 60 + 
                       int(match.group(7)) + 
                       int(match.group(8)) / 1000)
            
            text = ' '.join(lines[2:])
            segments.append(SubtitleSegment(start_time, end_time, text))
        
        return segments


class FuriganaSubtitleBurner:
    """Main class for burning furigana subtitles"""
    
    def __init__(self, main_font_size: int = 64, furigana_font_size: int = 32):
        self.furigana_generator = FuriganaGenerator()
        self.renderer = FuriganaRenderer(main_font_size, furigana_font_size)
        
    def burn_subtitles(self, video_path: str, srt_path: str, output_path: str,
                      subtitle_position: str = 'bottom', margin: int = 80):
        """Burn furigana subtitles onto video"""
        
        print(f"🎬 Processing: {video_path}")
        print(f"📄 Subtitles: {srt_path}")
        print(f"💾 Output: {output_path}")
        
        # Read SRT file
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        segments = SRTParser.parse_srt(srt_content)
        print(f"📝 Loaded {len(segments)} subtitle segments")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"🎥 Video: {width}x{height}, {fps:.2f} fps, {total_frames} frames")
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                current_time = frame_count / fps
                
                # Find active subtitle
                active_subtitle = None
                for segment in segments:
                    if segment.start_time <= current_time <= segment.end_time:
                        active_subtitle = segment
                        break
                
                # Add subtitle if present
                if active_subtitle:
                    frame = self._add_subtitle_to_frame(
                        frame, active_subtitle.text, 
                        subtitle_position, margin, width, height
                    )
                
                out.write(frame)
                frame_count += 1
                
                if frame_count % 100 == 0:
                    progress = (frame_count / total_frames) * 100
                    print(f"⏳ Progress: {progress:.1f}% ({frame_count}/{total_frames})")
        
        finally:
            cap.release()
            out.release()
            print(f"✅ Video saved to: {output_path}")
    
    def _add_subtitle_to_frame(self, frame: np.ndarray, text: str, 
                              position: str, margin: int, 
                              frame_width: int, frame_height: int) -> np.ndarray:
        """Add furigana subtitle to video frame"""
        
        # Generate furigana
        furigana_chars = self.furigana_generator.generate_furigana(text)
        
        # Calculate subtitle area size
        text_width, text_height = self.renderer.measure_text_with_furigana(furigana_chars)
        
        padding = 20
        subtitle_width = text_width + 2 * padding
        subtitle_height = text_height + 2 * padding
        
        # Create subtitle image
        subtitle_img = self.renderer.render_text_with_furigana(
            furigana_chars, subtitle_width, subtitle_height
        )
        
        # Convert PIL to OpenCV
        subtitle_cv = cv2.cvtColor(np.array(subtitle_img), cv2.COLOR_RGBA2BGRA)
        
        # Calculate position
        if position == 'bottom':
            x = (frame_width - subtitle_width) // 2
            y = frame_height - subtitle_height - margin
        elif position == 'top':
            x = (frame_width - subtitle_width) // 2
            y = margin
        else:  # center
            x = (frame_width - subtitle_width) // 2
            y = (frame_height - subtitle_height) // 2
        
        # Ensure subtitle fits
        x = max(0, min(x, frame_width - subtitle_width))
        y = max(0, min(y, frame_height - subtitle_height))
        
        # Alpha blending
        alpha = subtitle_cv[:, :, 3] / 255.0
        alpha = np.stack([alpha] * 3, axis=2)
        
        overlay_region = frame[y:y+subtitle_height, x:x+subtitle_width]
        subtitle_rgb = subtitle_cv[:, :, :3]
        
        blended = overlay_region * (1 - alpha) + subtitle_rgb * alpha
        frame[y:y+subtitle_height, x:x+subtitle_width] = blended.astype(np.uint8)
        
        return frame


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Burn furigana subtitles onto video')
    parser.add_argument('video', help='Input video file')
    parser.add_argument('srt', help='Input SRT subtitle file')
    parser.add_argument('output', help='Output video file')
    parser.add_argument('--main-font-size', type=int, default=64, help='Main text font size')
    parser.add_argument('--furigana-font-size', type=int, default=32, help='Furigana font size')
    parser.add_argument('--position', choices=['top', 'bottom', 'center'], default='bottom',
                       help='Subtitle position')
    parser.add_argument('--margin', type=int, default=80, help='Margin from edge')
    
    if len(sys.argv) == 1:
        # Auto-detect mode for current directory
        print("🔍 Auto-detecting video and subtitle files...")
        
        import glob
        mp4_files = glob.glob("*.MP4") + glob.glob("*.mp4")
        srt_files = glob.glob("*.srt")
        
        if mp4_files and srt_files:
            video_file = mp4_files[0]
            srt_file = srt_files[0]
            base_name = os.path.splitext(video_file)[0]
            output_file = f"{base_name}_furigana.mp4"
            
            print(f"📹 Found: {video_file}")
            print(f"📄 Found: {srt_file}")
            print(f"💾 Output: {output_file}")
            
            burner = FuriganaSubtitleBurner()
            burner.burn_subtitles(video_file, srt_file, output_file)
            
        else:
            print("❌ No video or subtitle files found in current directory")
            print("\n📖 Usage:")
            print("  python standalone_furigana_burner.py video.mp4 subtitle.srt output.mp4")
            print("  or place video.mp4 and subtitle.srt in same directory and run without arguments")
        
        return
    
    args = parser.parse_args()
    
    # Create burner and process
    burner = FuriganaSubtitleBurner(args.main_font_size, args.furigana_font_size)
    burner.burn_subtitles(args.video, args.srt, args.output, args.position, args.margin)


if __name__ == "__main__":
    main()
