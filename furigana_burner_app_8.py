#!/usr/bin/env python3
"""
Complete AI-Enhanced Furigana Subtitle Burner - Fixed Version
Features:
- Line-level furigana processing (not word-level)
- Pykakasi preprocessing + AI refinement 
- JSON format support with proper argument handling
- Fancy color palettes for colorful rendering
- Fixed JSON schema validation
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import re
import os
import sys
import glob
import json
import random
import colorsys
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
from abc import ABC, abstractmethod

# Import the OpenAI request handler
from openai_request import OpenAIRequestJSONBase

# Japanese text processing libraries
try:
    import pykakasi
    KAKASI_AVAILABLE = True
except ImportError:
    KAKASI_AVAILABLE = False
    print("Warning: pykakasi not available, falling back to AI-only mode")


@dataclass
class FuriganaChar:
    """Represents a character with its furigana and color"""
    char: str
    furigana: Optional[str]
    color: Tuple[int, int, int]
    is_kanji: bool


@dataclass
class SubtitleSegment:
    start_time: float
    end_time: float
    text: str
    lang: Optional[str] = None
    furigana_chars: Optional[List[FuriganaChar]] = None


@dataclass
class BurnerConfig:
    main_font_size: int = 64
    furigana_font_size: int = 32
    position: str = 'bottom'
    margin: int = 60
    max_width_ratio: float = 0.85
    line_spacing_ratio: float = 0.2
    stroke_width: int = 2
    background_opacity: float = 0.3
    auto_multi_line: bool = True
    furigana_spacing_ratio: float = 0.3
    openai_model: str = "gpt-4o-mini"
    use_openai_cache: bool = True
    max_openai_retries: int = 3
    use_ai: bool = True
    # Color palette settings
    use_fancy_colors: bool = True
    color_palette: str = "rainbow"  # "rainbow", "warm", "cool", "pastel", "neon"


class ColorPalette:
    """Generates fancy color palettes"""
    
    @staticmethod
    def generate_palette(palette_type: str, num_colors: int) -> List[Tuple[int, int, int]]:
        """Generate a color palette of specified type"""
        
        if palette_type == "rainbow":
            return ColorPalette._rainbow_palette(num_colors)
        elif palette_type == "warm":
            return ColorPalette._warm_palette(num_colors)
        elif palette_type == "cool":
            return ColorPalette._cool_palette(num_colors)
        elif palette_type == "pastel":
            return ColorPalette._pastel_palette(num_colors)
        elif palette_type == "neon":
            return ColorPalette._neon_palette(num_colors)
        else:
            return ColorPalette._rainbow_palette(num_colors)
    
    @staticmethod
    def _rainbow_palette(num_colors: int) -> List[Tuple[int, int, int]]:
        """Generate rainbow colors"""
        colors = []
        for i in range(num_colors):
            hue = i / max(num_colors, 1)
            rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.95)
            colors.append(tuple(int(c * 255) for c in rgb))
        return colors
    
    @staticmethod
    def _warm_palette(num_colors: int) -> List[Tuple[int, int, int]]:
        """Generate warm colors (reds, oranges, yellows)"""
        colors = []
        for i in range(num_colors):
            hue = (i / max(num_colors, 1)) * 0.17  # 0-60 degrees
            saturation = 0.7 + (i % 3) * 0.1
            value = 0.9
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            colors.append(tuple(int(c * 255) for c in rgb))
        return colors
    
    @staticmethod
    def _cool_palette(num_colors: int) -> List[Tuple[int, int, int]]:
        """Generate cool colors (blues, greens, purples)"""
        colors = []
        for i in range(num_colors):
            hue = 0.33 + (i / max(num_colors, 1)) * 0.5  # 120-300 degrees
            saturation = 0.7 + (i % 3) * 0.1
            value = 0.9
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            colors.append(tuple(int(c * 255) for c in rgb))
        return colors
    
    @staticmethod
    def _pastel_palette(num_colors: int) -> List[Tuple[int, int, int]]:
        """Generate pastel colors"""
        colors = []
        for i in range(num_colors):
            hue = i / max(num_colors, 1)
            saturation = 0.4 + (i % 3) * 0.1  # Lower saturation
            value = 0.95
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            colors.append(tuple(int(c * 255) for c in rgb))
        return colors
    
    @staticmethod
    def _neon_palette(num_colors: int) -> List[Tuple[int, int, int]]:
        """Generate neon/electric colors"""
        neon_colors = [
            (255, 20, 147),   # Deep pink
            (0, 255, 255),    # Cyan
            (50, 205, 50),    # Lime green  
            (255, 69, 0),     # Red orange
            (138, 43, 226),   # Blue violet
            (255, 215, 0),    # Gold
            (255, 105, 180),  # Hot pink
            (0, 250, 154),    # Medium spring green
        ]
        
        colors = []
        for i in range(num_colors):
            colors.append(neon_colors[i % len(neon_colors)])
        return colors


class HybridLineFuriganaGenerator:
    """Hybrid generator using pykakasi preprocessing + AI refinement for complete lines"""
    
    def __init__(self, config: BurnerConfig):
        self.config = config
        
        # Initialize pykakasi
        self.kakasi = None
        if KAKASI_AVAILABLE:
            try:
                self.kakasi = pykakasi.kakasi()
                print("✅ Pykakasi initialized for preprocessing")
            except Exception as e:
                print(f"⚠️ Pykakasi initialization failed: {e}")
        
        # Initialize OpenAI
        try:
            self.openai_client = OpenAIRequestJSONBase(
                use_cache=config.use_openai_cache,
                max_retries=config.max_openai_retries,
                cache_dir='furigana_cache'
            )
            print("✅ OpenAI client initialized for refinement")
        except Exception as e:
            print(f"❌ OpenAI initialization failed: {e}")
            self.openai_client = None
        
        # Fixed schema for line-level furigana (all properties required)
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
                "character_furigana": {
                    "type": "array",
                    "description": "Array of character-furigana pairs for characters that need readings",
                    "items": {
                        "type": "object",
                        "properties": {
                            "character": {
                                "type": "string",
                                "description": "The kanji character"
                            },
                            "reading": {
                                "type": "string",
                                "description": "The correct hiragana reading"
                            },
                            "position": {
                                "type": "integer",
                                "description": "Character position in original text"
                            }
                        },
                        "required": ["character", "reading", "position"],
                        "additionalProperties": False
                    }
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Overall confidence in the furigana analysis"
                }
            },
            "required": ["is_japanese", "original_text", "character_furigana", "confidence"],
            "additionalProperties": False
        }
    
    def get_line_furigana(self, text: str, lang_hint: Optional[str] = None) -> List[FuriganaChar]:
        """Generate line-level furigana using hybrid approach - FIXED VERSION"""
        
        if not text or len(text.strip()) < 1:
            return []
        
        # Check language hint
        if lang_hint and lang_hint.lower() not in ['ja', 'japanese', 'jpn']:
            print(f"🌐 Non-Japanese language ({lang_hint}): {text[:30]}...")
            return self._create_plain_chars(text)
        
        try:
            # Step 1: Pykakasi preprocessing (keep as fallback)
            pykakasi_result = self._get_pykakasi_preprocessing(text)
            
            # Step 2: AI refinement (word-based approach)
            word_mappings = self._get_ai_refinement(text, pykakasi_result)
            
            # Step 3: Create character info with colors
            chars = self._create_furigana_chars(text, word_mappings)
            
            readings_count = len([c for c in chars if c.furigana])
            print(f"✅ Hybrid furigana: {text[:30]}... ({readings_count} items with readings)")
            return chars
            
        except Exception as e:
            print(f"⚠️ Hybrid processing error: {e}")
            return self._create_plain_chars(text)
    
    def _get_pykakasi_preprocessing(self, text: str) -> Dict[str, str]:
        """Get pykakasi preprocessing results"""
        
        if not self.kakasi:
            return {}
        
        try:
            result = self.kakasi.convert(text)
            char_readings = {}
            
            if isinstance(result, list):
                char_pos = 0
                for item in result:
                    if isinstance(item, dict):
                        orig = item.get('orig', '')
                        hira = item.get('hira', '')
                        
                        # Process each character in this segment
                        if orig and hira and orig != hira:
                            for i, char in enumerate(orig):
                                if self._is_kanji(char):
                                    # Simple distribution of reading
                                    if len(orig) == 1:
                                        char_readings[char_pos] = hira
                                    else:
                                        # For multi-character segments, use the full reading for first kanji
                                        if i == 0:
                                            char_readings[char_pos] = hira
                                char_pos += 1
                        else:
                            char_pos += len(orig)
            
            print(f"🔧 Pykakasi preprocessing found {len(char_readings)} character readings")
            return char_readings
            
        except Exception as e:
            print(f"⚠️ Pykakasi preprocessing error: {e}")
            return {}
    
    def _get_ai_refinement(self, text: str, pykakasi_readings: Dict[str, str]) -> Dict[int, str]:
        """Get AI refinement of pykakasi results"""
        
        if not self.openai_client:
            print("⚠️ No OpenAI client, using pykakasi results as-is")
            return pykakasi_readings
        
        try:
            # Create context about pykakasi suggestions
            pykakasi_suggestions = []
            for pos, reading in pykakasi_readings.items():
                if pos < len(text):
                    char = text[pos]
                    pykakasi_suggestions.append(f"Position {pos}: '{char}' → '{reading}'")
            
            pykakasi_context = "\n".join(pykakasi_suggestions) if pykakasi_suggestions else "No suggestions from preprocessing"
            
            system_prompt = """You are a Japanese language expert specializing in accurate furigana generation.

