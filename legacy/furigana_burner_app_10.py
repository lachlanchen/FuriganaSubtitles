#!/usr/bin/env python3
"""
Grammatical Analysis Furigana Subtitle Burner
Features:
- Grammatical analysis of Japanese sentences
- Word-level furigana with grammatical type classification
- Fixed colors for different grammatical components (subject, object, verb, particles, etc.)
- Educational approach for Japanese learning
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
    print("Warning: pykakasi not available")


class GrammaticalType(Enum):
    """Grammatical types for Japanese components"""
    SUBJECT = "subject"           # 主語
    OBJECT = "object"             # 目的語  
    VERB = "verb"                 # 動詞
    ADJECTIVE = "adjective"       # 形容詞
    ADVERB = "adverb"            # 副詞
    NOUN = "noun"                # 名詞
    PARTICLE_WA = "particle_wa"   # は (topic marker)
    PARTICLE_GA = "particle_ga"   # が (subject marker)
    PARTICLE_WO = "particle_wo"   # を (object marker)
    PARTICLE_NI = "particle_ni"   # に (direction/time)
    PARTICLE_DE = "particle_de"   # で (location/means)
    PARTICLE_TO = "particle_to"   # と (and/with)
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
    description: Optional[str] = None


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
    use_openai_cache: bool = True
    max_openai_retries: int = 3


class GrammaticalColorScheme:
    """Fixed color scheme for different grammatical components"""
    
    COLOR_MAP = {
        GrammaticalType.SUBJECT: (255, 100, 100),      # Light red - 主語
        GrammaticalType.OBJECT: (100, 150, 255),       # Light blue - 目的語
        GrammaticalType.VERB: (100, 255, 100),         # Light green - 動詞
        GrammaticalType.ADJECTIVE: (255, 200, 100),    # Orange - 形容詞
        GrammaticalType.ADVERB: (200, 100, 255),       # Purple - 副詞
        GrammaticalType.NOUN: (255, 255, 150),         # Light yellow - 名詞
        GrammaticalType.PARTICLE_WA: (255, 150, 150),  # Pink - は
        GrammaticalType.PARTICLE_GA: (150, 255, 150),  # Light green - が
        GrammaticalType.PARTICLE_WO: (150, 150, 255),  # Light blue - を
        GrammaticalType.PARTICLE_NI: (255, 255, 100),  # Yellow - に
        GrammaticalType.PARTICLE_DE: (100, 255, 255),  # Cyan - で
        GrammaticalType.PARTICLE_TO: (255, 100, 255),  # Magenta - と
        GrammaticalType.PARTICLE_OTHER: (200, 200, 200),  # Gray - other particles
        GrammaticalType.AUXILIARY: (150, 200, 150),    # Muted green - 助動詞
        GrammaticalType.CONJUNCTION: (200, 150, 200),  # Muted purple - 接続詞
        GrammaticalType.PUNCTUATION: (180, 180, 180),  # Light gray - punctuation
        GrammaticalType.OTHER: (220, 220, 220),        # Very light gray - other
    }
    
    @classmethod
    def get_color(cls, grammatical_type: GrammaticalType) -> Tuple[int, int, int]:
        """Get color for grammatical type"""
        return cls.COLOR_MAP.get(grammatical_type, cls.COLOR_MAP[GrammaticalType.OTHER])


class GrammaticalAnalyzer:
    """AI-powered grammatical analyzer for Japanese text"""
    
    def __init__(self, config: BurnerConfig):
        self.config = config
        
        # Initialize OpenAI
        try:
            self.openai_client = OpenAIRequestJSONBase(
                use_cache=config.use_openai_cache,
                max_retries=config.max_openai_retries,
                cache_dir='grammatical_cache'
            )
            print("✅ Grammatical analyzer initialized")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")
            self.openai_client = None
        
        # Schema for grammatical analysis
        self.analysis_schema = {
            "type": "object",
            "properties": {
                "is_japanese": {
                    "type": "boolean",
                    "description": "Whether the text is Japanese"
                },
                "original_text": {
                    "type": "string",
                    "description": "The original input text"
                },
                "grammatical_words": {
                    "type": "array",
                    "description": "Array of words with grammatical analysis",
                    "items": {
                        "type": "object",
                        "properties": {
                            "word": {
                                "type": "string",
                                "description": "The word or morpheme"
                            },
                            "furigana": {
                                "type": "string",
                                "description": "Complete hiragana reading (ALWAYS provide, never empty)"
                            },
                            "grammatical_type": {
                                "type": "string",
                                "enum": [
                                    "subject", "object", "verb", "adjective", "adverb", "noun",
                                    "particle_wa", "particle_ga", "particle_wo", "particle_ni", 
                                    "particle_de", "particle_to", "particle_other",
                                    "auxiliary", "conjunction", "punctuation", "other"
                                ],
                                "description": "Grammatical classification"
                            },
                            "description": {
                                "type": "string",
                                "description": "Brief explanation of grammatical role"
                            }
                        },
                        "required": ["word", "furigana", "grammatical_type", "description"],
                        "additionalProperties": False
                    }
                },
                "sentence_analysis": {
                    "type": "string",
                    "description": "Brief overall sentence structure analysis"
                }
            },
            "required": ["is_japanese", "original_text", "grammatical_words", "sentence_analysis"],
            "additionalProperties": False
        }
    
    def analyze_sentence(self, text: str, lang_hint: Optional[str] = None) -> List[GrammaticalWord]:
        """Analyze Japanese sentence into grammatical components"""
        
        if not text or len(text.strip()) < 1:
            return []
        
        # Check language hint
        if lang_hint and lang_hint.lower() not in ['ja', 'japanese', 'jpn']:
            print(f"🌐 Non-Japanese language ({lang_hint}): {text[:30]}...")
            return self._create_plain_words(text)
        
        if not self.openai_client:
            print("⚠️ No OpenAI client available")
            return self._create_plain_words(text)
        
        try:
            system_prompt = """You are a Japanese grammar expert specializing in morphological and syntactic analysis.

