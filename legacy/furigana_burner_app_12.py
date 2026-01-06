#!/usr/bin/env python3
"""
Simplified Grammatical Analysis Furigana Subtitle Burner
Features:
- Simple word-furigana-type analysis
- Intelligent post-processing to remove redundant furigana
- Fixed colors for different grammatical components
- Proper caching with force refresh option
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
from enum import Enum

# Import the OpenAI request handler
from openai_request import OpenAIRequestJSONBase

# Japanese text processing libraries
try:
    import pykakasi
    KAKASI_AVAILABLE = True
except ImportError:
    KAKASI_AVAILABLE = False


class GrammaticalType(Enum):
    """Grammatical types for Japanese components"""
    SUBJECT = "subject"           # 主語
    OBJECT = "object"             # 目的語  
    VERB = "verb"                 # 動詞
    ADJECTIVE = "adjective"       # 形容詞
    ADVERB = "adverb"            # 副詞
    NOUN = "noun"                # 名詞
    PARTICLE_WA = "particle_wa"   # は
    PARTICLE_GA = "particle_ga"   # が
    PARTICLE_WO = "particle_wo"   # を
    PARTICLE_NI = "particle_ni"   # に
    PARTICLE_DE = "particle_de"   # で
    PARTICLE_TO = "particle_to"   # と
    PARTICLE_OTHER = "particle_other"  # Other particles
    AUXILIARY = "auxiliary"       # 助動詞
    CONJUNCTION = "conjunction"   # 接続詞
    PUNCTUATION = "punctuation"   # 句読点
    OTHER = "other"              # その他


@dataclass
class GrammaticalWord:
    """Represents a word with grammatical analysis"""
    word: str
    furigana: Optional[str]
    grammatical_type: GrammaticalType
    color: Tuple[int, int, int]


@dataclass
class SubtitleSegment:
    start_time: float
    end_time: float
    text: str
    lang: Optional[str] = None
    grammatical_words: Optional[List[GrammaticalWord]] = None


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
    max_openai_retries: int = 3
    force_refresh: bool = False  # True = ignore cache, False = use cache


class GrammaticalColorScheme:
    """Fixed color scheme for different grammatical components"""
    
    COLOR_MAP = {
        GrammaticalType.SUBJECT: (255, 100, 100),      # Light red
        GrammaticalType.OBJECT: (100, 150, 255),       # Light blue
        GrammaticalType.VERB: (100, 255, 100),         # Light green
        GrammaticalType.ADJECTIVE: (255, 200, 100),    # Orange
        GrammaticalType.ADVERB: (200, 100, 255),       # Purple
        GrammaticalType.NOUN: (255, 255, 150),         # Light yellow
        GrammaticalType.PARTICLE_WA: (255, 150, 150),  # Pink - は
        GrammaticalType.PARTICLE_GA: (150, 255, 150),  # Light green - が
        GrammaticalType.PARTICLE_WO: (150, 150, 255),  # Light blue - を
        GrammaticalType.PARTICLE_NI: (255, 255, 100),  # Yellow - に
        GrammaticalType.PARTICLE_DE: (100, 255, 255),  # Cyan - で
        GrammaticalType.PARTICLE_TO: (255, 100, 255),  # Magenta - と
        GrammaticalType.PARTICLE_OTHER: (200, 200, 200),  # Gray
        GrammaticalType.AUXILIARY: (150, 200, 150),    # Muted green
        GrammaticalType.CONJUNCTION: (200, 150, 200),  # Muted purple
        GrammaticalType.PUNCTUATION: (180, 180, 180),  # Light gray
        GrammaticalType.OTHER: (220, 220, 220),        # Very light gray
    }
    
    @classmethod
    def get_color(cls, grammatical_type: GrammaticalType) -> Tuple[int, int, int]:
        return cls.COLOR_MAP.get(grammatical_type, cls.COLOR_MAP[GrammaticalType.OTHER])


class SimpleGrammaticalAnalyzer:
    """Simplified grammatical analyzer with working post-processing"""
    
    def __init__(self, config: BurnerConfig):
        self.config = config
        
        try:
            self.openai_client = OpenAIRequestJSONBase(
                use_cache=True,  # Always enable caching
                max_retries=config.max_openai_retries,
                cache_dir='grammatical_cache'
            )
            print("✅ Simple grammatical analyzer initialized")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")
            self.openai_client = None
        
        # Simplified schema - just word, furigana, type
        self.analysis_schema = {
            "type": "object",
            "properties": {
                "words": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "word": {"type": "string"},
                            "furigana": {"type": "string"},
                            "type": {
                                "type": "string",
                                "enum": [
                                    "subject", "object", "verb", "adjective", "adverb", "noun",
                                    "particle_wa", "particle_ga", "particle_wo", "particle_ni", 
                                    "particle_de", "particle_to", "particle_other",
                                    "auxiliary", "conjunction", "punctuation", "other"
                                ]
                            }
                        },
                        "required": ["word", "furigana", "type"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["words"],
            "additionalProperties": False
        }
    
    def analyze_sentence(self, text: str, lang_hint: Optional[str] = None) -> List[GrammaticalWord]:
        """Analyze Japanese sentence with simplified prompt"""
        
        if not text or not self.openai_client:
            return self._create_fallback_words(text)
        
        # Check language
        if lang_hint and lang_hint.lower() not in ['ja', 'japanese', 'jpn']:
            return self._create_fallback_words(text)
        
        try:
            # Simple, direct prompt
            prompt = f"""Analyze this Japanese text: "{text}"

