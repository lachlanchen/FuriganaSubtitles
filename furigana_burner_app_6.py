#!/usr/bin/env python3
"""
Enhanced AI-First Furigana Subtitle Burner App
Features:
- JSON format as primary input with SRT support
- Comprehensive kanji/katakana detection and furigana generation
- Smart hybrid approach using character analysis + AI
- Language detection via JSON 'lang' field or text analysis
- Outputs both JSON and SRT with furigana
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import re
import os
import sys
import glob
import json
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional, Dict, Any, Union
from abc import ABC, abstractmethod

# Import the OpenAI request handler
from openai_request import OpenAIRequestJSONBase

# Japanese text processing libraries (optional)
try:
    import pykakasi
    KAKASI_AVAILABLE = True
except ImportError:
    KAKASI_AVAILABLE = False


@dataclass
class SubtitleSegment:
    start_time: float
    end_time: float
    text: str
    lang: Optional[str] = None
    furigana_text: Optional[str] = None  # Text with furigana annotations


@dataclass
class FuriganaChar:
    char: str
    furigana: Optional[str]
    is_kanji: bool
    is_katakana: bool
    
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
    use_ai: bool = True


class FuriganaGenerator(ABC):
    """Abstract base class for furigana generation"""
    
    @abstractmethod
    def get_furigana(self, text: str, lang_hint: Optional[str] = None) -> List[FuriganaChar]:
        """Generate furigana for given text"""
        pass


class EnhancedOpenAIFuriganaGenerator(FuriganaGenerator):
    """Enhanced OpenAI furigana generator with comprehensive kanji/katakana detection"""
    
    def __init__(self, config: BurnerConfig):
        self.config = config
        
        try:
            self.openai_client = OpenAIRequestJSONBase(
                use_cache=config.use_openai_cache,
                max_retries=config.max_openai_retries,
                cache_dir='furigana_cache'
            )
            print("✅ Enhanced OpenAI furigana generator initialized")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")
            raise
        
        # Enhanced schema for comprehensive furigana detection
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
                "character_analysis": {
                    "type": "array",
                    "description": "Detailed analysis of each character needing furigana",
                    "items": {
                        "type": "object",
                        "properties": {
                            "character": {
                                "type": "string",
                                "description": "The kanji or katakana character"
                            },
                            "position": {
                                "type": "integer",
                                "description": "Character position in original text"
                            },
                            "reading": {
                                "type": "string",
                                "description": "Hiragana reading for this character"
                            },
                            "type": {
                                "type": "string",
                                "enum": ["kanji", "katakana"],
                                "description": "Type of character"
                            },
                            "context": {
                                "type": "string",
                                "description": "Surrounding context that influenced the reading"
                            },
                            "confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Confidence in this specific reading"
                            }
                        },
                        "required": ["character", "position", "reading", "type", "confidence"],
                        "additionalProperties": False
                    }
                },
                "compound_words": {
                    "type": "array",
                    "description": "Multi-character compounds that should be read together",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The compound word"
                            },
                            "start_pos": {
                                "type": "integer",
                                "description": "Starting position in original text"
                            },
                            "end_pos": {
                                "type": "integer", 
                                "description": "Ending position in original text"
                            },
                            "reading": {
                                "type": "string",
                                "description": "Complete reading for the compound"
                            }
                        },
                        "required": ["text", "start_pos", "end_pos", "reading"],
                        "additionalProperties": False
                    }
                },
                "overall_confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Overall confidence in the furigana analysis"
                },
                "language_detected": {
                    "type": "string",
                    "description": "Primary language detected in the text"
                }
            },
            "required": ["is_japanese", "original_text", "character_analysis", "compound_words", "overall_confidence", "language_detected"],
            "additionalProperties": False
        }
    
    def get_furigana(self, text: str, lang_hint: Optional[str] = None) -> List[FuriganaChar]:
        """Generate furigana with comprehensive character analysis"""
        
        if not text or len(text.strip()) < 1:
            return [FuriganaChar(char, None, False, False) for char in text]
        
        # Use lang hint if available
        if lang_hint and lang_hint.lower() not in ['ja', 'japanese']:
            print(f"🌐 Non-Japanese language hint ({lang_hint}): {text[:30]}...")
            return [FuriganaChar(char, None, False, False) for char in text]
        
        # Pre-analyze text to identify all potential kanji/katakana
        char_analysis = self._analyze_characters(text)
        
        # Skip if no Japanese characters found
        if not any(info['needs_furigana'] for info in char_analysis):
            print(f"🔍 No kanji/katakana found: {text[:30]}...")
            return [FuriganaChar(char, None, False, False) for char in text]
        
        try:
            # Get comprehensive furigana from OpenAI
            openai_result = self._request_comprehensive_furigana(text, char_analysis)
            
            if openai_result and openai_result.get('is_japanese', False):
                furigana_chars = self._process_enhanced_result(text, openai_result)
                
                if self._validate_comprehensive_quality(furigana_chars, openai_result):
                    kanji_count = sum(1 for char in furigana_chars if char.furigana)
                    print(f"✅ Enhanced furigana: {text[:30]}... ({kanji_count} readings, confidence: {openai_result.get('overall_confidence', 0):.2f})")
                    return furigana_chars
            
            # Fallback: return with character type info but no furigana
            print(f"⚠️ Fallback for: {text[:30]}...")
            return [FuriganaChar(char, None, self._is_kanji(char), self._is_katakana(char)) for char in text]
        
        except Exception as e:
            print(f"⚠️ Enhanced OpenAI error: {e}")
            return [FuriganaChar(char, None, self._is_kanji(char), self._is_katakana(char)) for char in text]
    
    def _analyze_characters(self, text: str) -> List[Dict[str, Any]]:
        """Pre-analyze text to identify all characters that need furigana"""
        analysis = []
        
        for i, char in enumerate(text):
            is_kanji = self._is_kanji(char)
            is_katakana = self._is_katakana(char)
            needs_furigana = is_kanji or (is_katakana and self._katakana_needs_furigana(char, text, i))
            
            analysis.append({
                'char': char,
                'position': i,
                'is_kanji': is_kanji,
                'is_katakana': is_katakana,
                'needs_furigana': needs_furigana,
                'context': text[max(0, i-2):i+3]  # 2 chars before and after for context
            })
        
        return analysis
    
    def _katakana_needs_furigana(self, char: str, text: str, pos: int) -> bool:
        """Determine if katakana character needs furigana (rare cases)"""
        # Usually katakana doesn't need furigana, but some compound words might
        # For now, be conservative and don't add furigana to katakana
        return False
    
    def _request_comprehensive_furigana(self, text: str, char_analysis: List[Dict]) -> Optional[Dict[str, Any]]:
        """Request comprehensive furigana analysis from OpenAI"""
        
        # Create character list for AI analysis
        target_chars = [info for info in char_analysis if info['needs_furigana']]
        
        system_prompt = """You are a Japanese language expert specializing in comprehensive furigana generation.