Your task is to analyze Japanese sentences and break them into grammatical components with furigana.

GRAMMATICAL TYPES:
- subject: 主語 (what the sentence is about)
- object: 目的語 (what the action is done to)  
- verb: 動詞 (action/state words)
- adjective: 形容詞 (descriptive words)
- adverb: 副詞 (words modifying verbs/adjectives)
- noun: 名詞 (things, people, concepts)
- particle_wa: は (topic marker)
- particle_ga: が (subject marker) 
- particle_wo: を (direct object marker)
- particle_ni: に (direction, time, indirect object)
- particle_de: で (location of action, means)
- particle_to: と (and, with)
- particle_other: other particles (の、から、まで、など)
- auxiliary: 助動詞 (です、ます、だ、etc.)
- conjunction: 接続詞 (connecting words)
- punctuation: 句読点 (。、！？)
- other: その他

FURIGANA RULES:
- Provide furigana ONLY for kanji that need reading help
- For compound words, give complete readings (今日 → "きょう")
- Leave furigana empty ("") for hiragana, katakana, and punctuation
- Be contextually accurate with readings

WORD SEGMENTATION:
- Split into meaningful grammatical units
- Keep particles separate from nouns
- Keep compound words together when they function as single units"""

            user_prompt = f"""Analyze this Japanese sentence:

Text: "{text}"

Break it into grammatical components and provide:
1. Each word/morpheme with its grammatical classification
2. Furigana for kanji (empty string if not needed)
3. Brief description of each component's role

Example format:
- "私" → word: "私", furigana: "わたし", type: "subject", description: "speaker (subject)"
- "は" → word: "は", furigana: "", type: "particle_wa", description: "topic marker"  
- "学生" → word: "学生", furigana: "がくせい", type: "noun", description: "student (noun)"
- "です" → word: "です", furigana: "", type: "auxiliary", description: "polite copula"