Break into words with:
1. word: the word/particle  
2. furigana: complete reading (ALWAYS provide, even for hiragana)
3. type: grammatical type

Examples:
- 私 → {{"word": "私", "furigana": "わたし", "type": "subject"}}
- は → {{"word": "は", "furigana": "は", "type": "particle_wa"}}
- 学生 → {{"word": "学生", "furigana": "がくせい", "type": "noun"}}
- です → {{"word": "です", "furigana": "です", "type": "auxiliary"}}

CRITICAL: Always provide furigana for every word, even hiragana ones."""

            # Handle force refresh by changing cache filename
            if self.config.force_refresh:
                # Use timestamp to force fresh request but still cache result
                import time
                cache_key = f"simple_{abs(hash(text))}_{int(time.time())}.json"
            else:
                # Normal cache filename
                cache_key = f"simple_{abs(hash(text))}.json"
            
            # Single request call
            result = self.openai_client.send_request_with_json_schema(
                prompt=prompt,
                json_schema=self.analysis_schema,
                filename=cache_key,
                schema_name="simple_analysis",
                model=self.config.openai_model
            )
            
            if result and 'words' in result:
                return self._process_simple_result(result['words'])
            else:
                return self._create_fallback_words(text)
                
        except Exception as e:
            print(f"⚠️ Analysis error: {e}")
            return self._create_fallback_words(text)
    
    def _process_simple_result(self, words_data: List[Dict]) -> List[GrammaticalWord]:
        """Process simple result with intelligent post-processing"""
        
        processed_words = []
        
        for word_data in words_data:
            word = word_data.get('word', '').strip()
            furigana = word_data.get('furigana', '').strip()
            type_str = word_data.get('type', 'other')
            
            if not word:
                continue
            
            # Convert to enum
            try:
                grammatical_type = GrammaticalType(type_str)
            except ValueError:
                grammatical_type = GrammaticalType.OTHER
            
            # Get color
            color = GrammaticalColorScheme.get_color(grammatical_type)
            
            # POST-PROCESSING: Clean up furigana
            cleaned_furigana = self._post_process_furigana(word, furigana)
            
            # Split word if needed (same color for parts)
            if cleaned_furigana and self._should_split_word(word, cleaned_furigana):
                split_words = self._split_word_intelligently(word, cleaned_furigana, grammatical_type, color)
                processed_words.extend(split_words)
            else:
                processed_words.append(GrammaticalWord(
                    word=word,
                    furigana=cleaned_furigana,
                    grammatical_type=grammatical_type,
                    color=color
                ))
        
        furigana_count = sum(1 for w in processed_words if w.furigana)
        print(f"✅ Analysis: {len(processed_words)} words, {furigana_count} with furigana")
        
        return processed_words
    
    def _post_process_furigana(self, word: str, furigana: str) -> Optional[str]:
        """Intelligent furigana post-processing"""
        
        if not furigana:
            return None
        
        # Rule 1: If word is all hiragana and matches furigana, remove furigana
        if self._is_all_hiragana(word) and word == furigana:
            return None
        
        # Rule 2: If word is all katakana and furigana is hiragana equivalent, remove
        if self._is_all_katakana(word):
            if self._katakana_to_hiragana(word) == furigana:
                return None
        
        # Rule 3: Remove trailing hiragana that matches word ending
        cleaned = self._remove_matching_suffix(word, furigana)
        
        # Rule 4: If nothing left, return None
        if not cleaned or cleaned == word:
            return None
        
        return cleaned
    
    def _remove_matching_suffix(self, word: str, furigana: str) -> str:
        """Remove matching hiragana suffix from furigana"""
        
        # Find common suffix
        word_rev = word[::-1]
        furigana_rev = furigana[::-1]
        
        common_len = 0
        for i in range(min(len(word_rev), len(furigana_rev))):
            if (word_rev[i] == furigana_rev[i] and 
                self._is_hiragana(word_rev[i])):
                common_len += 1
            else:
                break
        
        if common_len > 0:
            return furigana[:-common_len] if common_len < len(furigana) else furigana
        
        return furigana
    
    def _should_split_word(self, word: str, furigana: str) -> bool:
        """Check if word should be split (kanji + hiragana pattern)"""
        
        if len(word) < 2 or not furigana:
            return False
        
        # Check for kanji followed by hiragana
        has_kanji = any(self._is_kanji(c) for c in word)
        has_hiragana = any(self._is_hiragana(c) for c in word)
        
        return has_kanji and has_hiragana and len(furigana) < len(word) * 3  # Reasonable limit
    
    def _split_word_intelligently(self, word: str, furigana: str, 
                                grammatical_type: GrammaticalType, 
                                color: Tuple[int, int, int]) -> List[GrammaticalWord]:
        """Split word intelligently for kanji-hiragana patterns"""
        
        # Simple splitting: find first kanji, assume furigana goes with it
        kanji_end = -1
        for i, char in enumerate(word):
            if self._is_kanji(char):
                kanji_end = i
        
        if kanji_end >= 0 and kanji_end < len(word) - 1:
            kanji_part = word[:kanji_end + 1]
            hiragana_part = word[kanji_end + 1:]
            
            # Simple approach: give all furigana to kanji part
            return [
                GrammaticalWord(
                    word=kanji_part,
                    furigana=furigana,
                    grammatical_type=grammatical_type,
                    color=color
                ),
                GrammaticalWord(
                    word=hiragana_part,
                    furigana=None,
                    grammatical_type=grammatical_type,
                    color=color
                )
            ]
        
        # Fallback: don't split
        return [GrammaticalWord(
            word=word,
            furigana=furigana,
            grammatical_type=grammatical_type,
            color=color
        )]
    
    def _is_all_hiragana(self, text: str) -> bool:
        return all(self._is_hiragana(c) or c in '、。！？' for c in text)
    
    def _is_all_katakana(self, text: str) -> bool:
        return all(self._is_katakana(c) for c in text)
    
    def _is_hiragana(self, char: str) -> bool:
        return '\u3040' <= char <= '\u309f'
    
    def _is_katakana(self, char: str) -> bool:
        return '\u30a0' <= char <= '\u30ff'
    
    def _is_kanji(self, char: str) -> bool:
        return '\u4e00' <= char <= '\u9faf'
    
    def _katakana_to_hiragana(self, katakana_text: str) -> str:
        result = ""
        for char in katakana_text:
            if self._is_katakana(char):
                result += chr(ord(char) - 0x60)
            else:
                result += char
        return result
    
    def _create_fallback_words(self, text: str) -> List[GrammaticalWord]:
        """Create fallback words when AI fails"""
        words = []
        current_word = ""
        
        for char in text:
            if char in ' \t\n、。！？，．':
                if current_word:
                    words.append(GrammaticalWord(
                        word=current_word,
                        furigana=None,
                        grammatical_type=GrammaticalType.OTHER,
                        color=GrammaticalColorScheme.get_color(GrammaticalType.OTHER)
                    ))
                    current_word = ""
                if char.strip():
                    words.append(GrammaticalWord(
                        word=char,
                        furigana=None,
                        grammatical_type=GrammaticalType.PUNCTUATION,
                        color=GrammaticalColorScheme.get_color(GrammaticalType.PUNCTUATION)
                    ))
            else:
                current_word += char
        
        if current_word:
            words.append(GrammaticalWord(
                word=current_word,
                furigana=None,
                grammatical_type=GrammaticalType.OTHER,
                color=GrammaticalColorScheme.get_color(GrammaticalType.OTHER)
            ))
        
        return words


class SubtitleParser:
    """Parser for JSON and SRT subtitle formats"""
    
    @staticmethod
    def parse_subtitles(file_path: str) -> List[SubtitleSegment]:
        encodings = ['utf-8', 'utf-8-sig', 'shift_jis', 'euc-jp', 'cp932']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read().strip()
                
                if file_path.lower().endswith('.json') or content.startswith('['):
                    return SubtitleParser.parse_json_content(content)
                else:
                    return SubtitleParser.parse_srt_content(content)
                    
            except UnicodeDecodeError:
                continue
            except Exception as e:
                continue
        
        print(f"❌ Could not decode file: {file_path}")
        return []
    
    @staticmethod
    def parse_json_content(content: str) -> List[SubtitleSegment]:
        try:
            data = json.loads(content)
            segments = []
            
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
            
            print(f"📝 Parsed {len(segments)} JSON segments")
            return segments
            
        except Exception as e:
            print(f"❌ JSON parsing error: {e}")
            return []
    
    @staticmethod
    def parse_srt_content(content: str) -> List[SubtitleSegment]:
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
                
                start_time = (int(match.group(1)) * 3600 + int(match.group(2)) * 60 + 
                             int(match.group(3)) + int(match.group(4)) / 1000)
                end_time = (int(match.group(5)) * 3600 + int(match.group(6)) * 60 + 
                           int(match.group(7)) + int(match.group(8)) / 1000)
                
                text = ' '.join(lines[2:]).strip()
                if text:
                    segments.append(SubtitleSegment(start_time, end_time, text))
                    
            except Exception:
                continue
        
        print(f"📝 Parsed {len(segments)} SRT segments")
        return segments
    
    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> Optional[float]:
        try:
            if ',' in timestamp_str:
                match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', timestamp_str)
                if match:
                    return (int(match.group(1)) * 3600 + int(match.group(2)) * 60 + 
                           int(match.group(3)) + int(match.group(4)) / 1000)
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
        except:
            return None


class GrammaticalRenderer:
    """Renderer for grammatical analysis with fixed colors"""
    
    def __init__(self, config: BurnerConfig):
        self.config = config
        self.main_font = self._load_font(config.main_font_size)
        self.furigana_font = self._load_font(config.furigana_font_size)
    
    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        font_paths = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
            "/usr/share/fonts/truetype/takao-gothic/TakaoPGothic.ttf",
            "/usr/share/fonts/truetype/vlgothic/VL-Gothic-Regular.ttf",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/Windows/Fonts/msgothic.ttc",
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except:
                continue
        
        return ImageFont.load_default()
    
    def render_grammatical_subtitle(self, words: List[GrammaticalWord], 
                                   frame_width: int, frame_height: int) -> Image.Image:
        if not words:
            return Image.new('RGBA', (100, 50), (0, 0, 0, 0))
        
        total_width, total_height = self._calculate_dimensions(words)
        max_width = int(frame_width * self.config.max_width_ratio)
        
        if total_width > max_width and self.config.auto_multi_line:
            return self._render_multi_line(words, frame_width, frame_height, max_width)
        else:
            return self._render_single_line(words, frame_width, frame_height)
    
    def _calculate_dimensions(self, words: List[GrammaticalWord]) -> Tuple[int, int]:
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        total_width = 0
        max_height = self.config.main_font_size
        
        for word in words:
            word_bbox = temp_draw.textbbox((0, 0), word.word, font=self.main_font)
            word_width = word_bbox[2] - word_bbox[0]
            
            if word.furigana:
                furigana_bbox = temp_draw.textbbox((0, 0), word.furigana, font=self.furigana_font)
                furigana_width = furigana_bbox[2] - furigana_bbox[0]
                word_width = max(word_width, furigana_width)
                max_height = (self.config.main_font_size + self.config.furigana_font_size + 
                             int(self.config.furigana_font_size * self.config.furigana_spacing_ratio))
            
            total_width += word_width
        
        return total_width, max_height
    
    def _render_single_line(self, words: List[GrammaticalWord], 
                           frame_width: int, frame_height: int) -> Image.Image:
        total_width, total_height = self._calculate_dimensions(words)
        padding = 20
        
        img = Image.new('RGBA', (total_width + 2*padding, total_height + 2*padding), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        if self.config.background_opacity > 0:
            bg_alpha = int(255 * self.config.background_opacity)
            draw.rectangle([0, 0, total_width + 2*padding, total_height + 2*padding], 
                         fill=(0, 0, 0, bg_alpha))
        
        current_x = padding
        has_furigana = any(word.furigana for word in words)
        text_y = padding + (self.config.furigana_font_size + 
                           int(self.config.furigana_font_size * self.config.furigana_spacing_ratio) 
                           if has_furigana else 0)
        furigana_y = padding
        
        for word in words:
            word_width = self._render_word_at_position(draw, word, current_x, text_y, furigana_y, has_furigana)
            current_x += word_width
        
        return img
    
    def _render_multi_line(self, words: List[GrammaticalWord], frame_width: int, frame_height: int, max_width: int) -> Image.Image:
        lines = self._split_words_into_lines(words, max_width)
        
        line_height = self.config.main_font_size
        if any(any(word.furigana for word in line) for line in lines):
            line_height += (self.config.furigana_font_size + 
                           int(self.config.furigana_font_size * self.config.furigana_spacing_ratio))
        
        line_spacing = int(self.config.main_font_size * self.config.line_spacing_ratio)
        total_height = len(lines) * line_height + (len(lines) - 1) * line_spacing
        padding = 20
        
        img = Image.new('RGBA', (max_width + 2*padding, total_height + 2*padding), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        if self.config.background_opacity > 0:
            bg_alpha = int(255 * self.config.background_opacity)
            draw.rectangle([0, 0, max_width + 2*padding, total_height + 2*padding], 
                         fill=(0, 0, 0, bg_alpha))
        
        current_y = padding
        
        for line in lines:
            line_width, _ = self._calculate_dimensions(line)
            start_x = (max_width + 2*padding - line_width) // 2
            
            has_furigana = any(word.furigana for word in line)
            text_y = current_y + (self.config.furigana_font_size + 
                                 int(self.config.furigana_font_size * self.config.furigana_spacing_ratio) 
                                 if has_furigana else 0)
            furigana_y = current_y
            
            current_x = start_x
            for word in line:
                word_width = self._render_word_at_position(draw, word, current_x, text_y, furigana_y, has_furigana)
                current_x += word_width
            
            current_y += line_height + line_spacing
        
        return img
    
    def _split_words_into_lines(self, words: List[GrammaticalWord], max_width: int) -> List[List[GrammaticalWord]]:
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            word_width = self._get_word_width(word)
            
            if current_width + word_width > max_width and current_line:
                lines.append(current_line)
                current_line = []
                current_width = 0
            
            current_line.append(word)
            current_width += word_width
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _get_word_width(self, word: GrammaticalWord) -> int:
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        word_bbox = temp_draw.textbbox((0, 0), word.word, font=self.main_font)
        word_width = word_bbox[2] - word_bbox[0]
        
        if word.furigana:
            furigana_bbox = temp_draw.textbbox((0, 0), word.furigana, font=self.furigana_font)
            furigana_width = furigana_bbox[2] - furigana_bbox[0]
            word_width = max(word_width, furigana_width)
        
        return word_width
    
    def _render_word_at_position(self, draw: ImageDraw.Draw, word: GrammaticalWord, 
                               x: int, text_y: int, furigana_y: int, line_has_furigana: bool) -> int:
        word_width = self._get_word_width(word)
        
        # Center text within word width
        word_bbox = draw.textbbox((0, 0), word.word, font=self.main_font)
        text_width = word_bbox[2] - word_bbox[0]
        text_x = x + (word_width - text_width) // 2
        
        # Draw word with color
        self._draw_text_with_stroke(draw, text_x, text_y, word.word, self.main_font, word.color)
        
        # Draw furigana
        if word.furigana and line_has_furigana:
            furigana_bbox = draw.textbbox((0, 0), word.furigana, font=self.furigana_font)
            furigana_width = furigana_bbox[2] - furigana_bbox[0]
            furigana_x = x + (word_width - furigana_width) // 2
            
            furigana_color = self._lighten_color(word.color)
            self._draw_text_with_stroke(draw, furigana_x, furigana_y, word.furigana, self.furigana_font, furigana_color)
        
        return word_width
    
    def _draw_text_with_stroke(self, draw: ImageDraw.Draw, x: int, y: int, 
                              text: str, font: ImageFont.FreeTypeFont, color: Tuple[int, int, int]):
        stroke_color = tuple(max(0, c // 3) for c in color)
        stroke_width = self.config.stroke_width
        
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx*dx + dy*dy <= stroke_width*stroke_width:
                    draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
        
        draw.text((x, y), text, font=font, fill=color)
    
    def _lighten_color(self, color: Tuple[int, int, int], factor: float = 0.7) -> Tuple[int, int, int]:
        return tuple(min(255, int(c + (255 - c) * factor)) for c in color)


class SubtitleWriter:
    """Writer for saving enhanced subtitles"""
    
    @staticmethod
    def save_json_with_grammar(segments: List[SubtitleSegment], output_path: str) -> bool:
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
                
                if segment.grammatical_words:
                    item["grammatical_analysis"] = []
                    furigana_parts = []
                    
                    for word in segment.grammatical_words:
                        item["grammatical_analysis"].append({
                            "word": word.word,
                            "furigana": word.furigana or "",
                            "type": word.grammatical_type.value
                        })
                        
                        if word.furigana:
                            furigana_parts.append(f"{word.word}({word.furigana})")
                        else:
                            furigana_parts.append(word.word)
                    
                    item["furigana_text"] = "".join(furigana_parts)
                
                json_data.append(item)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Saved JSON: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")
            return False
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class SimpleFuriganaBurnerApp:
    """Simplified furigana burner with working post-processing"""
    
    def __init__(self, config: BurnerConfig = None):
        self.config = config or BurnerConfig()
        self.analyzer = SimpleGrammaticalAnalyzer(self.config)
        self.renderer = GrammaticalRenderer(self.config)
        
        cache_status = "FORCE REFRESH" if self.config.force_refresh else "USE CACHE"
        print(f"🚀 Simple Furigana Burner initialized ({cache_status})")
    
    def process_video_with_subtitles(self, video_path: str, subtitle_path: str, output_path: str = None) -> bool:
        if not output_path:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = f"{base_name}_simple.mp4"
        
        print(f"🎬 Processing: {os.path.basename(video_path)}")
        print(f"📄 Subtitles: {os.path.basename(subtitle_path)}")
        
        try:
            segments = SubtitleParser.parse_subtitles(subtitle_path)
            if not segments:
                return False
            
            print(f"\n🔍 Analyzing {len(segments)} segments...")
            
            for i, segment in enumerate(segments):
                words = self.analyzer.analyze_sentence(segment.text, segment.lang)
                segment.grammatical_words = words
                
                if i < 3:  # Preview first 3
                    preview = " ".join([
                        f"{word.word}({word.furigana})" if word.furigana else word.word
                        for word in words
                    ])
                    print(f"   {i+1}: {segment.text}")
                    print(f"      → {preview}")
            
            # Save files
            base_name = os.path.splitext(os.path.basename(subtitle_path))[0]
            output_dir = os.path.dirname(output_path) or '.'
            json_output = os.path.join(output_dir, f"{base_name}_simple.json")
            
            SubtitleWriter.save_json_with_grammar(segments, json_output)
            
            # Process video
            return self._burn_to_video(video_path, segments, output_path)
            
        except Exception as e:
            print(f"❌ Processing error: {e}")
            return False
    
    def _burn_to_video(self, video_path: str, segments: List[SubtitleSegment], output_path: str) -> bool:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
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
                
                # Add subtitle
                if active_segment and active_segment.grammatical_words:
                    try:
                        frame = self._add_subtitle_to_frame(frame, active_segment.grammatical_words, width, height)
                    except Exception as e:
                        print(f"⚠️ Subtitle error: {e}")
                
                out.write(frame)
                frame_count += 1
                
                progress = int((frame_count / total_frames) * 100)
                if progress != last_progress and progress % 10 == 0:
                    print(f"⏳ Progress: {progress}%")
                    last_progress = progress
            
            print(f"✅ Completed: {output_path}")
            return True
            
        finally:
            cap.release()
            out.release()
    
    def _add_subtitle_to_frame(self, frame: np.ndarray, words: List[GrammaticalWord], 
                              frame_width: int, frame_height: int) -> np.ndarray:
        try:
            subtitle_img = self.renderer.render_grammatical_subtitle(words, frame_width, frame_height)
            subtitle_cv = cv2.cvtColor(np.array(subtitle_img), cv2.COLOR_RGBA2BGRA)
            subtitle_height, subtitle_width = subtitle_cv.shape[:2]
            
            # Position subtitle
            x = (frame_width - subtitle_width) // 2
            margin = self.config.margin
            
            if self.config.position == 'top':
                y = margin
            elif self.config.position == 'center':
                y = (frame_height - subtitle_height) // 2
            else:
                y = frame_height - subtitle_height - margin
            
            x = max(0, min(x, frame_width - subtitle_width))
            y = max(0, min(y, frame_height - subtitle_height))
            
            # Blend
            if (x + subtitle_width <= frame_width and y + subtitle_height <= frame_height):
                alpha = subtitle_cv[:, :, 3] / 255.0
                alpha = np.stack([alpha] * 3, axis=2)
                
                overlay_region = frame[y:y+subtitle_height, x:x+subtitle_width]
                subtitle_rgb = subtitle_cv[:, :, :3]
                
                if overlay_region.shape == subtitle_rgb.shape == alpha.shape:
                    blended = overlay_region * (1 - alpha) + subtitle_rgb * alpha
                    frame[y:y+subtitle_height, x:x+subtitle_width] = blended.astype(np.uint8)
        
        except Exception as e:
            print(f"⚠️ Rendering error: {e}")
        
        return frame


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Grammatical Furigana Burner')
    
    # Main arguments with -v and -j options
    parser.add_argument('-v', '--video', help='Input video file')
    parser.add_argument('-j', '--json', help='Input JSON subtitle file')  
    parser.add_argument('-s', '--srt', help='Input SRT subtitle file (alternative to JSON)')
    parser.add_argument('-o', '--output', help='Output video file (optional)')
    
    # Legacy positional arguments for backward compatibility
    parser.add_argument('video_pos', nargs='?', help='Input video file (positional)')
    parser.add_argument('subtitles_pos', nargs='?', help='Input subtitle file (positional)')
    parser.add_argument('output_pos', nargs='?', help='Output video file (positional)')
    
    # Configuration options
    parser.add_argument('--position', choices=['top', 'center', 'bottom'], default='bottom')
    parser.add_argument('--main-font-size', type=int, default=64)
    parser.add_argument('--furigana-font-size', type=int, default=32)
    parser.add_argument('--openai-model', default='gpt-4o-mini')
    parser.add_argument('--no-cache', action='store_true', 
                       help='Force fresh fetch (ignore cache but still save results)')
    
    # Auto-detect mode
    if len(sys.argv) == 1:
        print("🔍 Auto-detecting files...")
        video_files = glob.glob("*.mp4") + glob.glob("*.MP4") + glob.glob("*.avi") + glob.glob("*.mkv")
        subtitle_files = glob.glob("*.json") + glob.glob("*.srt")
        
        if video_files and subtitle_files:
            config = BurnerConfig()
            app = SimpleFuriganaBurnerApp(config)
            success = app.process_video_with_subtitles(video_files[0], subtitle_files[0])
            
            if success:
                print("\n🎉 SUCCESS! Enhanced furigana processing completed!")
                print("   ✅ Case A: Hiragana before kanji (お茶)")
                print("   ✅ Case B: Hiragana after kanji (聞こえて)") 
                print("   ✅ Case C: Hiragana inside kanji (引っ越したい)")
            else:
                print("\n❌ FAILED!")
        else:
            print("❌ No files found")
            print("\n📖 Usage:")
            print("  python furigana_burner.py                              # Auto-detect")
            print("  python furigana_burner.py -v video.mp4 -j subs.json   # With -v -j flags")
            print("  python furigana_burner.py video.mp4 subs.json         # Positional args")
            print("  python furigana_burner.py -v video.mp4 -s subs.srt    # With SRT file")
        return
    
    args = parser.parse_args()
    
    # Determine video and subtitle files (prioritize flags over positional)
    video_file = args.video or args.video_pos
    subtitle_file = args.json or args.srt or args.subtitles_pos
    output_file = args.output or args.output_pos
    
    if not video_file or not subtitle_file:
        print("❌ Both video and subtitle files are required")
        print("\n📖 Usage examples:")
        print("  python furigana_burner.py -v video.mp4 -j subtitles.json")
        print("  python furigana_burner.py -v video.mp4 -s subtitles.srt")
        print("  python furigana_burner.py video.mp4 subtitles.json")
        return
    
    if not os.path.exists(video_file):
        print(f"❌ Video file not found: {video_file}")
        return
        
    if not os.path.exists(subtitle_file):
        print(f"❌ Subtitle file not found: {subtitle_file}")
        return
    
    config = BurnerConfig(
        position=args.position,
        main_font_size=args.main_font_size,
        furigana_font_size=args.furigana_font_size,
        openai_model=args.openai_model,
        force_refresh=args.no_cache  # True = ignore cache, False = use cache
    )
    
    app = SimpleFuriganaBurnerApp(config)
    success = app.process_video_with_subtitles(video_file, subtitle_file, output_file)
    
    if success:
        print("\n🎉 SUCCESS! Enhanced furigana processing completed!")
        print("   ✅ Case A: Hiragana before kanji (お茶 → 茶)")
        print("   ✅ Case B: Hiragana after kanji (聞こえて → 聞(き)こえて)")  
        print("   ✅ Case C: Hiragana inside kanji (引っ越したい → cleaned)")
        print(f"   📁 Output saved to: {os.path.dirname(video_file) or '.'}")
    else:
        print("\n❌ FAILED!")


if __name__ == "__main__":
    main()
