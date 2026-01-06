#!/usr/bin/env python3
"""
Complete Furigana Subtitle Burner
Enhanced version with better furigana generation and error handling
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import re
import os
from dataclasses import dataclass
from typing import List, Tuple, Optional
import sys
import glob
import json

# Japanese text processing libraries
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


class EnhancedFuriganaGenerator:
    """Enhanced furigana generator with comprehensive kanji mapping"""
    
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
                # Try new API first
                self.kakasi = pykakasi.kakasi()
                print("✅ Using pykakasi (new API) for furigana generation")
            except Exception as e:
                print(f"⚠️  Pykakasi new API failed: {e}")
                # Try old API
                try:
                    kks = pykakasi.kakasi()
                    kks.setMode('J', 'H')  # Kanji to Hiragana
                    self.kakasi = kks.getConverter()
                    print("✅ Using pykakasi (old API) for furigana generation")
                except Exception as e2:
                    print(f"⚠️  Pykakasi old API failed: {e2}")
        
        if not self.tagger and not self.kakasi:
            print("⚠️  Using enhanced fallback furigana generation")
        
        # Enhanced kanji dictionary based on your subtitle content
        self.kanji_readings = self._load_kanji_readings()
    
    def _load_kanji_readings(self) -> dict:
        """Load comprehensive kanji to reading mappings"""
        return {
            # From your subtitle content
            '今': 'いま', '日': 'ひ', '空': 'そら', '気': 'き', '持': 'も',
            '晴': 'は', '朝': 'あさ', '時': 'じ', '間': 'かん', '静': 'しず',
            '心': 'こころ', '落': 'お', '着': 'つ', '深': 'ふか', '呼': 'こ',
            '吸': 'きゅう', '外': 'そと', '鳥': 'とり', '声': 'こえ', '聞': 'き',
            '温': 'あたた', '入': 'い', '笑': 'わら', '穏': 'おだ',
            
            # Additional common kanji
            '人': 'ひと', '大': 'おお', '小': 'ちい', '中': 'なか', '出': 'で',
            '来': 'き', '行': 'い', '見': 'み', '話': 'はな', '食': 'た',
            '飲': 'の', '読': 'よ', '書': 'か', '買': 'か', '売': 'う',
            '作': 'つく', '使': 'つか', '思': 'おも', '言': 'い', '考': 'かんが',
            '知': 'し', '分': 'わ', '手': 'て', '足': 'あし', '目': 'め',
            '耳': 'みみ', '口': 'くち', '頭': 'あたま', '体': 'からだ', '水': 'みず',
            '火': 'ひ', '土': 'つち', '木': 'き', '金': 'きん', '石': 'いし',
            '山': 'やま', '川': 'かわ', '海': 'うみ', '田': 'た', '花': 'はな',
            '雨': 'あめ', '雪': 'ゆき', '風': 'かぜ', '雲': 'くも', '星': 'ほし',
            '月': 'つき', '太': 'たい', '陽': 'よう', '光': 'ひかり', '電': 'でん',
            '車': 'くるま', '電': 'でん', '話': 'わ', '計': 'けい', '時': 'とき',
            '分': 'ふん', '秒': 'びょう', '年': 'とし', '月': 'がつ', '週': 'しゅう',
            '毎': 'まい', '全': 'ぜん', '半': 'はん', '少': 'すこ', '多': 'おお',
            '高': 'たか', '低': 'ひく', '長': 'なが', '短': 'みじか', '新': 'あたら',
            '古': 'ふる', '若': 'わか', '老': 'ろう', '美': 'うつく', '醜': 'みにく',
            '良': 'よ', '悪': 'わる', '正': 'ただ', '間': 'ま', '違': 'ちが'
        }
    
    def generate_furigana(self, text: str) -> List[FuriganaChar]:
        """Generate furigana using the best available method"""
        if self.tagger:
            return self._generate_with_fugashi(text)
        elif self.kakasi:
            return self._generate_with_enhanced_kakasi(text)
        else:
            return self._generate_enhanced_fallback(text)
    
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
                        distributed = self._distribute_furigana_smart(surface, reading)
                        result.extend(distributed)
                else:
                    for char in word.surface:
                        is_kanji = self._is_kanji(char)
                        fallback_reading = self.kanji_readings.get(char) if is_kanji else None
                        result.append(FuriganaChar(char, fallback_reading, is_kanji))
        except Exception as e:
            print(f"Fugashi error: {e}")
            return self._generate_enhanced_fallback(text)
        
        return result
    
    def _generate_with_enhanced_kakasi(self, text: str) -> List[FuriganaChar]:
        """Generate furigana using enhanced pykakasi"""
        result = []
        
        try:
            # Try new API first
            if hasattr(self.kakasi, 'convert'):
                conversion = self.kakasi.convert(text)
                result = self._process_kakasi_new_api(text, conversion)
            elif hasattr(self.kakasi, 'do'):
                conversion = self.kakasi.do(text)
                result = self._process_kakasi_old_api(text, conversion)
            else:
                result = self._generate_enhanced_fallback(text)
        
        except Exception as e:
            print(f"Pykakasi error: {e}")
            result = self._generate_enhanced_fallback(text)
        
        # Enhance with fallback readings for missing furigana
        enhanced_result = []
        for char_info in result:
            if char_info.is_kanji and not char_info.furigana:
                fallback_reading = self.kanji_readings.get(char_info.char)
                enhanced_result.append(FuriganaChar(char_info.char, fallback_reading, True))
            else:
                enhanced_result.append(char_info)
        
        return enhanced_result
    
    def _process_kakasi_new_api(self, text: str, conversion: any) -> List[FuriganaChar]:
        """Process pykakasi new API results"""
        result = []
        
        if isinstance(conversion, list):
            for item in conversion:
                if isinstance(item, dict):
                    orig = item.get('orig', '')
                    hira = item.get('hira', item.get('hiragana', ''))
                    
                    for char in orig:
                        is_kanji = self._is_kanji(char)
                        furigana = None
                        
                        if is_kanji:
                            if len(orig) == 1 and hira != orig:
                                furigana = hira
                            elif len(orig) > 1 and hira != orig:
                                # Distribute reading across kanji characters
                                kanji_positions = [i for i, c in enumerate(orig) if self._is_kanji(c)]
                                if char in orig and kanji_positions:
                                    char_index = orig.index(char)
                                    if char_index in kanji_positions:
                                        kanji_idx = kanji_positions.index(char_index)
                                        chars_per_kanji = len(hira) // len(kanji_positions)
                                        start = kanji_idx * chars_per_kanji
                                        end = start + chars_per_kanji
                                        if kanji_idx == len(kanji_positions) - 1:
                                            end = len(hira)
                                        furigana = hira[start:end] if end > start else None
                        
                        result.append(FuriganaChar(char, furigana, is_kanji))
                else:
                    for char in str(item):
                        result.append(FuriganaChar(char, None, self._is_kanji(char)))
        else:
            for char in text:
                result.append(FuriganaChar(char, None, self._is_kanji(char)))
        
        return result
    
    def _process_kakasi_old_api(self, text: str, conversion: any) -> List[FuriganaChar]:
        """Process pykakasi old API results"""
        result = []
        
        if isinstance(conversion, str):
            # Character by character mapping
            for i, char in enumerate(text):
                is_kanji = self._is_kanji(char)
                furigana = None
                
                if is_kanji and i < len(conversion) and conversion[i] != char:
                    furigana = conversion[i]
                
                result.append(FuriganaChar(char, furigana, is_kanji))
        else:
            for char in text:
                result.append(FuriganaChar(char, None, self._is_kanji(char)))
        
        return result
    
    def _generate_enhanced_fallback(self, text: str) -> List[FuriganaChar]:
        """Enhanced fallback with comprehensive kanji mapping"""
        result = []
        
        for char in text:
            is_kanji = self._is_kanji(char)
            furigana = self.kanji_readings.get(char) if is_kanji else None
            result.append(FuriganaChar(char, furigana, is_kanji))
        
        return result
    
    def _distribute_furigana_smart(self, surface: str, reading: str) -> List[FuriganaChar]:
        """Smart distribution of furigana across characters"""
        result = []
        kanji_chars = [i for i, c in enumerate(surface) if self._is_kanji(c)]
        
        if not kanji_chars:
            for char in surface:
                result.append(FuriganaChar(char, None, False))
            return result
        
        # Smart distribution based on character patterns
        if len(kanji_chars) == 1:
            # Single kanji gets all reading
            for i, char in enumerate(surface):
                is_kanji = self._is_kanji(char)
                furigana = reading if (is_kanji and i == kanji_chars[0]) else None
                result.append(FuriganaChar(char, furigana, is_kanji))
        else:
            # Multiple kanji - distribute reading
            reading_per_kanji = len(reading) // len(kanji_chars)
            
            for i, char in enumerate(surface):
                is_kanji = self._is_kanji(char)
                furigana = None
                
                if is_kanji and i in kanji_chars:
                    kanji_idx = kanji_chars.index(i)
                    start_idx = kanji_idx * reading_per_kanji
                    end_idx = start_idx + reading_per_kanji
                    if kanji_idx == len(kanji_chars) - 1:
                        end_idx = len(reading)
                    furigana = reading[start_idx:end_idx] if end_idx > start_idx else None
                
                # Fallback to dictionary if no furigana assigned
                if is_kanji and not furigana:
                    furigana = self.kanji_readings.get(char)
                
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


class SmartFuriganaRenderer:
    """Smart renderer that handles text sizing and positioning"""
    
    def __init__(self, main_font_size: int = 64, furigana_font_size: int = 32):
        self.main_font_size = main_font_size
        self.furigana_font_size = furigana_font_size
        self.main_font = self._load_font(main_font_size)
        self.furigana_font = self._load_font(furigana_font_size)
        self.line_spacing = 1.2
        self.furigana_spacing = 0.3
        
        print(f"🎨 Renderer initialized: main={main_font_size}px, furigana={furigana_font_size}px")
    
    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Load Japanese font with comprehensive search"""
        font_paths = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
            "/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf",
            "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/Windows/Fonts/msgothic.ttc",
            os.path.expanduser("~/.local/share/fonts/NotoSansJP-Regular.otf"),
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except Exception:
                continue
        
        return ImageFont.load_default()
    
    def measure_text_with_furigana(self, furigana_chars: List[FuriganaChar], 
                                  max_width: Optional[int] = None) -> Tuple[int, int]:
        """Measure text with optional width constraint"""
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
            
            column_width = max(char_width, furigana_width)
            total_width += column_width
            
            total_height = char_height
            if char_info.furigana:
                total_height += self.furigana_font_size + int(self.furigana_font_size * self.furigana_spacing)
            
            max_height = max(max_height, total_height)
        
        # Apply width constraint if specified
        if max_width and total_width > max_width:
            scale_factor = max_width / total_width
            total_width = max_width
            max_height = int(max_height * scale_factor)
        
        return total_width, max_height
    
    def render_text_with_furigana(self, furigana_chars: List[FuriganaChar], 
                                 width: int, height: int, 
                                 scale_factor: float = 1.0) -> Image.Image:
        """Render text with furigana with optional scaling"""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate actual font sizes with scaling
        actual_main_size = int(self.main_font_size * scale_factor)
        actual_furigana_size = int(self.furigana_font_size * scale_factor)
        
        main_font = self._load_font(actual_main_size) if scale_factor != 1.0 else self.main_font
        furigana_font = self._load_font(actual_furigana_size) if scale_factor != 1.0 else self.furigana_font
        
        text_width, text_height = self._measure_with_fonts(furigana_chars, main_font, furigana_font)
        
        start_x = max(0, (width - text_width) // 2)
        start_y = max(0, (height - text_height) // 2)
        current_x = start_x
        
        for char_info in furigana_chars:
            char_bbox = draw.textbbox((0, 0), char_info.char, font=main_font)
            char_width = char_bbox[2] - char_bbox[0]
            char_height = char_bbox[3] - char_bbox[1]
            
            furigana_width = 0
            if char_info.furigana:
                furigana_bbox = draw.textbbox((0, 0), char_info.furigana, font=furigana_font)
                furigana_width = furigana_bbox[2] - furigana_bbox[0]
            
            column_width = max(char_width, furigana_width)
            
            # Position main character
            char_x = current_x + (column_width - char_width) // 2
            char_y = start_y + (actual_furigana_size + int(actual_furigana_size * self.furigana_spacing))
            
            # Draw character with stroke
            stroke_width = max(1, int(2 * scale_factor))
            self._draw_text_with_stroke(draw, char_x, char_y, char_info.char, main_font, stroke_width)
            
            # Draw furigana if present
            if char_info.furigana:
                furigana_x = current_x + (column_width - furigana_width) // 2
                furigana_y = start_y
                self._draw_text_with_stroke(draw, furigana_x, furigana_y, char_info.furigana, furigana_font, stroke_width)
            
            current_x += column_width
        
        return img
    
    def _measure_with_fonts(self, furigana_chars: List[FuriganaChar], 
                           main_font: ImageFont.FreeTypeFont, 
                           furigana_font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
        """Measure text with specific fonts"""
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        total_width = 0
        max_height = 0
        
        for char_info in furigana_chars:
            char_bbox = temp_draw.textbbox((0, 0), char_info.char, font=main_font)
            char_width = char_bbox[2] - char_bbox[0]
            char_height = char_bbox[3] - char_bbox[1]
            
            furigana_width = 0
            if char_info.furigana:
                furigana_bbox = temp_draw.textbbox((0, 0), char_info.furigana, font=furigana_font)
                furigana_width = furigana_bbox[2] - furigana_bbox[0]
            
            total_width += max(char_width, furigana_width)
            
            total_height = char_height
            if char_info.furigana:
                total_height += furigana_font.size + int(furigana_font.size * self.furigana_spacing)
            
            max_height = max(max_height, total_height)
        
        return total_width, max_height
    
    def _draw_text_with_stroke(self, draw: ImageDraw.Draw, x: int, y: int, text: str, 
                              font: ImageFont.FreeTypeFont, stroke_width: int):
        """Draw text with stroke outline"""
        # Draw stroke
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx*dx + dy*dy <= stroke_width*stroke_width:
                    draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 255))
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))