Focus on accurate grammatical analysis and proper furigana for compound words."""

            cache_filename = f"grammatical_{abs(hash(text))}.json"
            
            result = self.openai_client.send_request_with_json_schema(
                prompt=user_prompt,
                json_schema=self.analysis_schema,
                system_content=system_prompt,
                filename=cache_filename,
                schema_name="grammatical_analysis",
                model=self.config.openai_model
            )
            
            if result and result.get('is_japanese', False):
                return self._process_analysis_result(result)
            else:
                print("⚠️ Analysis failed, using plain words")
                return self._create_plain_words(text)
                
        except Exception as e:
            print(f"⚠️ Grammatical analysis error: {e}")
            return self._create_plain_words(text)
    
    def _process_analysis_result(self, result: Dict[str, Any]) -> List[GrammaticalWord]:
        """Process AI analysis result into GrammaticalWord objects"""
        
        words = []
        grammatical_words = result.get('grammatical_words', [])
        
        for word_info in grammatical_words:
            word = word_info.get('word', '').strip()
            furigana = word_info.get('furigana', '').strip()
            grammatical_type_str = word_info.get('grammatical_type', 'other')
            description = word_info.get('description', '')
            
            # Convert string to enum
            try:
                grammatical_type = GrammaticalType(grammatical_type_str)
            except ValueError:
                grammatical_type = GrammaticalType.OTHER
            
            # Get color for this grammatical type
            color = GrammaticalColorScheme.get_color(grammatical_type)
            
            # Clean up furigana
            if not furigana or furigana.lower() in ['none', 'null', 'n/a']:
                furigana = None
            
            words.append(GrammaticalWord(
                word=word,
                furigana=furigana,
                grammatical_type=grammatical_type,
                color=color,
                description=description
            ))
        
        analysis = result.get('sentence_analysis', '')
        word_count = len([w for w in words if w.furigana])
        print(f"✅ Grammatical analysis: {len(words)} words, {word_count} with furigana")
        if analysis:
            print(f"   Structure: {analysis[:50]}...")
        
        return words
    
    def _create_plain_words(self, text: str) -> List[GrammaticalWord]:
        """Create plain word list without analysis"""
        
        # Simple tokenization
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
                if char.strip():  # Keep punctuation
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
        """Parse subtitle file with proper encoding detection"""
        
        encodings = ['utf-8', 'utf-8-sig', 'shift_jis', 'euc-jp', 'cp932']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read().strip()
                
                if file_path.lower().endswith('.json') or content.startswith('[') or content.startswith('{'):
                    return SubtitleParser.parse_json_content(content)
                else:
                    return SubtitleParser.parse_srt_content(content)
                    
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"⚠️ Error with encoding {encoding}: {e}")
                continue
        
        print(f"❌ Could not decode file: {file_path}")
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


class GrammaticalRenderer:
    """Renderer for grammatical analysis with fixed colors"""
    
    def __init__(self, config: BurnerConfig):
        self.config = config
        self.main_font = self._load_font(config.main_font_size)
        self.furigana_font = self._load_font(config.furigana_font_size)
        
        print(f"🎨 Grammatical renderer initialized: main={config.main_font_size}px, furigana={config.furigana_font_size}px")
    
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
    
    def render_grammatical_subtitle(self, words: List[GrammaticalWord], 
                                   frame_width: int, frame_height: int) -> Image.Image:
        """Render grammatical subtitle with word-level colors"""
        
        if not words:
            return Image.new('RGBA', (100, 50), (0, 0, 0, 0))
        
        # Calculate dimensions
        total_width, total_height = self._calculate_dimensions(words)
        max_width = int(frame_width * self.config.max_width_ratio)
        
        # Handle multi-line if needed
        if total_width > max_width and self.config.auto_multi_line:
            return self._render_multi_line_grammatical(words, frame_width, frame_height, max_width)
        else:
            return self._render_single_line_grammatical(words, frame_width, frame_height)
    
    def _calculate_dimensions(self, words: List[GrammaticalWord]) -> Tuple[int, int]:
        """Calculate total dimensions needed"""
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
                max_height = self.config.main_font_size + self.config.furigana_font_size + int(self.config.furigana_font_size * self.config.furigana_spacing_ratio)
            
            total_width += word_width
        
        return total_width, max_height
    
    def _render_single_line_grammatical(self, words: List[GrammaticalWord], 
                                       frame_width: int, frame_height: int) -> Image.Image:
        """Render single line with grammatical colors"""
        
        total_width, total_height = self._calculate_dimensions(words)
        
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
        
        # Render words
        current_x = padding
        text_y = padding
        furigana_y = padding
        
        # Calculate Y positions if we have furigana
        has_any_furigana = any(word.furigana for word in words)
        if has_any_furigana:
            text_y = padding + self.config.furigana_font_size + int(self.config.furigana_font_size * self.config.furigana_spacing_ratio)
        
        for word in words:
            word_width = self._render_word_at_position(draw, word, current_x, text_y, furigana_y, has_any_furigana)
            current_x += word_width
        
        return img
    
    def _render_multi_line_grammatical(self, words: List[GrammaticalWord], 
                                      frame_width: int, frame_height: int, max_width: int) -> Image.Image:
        """Render multi-line grammatical subtitle"""
        
        # Split words into lines
        lines = self._split_words_into_lines(words, max_width)
        
        # Calculate total height
        line_height = self.config.main_font_size
        if any(any(word.furigana for word in line) for line in lines):
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
            
            has_furigana = any(word.furigana for word in line)
            text_y = current_y
            furigana_y = current_y
            
            if has_furigana:
                text_y = current_y + self.config.furigana_font_size + int(self.config.furigana_font_size * self.config.furigana_spacing_ratio)
            
            current_x = start_x
            for word in line:
                word_width = self._render_word_at_position(draw, word, current_x, text_y, furigana_y, has_furigana)
                current_x += word_width
            
            current_y += line_height + line_spacing
        
        return img
    
    def _split_words_into_lines(self, words: List[GrammaticalWord], max_width: int) -> List[List[GrammaticalWord]]:
        """Split words into lines based on max width"""
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
        """Get width needed for a word"""
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
        """Render a single word at specified position with grammatical color"""
        
        word_width = self._get_word_width(word)
        
        # Calculate text position (center within word width)
        word_bbox = draw.textbbox((0, 0), word.word, font=self.main_font)
        text_width = word_bbox[2] - word_bbox[0]
        text_x = x + (word_width - text_width) // 2
        
        # Draw main word with grammatical color and stroke
        self._draw_text_with_stroke(draw, text_x, text_y, word.word, self.main_font, word.color)
        
        # Draw furigana if present
        if word.furigana and line_has_furigana:
            furigana_bbox = draw.textbbox((0, 0), word.furigana, font=self.furigana_font)
            furigana_width = furigana_bbox[2] - furigana_bbox[0]
            furigana_x = x + (word_width - furigana_width) // 2
            
            # Use slightly lighter version of word color for furigana
            furigana_color = self._lighten_color(word.color)
            self._draw_text_with_stroke(draw, furigana_x, furigana_y, word.furigana, self.furigana_font, furigana_color)
        
        return word_width
    
    def _draw_text_with_stroke(self, draw: ImageDraw.Draw, x: int, y: int, 
                              text: str, font: ImageFont.FreeTypeFont, color: Tuple[int, int, int]):
        """Draw text with stroke"""
        
        # Draw stroke (darker version of color)
        stroke_color = tuple(max(0, c // 3) for c in color)
        stroke_width = self.config.stroke_width
        
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx*dx + dy*dy <= stroke_width*stroke_width:
                    draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
        
        # Draw main text in grammatical color
        draw.text((x, y), text, font=font, fill=color)
    
    def _lighten_color(self, color: Tuple[int, int, int], factor: float = 0.7) -> Tuple[int, int, int]:
        """Lighten a color for furigana"""
        return tuple(min(255, int(c + (255 - c) * factor)) for c in color)


class SubtitleWriter:
    """Writer for saving enhanced subtitles with grammatical analysis"""
    
    @staticmethod
    def save_json_with_grammar(segments: List[SubtitleSegment], output_path: str) -> bool:
        """Save segments with grammatical analysis to JSON"""
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
                    furigana_text_parts = []
                    
                    for word in segment.grammatical_words:
                        word_analysis = {
                            "word": word.word,
                            "furigana": word.furigana or "",
                            "type": word.grammatical_type.value,
                            "description": word.description or ""
                        }
                        item["grammatical_analysis"].append(word_analysis)
                        
                        # Build furigana text representation
                        if word.furigana:
                            furigana_text_parts.append(f"{word.word}({word.furigana})")
                        else:
                            furigana_text_parts.append(word.word)
                    
                    item["furigana_text"] = "".join(furigana_text_parts)
                
                json_data.append(item)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Saved grammatical JSON: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")
            return False
    
    @staticmethod
    def save_srt_with_grammar(segments: List[SubtitleSegment], output_path: str) -> bool:
        """Save segments with grammatical analysis to SRT"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments, 1):
                    f.write(f"{i}\n")
                    f.write(f"{SubtitleWriter._format_timestamp(segment.start_time)} --> ")
                    f.write(f"{SubtitleWriter._format_timestamp(segment.end_time)}\n")
                    
                    if segment.grammatical_words:
                        furigana_text = "".join([
                            f"{word.word}({word.furigana})" if word.furigana else word.word
                            for word in segment.grammatical_words
                        ])
                        f.write(f"{furigana_text}\n\n")
                    else:
                        f.write(f"{segment.text}\n\n")
            
            print(f"💾 Saved grammatical SRT: {output_path}")
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


