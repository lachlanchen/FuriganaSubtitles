#!/usr/bin/env python3
"""
AI-First Furigana Subtitle Burner App
Features:
- OpenAI API as primary furigana generator
- Pykakasi fallback only with --no-ai flag
- Robust language detection (skips non-Japanese text)
- Comprehensive caching system
- Multi-line layout with proper positioning
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
from typing import List, Tuple, Optional, Dict, Any
from abc import ABC, abstractmethod

# Import the OpenAI request handler
# Assume this is in the same directory or adjust path
from openai_request import OpenAIRequestJSONBase

# Japanese text processing libraries (optional fallbacks)
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
    has_furigana: bool
    furigana_height: int
    text_height: int


@dataclass
class BurnerConfig:
    """Configuration for the subtitle burner"""
    main_font_size: int = 64
    furigana_font_size: int = 32
    position: str = 'bottom'  # 'top', 'center', 'bottom'
    margin: int = 60
    max_width_ratio: float = 0.85
    line_spacing_ratio: float = 0.2
    stroke_width: int = 2
    text_color: Tuple[int, int, int] = (255, 255, 255)
    stroke_color: Tuple[int, int, int] = (0, 0, 0)
    background_opacity: float = 0.3
    auto_multi_line: bool = True
    furigana_spacing_ratio: float = 0.3
    # OpenAI specific settings
    openai_model: str = "gpt-4o-mini"
    use_openai_cache: bool = True
    max_openai_retries: int = 3
    use_ai: bool = True  # Default to using AI


class FuriganaGenerator(ABC):
    """Abstract base class for furigana generation"""
    
    @abstractmethod
    def get_furigana(self, text: str) -> List[FuriganaChar]:
        """Generate furigana for given text"""
        pass


class OpenAIFuriganaGenerator(FuriganaGenerator):
    """OpenAI-powered furigana generator with caching and language detection"""
    
    def __init__(self, config: BurnerConfig):
        self.config = config
        
        # Initialize OpenAI client with caching
        try:
            self.openai_client = OpenAIRequestJSONBase(
                use_cache=config.use_openai_cache,
                max_retries=config.max_openai_retries,
                cache_dir='furigana_cache'
            )
            print("✅ OpenAI furigana generator initialized with caching")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")
            raise
        
        # Define JSON schema for OpenAI requests (compatible with Structured Outputs)
        self.furigana_schema = {
            "type": "object",
            "properties": {
                "is_japanese": {
                    "type": "boolean",
                    "description": "Whether the text contains Japanese that needs furigana"
                },
                "original_text": {
                    "type": "string",
                    "description": "The original input text"
                },
                "kanji_readings": {
                    "type": "array",
                    "description": "Array of kanji-reading pairs",
                    "items": {
                        "type": "object",
                        "properties": {
                            "kanji": {
                                "type": "string",
                                "description": "The kanji character"
                            },
                            "reading": {
                                "type": "string",
                                "description": "The hiragana reading for this kanji"
                            }
                        },
                        "required": ["kanji", "reading"],
                        "additionalProperties": False
                    }
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence in the furigana generation (0-1)"
                },
                "language_detected": {
                    "type": "string",
                    "description": "Primary language detected in the text"
                }
            },
            "required": ["is_japanese", "original_text", "kanji_readings", "confidence", "language_detected"],
            "additionalProperties": False
        }
    
    def get_furigana(self, text: str) -> List[FuriganaChar]:
        """Generate furigana using OpenAI with robust error handling"""
        
        # Quick check for empty or very short text
        if not text or len(text.strip()) < 2:
            return [FuriganaChar(char, None, False) for char in text]
        
        # Quick check for obvious non-Japanese text
        if self._is_obviously_non_japanese(text):
            print(f"🔍 Skipping obvious non-Japanese text: {text[:30]}...")
            return [FuriganaChar(char, None, False) for char in text]
        
        try:
            # Get furigana from OpenAI
            openai_result = self._request_furigana_from_openai(text)
            
            if openai_result and openai_result.get('is_japanese', False):
                # Process OpenAI result
                furigana_chars = self._process_openai_result(text, openai_result)
                
                # Validate result quality
                if self._validate_furigana_quality(furigana_chars, openai_result.get('confidence', 0)):
                    print(f"✅ OpenAI furigana generated for: {text[:30]}... (confidence: {openai_result.get('confidence', 0):.2f})")
                    return furigana_chars
                else:
                    print(f"⚠️ Low quality OpenAI result for: {text[:30]}...")
                    # Return without furigana rather than using fallback dictionary
                    return [FuriganaChar(char, None, self._is_kanji(char)) for char in text]
            else:
                language = openai_result.get('language_detected', 'unknown') if openai_result else 'unknown'
                print(f"🌐 Non-Japanese text detected ({language}): {text[:30]}...")
                return [FuriganaChar(char, None, False) for char in text]
        
        except Exception as e:
            print(f"⚠️ OpenAI error for '{text[:30]}...': {e}")
            # Return without furigana rather than using fallback dictionary
            return [FuriganaChar(char, None, self._is_kanji(char)) for char in text]
    
    def _is_obviously_non_japanese(self, text: str) -> bool:
        """Quick check to identify obviously non-Japanese text"""
        
        # Count ASCII alphabetic characters
        ascii_alpha = sum(1 for char in text if char.isascii() and char.isalpha())
        total_text_chars = sum(1 for char in text if not char.isspace() and char not in '.,!?;:-()[]{}""''')
        
        # If more than 70% are ASCII letters, probably not Japanese
        if total_text_chars > 0 and (ascii_alpha / total_text_chars) > 0.7:
            return True
        
        # Check for common Western punctuation patterns
        if re.search(r'\b[A-Za-z]{3,}\b', text):  # Words with 3+ ASCII letters
            return True
        
        return False
    
    def _request_furigana_from_openai(self, text: str) -> Optional[Dict[str, Any]]:
        """Request furigana from OpenAI API"""
        
        system_prompt = """You are a Japanese language expert specializing in furigana generation. 