Your task is to provide accurate hiragana readings for ALL kanji and katakana characters that need furigana assistance.

Critical requirements:
1. Analyze EVERY kanji character in the text - do not miss any
2. Consider context for proper readings (not just dictionary readings)
3. Handle compound words correctly (e.g., 今日 = きょう, not いま+ひ)
4. For multi-kanji compounds, decide whether to break down or keep together
5. Be extremely thorough - missing kanji is worse than false positives
6. Provide character-by-character analysis AND compound word analysis

Examples:
- 今日 (compound): きょう (not broken down)
- 学校 (compound): がっこう (not broken down) 
- 空気 (compound): くうき (not broken down)
- 朝 (single): あさ
- 気持ち (compound): きもち"""

        chars_info = "\n".join([
            f"Position {info['position']}: '{info['char']}' ({'kanji' if info['is_kanji'] else 'katakana'}) in context '{info['context']}'"
            for info in target_chars
        ])

        user_prompt = f"""Analyze this Japanese text and provide comprehensive furigana:

Text: "{text}"

Characters needing analysis:
{chars_info}

Requirements:
1. Provide readings for ALL kanji characters listed above
2. Identify any compound words that should be read as units
3. Give contextually appropriate readings
4. Provide high confidence scores for accurate readings
5. Do NOT miss any kanji characters