class GrammaticalFuriganaBurnerApp:
    """Complete grammatical furigana burner app"""
    
    def __init__(self, config: BurnerConfig = None):
        self.config = config or BurnerConfig()
        self.analyzer = GrammaticalAnalyzer(self.config)
        self.renderer = GrammaticalRenderer(self.config)
        
        print(f"🚀 Grammatical Furigana Burner App initialized")
        print(f"   Position: {self.config.position}")
        print("   🎨 Color scheme: Fixed colors for grammatical types")
        print("   📚 Features: Subject/Object/Verb analysis, Particle identification")
    
    def process_video_with_subtitles(self, video_path: str, subtitle_path: str, output_path: str = None) -> bool:
        """Process video with grammatical analysis"""
        
        if not output_path:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = f"{base_name}_grammatical.mp4"
        
        print(f"🎬 Processing: {os.path.basename(video_path)}")
        print(f"📄 Subtitles: {os.path.basename(subtitle_path)}")
        print(f"💾 Output: {os.path.basename(output_path)}")
        
        try:
            # Parse subtitles
            segments = SubtitleParser.parse_subtitles(subtitle_path)
            if not segments:
                return False
            
            # Process grammatical analysis for all segments
            print(f"\n🔍 Analyzing {len(segments)} segments with grammatical AI...")
            
            for i, segment in enumerate(segments):
                words = self.analyzer.analyze_sentence(segment.text, segment.lang)
                segment.grammatical_words = words
                
                # Show preview for first few
                if i < 3:
                    word_preview = " ".join([
                        f"{word.word}({word.furigana})" if word.furigana else word.word
                        for word in words
                    ])
                    types_preview = " | ".join([
                        f"{word.word}:{word.grammatical_type.value}"
                        for word in words[:3]
                    ])
                    print(f"   {i+1}: {segment.text}")
                    print(f"      → {word_preview}")
                    print(f"      Types: {types_preview}...")
            
            # Save enhanced subtitle files
            base_name = os.path.splitext(os.path.basename(subtitle_path))[0]
            output_dir = os.path.dirname(output_path) or '.'
            
            json_output = os.path.join(output_dir, f"{base_name}_grammatical.json")
            srt_output = os.path.join(output_dir, f"{base_name}_grammatical.srt")
            
            SubtitleWriter.save_json_with_grammar(segments, json_output)
            SubtitleWriter.save_srt_with_grammar(segments, srt_output)
            
            # Process video
            return self._burn_to_video(video_path, segments, output_path)
            
        except Exception as e:
            print(f"❌ Processing error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _burn_to_video(self, video_path: str, segments: List[SubtitleSegment], output_path: str) -> bool:
        """Burn grammatical subtitles to video"""
        
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
                
                # Add grammatical subtitle
                if active_segment and active_segment.grammatical_words:
                    try:
                        frame = self._add_grammatical_subtitle_to_frame(
                            frame, active_segment.grammatical_words, width, height
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
    
    def _add_grammatical_subtitle_to_frame(self, frame: np.ndarray, words: List[GrammaticalWord], 
                                         frame_width: int, frame_height: int) -> np.ndarray:
        """Add grammatical subtitle to frame"""
        
        try:
            subtitle_img = self.renderer.render_grammatical_subtitle(words, frame_width, frame_height)
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
            print(f"⚠️ Grammatical rendering error: {e}")
        
        return frame


def main():
    """Main function with grammatical analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Grammatical Analysis Furigana Subtitle Burner')
    parser.add_argument('video', nargs='?', help='Input video file')  
    parser.add_argument('subtitles', nargs='?', help='Input subtitle file (JSON or SRT)')
    parser.add_argument('output', nargs='?', help='Output video file (optional)')
    
    # Configuration options
    parser.add_argument('--position', choices=['top', 'center', 'bottom'], 
                       default='bottom', help='Subtitle position')
    parser.add_argument('--main-font-size', type=int, default=64, help='Main font size')
    parser.add_argument('--furigana-font-size', type=int, default=32, help='Furigana font size')
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
            app = GrammaticalFuriganaBurnerApp(config)
            success = app.process_video_with_subtitles(video_file, subtitle_file)
            
            if success:
                print("\n🎉 SUCCESS! Grammatical furigana processing completed!")
                print("   📚 Grammatical analysis with fixed colors")
                print("   🎨 Subject=Red, Object=Blue, Verb=Green, Particles=Pink/Yellow")
                print("   📖 Perfect for Japanese learning!")
            else:
                print("\n❌ FAILED! Check error messages above.")
        else:
            print("❌ No video or subtitle files found")
            print("\n📖 Usage:")
            print("  python grammatical_furigana_burner.py                              # Auto-detect")
            print("  python grammatical_furigana_burner.py video.mp4 subtitles.json    # Specify files")
            print("  python grammatical_furigana_burner.py --position top               # Top position")
        
        return
    
    args = parser.parse_args()
    
    # Create configuration
    config = BurnerConfig(
        position=args.position,
        main_font_size=args.main_font_size,
        furigana_font_size=args.furigana_font_size,
        openai_model=args.openai_model,
        use_openai_cache=not args.no_cache
    )
    
    # Process
    app = GrammaticalFuriganaBurnerApp(config)
    success = app.process_video_with_subtitles(args.video, args.subtitles, args.output)
    
    if success:
        print("\n🎉 SUCCESS! Grammatical furigana processing completed!")
    else:
        print("\n❌ FAILED! Check error messages above.")


if __name__ == "__main__":
    main()