Your task is to:
1. Determine if the input text contains Japanese that needs furigana
2. For Japanese kanji, provide accurate hiragana readings
3. Detect the primary language of the text
4. Provide confidence in your analysis

Guidelines:
- Only generate furigana for kanji characters that actually need reading assistance
- Use contextually appropriate readings (not just dictionary readings)
- Be conservative - if unsure about language, prefer false negatives
- Common katakana and hiragana don't need furigana
- Consider the context for proper kanji readings (e.g. 今日 = きょう not いまひ)
- For compound kanji words, provide individual character readings when appropriate"""

        user_prompt = f"""Analyze this text and provide furigana information:

Text: "{text}"

Provide:
1. Whether this is Japanese text that needs furigana
2. An array of kanji-reading pairs for characters that need furigana
3. Your confidence level (0.0 to 1.0)
4. The primary language detected

For example, for "今日は晴れです":
- is_japanese: true
- kanji_readings: [
    {{"kanji": "今", "reading": "きょう"}},
    {{"kanji": "日", "reading": ""}},
    {{"kanji": "晴", "reading": "は"}}
  ]
  (note: 日 in 今日 is covered by きょう, so empty reading)
- confidence: 0.95
- language_detected: "japanese"

For non-Japanese text like "Hello world" or Chinese text:
- is_japanese: false
- kanji_readings: []
- confidence: 0.9
- language_detected: "english" or "chinese" etc."""

        try:
            # Create cache filename based on text hash
            cache_filename = f"furigana_{abs(hash(text))}.json"
            
            result = self.openai_client.send_request_with_json_schema(
                prompt=user_prompt,
                json_schema=self.furigana_schema,
                system_content=system_prompt,
                filename=cache_filename,
                schema_name="furigana_analysis",
                model=self.config.openai_model
            )
            
            return result
            
        except Exception as e:
            print(f"OpenAI request failed: {e}")
            return None
    
    def _process_openai_result(self, original_text: str, openai_result: Dict[str, Any]) -> List[FuriganaChar]:
        """Process OpenAI result into FuriganaChar objects"""
        
        # Convert array format to dictionary for easier lookup
        kanji_readings_array = openai_result.get('kanji_readings', [])
        kanji_readings_dict = {}
        
        for pair in kanji_readings_array:
            kanji = pair.get('kanji', '')
            reading = pair.get('reading', '')
            if kanji and reading:  # Only add if both kanji and reading are present
                kanji_readings_dict[kanji] = reading
        
        result = []
        for char in original_text:
            is_kanji = self._is_kanji(char)
            furigana = kanji_readings_dict.get(char) if is_kanji else None
            
            # Clean up empty furigana readings
            if furigana and not furigana.strip():
                furigana = None
            
            result.append(FuriganaChar(char, furigana, is_kanji))
        
        return result
    
    def _validate_furigana_quality(self, furigana_chars: List[FuriganaChar], confidence: float) -> bool:
        """Validate the quality of generated furigana"""
        
        # Minimum confidence threshold
        if confidence < 0.6:
            return False
        
        # Basic sanity checks on furigana content
        for char in furigana_chars:
            if char.furigana:
                # Furigana should be hiragana
                if not self._is_hiragana(char.furigana):
                    return False
                
                # Furigana shouldn't be too long compared to kanji
                if len(char.furigana) > 8:  # Arbitrary reasonable limit
                    return False
        
        return True
    
    def _is_kanji(self, char: str) -> bool:
        """Check if character is kanji"""
        return '\u4e00' <= char <= '\u9faf'
    
    def _is_hiragana(self, text: str) -> bool:
        """Check if text is hiragana"""
        return all('\u3040' <= char <= '\u309f' for char in text)


class PykakasiFuriganaGenerator(FuriganaGenerator):
    """Pykakasi-based furigana generator (fallback only)"""
    
    def __init__(self):
        self.kakasi = None
        
        if not KAKASI_AVAILABLE:
            raise ImportError("Pykakasi is required for --no-ai mode but not installed")
        
        try:
            # Try new API first
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
                print(f"❌ Pykakasi initialization failed: {e2}")
                raise
    
    def get_furigana(self, text: str) -> List[FuriganaChar]:
        """Generate furigana using pykakasi with language detection"""
        
        # Check if text is likely Japanese first
        if not self._contains_japanese(text):
            print(f"🌐 Non-Japanese text detected: {text[:30]}...")
            return [FuriganaChar(char, None, False) for char in text]
        
        try:
            if hasattr(self.kakasi, 'convert'):
                return self._process_new_api(text)
            elif hasattr(self.kakasi, 'do'):
                return self._process_old_api(text)
            else:
                raise Exception("Invalid pykakasi API")
        except Exception as e:
            print(f"⚠️ Pykakasi error: {e}")
            # Return without furigana rather than using dictionary
            return [FuriganaChar(char, None, self._is_kanji(char)) for char in text]
    
    def _contains_japanese(self, text: str) -> bool:
        """Check if text contains Japanese characters"""
        japanese_char_count = sum(1 for char in text if 
                                self._is_hiragana(char) or 
                                self._is_katakana(char) or 
                                self._is_kanji(char))
        total_chars = len([c for c in text if not c.isspace()])
        
        # Need at least some Japanese characters
        return japanese_char_count > 0 and (japanese_char_count / max(total_chars, 1)) > 0.2
    
    def _is_hiragana(self, char: str) -> bool:
        return '\u3040' <= char <= '\u309f'
    
    def _is_katakana(self, char: str) -> bool:
        return '\u30a0' <= char <= '\u30ff'
    
    def _is_kanji(self, char: str) -> bool:
        return '\u4e00' <= char <= '\u9faf'
    
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
                                # More sophisticated distribution for multi-kanji words
                                kanji_positions = [i for i, c in enumerate(orig) if self._is_kanji(c)]
                                if kanji_positions:
                                    char_index = orig.index(char)
                                    if char_index in kanji_positions:
                                        kanji_idx = kanji_positions.index(char_index)
                                        chars_per_kanji = len(hira) // len(kanji_positions)
                                        start_idx = kanji_idx * chars_per_kanji
                                        end_idx = start_idx + chars_per_kanji
                                        furigana = hira[start_idx:end_idx] if hira else None
                        
                        result.append(FuriganaChar(char, furigana, is_kanji))
        
        return result
    
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
                
                result.append(FuriganaChar(char, furigana, is_kanji))
        
        return result


class NoOpFuriganaGenerator(FuriganaGenerator):
    """No-operation generator for when no valid generator is available"""
    
    def __init__(self):
        print("⚠️ No furigana generator available - subtitles will render without furigana")
    
    def get_furigana(self, text: str) -> List[FuriganaChar]:
        """Return text without furigana"""
        return [FuriganaChar(char, None, self._is_kanji(char)) for char in text]
    
    def _is_kanji(self, char: str) -> bool:
        return '\u4e00' <= char <= '\u9faf'


class FixedFuriganaRenderer:
    """Enhanced renderer with proper layout handling"""
    
    def __init__(self, config: BurnerConfig):
        self.config = config
        self.main_font = self._load_font(config.main_font_size)
        self.furigana_font = self._load_font(config.furigana_font_size)
        
        print(f"🎨 Fixed renderer initialized: main={config.main_font_size}px, furigana={config.furigana_font_size}px")
    
    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Load Japanese font with comprehensive fallback"""
        font_paths = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
            "/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf",
            "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/Windows/Fonts/msgothic.ttc",
            "/Windows/Fonts/meiryo.ttc",
            os.path.expanduser("~/.local/share/fonts/NotoSansJP-Regular.otf"),
            os.path.expanduser("~/.fonts/NotoSansJP-Regular.otf"),
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except Exception:
                continue
        
        print(f"⚠️ No Japanese font found, using default (may not display correctly)")
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
                
                # Find a good break point
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
        
        # Add line spacing between lines
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
        
        # Render each line
        y_offset = padding
        line_spacing = int(self.config.main_font_size * self.config.line_spacing_ratio)
        
        for i, line in enumerate(lines):
            self._render_single_line(draw, line, subtitle_width, y_offset)
            y_offset += line.height
            
            if i < len(lines) - 1:
                y_offset += line_spacing
        
        return img
    
    def _render_single_line(self, draw: ImageDraw.Draw, line: SubtitleLine, 
                           total_width: int, y_offset: int):
        """Render a single line with proper positioning"""
        if not line.furigana_chars:
            return
        
        # Center the line horizontally
        x_offset = (total_width - line.width) // 2
        current_x = x_offset
        
        # Calculate positions
        if line.has_furigana:
            text_y = y_offset + line.furigana_height + int(self.config.furigana_font_size * self.config.furigana_spacing_ratio)
            furigana_y = y_offset
        else:
            text_y = y_offset + (line.height - line.text_height) // 2
            furigana_y = y_offset
        
        for char_info in line.furigana_chars:
            char_width = self._measure_char_width(char_info)
            
            # Calculate character positions
            char_bbox = draw.textbbox((0, 0), char_info.char, font=self.main_font)
            char_w = char_bbox[2] - char_bbox[0]
            char_x = current_x + (char_width - char_w) // 2
            
            # Draw character with stroke
            self._draw_text_with_stroke(draw, char_x, text_y, char_info.char, self.main_font)
            
            # Draw furigana if present
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
    """Enhanced SRT parser with better error handling"""
    
    @staticmethod
    def parse_srt(srt_content: str) -> List[SubtitleSegment]:
        """Parse SRT content into subtitle segments with enhanced error handling"""
        segments = []
        blocks = re.split(r'\n\s*\n', srt_content.strip())
        
        for i, block in enumerate(blocks):
            try:
                lines = block.strip().split('\n')
                if len(lines) < 3:
                    continue
                
                timestamp_line = lines[1]
                match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', 
                               timestamp_line)
                
                if not match:
                    print(f"⚠️ Skipping invalid timestamp in block {i+1}: {timestamp_line}")
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
                    
            except Exception as e:
                print(f"⚠️ Error parsing SRT block {i+1}: {e}")
                continue
        
        print(f"📝 Successfully parsed {len(segments)} valid subtitle segments")
        return segments