For each character, provide:
- The exact character
- Its position in the original text
- The correct hiragana reading based on context
- Whether it's part of a compound word
- Your confidence in this reading

For compound words, also provide:
- The complete compound text
- Start and end positions
- The complete reading for the compound"""

        try:
            cache_filename = f"enhanced_furigana_{abs(hash(text + str(len(target_chars))))}.json"
            
            result = self.openai_client.send_request_with_json_schema(
                prompt=user_prompt,
                json_schema=self.furigana_schema,
                system_content=system_prompt,
                filename=cache_filename,
                schema_name="comprehensive_furigana_analysis",
                model=self.config.openai_model
            )
            
            return result
            
        except Exception as e:
            print(f"Enhanced OpenAI request failed: {e}")
            return None
    
    def _process_enhanced_result(self, original_text: str, openai_result: Dict[str, Any]) -> List[FuriganaChar]:
        """Process enhanced OpenAI result with compound word handling"""
        
        result = []
        
        # Create position-based reading map
        readings_map = {}
        
        # First, process compound words (they take precedence)
        compounds = openai_result.get('compound_words', [])
        compound_positions = set()
        
        for compound in compounds:
            start_pos = compound.get('start_pos', 0)
            end_pos = compound.get('end_pos', start_pos + 1)
            reading = compound.get('reading', '')
            compound_text = compound.get('text', '')
            
            if reading and start_pos < len(original_text) and end_pos <= len(original_text):
                # Distribute reading across compound characters
                compound_chars = original_text[start_pos:end_pos]
                kanji_chars = [i for i, c in enumerate(compound_chars) if self._is_kanji(c)]
                
                if kanji_chars:
                    # Simple distribution - divide reading among kanji characters
                    if len(kanji_chars) == 1:
                        readings_map[start_pos + kanji_chars[0]] = reading
                    else:
                        # For multi-kanji compounds, use the full reading for the first kanji
                        # This is a simplification - ideally we'd have character-level breakdown
                        readings_map[start_pos + kanji_chars[0]] = reading
                    
                    # Mark all positions as part of compound
                    for pos in range(start_pos, end_pos):
                        compound_positions.add(pos)
        
        # Then process individual character analysis
        char_analysis = openai_result.get('character_analysis', [])
        for char_info in char_analysis:
            pos = char_info.get('position', 0)
            reading = char_info.get('reading', '')
            
            if pos < len(original_text) and reading and pos not in compound_positions:
                readings_map[pos] = reading
        
        # Build final result
        for i, char in enumerate(original_text):
            is_kanji = self._is_kanji(char)
            is_katakana = self._is_katakana(char)
            furigana = readings_map.get(i)
            
            # Clean up empty readings
            if furigana and not furigana.strip():
                furigana = None
            
            result.append(FuriganaChar(char, furigana, is_kanji, is_katakana))
        
        return result
    
    def _validate_comprehensive_quality(self, furigana_chars: List[FuriganaChar], openai_result: Dict[str, Any]) -> bool:
        """Validate comprehensive furigana quality"""
        
        confidence = openai_result.get('overall_confidence', 0)
        if confidence < 0.5:
            return False
        
        # Check that we have reasonable furigana coverage for kanji
        kanji_count = sum(1 for char in furigana_chars if char.is_kanji)
        furigana_count = sum(1 for char in furigana_chars if char.furigana)
        
        if kanji_count > 0:
            coverage = furigana_count / kanji_count
            # Expect at least 60% of kanji to have furigana (accounting for compounds)
            if coverage < 0.6:
                print(f"⚠️ Low furigana coverage: {furigana_count}/{kanji_count} ({coverage:.1%})")
                return False
        
        # Validate furigana content
        for char in furigana_chars:
            if char.furigana:
                if not self._is_hiragana(char.furigana):
                    return False
                if len(char.furigana) > 10:  # Reasonable limit
                    return False
        
        return True
    
    def _is_kanji(self, char: str) -> bool:
        return '\u4e00' <= char <= '\u9faf'
    
    def _is_katakana(self, char: str) -> bool:
        return '\u30a0' <= char <= '\u30ff'
    
    def _is_hiragana(self, text: str) -> bool:
        return all('\u3040' <= char <= '\u309f' for char in text)


class NoOpFuriganaGenerator(FuriganaGenerator):
    """No-operation generator"""
    
    def get_furigana(self, text: str, lang_hint: Optional[str] = None) -> List[FuriganaChar]:
        return [FuriganaChar(char, None, self._is_kanji(char), self._is_katakana(char)) for char in text]
    
    def _is_kanji(self, char: str) -> bool:
        return '\u4e00' <= char <= '\u9faf'
    
    def _is_katakana(self, char: str) -> bool:
        return '\u30a0' <= char <= '\u30ff'


class SubtitleParser:
    """Enhanced parser supporting both JSON and SRT formats"""
    
    @staticmethod
    def parse_subtitles(file_path: str) -> List[SubtitleSegment]:
        """Parse subtitle file (JSON or SRT) into segments"""
        
        if file_path.lower().endswith('.json'):
            return SubtitleParser.parse_json(file_path)
        elif file_path.lower().endswith('.srt'):
            return SubtitleParser.parse_srt(file_path)
        else:
            # Try to detect format
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if content.startswith('[') or content.startswith('{'):
                    return SubtitleParser.parse_json_content(content)
                else:
                    return SubtitleParser.parse_srt_content(content)
                    
            except Exception as e:
                print(f"❌ Error detecting subtitle format: {e}")
                return []
    
    @staticmethod
    def parse_json(file_path: str) -> List[SubtitleSegment]:
        """Parse JSON subtitle file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SubtitleParser.parse_json_content_data(data)
        except Exception as e:
            print(f"❌ Error parsing JSON file: {e}")
            return []
    
    @staticmethod
    def parse_json_content(content: str) -> List[SubtitleSegment]:
        """Parse JSON content string"""
        try:
            data = json.loads(content)
            return SubtitleParser.parse_json_content_data(data)
        except Exception as e:
            print(f"❌ Error parsing JSON content: {e}")
            return []
    
    @staticmethod
    def parse_json_content_data(data: Any) -> List[SubtitleSegment]:
        """Parse JSON data into segments"""
        segments = []
        
        if not isinstance(data, list):
            print("❌ JSON data must be an array")
            return []
        
        for i, item in enumerate(data):
            try:
                if not isinstance(item, dict):
                    continue
                
                # Extract timing information
                start = item.get('start', '')
                end = item.get('end', '')
                text = item.get('text', '').strip()
                lang = item.get('lang')
                
                if not text:
                    continue
                
                # Parse timestamp
                start_time = SubtitleParser._parse_timestamp(start)
                end_time = SubtitleParser._parse_timestamp(end)
                
                if start_time is not None and end_time is not None:
                    segments.append(SubtitleSegment(start_time, end_time, text, lang))
                else:
                    print(f"⚠️ Invalid timestamps in JSON item {i+1}")
                    
            except Exception as e:
                print(f"⚠️ Error parsing JSON item {i+1}: {e}")
                continue
        
        print(f"📝 Successfully parsed {len(segments)} JSON subtitle segments")
        return segments
    
    @staticmethod
    def parse_srt(file_path: str) -> List[SubtitleSegment]:
        """Parse SRT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return SubtitleParser.parse_srt_content(content)
        except Exception as e:
            print(f"❌ Error parsing SRT file: {e}")
            return []
    
    @staticmethod
    def parse_srt_content(content: str) -> List[SubtitleSegment]:
        """Parse SRT content into segments"""
        segments = []
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for i, block in enumerate(blocks):
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
                    
            except Exception as e:
                print(f"⚠️ Error parsing SRT block {i+1}: {e}")
                continue
        
        print(f"📝 Successfully parsed {len(segments)} SRT subtitle segments")
        return segments
    
    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> Optional[float]:
        """Parse timestamp string to seconds"""
        try:
            if not timestamp_str:
                return None
                
            # Handle different timestamp formats
            if ',' in timestamp_str:
                # SRT format: HH:MM:SS,mmm
                match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', timestamp_str)
                if match:
                    return (int(match.group(1)) * 3600 + 
                           int(match.group(2)) * 60 + 
                           int(match.group(3)) + 
                           int(match.group(4)) / 1000)
            else:
                # Other formats: HH:MM:SS.mmm or HH:MM:SS
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


class SubtitleWriter:
    """Writer for saving subtitles with furigana in both JSON and SRT formats"""
    
    @staticmethod
    def save_json_with_furigana(segments: List[SubtitleSegment], output_path: str) -> bool:
        """Save segments with furigana to JSON file"""
        try:
            json_data = []
            
            for segment in segments:
                item = {
                    "start": SubtitleWriter._format_timestamp_json(segment.start_time),
                    "end": SubtitleWriter._format_timestamp_json(segment.end_time),
                    "text": segment.text,
                    "furigana_text": segment.furigana_text or segment.text
                }
                
                if segment.lang:
                    item["lang"] = segment.lang
                    
                json_data.append(item)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Saved JSON with furigana: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")
            return False
    
    @staticmethod
    def save_srt_with_furigana(segments: List[SubtitleSegment], output_path: str) -> bool:
        """Save segments with furigana to SRT file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments, 1):
                    f.write(f"{i}\n")
                    f.write(f"{SubtitleWriter._format_timestamp_srt(segment.start_time)} --> ")
                    f.write(f"{SubtitleWriter._format_timestamp_srt(segment.end_time)}\n")
                    f.write(f"{segment.furigana_text or segment.text}\n\n")
            
            print(f"💾 Saved SRT with furigana: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving SRT: {e}")
            return False
    
    @staticmethod
    def _format_timestamp_json(seconds: float) -> str:
        """Format timestamp for JSON (SRT format)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def _format_timestamp_srt(seconds: float) -> str:
        """Format timestamp for SRT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class FixedFuriganaRenderer:
    """Enhanced renderer with proper layout handling"""
    
    def __init__(self, config: BurnerConfig):
        self.config = config
        self.main_font = self._load_font(config.main_font_size)
        self.furigana_font = self._load_font(config.furigana_font_size)
        
        print(f"🎨 Renderer initialized: main={config.main_font_size}px, furigana={config.furigana_font_size}px")
    
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
        
        print(f"⚠️ No Japanese font found, using default")
        return ImageFont.load_default()
    
    def split_into_lines(self, furigana_chars: List[FuriganaChar], max_width: int) -> List[SubtitleLine]:
        """Split furigana text into multiple lines"""
        if not furigana_chars:
            return []
        
        lines = []
        current_line = []
        current_width = 0
        
        for char_info in furigana_chars:
            char_width = self._measure_char_width(char_info)
            
            if (current_width + char_width > max_width and 
                current_line and 
                self.config.auto_multi_line):
                
                if self._is_good_break_point(char_info.char) or len(current_line) > 10:
                    line = self._create_subtitle_line(current_line)
                    lines.append(line)
                    current_line = []
                    current_width = 0
            
            current_line.append(char_info)
            current_width += char_width
        
        if current_line:
            line = self._create_subtitle_line(current_line)
            lines.append(line)
        
        return lines or [self._create_subtitle_line(furigana_chars)]
    
    def _create_subtitle_line(self, furigana_chars: List[FuriganaChar]) -> SubtitleLine:
        """Create a SubtitleLine with proper height calculation"""
        if not furigana_chars:
            return SubtitleLine([], 0, 0, False, 0, 0)
        
        width = sum(self._measure_char_width(char) for char in furigana_chars)
        has_furigana = any(char.furigana for char in furigana_chars)
        
        text_height = self.config.main_font_size
        furigana_height = 0
        
        if has_furigana:
            furigana_height = self.config.furigana_font_size
        
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
        """Measure width needed for character with furigana"""
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
        return char in ' 、。！？\n\t'
    
    def render_multi_line_subtitle(self, lines: List[SubtitleLine], 
                                  frame_width: int, frame_height: int) -> Image.Image:
        """Render multi-line subtitle"""
        if not lines:
            return Image.new('RGBA', (100, 50), (0, 0, 0, 0))
        
        max_line_width = max(line.width for line in lines)
        total_height = sum(line.height for line in lines)
        
        if len(lines) > 1:
            line_spacing = int(self.config.main_font_size * self.config.line_spacing_ratio)
            total_height += (len(lines) - 1) * line_spacing
        
        padding = 20
        subtitle_width = min(max_line_width + 2 * padding, frame_width - 40)
        subtitle_height = min(total_height + 2 * padding, frame_height // 2)
        
        subtitle_width = max(subtitle_width, 100)
        subtitle_height = max(subtitle_height, 50)
        
        img = Image.new('RGBA', (subtitle_width, subtitle_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        if self.config.background_opacity > 0:
            bg_alpha = int(255 * self.config.background_opacity)
            draw.rectangle([0, 0, subtitle_width, subtitle_height], 
                         fill=(0, 0, 0, bg_alpha))
        
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
        
        x_offset = (total_width - line.width) // 2
        current_x = x_offset
        
        if line.has_furigana:
            text_y = y_offset + line.furigana_height + int(self.config.furigana_font_size * self.config.furigana_spacing_ratio)
            furigana_y = y_offset
        else:
            text_y = y_offset + (line.height - line.text_height) // 2
            furigana_y = y_offset
        
        for char_info in line.furigana_chars:
            char_width = self._measure_char_width(char_info)
            
            char_bbox = draw.textbbox((0, 0), char_info.char, font=self.main_font)
            char_w = char_bbox[2] - char_bbox[0]
            char_x = current_x + (char_width - char_w) // 2
            
            self._draw_text_with_stroke(draw, char_x, text_y, char_info.char, self.main_font)
            
            if char_info.furigana and line.has_furigana:
                furigana_bbox = draw.textbbox((0, 0), char_info.furigana, font=self.furigana_font)
                furigana_w = furigana_bbox[2] - furigana_bbox[0]
                furigana_x = current_x + (char_width - furigana_w) // 2
                self._draw_text_with_stroke(draw, furigana_x, furigana_y, char_info.furigana, self.furigana_font)
            
            current_x += char_width
    
    def _draw_text_with_stroke(self, draw: ImageDraw.Draw, x: int, y: int, text: str, font: ImageFont.FreeTypeFont):
        """Draw text with stroke outline"""
        stroke_width = self.config.stroke_width
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx*dx + dy*dy <= stroke_width*stroke_width:
                    draw.text((x + dx, y + dy), text, font=font, fill=self.config.stroke_color)
        
        draw.text((x, y), text, font=font, fill=self.config.text_color)


class EnhancedFuriganaBurnerApp:
    """Enhanced furigana subtitle burner with JSON support"""
    
    def __init__(self, config: BurnerConfig = None):
        self.config = config or BurnerConfig()
        self.furigana_generator = self._create_furigana_generator()
        self.renderer = FixedFuriganaRenderer(self.config)
        
        print(f"🚀 Enhanced Furigana Burner App initialized")
        print(f"   Generator: {type(self.furigana_generator).__name__}")
    
    def _create_furigana_generator(self) -> FuriganaGenerator:
        """Create appropriate furigana generator"""
        
        if not self.config.use_ai:
            print("❌ Non-AI mode not fully implemented in enhanced version")
            return NoOpFuriganaGenerator()
        
        try:
            if not os.getenv('OPENAI_API_KEY'):
                print("❌ No OpenAI API key found")
                return NoOpFuriganaGenerator()
            
            return EnhancedOpenAIFuriganaGenerator(self.config)
            
        except Exception as e:
            print(f"❌ Failed to create enhanced generator: {e}")
            return NoOpFuriganaGenerator()
    
    def process_subtitles(self, input_path: str, video_path: str = None, output_dir: str = None) -> bool:
        """Process subtitle file and optionally burn to video"""
        
        if not output_dir:
            output_dir = os.path.dirname(input_path) or '.'
        
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        
        print(f"📄 Processing subtitles: {input_path}")
        
        try:
            # Parse subtitles
            segments = SubtitleParser.parse_subtitles(input_path)
            if not segments:
                print("❌ No valid subtitle segments found")
                return False
            
            # Generate furigana for each segment
            print(f"\n🔍 Generating furigana for {len(segments)} segments...")
            
            processed_segments = []
            for i, segment in enumerate(segments):
                print(f"Processing segment {i+1}/{len(segments)}: {segment.text[:30]}...")
                
                furigana_chars = self.furigana_generator.get_furigana(segment.text, segment.lang)
                furigana_text = ''.join(str(char) for char in furigana_chars)
                
                # Update segment with furigana
                segment.furigana_text = furigana_text
                processed_segments.append(segment)
                
                # Show preview for first few
                if i < 5:
                    has_furigana = any(char.furigana for char in furigana_chars)
                    status = "✅ furigana" if has_furigana else "⭕ no furigana"
                    print(f"   → {furigana_text} ({status})")
            
            # Save enhanced subtitles
            json_output = os.path.join(output_dir, f"{base_name}_furigana.json")
            srt_output = os.path.join(output_dir, f"{base_name}_furigana.srt")
            
            json_success = SubtitleWriter.save_json_with_furigana(processed_segments, json_output)
            srt_success = SubtitleWriter.save_srt_with_furigana(processed_segments, srt_output)
            
            if not (json_success or srt_success):
                print("❌ Failed to save processed subtitles")
                return False
            
            # Burn to video if requested
            if video_path:
                video_output = os.path.join(output_dir, f"{base_name}_furigana.mp4")
                return self._burn_to_video(video_path, processed_segments, video_output)
            
            print("✅ Subtitle processing completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error processing subtitles: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _burn_to_video(self, video_path: str, segments: List[SubtitleSegment], output_path: str) -> bool:
        """Burn furigana subtitles to video"""
        
        print(f"🎬 Burning furigana to video: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ Could not open video: {video_path}")
            return False
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            print(f"🎥 Video: {width}x{height}, {fps:.2f} fps, {total_frames} frames")
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            if not out.isOpened():
                print(f"❌ Could not create output video")
                return False
            
            max_subtitle_width = int(width * self.config.max_width_ratio)
            
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
                if active_subtitle and active_subtitle.furigana_text:
                    try:
                        frame = self._add_furigana_subtitle_to_frame(
                            frame, active_subtitle.furigana_text, width, height, max_subtitle_width
                        )
                    except Exception as e:
                        print(f"⚠️ Error adding subtitle at {current_time:.2f}s: {e}")
                
                out.write(frame)
                frame_count += 1
                
                progress = int((frame_count / total_frames) * 100)
                if progress != last_progress and progress % 10 == 0:
                    print(f"⏳ Progress: {progress}% ({frame_count}/{total_frames})")
                    last_progress = progress
            
            print(f"✅ Video processing completed: {output_path}")
            return True
            
        finally:
            cap.release()
            out.release()
    
    def _add_furigana_subtitle_to_frame(self, frame: np.ndarray, furigana_text: str, 
                                       frame_width: int, frame_height: int, max_width: int) -> np.ndarray:
        """Add furigana subtitle to frame"""
        
        try:
            # Parse furigana text back into characters
            furigana_chars = self._parse_furigana_text(furigana_text)
            if not furigana_chars:
                return frame
            
            lines = self.renderer.split_into_lines(furigana_chars, max_width)
            if not lines:
                return frame
            
            subtitle_img = self.renderer.render_multi_line_subtitle(lines, frame_width, frame_height)
            subtitle_cv = cv2.cvtColor(np.array(subtitle_img), cv2.COLOR_RGBA2BGRA)
            subtitle_height, subtitle_width = subtitle_cv.shape[:2]
            
            x, y = self._calculate_subtitle_position(
                frame_width, frame_height, subtitle_width, subtitle_height
            )
            
            x = max(0, min(x, frame_width - subtitle_width))
            y = max(0, min(y, frame_height - subtitle_height))
            
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
            print(f"⚠️ Subtitle rendering error: {e}")
        
        return frame
    
    def _parse_furigana_text(self, furigana_text: str) -> List[FuriganaChar]:
        """Parse furigana text back into FuriganaChar objects"""
        result = []
        i = 0
        
        while i < len(furigana_text):
            char = furigana_text[i]
            
            # Check for furigana annotation
            if i + 1 < len(furigana_text) and furigana_text[i + 1] == '(':
                # Find closing parenthesis
                close_paren = furigana_text.find(')', i + 2)
                if close_paren != -1:
                    furigana = furigana_text[i + 2:close_paren]
                    result.append(FuriganaChar(char, furigana, self._is_kanji(char), self._is_katakana(char)))
                    i = close_paren + 1
                else:
                    result.append(FuriganaChar(char, None, self._is_kanji(char), self._is_katakana(char)))
                    i += 1
            else:
                result.append(FuriganaChar(char, None, self._is_kanji(char), self._is_katakana(char)))
                i += 1
        
        return result
    
    def _is_kanji(self, char: str) -> bool:
        return '\u4e00' <= char <= '\u9faf'
    
    def _is_katakana(self, char: str) -> bool:
        return '\u30a0' <= char <= '\u30ff'
    
    def _calculate_subtitle_position(self, frame_width: int, frame_height: int, 
                                   subtitle_width: int, subtitle_height: int) -> Tuple[int, int]:
        """Calculate subtitle position"""
        
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
    """Enhanced main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced AI Furigana Subtitle Processor')
    parser.add_argument('input', nargs='?', help='Input subtitle file (JSON or SRT)')
    parser.add_argument('video', nargs='?', help='Input video file (optional, for burning)')
    parser.add_argument('--output-dir', help='Output directory')
    
    # Configuration options
    parser.add_argument('--position', choices=['top', 'center', 'bottom'], 
                       default='bottom', help='Subtitle position')
    parser.add_argument('--main-font-size', type=int, default=64, help='Main font size')
    parser.add_argument('--furigana-font-size', type=int, default=32, help='Furigana font size')
    parser.add_argument('--openai-model', default='gpt-4o-mini', help='OpenAI model')
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')
    
    # Auto-detect mode
    if len(sys.argv) == 1:
        print("🔍 Auto-detecting subtitle files...")
        
        json_files = glob.glob("*.json")
        srt_files = glob.glob("*.srt")
        video_files = glob.glob("*.mp4") + glob.glob("*.avi") + glob.glob("*.mkv")
        
        subtitle_file = None
        if json_files:
            subtitle_file = json_files[0]
            print(f"📄 Found JSON: {subtitle_file}")
        elif srt_files:
            subtitle_file = srt_files[0]
            print(f"📄 Found SRT: {subtitle_file}")
        
        if subtitle_file:
            config = BurnerConfig()
            app = EnhancedFuriganaBurnerApp(config)
            
            video_file = video_files[0] if video_files else None
            if video_file:
                print(f"🎬 Found video: {video_file}")
            
            success = app.process_subtitles(subtitle_file, video_file)
            
            if success:
                print("\n🎉 SUCCESS! Enhanced furigana processing completed!")
                print("   ✅ Comprehensive kanji detection!")
                print("   ✅ AI-powered contextual readings!")
                print("   ✅ JSON and SRT output formats!")
            else:
                print("\n❌ FAILED! Check error messages above.")
        else:
            print("❌ No subtitle files found")
            print("\n📖 Usage:")
            print("  python enhanced_furigana_burner.py                     # Auto-detect")
            print("  python enhanced_furigana_burner.py subtitles.json     # Process JSON")
            print("  python enhanced_furigana_burner.py subtitles.json video.mp4  # With video")
        
        return
    
    args = parser.parse_args()
    
    config = BurnerConfig(
        main_font_size=args.main_font_size,
        furigana_font_size=args.furigana_font_size,
        position=args.position,
        openai_model=args.openai_model,
        use_openai_cache=not args.no_cache
    )
    
    app = EnhancedFuriganaBurnerApp(config)
    success = app.process_subtitles(args.input, args.video, args.output_dir)
    
    if success:
        print("\n🎉 SUCCESS! Enhanced furigana processing completed!")
    else:
        print("\n❌ FAILED! Check error messages above.")


if __name__ == "__main__":
    main()