Your task is to provide accurate hiragana readings for kanji characters in the given text.

Guidelines:
- Consider context for proper readings (not just dictionary readings)
- Handle compound kanji correctly (e.g., 今日 = きょう as a unit)
- Provide character-position mappings for accurate placement
- Focus on contextually appropriate readings
- Correct any inaccurate preprocessing suggestions"""

            user_prompt = f"""Analyze this Japanese text and provide accurate character-level furigana:

Original text: "{text}"

Preprocessing suggestions:
{pykakasi_context}

Please provide:
1. Whether this is Japanese text that needs furigana
2. For each kanji character that needs furigana:
   - The exact character
   - Its position in the original text (0-based index)
   - The correct hiragana reading based on context
3. Your overall confidence in the analysis

Focus on accuracy and contextual appropriateness."""

            cache_filename = f"line_furigana_{abs(hash(text + str(len(pykakasi_readings))))}.json"
            
            result = self.openai_client.send_request_with_json_schema(
                prompt=user_prompt,
                json_schema=self.furigana_schema,
                system_content=system_prompt,
                filename=cache_filename,
                schema_name="line_furigana_analysis",
                model=self.config.openai_model
            )
            
            if result and result.get('is_japanese', False):
                # Extract refined readings
                refined_readings = {}
                for char_info in result.get('character_furigana', []):
                    pos = char_info.get('position', -1)
                    reading = char_info.get('reading', '').strip()
                    
                    if pos >= 0 and pos < len(text) and reading:
                        refined_readings[pos] = reading
                
                print(f"🤖 AI refinement: {len(refined_readings)} character readings (confidence: {result.get('confidence', 0):.2f})")
                return refined_readings
            else:
                print("⚠️ AI refinement failed, using pykakasi results")
                return pykakasi_readings
                
        except Exception as e:
            print(f"⚠️ AI refinement error: {e}")
            return pykakasi_readings
    
    def _create_furigana_chars(self, text: str, readings: Dict[int, str]) -> List[FuriganaChar]:
        """Create FuriganaChar list with colors"""
        
        # Generate color palette
        if self.config.use_fancy_colors:
            colors = ColorPalette.generate_palette(self.config.color_palette, len(text))
        else:
            colors = [(255, 255, 255)] * len(text)  # White
        
        chars = []
        
        for i, char in enumerate(text):
            furigana = readings.get(i)
            is_kanji = self._is_kanji(char)
            color = colors[i % len(colors)] if colors else (255, 255, 255)
            
            chars.append(FuriganaChar(
                char=char,
                furigana=furigana if is_kanji else None,
                color=color,
                is_kanji=is_kanji
            ))
        
        return chars
    
    def _create_plain_chars(self, text: str) -> List[FuriganaChar]:
        """Create plain character list without furigana"""
        
        # Use single color for non-Japanese text
        color = (255, 255, 255)
        
        return [
            FuriganaChar(
                char=char,
                furigana=None,
                color=color,
                is_kanji=False
            ) 
            for char in text
        ]
    
    def _is_kanji(self, char: str) -> bool:
        """Check if character is kanji"""
        return '\u4e00' <= char <= '\u9faf'


class SubtitleParser:
    """Parser for JSON and SRT subtitle formats with proper encoding detection"""
    
    @staticmethod
    def parse_subtitles(file_path: str) -> List[SubtitleSegment]:
        """Parse subtitle file with proper encoding detection"""
        
        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'shift_jis', 'euc-jp', 'cp932']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read().strip()
                
                # Determine format based on file extension and content
                if file_path.lower().endswith('.json') or content.startswith('[') or content.startswith('{'):
                    return SubtitleParser.parse_json_content(content)
                else:
                    return SubtitleParser.parse_srt_content(content)
                    
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"⚠️ Error with encoding {encoding}: {e}")
                continue
        
        print(f"❌ Could not decode file with any encoding: {file_path}")
        return []
    
    @staticmethod
    def parse_json_content(content: str) -> List[SubtitleSegment]:
        """Parse JSON content"""
        try:
            data = json.loads(content)
            segments = []
            
            if not isinstance(data, list):
                return []
            
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                start = item.get('start', '')
                end = item.get('end', '')
                text = item.get('text', '').strip()
                lang = item.get('lang')
                
                if not text:
                    continue
                
                start_time = SubtitleParser._parse_timestamp(start)
                end_time = SubtitleParser._parse_timestamp(end)
                
                if start_time is not None and end_time is not None:
                    segments.append(SubtitleSegment(start_time, end_time, text, lang))
            
            print(f"📝 Parsed {len(segments)} JSON subtitle segments")
            return segments
            
        except Exception as e:
            print(f"❌ JSON parsing error: {e}")
            return []
    
    @staticmethod
    def parse_srt_content(content: str) -> List[SubtitleSegment]:
        """Parse SRT content"""
        segments = []
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            try:
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
                    
            except Exception:
                continue
        
        print(f"📝 Parsed {len(segments)} SRT subtitle segments")
        return segments
    
    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> Optional[float]:
        """Parse timestamp to seconds"""
        try:
            if not timestamp_str:
                return None
                
            if ',' in timestamp_str:
                match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', timestamp_str)
                if match:
                    return (int(match.group(1)) * 3600 + 
                           int(match.group(2)) * 60 + 
                           int(match.group(3)) + 
                           int(match.group(4)) / 1000)
            else:
                parts = timestamp_str.split(':')
                if len(parts) == 3:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds_parts = parts[2].split('.')
                    seconds = int(seconds_parts[0])
                    milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
                    
                    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
            
            return None
            
        except Exception:
            return None


class ColorfulFuriganaRenderer:
    """Enhanced renderer with colorful character-based rendering"""
    
    def __init__(self, config: BurnerConfig):
        self.config = config
        self.main_font = self._load_font(config.main_font_size)
        self.furigana_font = self._load_font(config.furigana_font_size)
        
        print(f"🎨 Colorful renderer initialized: main={config.main_font_size}px, furigana={config.furigana_font_size}px")
    
    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Load Japanese font"""
        font_paths = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
            "/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf",
            "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/Windows/Fonts/msgothic.ttc",
            "/Windows/Fonts/meiryo.ttc",
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except Exception:
                continue
        
        return ImageFont.load_default()
    
    def render_colorful_subtitle(self, chars: List[FuriganaChar], frame_width: int, frame_height: int) -> Image.Image:
        """Render colorful subtitle with character-based colors"""
        
        if not chars:
            return Image.new('RGBA', (100, 50), (0, 0, 0, 0))
        
        # Calculate dimensions
        total_width, total_height = self._calculate_dimensions(chars)
        max_width = int(frame_width * self.config.max_width_ratio)
        
        # Handle multi-line if needed
        if total_width > max_width and self.config.auto_multi_line:
            return self._render_multi_line_colorful(chars, frame_width, frame_height, max_width)
        else:
            return self._render_single_line_colorful(chars, frame_width, frame_height)
    
    def _calculate_dimensions(self, chars: List[FuriganaChar]) -> Tuple[int, int]:
        """Calculate total dimensions needed"""
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        total_width = 0
        max_height = self.config.main_font_size
        
        for char_info in chars:
            char_bbox = temp_draw.textbbox((0, 0), char_info.char, font=self.main_font)
            char_width = char_bbox[2] - char_bbox[0]
            
            if char_info.furigana:
                furigana_bbox = temp_draw.textbbox((0, 0), char_info.furigana, font=self.furigana_font)
                furigana_width = furigana_bbox[2] - furigana_bbox[0]
                char_width = max(char_width, furigana_width)
                max_height = self.config.main_font_size + self.config.furigana_font_size + int(self.config.furigana_font_size * self.config.furigana_spacing_ratio)
            
            total_width += char_width
        
        return total_width, max_height
    
    def _render_single_line_colorful(self, chars: List[FuriganaChar], frame_width: int, frame_height: int) -> Image.Image:
        """Render single line with colorful characters"""
        
        total_width, total_height = self._calculate_dimensions(chars)
        
        padding = 20
        subtitle_width = total_width + 2 * padding
        subtitle_height = total_height + 2 * padding
        
        # Create image
        img = Image.new('RGBA', (subtitle_width, subtitle_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Background
        if self.config.background_opacity > 0:
            bg_alpha = int(255 * self.config.background_opacity)
            draw.rectangle([0, 0, subtitle_width, subtitle_height], 
                         fill=(0, 0, 0, bg_alpha))
        
        # Render characters
        current_x = padding
        text_y = padding
        furigana_y = padding
        
        # Calculate Y positions if we have furigana
        has_any_furigana = any(char.furigana for char in chars)
        if has_any_furigana:
            text_y = padding + self.config.furigana_font_size + int(self.config.furigana_font_size * self.config.furigana_spacing_ratio)
        
        for char_info in chars:
            char_width = self._render_char_at_position(draw, char_info, current_x, text_y, furigana_y, has_any_furigana)
            current_x += char_width
        
        return img
    
    def _render_multi_line_colorful(self, chars: List[FuriganaChar], frame_width: int, frame_height: int, max_width: int) -> Image.Image:
        """Render multi-line colorful subtitle"""
        
        # Split characters into lines
        lines = self._split_chars_into_lines(chars, max_width)
        
        # Calculate total height
        line_height = self.config.main_font_size
        if any(any(char.furigana for char in line) for line in lines):
            line_height += self.config.furigana_font_size + int(self.config.furigana_font_size * self.config.furigana_spacing_ratio)
        
        line_spacing = int(self.config.main_font_size * self.config.line_spacing_ratio)
        total_height = len(lines) * line_height + (len(lines) - 1) * line_spacing
        
        padding = 20
        subtitle_width = min(max_width + 2 * padding, frame_width - 40)
        subtitle_height = total_height + 2 * padding
        
        # Create image
        img = Image.new('RGBA', (subtitle_width, subtitle_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Background
        if self.config.background_opacity > 0:
            bg_alpha = int(255 * self.config.background_opacity)
            draw.rectangle([0, 0, subtitle_width, subtitle_height], 
                         fill=(0, 0, 0, bg_alpha))
        
        # Render each line
        current_y = padding
        
        for line in lines:
            line_width, _ = self._calculate_dimensions(line)
            start_x = (subtitle_width - line_width) // 2
            
            has_furigana = any(char.furigana for char in line)
            text_y = current_y
            furigana_y = current_y
            
            if has_furigana:
                text_y = current_y + self.config.furigana_font_size + int(self.config.furigana_font_size * self.config.furigana_spacing_ratio)
            
            current_x = start_x
            for char_info in line:
                char_width = self._render_char_at_position(draw, char_info, current_x, text_y, furigana_y, has_furigana)
                current_x += char_width
            
            current_y += line_height + line_spacing
        
        return img
    
    def _split_chars_into_lines(self, chars: List[FuriganaChar], max_width: int) -> List[List[FuriganaChar]]:
        """Split characters into lines based on max width"""
        lines = []
        current_line = []
        current_width = 0
        
        for char_info in chars:
            char_width = self._get_char_width(char_info)
            
            if current_width + char_width > max_width and current_line:
                lines.append(current_line)
                current_line = []
                current_width = 0
            
            current_line.append(char_info)
            current_width += char_width
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _get_char_width(self, char_info: FuriganaChar) -> int:
        """Get width needed for a character"""
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        char_bbox = temp_draw.textbbox((0, 0), char_info.char, font=self.main_font)
        char_width = char_bbox[2] - char_bbox[0]
        
        if char_info.furigana:
            furigana_bbox = temp_draw.textbbox((0, 0), char_info.furigana, font=self.furigana_font)
            furigana_width = furigana_bbox[2] - furigana_bbox[0]
            char_width = max(char_width, furigana_width)
        
        return char_width
    
    def _render_char_at_position(self, draw: ImageDraw.Draw, char_info: FuriganaChar, 
                               x: int, text_y: int, furigana_y: int, line_has_furigana: bool) -> int:
        """Render a single character at specified position and return its width"""
        
        char_width = self._get_char_width(char_info)
        
        # Calculate text position (center within char width)
        char_bbox = draw.textbbox((0, 0), char_info.char, font=self.main_font)
        text_width = char_bbox[2] - char_bbox[0]
        text_x = x + (char_width - text_width) // 2
        
        # Draw main character with color and stroke
        self._draw_colorful_text_with_stroke(draw, text_x, text_y, char_info.char, self.main_font, char_info.color)
        
        # Draw furigana if present
        if char_info.furigana and line_has_furigana:
            furigana_bbox = draw.textbbox((0, 0), char_info.furigana, font=self.furigana_font)
            furigana_width = furigana_bbox[2] - furigana_bbox[0]
            furigana_x = x + (char_width - furigana_width) // 2
            
            # Use slightly lighter version of char color for furigana
            furigana_color = self._lighten_color(char_info.color)
            self._draw_colorful_text_with_stroke(draw, furigana_x, furigana_y, char_info.furigana, self.furigana_font, furigana_color)
        
        return char_width
    
    def _draw_colorful_text_with_stroke(self, draw: ImageDraw.Draw, x: int, y: int, 
                                      text: str, font: ImageFont.FreeTypeFont, color: Tuple[int, int, int]):
        """Draw colorful text with stroke"""
        
        # Draw stroke (darker version of color)
        stroke_color = tuple(max(0, c // 3) for c in color)  # Darker stroke
        stroke_width = self.config.stroke_width
        
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx*dx + dy*dy <= stroke_width*stroke_width:
                    draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
        
        # Draw main text in color
        draw.text((x, y), text, font=font, fill=color)
    
    def _lighten_color(self, color: Tuple[int, int, int], factor: float = 0.7) -> Tuple[int, int, int]:
        """Lighten a color for furigana"""
        return tuple(min(255, int(c + (255 - c) * factor)) for c in color)


class SubtitleWriter:
    """Writer for saving enhanced subtitles"""
    
    @staticmethod
    def save_json_with_furigana(segments: List[SubtitleSegment], output_path: str) -> bool:
        """Save segments with furigana to JSON"""
        try:
            json_data = []
            
            for segment in segments:
                item = {
                    "start": SubtitleWriter._format_timestamp(segment.start_time),
                    "end": SubtitleWriter._format_timestamp(segment.end_time),
                    "text": segment.text
                }
                
                if segment.lang:
                    item["lang"] = segment.lang
                
                if segment.furigana_chars:
                    item["furigana_text"] = "".join([
                        f"{char.char}({char.furigana})" if char.furigana else char.char
                        for char in segment.furigana_chars
                    ])
                
                json_data.append(item)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Saved enhanced JSON: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")
            return False
    
    @staticmethod
    def save_srt_with_furigana(segments: List[SubtitleSegment], output_path: str) -> bool:
        """Save segments with furigana to SRT"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments, 1):
                    f.write(f"{i}\n")
                    f.write(f"{SubtitleWriter._format_timestamp(segment.start_time)} --> ")
                    f.write(f"{SubtitleWriter._format_timestamp(segment.end_time)}\n")
                    
                    if segment.furigana_chars:
                        furigana_text = "".join([
                            f"{char.char}({char.furigana})" if char.furigana else char.char
                            for char in segment.furigana_chars
                        ])
                        f.write(f"{furigana_text}\n\n")
                    else:
                        f.write(f"{segment.text}\n\n")
            
            print(f"💾 Saved enhanced SRT: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving SRT: {e}")
            return False
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format timestamp for SRT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class CompleteFuriganaBurnerApp:
    """Complete furigana burner with all features - FIXED VERSION"""
    
    def __init__(self, config: BurnerConfig = None):
        self.config = config or BurnerConfig()
        self.furigana_generator = HybridLineFuriganaGenerator(self.config)
        self.renderer = ColorfulFuriganaRenderer(self.config)
        
        print(f"🚀 Complete Furigana Burner App initialized")
        print(f"   Colors: {self.config.color_palette} palette")
        print(f"   Position: {self.config.position}")
    
    def process_video_with_subtitles(self, video_path: str, subtitle_path: str, output_path: str = None) -> bool:
        """Process video with enhanced furigana subtitles"""
        
        if not output_path:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = f"{base_name}_furigana.mp4"
        
        print(f"🎬 Processing: {os.path.basename(video_path)}")
        print(f"📄 Subtitles: {os.path.basename(subtitle_path)}")
        print(f"💾 Output: {os.path.basename(output_path)}")
        
        try:
            # Parse subtitles
            segments = SubtitleParser.parse_subtitles(subtitle_path)
            if not segments:
                return False
            
            # Process furigana for all segments
            print(f"\n🔍 Processing {len(segments)} segments with hybrid furigana...")
            
            for i, segment in enumerate(segments):
                chars = self.furigana_generator.get_line_furigana(segment.text, segment.lang)
                segment.furigana_chars = chars
                
                # Show preview for first few
                if i < 3:
                    furigana_preview = "".join([
                        f"{char.char}({char.furigana})" if char.furigana else char.char
                        for char in chars
                    ])
                    print(f"   {i+1}: {segment.text}")
                    print(f"      → {furigana_preview}")
            
            # Save enhanced subtitle files
            base_name = os.path.splitext(os.path.basename(subtitle_path))[0]
            output_dir = os.path.dirname(output_path) or '.'
            
            json_output = os.path.join(output_dir, f"{base_name}_furigana.json")
            srt_output = os.path.join(output_dir, f"{base_name}_furigana.srt")
            
            SubtitleWriter.save_json_with_furigana(segments, json_output)
            SubtitleWriter.save_srt_with_furigana(segments, srt_output)
            
            # Process video
            return self._burn_to_video(video_path, segments, output_path)
            
        except Exception as e:
            print(f"❌ Processing error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _burn_to_video(self, video_path: str, segments: List[SubtitleSegment], output_path: str) -> bool:
        """Burn colorful furigana subtitles to video"""
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            print(f"🎥 Video: {width}x{height}, {fps:.2f} fps, {total_frames} frames")
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frame_count = 0
            last_progress = -1
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                current_time = frame_count / fps
                
                # Find active subtitle
                active_segment = None
                for segment in segments:
                    if segment.start_time <= current_time <= segment.end_time:
                        active_segment = segment
                        break
                
                # Add colorful subtitle
                if active_segment and active_segment.furigana_chars:
                    try:
                        frame = self._add_colorful_subtitle_to_frame(
                            frame, active_segment.furigana_chars, width, height
                        )
                    except Exception as e:
                        print(f"⚠️ Subtitle error at {current_time:.2f}s: {e}")
                
                out.write(frame)
                frame_count += 1
                
                progress = int((frame_count / total_frames) * 100)
                if progress != last_progress and progress % 10 == 0:
                    print(f"⏳ Progress: {progress}% ({frame_count}/{total_frames})")
                    last_progress = progress
            
            print(f"✅ Video completed: {output_path}")
            return True
            
        finally:
            cap.release()
            out.release()
    
    def _add_colorful_subtitle_to_frame(self, frame: np.ndarray, chars: List[FuriganaChar], 
                                       frame_width: int, frame_height: int) -> np.ndarray:
        """Add colorful subtitle to frame"""
        
        try:
            subtitle_img = self.renderer.render_colorful_subtitle(chars, frame_width, frame_height)
            subtitle_cv = cv2.cvtColor(np.array(subtitle_img), cv2.COLOR_RGBA2BGRA)
            subtitle_height, subtitle_width = subtitle_cv.shape[:2]
            
            # Calculate position
            x = (frame_width - subtitle_width) // 2
            margin = self.config.margin
            
            if self.config.position == 'top':
                y = margin
            elif self.config.position == 'center':
                y = (frame_height - subtitle_height) // 2
            else:  # bottom
                y = frame_height - subtitle_height - margin
            
            # Safety bounds
            x = max(0, min(x, frame_width - subtitle_width))
            y = max(0, min(y, frame_height - subtitle_height))
            
            # Alpha blend
            if (x + subtitle_width <= frame_width and 
                y + subtitle_height <= frame_height and
                subtitle_width > 0 and subtitle_height > 0):
                
                alpha = subtitle_cv[:, :, 3] / 255.0
                alpha = np.stack([alpha] * 3, axis=2)
                
                overlay_region = frame[y:y+subtitle_height, x:x+subtitle_width]
                subtitle_rgb = subtitle_cv[:, :, :3]
                
                if overlay_region.shape == subtitle_rgb.shape == alpha.shape:
                    blended = overlay_region * (1 - alpha) + subtitle_rgb * alpha
                    frame[y:y+subtitle_height, x:x+subtitle_width] = blended.astype(np.uint8)
            
        except Exception as e:
            print(f"⚠️ Colorful rendering error: {e}")
        
        return frame


def main():
    """Main function with FIXED argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Complete AI Furigana Subtitle Burner - FIXED')
    parser.add_argument('video', nargs='?', help='Input video file')  
    parser.add_argument('subtitles', nargs='?', help='Input subtitle file (JSON or SRT)')
    parser.add_argument('output', nargs='?', help='Output video file (optional)')
    
    # Configuration options
    parser.add_argument('--position', choices=['top', 'center', 'bottom'], 
                       default='bottom', help='Subtitle position')
    parser.add_argument('--main-font-size', type=int, default=64, help='Main font size')
    parser.add_argument('--furigana-font-size', type=int, default=32, help='Furigana font size')
    parser.add_argument('--color-palette', choices=['rainbow', 'warm', 'cool', 'pastel', 'neon'], 
                       default='rainbow', help='Color palette for characters')
    parser.add_argument('--no-colors', action='store_true', help='Disable fancy colors')
    parser.add_argument('--openai-model', default='gpt-4o-mini', help='OpenAI model')
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')
    
    # Auto-detect mode
    if len(sys.argv) == 1:
        print("🔍 Auto-detecting files...")
        
        video_files = glob.glob("*.mp4") + glob.glob("*.MP4") + glob.glob("*.avi") + glob.glob("*.mkv")
        subtitle_files = glob.glob("*.json") + glob.glob("*.srt")
        
        if video_files and subtitle_files:
            video_file = video_files[0]
            subtitle_file = subtitle_files[0]
            
            print(f"🎬 Found video: {video_file}")
            print(f"📄 Found subtitles: {subtitle_file}")
            
            config = BurnerConfig()
            app = CompleteFuriganaBurnerApp(config)
            success = app.process_video_with_subtitles(video_file, subtitle_file)
            
            if success:
                print("\n🎉 SUCCESS! Complete furigana processing finished!")
                print("   ✅ Pykakasi preprocessing + AI refinement!")
                print("   ✅ Colorful character-based rendering!")
                print("   ✅ Enhanced JSON and SRT output!")
            else:
                print("\n❌ FAILED! Check error messages above.")
        else:
            print("❌ No video or subtitle files found")
            print("\n📖 Usage:")
            print("  python furigana_burner_fixed.py                              # Auto-detect")
            print("  python furigana_burner_fixed.py video.mp4 subtitles.json    # Specify files")
            print("  python furigana_burner_fixed.py --color-palette neon         # Neon colors")
            print("  python furigana_burner_fixed.py --position top               # Top position")
        
        return
    
    args = parser.parse_args()
    
    # Create configuration
    config = BurnerConfig(
        position=args.position,
        main_font_size=args.main_font_size,
        furigana_font_size=args.furigana_font_size,
        color_palette=args.color_palette,
        use_fancy_colors=not args.no_colors,
        openai_model=args.openai_model,
        use_openai_cache=not args.no_cache
    )
    
    # Process
    app = CompleteFuriganaBurnerApp(config)
    success = app.process_video_with_subtitles(args.video, args.subtitles, args.output)
    
    if success:
        print("\n🎉 SUCCESS! Complete furigana processing finished!")
    else:
        print("\n❌ FAILED! Check error messages above.")


if __name__ == "__main__":
    main()