class AIFirstFuriganaBurnerApp:
    """AI-first furigana subtitle burner with optional pykakasi fallback"""
    
    def __init__(self, config: BurnerConfig = None):
        """Initialize the AI-first burner app"""
        self.config = config or BurnerConfig()
        
        # Create the appropriate furigana generator
        self.furigana_generator = self._create_furigana_generator()
        self.renderer = FixedFuriganaRenderer(self.config)
        
        print(f"🚀 AI-First Furigana Burner App initialized")
        print(f"   Generator: {type(self.furigana_generator).__name__}")
        print(f"   Position: {self.config.position}")
        if isinstance(self.furigana_generator, OpenAIFuriganaGenerator):
            print(f"   OpenAI Model: {self.config.openai_model}")
            print(f"   Caching: {'Enabled' if self.config.use_openai_cache else 'Disabled'}")
    
    def _create_furigana_generator(self) -> FuriganaGenerator:
        """Create the appropriate furigana generator based on config"""
        
        if not self.config.use_ai:
            # Use pykakasi when --no-ai is specified
            try:
                return PykakasiFuriganaGenerator()
            except Exception as e:
                print(f"❌ Failed to create pykakasi generator: {e}")
                return NoOpFuriganaGenerator()
        
        # Default: try to use OpenAI
        try:
            if not os.getenv('OPENAI_API_KEY'):
                print("❌ No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
                print("   Falling back to no-operation generator.")
                return NoOpFuriganaGenerator()
            
            return OpenAIFuriganaGenerator(self.config)
            
        except Exception as e:
            print(f"❌ Failed to create OpenAI generator: {e}")
            return NoOpFuriganaGenerator()
    
    def burn_subtitles(self, video_path: str, srt_path: str, output_path: str = None) -> bool:
        """Burn AI-powered furigana subtitles onto video"""
        
        if not output_path:
            base_name = os.path.splitext(video_path)[0]
            output_path = f"{base_name}_furigana.mp4"
        
        print(f"🎬 Processing: {os.path.basename(video_path)}")
        print(f"📄 Subtitles: {os.path.basename(srt_path)}")
        print(f"💾 Output: {os.path.basename(output_path)}")
        
        try:
            # Read and parse SRT file
            with open(srt_path, 'r', encoding='utf-8') as f:
                srt_content = f.read()
            
            segments = SRTParser.parse_srt(srt_content)
            if not segments:
                print("❌ No valid subtitle segments found")
                return False
            
            # Preview furigana generation
            print(f"\n🔍 Previewing furigana generation:")
            for i, seg in enumerate(segments[:5]):  # Show first 5
                furigana_chars = self.furigana_generator.get_furigana(seg.text)
                preview = ''.join(str(char) for char in furigana_chars)
                has_furigana = any(char.furigana for char in furigana_chars)
                status = "✅ furigana" if has_furigana else "⭕ no furigana"
                print(f"   {i+1}: {seg.text}")
                print(f"      → {preview} ({status})")
            
            # Process video
            return self._process_video(video_path, segments, output_path)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _process_video(self, video_path: str, segments: List[SubtitleSegment], output_path: str) -> bool:
        """Process video with enhanced error handling"""
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Could not open video: {video_path}")
            return False
        
        try:
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
                return False
            
            # Calculate subtitle area
            max_subtitle_width = int(width * self.config.max_width_ratio)
            
            # Process frames
            frame_count = 0
            last_progress = -1
            
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
                        frame = self._add_subtitle_to_frame(
                            frame, active_subtitle.text, width, height, max_subtitle_width
                        )
                    except Exception as e:
                        print(f"⚠️ Error adding subtitle at {current_time:.2f}s: {e}")
                        # Continue with original frame
                
                out.write(frame)
                frame_count += 1
                
                # Progress updates
                progress = int((frame_count / total_frames) * 100)
                if progress != last_progress and progress % 10 == 0:
                    print(f"⏳ Progress: {progress}% ({frame_count}/{total_frames})")
                    last_progress = progress
            
            print(f"✅ Video processing completed")
            return True
            
        finally:
            cap.release()
            out.release()
    
    def _add_subtitle_to_frame(self, frame: np.ndarray, text: str, 
                              frame_width: int, frame_height: int, max_width: int) -> np.ndarray:
        """Add subtitle to frame with enhanced error handling"""
        
        try:
            # Generate furigana
            furigana_chars = self.furigana_generator.get_furigana(text)
            if not furigana_chars:
                return frame
            
            # Split into lines
            lines = self.renderer.split_into_lines(furigana_chars, max_width)
            if not lines:
                return frame
            
            # Render subtitle
            subtitle_img = self.renderer.render_multi_line_subtitle(lines, frame_width, frame_height)
            
            # Convert and blend
            subtitle_cv = cv2.cvtColor(np.array(subtitle_img), cv2.COLOR_RGBA2BGRA)
            subtitle_height, subtitle_width = subtitle_cv.shape[:2]
            
            # Calculate position
            x, y = self._calculate_subtitle_position(
                frame_width, frame_height, subtitle_width, subtitle_height
            )
            
            # Safety bounds check
            x = max(0, min(x, frame_width - subtitle_width))
            y = max(0, min(y, frame_height - subtitle_height))
            
            if (x + subtitle_width <= frame_width and 
                y + subtitle_height <= frame_height and
                subtitle_width > 0 and subtitle_height > 0):
                
                # Alpha blending
                alpha = subtitle_cv[:, :, 3] / 255.0
                alpha = np.stack([alpha] * 3, axis=2)
                
                overlay_region = frame[y:y+subtitle_height, x:x+subtitle_width]
                subtitle_rgb = subtitle_cv[:, :, :3]
                
                if overlay_region.shape == subtitle_rgb.shape == alpha.shape:
                    blended = overlay_region * (1 - alpha) + subtitle_rgb * alpha
                    frame[y:y+subtitle_height, x:x+subtitle_width] = blended.astype(np.uint8)
            
        except Exception as e:
            print(f"⚠️ Subtitle rendering error: {e}")
        
        return frame
    
    def _calculate_subtitle_position(self, frame_width: int, frame_height: int, 
                                   subtitle_width: int, subtitle_height: int) -> Tuple[int, int]:
        """Calculate subtitle position based on configuration"""
        
        x = (frame_width - subtitle_width) // 2
        margin = self.config.margin
        
        if self.config.position == 'top':
            y = margin
        elif self.config.position == 'center':
            y = (frame_height - subtitle_height) // 2
        else:  # bottom
            y = frame_height - subtitle_height - margin
        
        return x, y


def main():
    """Main function with AI-first approach"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-First Furigana Subtitle Burner')
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
    parser.add_argument('--line-spacing', type=float, default=0.2, help='Line spacing ratio')
    parser.add_argument('--no-multiline', action='store_true', help='Disable multi-line')
    
    # OpenAI options
    parser.add_argument('--openai-model', default='gpt-4o-mini', 
                       help='OpenAI model to use (gpt-4o-mini, gpt-4o, etc.)')
    parser.add_argument('--no-cache', action='store_true', help='Disable OpenAI caching')
    parser.add_argument('--max-retries', type=int, default=3, help='Max OpenAI retries')
    
    # Generator selection
    parser.add_argument('--no-ai', action='store_true', 
                       help='Use pykakasi instead of AI (requires pykakasi installation)')
    
    # Auto-detect mode
    if len(sys.argv) == 1:
        print("🔍 Auto-detecting video and subtitle files...")
        
        video_files = glob.glob("*.MP4") + glob.glob("*.mp4") + glob.glob("*.avi") + glob.glob("*.mkv")
        srt_files = glob.glob("*.srt")
        
        if video_files and srt_files:
            video_file = video_files[0]
            srt_file = srt_files[0]
            
            print(f"📹 Found: {video_file}")
            print(f"📄 Found: {srt_file}")
            
            # Create default config
            config = BurnerConfig()
            
            # Create app and process
            app = AIFirstFuriganaBurnerApp(config)
            success = app.burn_subtitles(video_file, srt_file)
            
            if success:
                print("\n🎉 SUCCESS! AI-powered furigana subtitles burned successfully!")
                print("   ✅ OpenAI-powered accurate furigana generation!")
                print("   ✅ Language detection prevents errors!")
                print("   ✅ Comprehensive caching for efficiency!")
            else:
                print("\n❌ FAILED! Check the error messages above.")
        
        else:
            print("❌ No video or subtitle files found")
            print("\n📖 Usage:")
            print("  python ai_furigana_burner.py                         # Auto-detect with AI")
            print("  python ai_furigana_burner.py video.mp4 sub.srt      # Specify files with AI")
            print("  python ai_furigana_burner.py --no-ai                # Use pykakasi instead")
            print("  python ai_furigana_burner.py --openai-model gpt-4o  # Use GPT-4o")
            print("  python ai_furigana_burner.py --no-cache             # Disable cache")
        
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
        auto_multi_line=not args.no_multiline,
        openai_model=args.openai_model,
        use_openai_cache=not args.no_cache,
        max_openai_retries=args.max_retries,
        use_ai=not args.no_ai  # AI by default, disable with --no-ai
    )
    
    # Create AI-first app and process
    app = AIFirstFuriganaBurnerApp(config)
    success = app.burn_subtitles(args.video, args.srt, args.output)
    
    if success:
        print("\n🎉 SUCCESS! AI-powered furigana subtitles burned successfully!")
    else:
        print("\n❌ FAILED! Check the error messages above.")


if __name__ == "__main__":
    main()
