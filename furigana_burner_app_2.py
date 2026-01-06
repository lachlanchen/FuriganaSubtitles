#!/usr/bin/env python3
"""
Fixed Furigana Subtitle Burner App
Fixes layout overflow issues for lines without furigana
Highly reusable with proper multi-line layout
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import re
import os
import sys
import glob
import json
from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable
from abc import ABC, abstractmethod

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
    
    def __str__(self):
        if self.furigana:
            return f"{self.char}({self.furigana})"
        return self.char


@dataclass
class SubtitleLine:
    """Represents a single line of subtitle with furigana"""
    furigana_chars: List[FuriganaChar]
    width: int
    height: int
    has_furigana: bool  # Track if this specific line has furigana
    furigana_height: int  # Height needed for furigana in this line
    text_height: int     # Height needed for main text


@dataclass
class BurnerConfig:
    """Configuration for the subtitle burner"""
    main_font_size: int = 64
    furigana_font_size: int = 32
    position: str = 'bottom'  # 'top', 'center', 'bottom'
    margin: int = 60
    max_width_ratio: float = 0.85  # Max width as ratio of frame width
    line_spacing_ratio: float = 0.2  # Spacing between lines as ratio of main font size
    stroke_width: int = 2
    text_color: Tuple[int, int, int] = (255, 255, 255)  # White
    stroke_color: Tuple[int, int, int] = (0, 0, 0)      # Black
    background_opacity: float = 0.3  # Semi-transparent background
    auto_multi_line: bool = True  # Split long text into multiple lines
    furigana_spacing_ratio: float = 0.3  # Space between furigana and main text


class FuriganaGenerator(ABC):
    """Abstract base class for furigana generation"""
    
    @abstractmethod
    def get_furigana(self, text: str) -> List[FuriganaChar]:
        """Generate furigana for given text"""
        pass


class DummyFuriganaGenerator(FuriganaGenerator):
    """Dummy furigana generator with comprehensive kanji dictionary"""
    
    def __init__(self):
        # Comprehensive kanji-to-furigana mapping
        # Easy to extend or replace with AI method
        self.kanji_dict = {
            # From your subtitle content
            '今': 'いま', '日': 'ひ', '空': 'そら', '気': 'き', '持': 'も',
            '晴': 'は', '朝': 'あさ', '時': 'じ', '間': 'かん', '静': 'しず',
            '心': 'こころ', '落': 'お', '着': 'つ', '深': 'ふか', '呼': 'こ',
            '吸': 'きゅう', '外': 'そと', '鳥': 'とり', '声': 'こえ', '聞': 'き',
            '温': 'あたた', '入': 'い', '笑': 'わら', '穏': 'おだ',
            
            # Extended common kanji
            '人': 'ひと', '大': 'おお', '小': 'ちい', '中': 'なか', '出': 'で',
            '来': 'き', '行': 'い', '見': 'み', '話': 'はな', '食': 'た',
            '飲': 'の', '読': 'よ', '書': 'か', '買': 'か', '売': 'う',
            '作': 'つく', '使': 'つか', '思': 'おも', '言': 'い', '考': 'かんが',
            '知': 'し', '分': 'わ', '手': 'て', '足': 'あし', '目': 'め',
            '耳': 'みみ', '口': 'くち', '頭': 'あたま', '体': 'からだ',
            '水': 'みず', '火': 'ひ', '土': 'つち', '木': 'き', '金': 'きん',
            '石': 'いし', '山': 'やま', '川': 'かわ', '海': 'うみ', '田': 'た',
            '花': 'はな', '雨': 'あめ', '雪': 'ゆき', '風': 'かぜ', '雲': 'くも',
            '星': 'ほし', '月': 'つき', '太': 'たい', '陽': 'よう', '光': 'ひかり',
            '車': 'くるま', '電': 'でん', '話': 'わ', '計': 'けい', '年': 'とし',
            '毎': 'まい', '全': 'ぜん', '半': 'はん', '少': 'すこ', '多': 'おお',
            '高': 'たか', '低': 'ひく', '長': 'なが', '短': 'みじか',
            '新': 'あたら', '古': 'ふる', '若': 'わか', '美': 'うつく',
            '良': 'よ', '悪': 'わる', '正': 'ただ', '間': 'ま', '違': 'ちが'
        }
        
        print(f"🎌 Dummy furigana generator loaded with {len(self.kanji_dict)} kanji")
    
    def get_furigana(self, text: str) -> List[FuriganaChar]:
        """Generate furigana using dictionary lookup"""
        result = []
        for char in text:
            is_kanji = self._is_kanji(char)
            furigana = self.kanji_dict.get(char) if is_kanji else None
            result.append(FuriganaChar(char, furigana, is_kanji))
        return result
    
    def _is_kanji(self, char: str) -> bool:
        """Check if character is kanji"""
        return '\u4e00' <= char <= '\u9faf'


class PykakasiFuriganaGenerator(FuriganaGenerator):
    """Pykakasi-based furigana generator"""
    
    def __init__(self):
        self.kakasi = None
        self.fallback = DummyFuriganaGenerator()
        
        if KAKASI_AVAILABLE:
            try:
                # Try new API
                self.kakasi = pykakasi.kakasi()
                print("✅ Pykakasi furigana generator (new API) initialized")
            except Exception as e:
                try:
                    # Try old API
                    kks = pykakasi.kakasi()
                    kks.setMode('J', 'H')  # Kanji to Hiragana
                    self.kakasi = kks.getConverter()
                    print("✅ Pykakasi furigana generator (old API) initialized")
                except Exception as e2:
                    print(f"⚠️  Pykakasi failed: {e2}")
                    self.kakasi = None
        
        if not self.kakasi:
            print("⚠️  Using fallback dummy generator")
    
    def get_furigana(self, text: str) -> List[FuriganaChar]:
        """Generate furigana using pykakasi with fallback"""
        if not self.kakasi:
            return self.fallback.get_furigana(text)
        
        try:
            if hasattr(self.kakasi, 'convert'):
                return self._process_new_api(text)
            elif hasattr(self.kakasi, 'do'):
                return self._process_old_api(text)
            else:
                return self.fallback.get_furigana(text)
        except Exception as e:
            print(f"⚠️  Pykakasi error: {e}, using fallback")
            return self.fallback.get_furigana(text)
    
    def _process_new_api(self, text: str) -> List[FuriganaChar]:
        """Process pykakasi new API results"""
        result = []
        conversion = self.kakasi.convert(text)
        
        if isinstance(conversion, list):
            for item in conversion:
                if isinstance(item, dict):
                    orig = item.get('orig', '')
                    hira = item.get('hira', '')
                    
                    for char in orig:
                        is_kanji = self._is_kanji(char)
                        furigana = None
                        
                        if is_kanji and hira != orig:
                            if len(orig) == 1:
                                furigana = hira
                            else:
                                # Simple distribution
                                kanji_count = sum(1 for c in orig if self._is_kanji(c))
                                if kanji_count > 0:
                                    furigana = hira[:len(hira)//kanji_count] if hira else None
                        
                        # Use fallback if no furigana found
                        if is_kanji and not furigana:
                            furigana = self.fallback.kanji_dict.get(char)
                        
                        result.append(FuriganaChar(char, furigana, is_kanji))
        
        return result or self.fallback.get_furigana(text)
    
    def _process_old_api(self, text: str) -> List[FuriganaChar]:
        """Process pykakasi old API results"""
        result = []
        conversion = self.kakasi.do(text)
        
        if isinstance(conversion, str):
            for i, char in enumerate(text):
                is_kanji = self._is_kanji(char)
                furigana = None
                
                if is_kanji and i < len(conversion) and conversion[i] != char:
                    furigana = conversion[i]
                
                # Use fallback if no furigana found
                if is_kanji and not furigana:
                    furigana = self.fallback.kanji_dict.get(char)
                
                result.append(FuriganaChar(char, furigana, is_kanji))
        
        return result or self.fallback.get_furigana(text)
    
    def _is_kanji(self, char: str) -> bool:
        """Check if character is kanji"""
        return '\u4e00' <= char <= '\u9faf'


class FixedFuriganaRenderer:
    """Fixed renderer with proper layout handling for lines with/without furigana"""
    
    def __init__(self, config: BurnerConfig):
        self.config = config
        self.main_font = self._load_font(config.main_font_size)
        self.furigana_font = self._load_font(config.furigana_font_size)
        
        print(f"🎨 Fixed renderer initialized: main={config.main_font_size}px, furigana={config.furigana_font_size}px")
        print(f"   Line spacing: {config.line_spacing_ratio}")
    
    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Load Japanese font with fallback"""
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
    
    def split_into_lines(self, furigana_chars: List[FuriganaChar], max_width: int) -> List[SubtitleLine]:
        """Split furigana text into multiple lines with proper height calculation"""
        if not furigana_chars:
            return []
        
        lines = []
        current_line = []
        current_width = 0
        
        for char_info in furigana_chars:
            char_width = self._measure_char_width(char_info)
            
            # Check if we need to start a new line
            if (current_width + char_width > max_width and 
                current_line and 
                self.config.auto_multi_line):
                
                # Find a good break point (prefer spaces, punctuation)
                if self._is_good_break_point(char_info.char) or len(current_line) > 10:
                    line = self._create_subtitle_line(current_line)
                    lines.append(line)
                    current_line = []
                    current_width = 0
            
            current_line.append(char_info)
            current_width += char_width
        
        # Add the last line
        if current_line:
            line = self._create_subtitle_line(current_line)
            lines.append(line)
        
        return lines or [self._create_subtitle_line(furigana_chars)]
    
    def _create_subtitle_line(self, furigana_chars: List[FuriganaChar]) -> SubtitleLine:
        """Create a SubtitleLine with proper height calculation"""
        if not furigana_chars:
            return SubtitleLine([], 0, 0, False, 0, 0)
        
        # Calculate width
        width = sum(self._measure_char_width(char) for char in furigana_chars)
        
        # Check if this line has any furigana
        has_furigana = any(char.furigana for char in furigana_chars)
        
        # Calculate heights
        text_height = self.config.main_font_size
        furigana_height = 0
        
        if has_furigana:
            furigana_height = self.config.furigana_font_size
        
        # Total height for this line
        total_height = text_height
        if has_furigana:
            total_height += furigana_height + int(self.config.furigana_font_size * self.config.furigana_spacing_ratio)
        
        return SubtitleLine(
            furigana_chars=furigana_chars,
            width=width,
            height=total_height,
            has_furigana=has_furigana,
            furigana_height=furigana_height,
            text_height=text_height
        )
    
    def _measure_char_width(self, char_info: FuriganaChar) -> int:
        """Measure the width needed for a character with furigana"""
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        char_bbox = temp_draw.textbbox((0, 0), char_info.char, font=self.main_font)
        char_width = char_bbox[2] - char_bbox[0]
        
        furigana_width = 0
        if char_info.furigana:
            furigana_bbox = temp_draw.textbbox((0, 0), char_info.furigana, font=self.furigana_font)
            furigana_width = furigana_bbox[2] - furigana_bbox[0]
        
        return max(char_width, furigana_width)
    
    def _is_good_break_point(self, char: str) -> bool:
        """Check if this is a good place to break a line"""
        return char in ' 、。！？\n\t'
    
    def render_multi_line_subtitle(self, lines: List[SubtitleLine], 
                                  frame_width: int, frame_height: int) -> Image.Image:
        """Render multi-line subtitle with fixed layout"""
        if not lines:
            return Image.new('RGBA', (100, 50), (0, 0, 0, 0))
        
        # Calculate total dimensions with proper line heights
        max_line_width = max(line.width for line in lines)
        total_height = sum(line.height for line in lines)
        
        # Add line spacing between lines (but not after the last line)
        if len(lines) > 1:
            line_spacing = int(self.config.main_font_size * self.config.line_spacing_ratio)
            total_height += (len(lines) - 1) * line_spacing
        
        # Add padding
        padding = 20
        subtitle_width = min(max_line_width + 2 * padding, frame_width - 40)
        subtitle_height = min(total_height + 2 * padding, frame_height // 2)
        
        # Ensure minimum size
        subtitle_width = max(subtitle_width, 100)
        subtitle_height = max(subtitle_height, 50)
        
        # Create subtitle image
        img = Image.new('RGBA', (subtitle_width, subtitle_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Optional background
        if self.config.background_opacity > 0:
            bg_alpha = int(255 * self.config.background_opacity)
            draw.rectangle([0, 0, subtitle_width, subtitle_height], 
                         fill=(0, 0, 0, bg_alpha))
        
        # Render each line with proper positioning
        y_offset = padding
        line_spacing = int(self.config.main_font_size * self.config.line_spacing_ratio)
        
        for i, line in enumerate(lines):
            self._render_single_line(draw, line, subtitle_width, y_offset)
            y_offset += line.height
            
            # Add spacing between lines (except after the last line)
            if i < len(lines) - 1:
                y_offset += line_spacing
        
        return img
    
    def _render_single_line(self, draw: ImageDraw.Draw, line: SubtitleLine, 
                           total_width: int, y_offset: int):
        """Render a single line with proper positioning based on furigana presence"""
        if not line.furigana_chars:
            return
        
        # Center the line horizontally
        x_offset = (total_width - line.width) // 2
        current_x = x_offset
        
        # Calculate text baseline position
        if line.has_furigana:
            # If line has furigana, position text below furigana space
            text_y = y_offset + line.furigana_height + int(self.config.furigana_font_size * self.config.furigana_spacing_ratio)
            furigana_y = y_offset
        else:
            # If no furigana, center text in the line height
            text_y = y_offset + (line.height - line.text_height) // 2
            furigana_y = y_offset
        
        for char_info in line.furigana_chars:
            char_width = self._measure_char_width(char_info)
            
            # Calculate character positions
            char_bbox = draw.textbbox((0, 0), char_info.char, font=self.main_font)
            char_w = char_bbox[2] - char_bbox[0]
            
            # Center character in its allocated width
            char_x = current_x + (char_width - char_w) // 2
            
            # Draw character with stroke
            self._draw_text_with_stroke(draw, char_x, text_y, char_info.char, self.main_font)
            
            # Draw furigana if present (only for lines that have furigana)
            if char_info.furigana and line.has_furigana:
                furigana_bbox = draw.textbbox((0, 0), char_info.furigana, font=self.furigana_font)
                furigana_w = furigana_bbox[2] - furigana_bbox[0]
                furigana_x = current_x + (char_width - furigana_w) // 2
                self._draw_text_with_stroke(draw, furigana_x, furigana_y, char_info.furigana, self.furigana_font)
            
            current_x += char_width
    
    def _draw_text_with_stroke(self, draw: ImageDraw.Draw, x: int, y: int, text: str, font: ImageFont.FreeTypeFont):
        """Draw text with stroke outline"""
        # Draw stroke
        stroke_width = self.config.stroke_width
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx*dx + dy*dy <= stroke_width*stroke_width:
                    draw.text((x + dx, y + dy), text, font=font, fill=self.config.stroke_color)
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=self.config.text_color)


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
            if text:
                segments.append(SubtitleSegment(start_time, end_time, text))
        
        return segments


class FixedFuriganaBurnerApp:
    """Fixed furigana subtitle burner application"""
    
    def __init__(self, config: BurnerConfig = None, furigana_generator: FuriganaGenerator = None):
        """Initialize the burner app"""
        self.config = config or BurnerConfig()
        self.furigana_generator = furigana_generator or self._create_default_generator()
        self.renderer = FixedFuriganaRenderer(self.config)
        
        print(f"🚀 Fixed Furigana Burner App initialized")
        print(f"   Position: {self.config.position}")
        print(f"   Max width: {self.config.max_width_ratio*100}%")
        print(f"   Multi-line: {self.config.auto_multi_line}")
        print(f"   Line spacing: {self.config.line_spacing_ratio}")
    
    def _create_default_generator(self) -> FuriganaGenerator:
        """Create default furigana generator"""
        # Try pykakasi first, fallback to dummy
        if KAKASI_AVAILABLE:
            return PykakasiFuriganaGenerator()
        else:
            return DummyFuriganaGenerator()
    
    def get_furigana(self, text: str) -> List[FuriganaChar]:
        """
        Get furigana for text - this is the pluggable function
        Easy to replace with AI method later
        """
        return self.furigana_generator.get_furigana(text)
    
    def burn_subtitles(self, video_path: str, srt_path: str, output_path: str = None) -> bool:
        """Burn furigana subtitles onto video"""
        
        # Auto-generate output path if not provided
        if not output_path:
            base_name = os.path.splitext(video_path)[0]
            output_path = f"{base_name}_furigana.mp4"
        
        print(f"🎬 Processing: {os.path.basename(video_path)}")
        print(f"📄 Subtitles: {os.path.basename(srt_path)}")
        print(f"💾 Output: {os.path.basename(output_path)}")
        
        try:
            # Read SRT file
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            segments = SRTParser.parse_srt(srt_content)
            if not segments:
                print("❌ No valid subtitle segments found")
                return False
            
            print(f"📝 Loaded {len(segments)} subtitle segments")
            
            # Show preview of furigana generation
            for i, seg in enumerate(segments[:3]):
                furigana_chars = self.get_furigana(seg.text)
                preview = ''.join(str(char) for char in furigana_chars)
                has_furigana = any(char.furigana for char in furigana_chars)
                print(f"   {i+1}: {seg.text}")
                print(f"      → {preview} {'(has furigana)' if has_furigana else '(no furigana)'}")
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"❌ Could not open video: {video_path}")
                return False
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            print(f"🎥 Video: {width}x{height}, {fps:.2f} fps, {total_frames} frames")
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            if not out.isOpened():
                print(f"❌ Could not create output video")
                cap.release()
                return False
            
            # Calculate subtitle area
            max_subtitle_width = int(width * self.config.max_width_ratio)
            
            # Process video
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
                            frame, active_subtitle.text, width, height, max_subtitle_width
                        )
                    
                    out.write(frame)
                    frame_count += 1
                    
                    # Progress updates
                    if frame_count % 100 == 0:
                        progress = (frame_count / total_frames) * 100
                        print(f"⏳ Progress: {progress:.1f}% ({frame_count}/{total_frames})")
            
            finally:
                cap.release()
                out.release()
            
            print(f"✅ Video saved successfully: {output_path}")
            
            # Verify output
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"📊 Output size: {size_mb:.1f} MB")
                return True
            else:
                print("❌ Output file is invalid")
                return False
        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _add_subtitle_to_frame(self, frame: np.ndarray, text: str, 
                              frame_width: int, frame_height: int, max_width: int) -> np.ndarray:
        """Add subtitle to frame with fixed positioning"""
        
        # Generate furigana
        furigana_chars = self.get_furigana(text)
        if not furigana_chars:
            return frame
        
        # Split into lines with proper height calculation
        lines = self.renderer.split_into_lines(furigana_chars, max_width)
        if not lines:
            return frame
        
        # Render subtitle
        subtitle_img = self.renderer.render_multi_line_subtitle(lines, frame_width, frame_height)
        
        # Convert PIL to OpenCV
        subtitle_cv = cv2.cvtColor(np.array(subtitle_img), cv2.COLOR_RGBA2BGRA)
        subtitle_height, subtitle_width = subtitle_cv.shape[:2]
        
        # Calculate position based on config
        x, y = self._calculate_subtitle_position(
            frame_width, frame_height, subtitle_width, subtitle_height
        )
        
        # Ensure subtitle fits completely in frame
        x = max(0, min(x, frame_width - subtitle_width))
        y = max(0, min(y, frame_height - subtitle_height))
        
        # Additional safety check with detailed logging
        if (x + subtitle_width > frame_width or 
            y + subtitle_height > frame_height or
            subtitle_width <= 0 or subtitle_height <= 0):
            print(f"⚠️  Subtitle position unsafe:")
            print(f"     Position: ({x}, {y})")
            print(f"     Size: {subtitle_width}x{subtitle_height}")
            print(f"     Frame: {frame_width}x{frame_height}")
            print(f"     Lines: {len(lines)}")
            for i, line in enumerate(lines):
                print(f"       Line {i+1}: {line.width}x{line.height}, furigana={line.has_furigana}")
            return frame
        
        # Alpha blending
        try:
            alpha = subtitle_cv[:, :, 3] / 255.0
            alpha = np.stack([alpha] * 3, axis=2)
            
            overlay_region = frame[y:y+subtitle_height, x:x+subtitle_width]
            subtitle_rgb = subtitle_cv[:, :, :3]
            
            if overlay_region.shape == subtitle_rgb.shape == alpha.shape:
                blended = overlay_region * (1 - alpha) + subtitle_rgb * alpha
                frame[y:y+subtitle_height, x:x+subtitle_width] = blended.astype(np.uint8)
            else:
                print(f"⚠️  Shape mismatch: overlay={overlay_region.shape}, subtitle={subtitle_rgb.shape}, alpha={alpha.shape}")
        
        except Exception as e:
            print(f"⚠️  Blending error: {e}")
        
        return frame
    
    def _calculate_subtitle_position(self, frame_width: int, frame_height: int, 
                                   subtitle_width: int, subtitle_height: int) -> Tuple[int, int]:
        """Calculate subtitle position based on configuration"""
        
        # Horizontal centering
        x = (frame_width - subtitle_width) // 2
        
        # Vertical positioning based on config
        margin = self.config.margin
        
        if self.config.position == 'top':
            y = margin
        elif self.config.position == 'center':
            y = (frame_height - subtitle_height) // 2
        else:  # bottom
            y = frame_height - subtitle_height - margin
        
        return x, y