class SRTParser:
    """Parse SRT subtitle files"""
    
    @staticmethod
    def parse_srt(srt_content: str) -> List[SubtitleSegment]:
        """Parse SRT content into subtitle segments"""
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
            
            text = ' '.join(lines[2:]).strip()
            if text:  # Only add non-empty subtitles
                segments.append(SubtitleSegment(start_time, end_time, text))
        
        return segments


class CompleteFuriganaSubtitleBurner:
    """Complete furigana subtitle burner with enhanced features"""
    
    def __init__(self, config: dict = None):
        """Initialize with configuration"""
        self.config = {
            'main_font_size': 64,
            'furigana_font_size': 32,
            'subtitle_position': 'bottom',
            'margin': 80,
            'max_subtitle_width_ratio': 0.9,  # Max 90% of frame width
            'auto_scale': True,
            'stroke_width': 2,
            'preview_mode': False
        }
        
        if config:
            self.config.update(config)
        
        self.furigana_generator = EnhancedFuriganaGenerator()
        self.renderer = SmartFuriganaRenderer(
            self.config['main_font_size'], 
            self.config['furigana_font_size']
        )
        
        print(f"🚀 Complete Furigana Burner initialized")
        print(f"   Config: {self.config}")
    
    def burn_subtitles(self, video_path: str, srt_path: str, output_path: str) -> bool:
        """Burn furigana subtitles onto video with error handling"""
        
        try:
            print(f"🎬 Processing: {os.path.basename(video_path)}")
            print(f"📄 Subtitles: {os.path.basename(srt_path)}")
            print(f"💾 Output: {os.path.basename(output_path)}")
            
            # Read and validate SRT file
            try:
                with open(srt_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
            except Exception as e:
                print(f"❌ Failed to read SRT file: {e}")
                return False
            
            segments = SRTParser.parse_srt(srt_content)
            if not segments:
                print("❌ No valid subtitle segments found")
                return False
            
            print(f"📝 Loaded {len(segments)} subtitle segments")
            
            # Show sample segments
            for i, seg in enumerate(segments[:3]):
                furigana_preview = self._generate_furigana_preview(seg.text)
                print(f"   {i+1}: {seg.text} → {furigana_preview}")
            
            # Open and validate video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"❌ Could not open video: {video_path}")
                return False
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if fps <= 0 or width <= 0 or height <= 0 or total_frames <= 0:
                print("❌ Invalid video properties")
                cap.release()
                return False
            
            print(f"🎥 Video: {width}x{height}, {fps:.2f} fps, {total_frames} frames")
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            if not out.isOpened():
                print(f"❌ Could not create output video: {output_path}")
                cap.release()
                return False
            
            # Process video
            frame_count = 0
            max_subtitle_width = int(width * self.config['max_subtitle_width_ratio'])
            
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
                        try:
                            frame = self._add_subtitle_to_frame_safe(
                                frame, active_subtitle.text, 
                                width, height, max_subtitle_width
                            )
                        except Exception as e:
                            print(f"⚠️  Error adding subtitle at {current_time:.2f}s: {e}")
                            # Continue without subtitle for this frame
                    
                    out.write(frame)
                    frame_count += 1
                    
                    # Progress updates
                    if frame_count % 100 == 0:
                        progress = (frame_count / total_frames) * 100
                        print(f"⏳ Progress: {progress:.1f}% ({frame_count}/{total_frames})")
                    
                    # Preview mode - process only first 300 frames
                    if self.config.get('preview_mode') and frame_count >= 300:
                        print("🎯 Preview mode - stopping at 10 seconds")
                        break
            
            finally:
                cap.release()
                out.release()
            
            print(f"✅ Video saved successfully: {output_path}")
            
            # Verify output file
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"📊 Output size: {os.path.getsize(output_path):,} bytes")
                return True
            else:
                print("❌ Output file is invalid or empty")
                return False
        
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def _generate_furigana_preview(self, text: str, max_chars: int = 30) -> str:
        """Generate a preview string showing furigana"""
        furigana_chars = self.furigana_generator.generate_furigana(text)
        
        preview = ""
        for char_info in furigana_chars:
            if char_info.furigana:
                preview += f"{char_info.char}({char_info.furigana})"
            else:
                preview += char_info.char
        
        return preview[:max_chars] + "..." if len(preview) > max_chars else preview
    
    def _add_subtitle_to_frame_safe(self, frame: np.ndarray, text: str, 
                                   frame_width: int, frame_height: int, 
                                   max_subtitle_width: int) -> np.ndarray:
        """Safely add subtitle to frame with dimension checking"""
        
        # Generate furigana
        furigana_chars = self.furigana_generator.generate_furigana(text)
        if not furigana_chars:
            return frame
        
        # Measure subtitle size
        text_width, text_height = self.renderer.measure_text_with_furigana(
            furigana_chars, max_subtitle_width
        )
        
        # Calculate scale factor if needed
        scale_factor = 1.0
        if self.config['auto_scale'] and text_width > max_subtitle_width:
            scale_factor = max_subtitle_width / text_width
            text_width = max_subtitle_width
            text_height = int(text_height * scale_factor)
        
        # Add padding
        padding = max(10, int(20 * scale_factor))
        subtitle_width = min(text_width + 2 * padding, frame_width - 20)
        subtitle_height = min(text_height + 2 * padding, frame_height // 4)
        
        # Create subtitle image
        subtitle_img = self.renderer.render_text_with_furigana(
            furigana_chars, subtitle_width, subtitle_height, scale_factor
        )
        
        # Convert PIL to OpenCV
        subtitle_cv = cv2.cvtColor(np.array(subtitle_img), cv2.COLOR_RGBA2BGRA)
        
        # Calculate safe position
        position = self.config['subtitle_position']
        margin = self.config['margin']
        
        if position == 'bottom':
            x = (frame_width - subtitle_width) // 2
            y = frame_height - subtitle_height - margin
        elif position == 'top':
            x = (frame_width - subtitle_width) // 2
            y = margin
        else:  # center
            x = (frame_width - subtitle_width) // 2
            y = (frame_height - subtitle_height) // 2
        
        # Ensure subtitle fits completely within frame
        x = max(0, min(x, frame_width - subtitle_width))
        y = max(0, min(y, frame_height - subtitle_height))
        
        # Additional safety check
        if (x + subtitle_width > frame_width or 
            y + subtitle_height > frame_height or
            subtitle_width <= 0 or subtitle_height <= 0):
            print(f"⚠️  Subtitle dimensions unsafe, skipping")
            return frame
        
        # Safe alpha blending
        try:
            alpha = subtitle_cv[:subtitle_height, :subtitle_width, 3] / 255.0
            alpha = np.stack([alpha] * 3, axis=2)
            
            overlay_region = frame[y:y+subtitle_height, x:x+subtitle_width]
            subtitle_rgb = subtitle_cv[:subtitle_height, :subtitle_width, :3]
            
            # Ensure dimensions match
            if (overlay_region.shape == subtitle_rgb.shape == alpha.shape):
                blended = overlay_region * (1 - alpha) + subtitle_rgb * alpha
                frame[y:y+subtitle_height, x:x+subtitle_width] = blended.astype(np.uint8)
            else:
                print(f"⚠️  Dimension mismatch: {overlay_region.shape} vs {subtitle_rgb.shape}")
        
        except Exception as e:
            print(f"⚠️  Blending error: {e}")
        
        return frame


def save_config(config: dict, config_path: str = "furigana_config.json"):
    """Save configuration to file"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"💾 Configuration saved to {config_path}")
    except Exception as e:
        print(f"⚠️  Failed to save config: {e}")


def load_config(config_path: str = "furigana_config.json") -> dict:
    """Load configuration from file"""
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"📂 Configuration loaded from {config_path}")
            return config
    except Exception as e:
        print(f"⚠️  Failed to load config: {e}")
    
    return {}


def main():
    """Main function with improved argument handling"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Complete Furigana Subtitle Burner')
    parser.add_argument('video', nargs='?', help='Input video file')
    parser.add_argument('srt', nargs='?', help='Input SRT subtitle file')
    parser.add_argument('output', nargs='?', help='Output video file')
    parser.add_argument('--main-font-size', type=int, default=64, help='Main text font size')
    parser.add_argument('--furigana-font-size', type=int, default=32, help='Furigana font size')
    parser.add_argument('--position', choices=['top', 'bottom', 'center'], default='bottom')
    parser.add_argument('--margin', type=int, default=80, help='Margin from edge')
    parser.add_argument('--preview', action='store_true', help='Preview mode (first 10 seconds)')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--save-config', action='store_true', help='Save current config as default')
    
    if len(sys.argv) == 1:
        # Auto-detect mode
        print("🔍 Auto-detecting video and subtitle files...")
        
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
            
            # Load configuration
            config = load_config()
            burner = CompleteFuriganaSubtitleBurner(config)
            
            success = burner.burn_subtitles(video_file, srt_file, output_file)
            
            if success:
                print("\n🎉 SUCCESS! Furigana subtitles burned successfully!")
                print(f"📁 Check your output: {output_file}")
            else:
                print("\n❌ FAILED! Check the error messages above.")
            
        else:
            print("❌ No video or subtitle files found")
            print("\n📖 Usage:")
            print("  python complete_furigana_burner.py                           # Auto-detect files")
            print("  python complete_furigana_burner.py video.mp4 sub.srt out.mp4  # Manual files")
            print("  python complete_furigana_burner.py --preview video.mp4 sub.srt out.mp4  # Preview mode")
        
        return
    
    args = parser.parse_args()
    
    # Build configuration
    config = load_config(args.config) if args.config else load_config()
    
    # Override with command line arguments
    config.update({
        'main_font_size': args.main_font_size,
        'furigana_font_size': args.furigana_font_size,
        'subtitle_position': args.position,
        'margin': args.margin,
        'preview_mode': args.preview
    })
    
    # Save configuration if requested
    if args.save_config:
        save_config(config)
    
    # Create burner and process
    burner = CompleteFuriganaSubtitleBurner(config)
    success = burner.burn_subtitles(args.video, args.srt, args.output)
    
    if success:
        print("\n🎉 SUCCESS! Furigana subtitles burned successfully!")
    else:
        print("\n❌ FAILED! Check the error messages above.")


if __name__ == "__main__":
    main()