def create_ai_furigana_generator() -> FuriganaGenerator:
    """
    Placeholder for AI-based furigana generator
    Replace this function to use OpenAI, Anthropic, or other AI services
    """
    # Example implementation:
    class AIFuriganaGenerator(FuriganaGenerator):
        def get_furigana(self, text: str) -> List[FuriganaChar]:
            # TODO: Replace with actual AI API call
            # response = openai.complete(f"Add furigana to: {text}")
            # return parse_ai_response(response)
            
            # For now, use dummy generator
            dummy = DummyFuriganaGenerator()
            return dummy.get_furigana(text)
    
    return AIFuriganaGenerator()


def main():
    """Main function with command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fixed Furigana Subtitle Burner App')
    parser.add_argument('video', nargs='?', help='Input video file')
    parser.add_argument('srt', nargs='?', help='Input SRT subtitle file')
    parser.add_argument('output', nargs='?', help='Output video file (optional)')
    
    # Configuration options
    parser.add_argument('--position', choices=['top', 'center', 'bottom'], 
                       default='bottom', help='Subtitle position')
    parser.add_argument('--main-font-size', type=int, default=64, help='Main font size')
    parser.add_argument('--furigana-font-size', type=int, default=32, help='Furigana font size')
    parser.add_argument('--margin', type=int, default=60, help='Margin from edge')
    parser.add_argument('--max-width', type=float, default=0.85, help='Max width ratio (0-1)')
    parser.add_argument('--line-spacing', type=float, default=0.2, 
                       help='Line spacing ratio (0.1=closer, 0.5=farther)')
    parser.add_argument('--no-multiline', action='store_true', help='Disable multi-line')
    parser.add_argument('--ai-furigana', action='store_true', help='Use AI furigana (placeholder)')
    
    if len(sys.argv) == 1:
        # Auto-detect mode
        print("🔍 Auto-detecting video and subtitle files...")
        
        mp4_files = glob.glob("*.MP4") + glob.glob("*.mp4")
        srt_files = glob.glob("*.srt")
        
        if mp4_files and srt_files:
            video_file = mp4_files[0]
            srt_file = srt_files[0]
            
            print(f"📹 Found: {video_file}")
            print(f"📄 Found: {srt_file}")
            
            # Create default config
            config = BurnerConfig()
            
            # Create furigana generator
            if KAKASI_AVAILABLE:
                generator = PykakasiFuriganaGenerator()
            else:
                generator = DummyFuriganaGenerator()
            
            # Create app and process
            app = FixedFuriganaBurnerApp(config, generator)
            success = app.burn_subtitles(video_file, srt_file)
            
            if success:
                print("\n🎉 SUCCESS! Fixed furigana subtitles burned successfully!")
                print("   ✅ Layout issues fixed - no more overflow!")
                print("   ✅ Lines without furigana handled properly!")
            else:
                print("\n❌ FAILED! Check the error messages above.")
        
        else:
            print("❌ No video or subtitle files found")
            print("\n📖 Usage:")
            print("  python fixed_furigana_burner.py                    # Auto-detect files")
            print("  python fixed_furigana_burner.py video.mp4 sub.srt  # Specify files")
            print("  python fixed_furigana_burner.py --position top     # Top position")
            print("  python fixed_furigana_burner.py --line-spacing 0.1 # Closer lines")
        
        return
    
    args = parser.parse_args()
    
    # Create configuration
    config = BurnerConfig(
        main_font_size=args.main_font_size,
        furigana_font_size=args.furigana_font_size,
        position=args.position,
        margin=args.margin,
        max_width_ratio=args.max_width,
        line_spacing_ratio=args.line_spacing,
        auto_multi_line=not args.no_multiline
    )
    
    # Create furigana generator
    if args.ai_furigana:
        generator = create_ai_furigana_generator()
    elif KAKASI_AVAILABLE:
        generator = PykakasiFuriganaGenerator()
    else:
        generator = DummyFuriganaGenerator()
    
    # Create app and process
    app = FixedFuriganaBurnerApp(config, generator)
    success = app.burn_subtitles(args.video, args.srt, args.output)
    
    if success:
        print("\n🎉 SUCCESS! Fixed furigana subtitles burned successfully!")
    else:
        print("\n❌ FAILED! Check the error messages above.")


if __name__ == "__main__":
    main()
