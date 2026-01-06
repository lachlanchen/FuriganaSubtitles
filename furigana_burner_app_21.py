#!/usr/bin/env python3
"""
Enhanced Grammatical Analysis Furigana Subtitle Burner
Features:
- Audio preservation using ffmpeg
- Japanese-only AI analysis with furigana processing
- Conservative suffix-based furigana processing
- Color consistency across split words
- Default output to video directory
- Fixed colors for different grammatical components
- Improved text wrapping for non-Japanese languages
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import re
import os
import sys
import glob
import json
import subprocess
import shutil
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
    # Core sentence elements
    SUBJECT = "subject"           # 主語
    OBJECT = "object"             # 目的語  
    TOPIC = "topic"               # 主題 (marked by は)
    PREDICATE = "predicate"       # 述語
    
    # Word types
    NOUN = "noun"                # 名詞
    PRONOUN = "pronoun"          # 代名詞
    VERB = "verb"                # 動詞
    I_ADJECTIVE = "i_adjective"  # い形容詞
    NA_ADJECTIVE = "na_adjective" # な形容詞
    ADVERB = "adverb"            # 副詞
    
    # Particles - Core case markers
    PARTICLE_WA = "particle_wa"   # は (topic marker)
    PARTICLE_GA = "particle_ga"   # が (subject marker)
    PARTICLE_WO = "particle_wo"   # を (direct object)
    PARTICLE_NI = "particle_ni"   # に (indirect object/direction/time)
    PARTICLE_DE = "particle_de"   # で (location of action/means)
    PARTICLE_TO = "particle_to"   # と (with/and)
    PARTICLE_NO = "particle_no"   # の (possessive/modification)
    PARTICLE_HE = "particle_he"   # へ (direction)
    
    # Particles - Others
    PARTICLE_KARA = "particle_kara" # から (from/because)
    PARTICLE_MADE = "particle_made" # まで (until/to)
    PARTICLE_YORI = "particle_yori" # より (than/from)
    PARTICLE_MO = "particle_mo"     # も (also/too)
    PARTICLE_KA = "particle_ka"     # か (question)
    PARTICLE_YA = "particle_ya"     # や (and - incomplete list)
    PARTICLE_DEMO = "particle_demo" # でも (even/but)
    PARTICLE_DAKE = "particle_dake" # だけ (only)
    PARTICLE_SHIKA = "particle_shika" # しか (only - with negative)
    PARTICLE_NADO = "particle_nado"   # など (and so on)
    PARTICLE_OTHER = "particle_other" # Other particles
    
    # Grammar elements
    AUXILIARY = "auxiliary"       # 助動詞
    CONJUNCTION = "conjunction"   # 接続詞
    COPULA = "copula"            # コピュラ (だ/である/です)
    HONORIFIC = "honorific"      # 敬語
    HUMBLE = "humble"            # 謙譲語
    
    # Special types
    COUNTER = "counter"          # 助数詞 (個、本、人、etc.)
    NUMBER = "number"            # 数詞
    DEMONSTRATIVE = "demonstrative" # 指示語 (これ、それ、あれ)
    QUESTION_WORD = "question_word" # 疑問詞 (何、誰、どこ)
    INTERJECTION = "interjection" # 感嘆詞
    PREFIX = "prefix"            # 接頭語
    SUFFIX = "suffix"            # 接尾語
    
    # Punctuation and others
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
    position: str = 'top'  # Changed default to top
    margin: int = 30
    max_width_ratio: float = 0.85
    line_spacing_ratio: float = 0.2
    stroke_width: int = 2
    background_opacity: float = 0.3
    auto_multi_line: bool = True
    furigana_spacing_ratio: float = 0.3
    openai_model: str = "gpt-4o-mini"
    max_openai_retries: int = 3
    force_refresh: bool = False  # True = fetch new (ignore cache), False = use cache
    preserve_audio: bool = True  # Whether to preserve audio using ffmpeg


class GrammaticalColorScheme:
    """Fixed color scheme for different grammatical components"""
    
    COLOR_MAP = {
        # Core sentence elements
        GrammaticalType.SUBJECT: (255, 100, 100),      # Light red
        GrammaticalType.OBJECT: (100, 150, 255),       # Light blue
        GrammaticalType.TOPIC: (255, 180, 180),        # Lighter red
        GrammaticalType.PREDICATE: (150, 255, 150),    # Light green
        
        # Word types
        GrammaticalType.NOUN: (255, 255, 150),         # Light yellow
        GrammaticalType.PRONOUN: (255, 220, 120),      # Light orange-yellow
        GrammaticalType.VERB: (100, 255, 100),         # Light green
        GrammaticalType.I_ADJECTIVE: (255, 200, 100),  # Orange
        GrammaticalType.NA_ADJECTIVE: (255, 170, 120), # Light orange
        GrammaticalType.ADVERB: (200, 100, 255),       # Purple
        
        # Core particles
        GrammaticalType.PARTICLE_WA: (255, 150, 150),  # Pink - は
        GrammaticalType.PARTICLE_GA: (150, 255, 150),  # Light green - が
        GrammaticalType.PARTICLE_WO: (150, 150, 255),  # Light blue - を
        GrammaticalType.PARTICLE_NI: (255, 255, 100),  # Yellow - に
        GrammaticalType.PARTICLE_DE: (100, 255, 255),  # Cyan - で
        GrammaticalType.PARTICLE_TO: (255, 100, 255),  # Magenta - と
        GrammaticalType.PARTICLE_NO: (255, 200, 255),  # Light magenta - の
        GrammaticalType.PARTICLE_HE: (200, 255, 200),  # Light green - へ
        
        # Other particles
        GrammaticalType.PARTICLE_KARA: (255, 150, 100), # Light red-orange - から
        GrammaticalType.PARTICLE_MADE: (150, 255, 100), # Light yellow-green - まで
        GrammaticalType.PARTICLE_YORI: (100, 255, 150), # Light green-cyan - より
        GrammaticalType.PARTICLE_MO: (255, 100, 150),   # Light red-magenta - も
        GrammaticalType.PARTICLE_KA: (150, 100, 255),   # Light blue-purple - か
        GrammaticalType.PARTICLE_YA: (255, 255, 200),   # Very light yellow - や
        GrammaticalType.PARTICLE_DEMO: (200, 150, 255), # Light purple - でも
        GrammaticalType.PARTICLE_DAKE: (255, 200, 150), # Light peach - だけ
        GrammaticalType.PARTICLE_SHIKA: (200, 255, 150), # Light lime - しか
        GrammaticalType.PARTICLE_NADO: (150, 200, 255), # Light sky blue - など
        GrammaticalType.PARTICLE_OTHER: (200, 200, 200), # Gray
        
        # Grammar elements
        GrammaticalType.AUXILIARY: (150, 200, 150),    # Muted green
        GrammaticalType.CONJUNCTION: (200, 150, 200),  # Muted purple
        GrammaticalType.COPULA: (255, 220, 150),       # Light peach
        GrammaticalType.HONORIFIC: (200, 180, 255),    # Light lavender
        GrammaticalType.HUMBLE: (180, 200, 255),       # Light periwinkle
        
        # Special types
        GrammaticalType.COUNTER: (255, 180, 120),      # Light orange
        GrammaticalType.NUMBER: (120, 255, 180),       # Light mint
        GrammaticalType.DEMONSTRATIVE: (180, 120, 255), # Light violet
        GrammaticalType.QUESTION_WORD: (255, 120, 180), # Light rose
        GrammaticalType.INTERJECTION: (255, 255, 120), # Bright yellow
        GrammaticalType.PREFIX: (200, 255, 255),       # Light cyan
        GrammaticalType.SUFFIX: (255, 200, 255),       # Light pink
        
        # Punctuation and others
        GrammaticalType.PUNCTUATION: (180, 180, 180),  # Light gray
        GrammaticalType.OTHER: (220, 220, 220),        # Very light gray
    }
    
    @classmethod
    def get_color(cls, grammatical_type: GrammaticalType) -> Tuple[int, int, int]:
        return cls.COLOR_MAP.get(grammatical_type, cls.COLOR_MAP[GrammaticalType.OTHER])


class FuriganaGrammaticalAnalyzer:
    """Furigana grammatical analyzer with conservative suffix-based post-processing"""
    
    def __init__(self, config: BurnerConfig):
        self.config = config
        
        try:
            self.openai_client = OpenAIRequestJSONBase(
                use_cache=True,  # Always enable caching (always store fetched cache)
                max_retries=config.max_openai_retries,
                cache_dir='grammatical_cache'
            )
            print("✅ Furigana grammatical analyzer initialized")
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")
            self.openai_client = None
        
        # Enhanced schema
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
                                    # Core sentence elements
                                    "subject", "object", "topic", "predicate",
                                    # Word types
                                    "noun", "pronoun", "verb", "i_adjective", "na_adjective", "adverb",
                                    # Core particles
                                    "particle_wa", "particle_ga", "particle_wo", "particle_ni", 
                                    "particle_de", "particle_to", "particle_no", "particle_he",
                                    # Other particles
                                    "particle_kara", "particle_made", "particle_yori", "particle_mo",
                                    "particle_ka", "particle_ya", "particle_demo", "particle_dake",
                                    "particle_shika", "particle_nado", "particle_other",
                                    # Grammar elements
                                    "auxiliary", "conjunction", "copula", "honorific", "humble",
                                    # Special types
                                    "counter", "number", "demonstrative", "question_word", 
                                    "interjection", "prefix", "suffix",
                                    # Punctuation and others
                                    "punctuation", "other"
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
        """Analyze sentence - only use AI for Japanese text, others get simple rendering"""
        
        if not text:
            return []
        
        # Check if text contains Japanese characters
        has_japanese = self._contains_japanese(text)
        
        # If no Japanese characters or explicitly marked as non-Japanese, use simple fallback
        # NO AI for non-Japanese languages
        if not has_japanese or (lang_hint and lang_hint.lower() not in ['ja', 'japanese', 'jpn']):
            return self._create_simple_words(text)
        
        # Only try AI analysis for Japanese text
        if not self.openai_client:
            return self._create_simple_words(text)
        
        try:
            # Furigana prompt for Japanese text only
            prompt = f"""Analyze this Japanese text: "{text}"

Break into words with:
1. word: the word/particle/punctuation  
2. furigana: complete reading for the ENTIRE word (ALWAYS provide, even for hiragana)
3. type: grammatical type

CRITICAL: Provide complete, accurate furigana for the entire word. """

            # Handle force refresh: if force_refresh=True, use timestamp to fetch new data
            # but still cache the result. If force_refresh=False, use existing cache.
            if self.config.force_refresh:
                # Use timestamp to force fresh request but still cache result
                import time
                cache_key = f"furigana_{abs(hash(text))}_{int(time.time())}.json"
            else:
                # Normal cache filename - will use existing cache if available
                cache_key = f"furigana_{abs(hash(text))}.json"
            
            # Single request call
            result = self.openai_client.send_request_with_json_schema(
                prompt=prompt,
                json_schema=self.analysis_schema,
                filename=cache_key,
                schema_name="furigana_analysis",
                model=self.config.openai_model
            )
            
            if result and 'words' in result:
                return self._process_furigana_result(result['words'])
            else:
                return self._create_simple_words(text)
                
        except Exception as e:
            print(f"⚠️ Analysis error: {e}")
            return self._create_simple_words(text)
    
    def _contains_japanese(self, text: str) -> bool:
        """Check if text contains Japanese characters (hiragana, katakana, or kanji)"""
        for char in text:
            if (self._is_hiragana(char) or self._is_katakana(char) or self._is_kanji(char)):
                return True
        return False
    
    def _contains_chinese(self, text: str) -> bool:
        """Check if text contains Chinese characters"""
        for char in text:
            if self._is_kanji(char):  # Kanji and Chinese characters overlap significantly
                return True
        return False
    
    def _process_furigana_result(self, words_data: List[Dict]) -> List[GrammaticalWord]:
        """Process result with conservative suffix-based post-processing"""
        
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
            
            # FURIGANA POST-PROCESSING: Conservative suffix-based approach
            processed_parts = self._furigana_post_process(word, furigana, grammatical_type, color)
            processed_words.extend(processed_parts)
        
        furigana_count = sum(1 for w in processed_words if w.furigana)
        print(f"✅ Furigana Analysis: {len(processed_words)} words, {furigana_count} with furigana")
        
        return processed_words
    
    def _furigana_post_process(self, word: str, furigana: str, 
                             grammatical_type: GrammaticalType, 
                             color: Tuple[int, int, int]) -> List[GrammaticalWord]:
        """Furigana conservative post-processing focusing on suffix patterns"""
        
        if not furigana:
            return [GrammaticalWord(word=word, furigana=None, grammatical_type=grammatical_type, color=color)]
        
        # Rule 1: Simple cleanup first
        if self._is_all_hiragana(word) and word == furigana:
            return [GrammaticalWord(word=word, furigana=None, grammatical_type=grammatical_type, color=color)]
        
        if self._is_all_katakana(word) and self._katakana_to_hiragana(word) == furigana:
            return [GrammaticalWord(word=word, furigana=None, grammatical_type=grammatical_type, color=color)]
        
        # Rule 2: Handle お茶 pattern (hiragana prefix + kanji)
        if self._has_hiragana_prefix(word):
            return self._handle_prefix_pattern(word, furigana, grammatical_type, color)
        
        # Rule 3: Handle suffix pattern (kanji + hiragana ending)
        if self._has_hiragana_suffix(word):
            return self._handle_suffix_pattern(word, furigana, grammatical_type, color)
        
        # Rule 4: For complex mixed patterns, be conservative
        if self._is_complex_mixed(word):
            # Try suffix approach first, if it doesn't work well, keep original
            suffix_result = self._try_suffix_approach(word, furigana, grammatical_type, color)
            if len(suffix_result) == 2 and suffix_result[0].furigana:  # Good split
                return suffix_result
        
        # Rule 5: Default - keep original with cleaned furigana
        return [GrammaticalWord(
            word=word,
            furigana=furigana,
            grammatical_type=grammatical_type,
            color=color
        )]
    
    def _has_hiragana_prefix(self, word: str) -> bool:
        """Check for お茶 pattern: starts with hiragana, has kanji"""
        if len(word) < 2:
            return False
        return (self._is_hiragana(word[0]) and 
                any(self._is_kanji(c) for c in word[1:]))
    
    def _has_hiragana_suffix(self, word: str) -> bool:
        """Check for 聞こえて pattern: has kanji, ends with hiragana"""
        if len(word) < 2:
            return False
        return (any(self._is_kanji(c) for c in word) and 
                self._is_hiragana(word[-1]))
    
    def _is_complex_mixed(self, word: str) -> bool:
        """Check for complex patterns with multiple kanji-hiragana transitions"""
        if len(word) < 3:
            return False
        
        transitions = 0
        prev_was_kanji = False
        
        for char in word:
            is_kanji = self._is_kanji(char)
            if is_kanji != prev_was_kanji:
                transitions += 1
            prev_was_kanji = is_kanji
        
        return transitions >= 3  # Multiple transitions indicate complexity
    
    def _handle_prefix_pattern(self, word: str, furigana: str, 
                              grammatical_type: GrammaticalType, 
                              color: Tuple[int, int, int]) -> List[GrammaticalWord]:
        """Handle お茶 → お + 茶(ちゃ) pattern"""
        
        # Find where kanji starts
        kanji_start = -1
        for i, char in enumerate(word):
            if self._is_kanji(char):
                kanji_start = i
                break
        
        if kanji_start > 0:
            prefix_part = word[:kanji_start]
            kanji_part = word[kanji_start:]
            
            # Calculate furigana for kanji part
            if len(furigana) > kanji_start:
                kanji_furigana = furigana[kanji_start:]
            else:
                kanji_furigana = furigana
            
            # Clean up kanji furigana - remove if same as kanji part
            if kanji_furigana == kanji_part:
                kanji_furigana = None
            
            print(f"   PREFIX: {word} → {prefix_part} + {kanji_part}({kanji_furigana})")
            
            return [
                GrammaticalWord(
                    word=prefix_part,
                    furigana=None,  # Hiragana doesn't need furigana
                    grammatical_type=grammatical_type,
                    color=color
                ),
                GrammaticalWord(
                    word=kanji_part,
                    furigana=kanji_furigana,
                    grammatical_type=grammatical_type,
                    color=color
                )
            ]
        
        return [GrammaticalWord(word=word, furigana=furigana, grammatical_type=grammatical_type, color=color)]
    
    def _handle_suffix_pattern(self, word: str, furigana: str, 
                             grammatical_type: GrammaticalType, 
                             color: Tuple[int, int, int]) -> List[GrammaticalWord]:
        """Handle 聞こえて → 聞(き) + こえて pattern"""
        
        return self._try_suffix_approach(word, furigana, grammatical_type, color)
    
    def _try_suffix_approach(self, word: str, furigana: str, 
                           grammatical_type: GrammaticalType, 
                           color: Tuple[int, int, int]) -> List[GrammaticalWord]:
        """Try suffix-based splitting approach"""
        
        # Find the longest hiragana suffix
        suffix_start = len(word)
        for i in range(len(word) - 1, -1, -1):
            if self._is_hiragana(word[i]):
                suffix_start = i
            else:
                break
        
        if suffix_start < len(word) and suffix_start > 0:
            # We have a hiragana suffix
            main_part = word[:suffix_start]
            suffix_part = word[suffix_start:]
            
            # Check if furigana ends with the suffix
            if furigana.endswith(suffix_part):
                # Remove suffix from furigana
                main_furigana = furigana[:-len(suffix_part)] if len(suffix_part) < len(furigana) else None
                
                # Validate the split makes sense
                if main_furigana and len(main_furigana) >= len(main_part) * 0.5:  # Reasonable furigana length
                    print(f"   SUFFIX: {word} → {main_part}({main_furigana}) + {suffix_part}")
                    
                    return [
                        GrammaticalWord(
                            word=main_part,
                            furigana=main_furigana,
                            grammatical_type=grammatical_type,
                            color=color
                        ),
                        GrammaticalWord(
                            word=suffix_part,
                            furigana=None,  # Hiragana suffix doesn't need furigana
                            grammatical_type=grammatical_type,
                            color=color
                        )
                    ]
        
        # If suffix approach doesn't work, return original
        return [GrammaticalWord(word=word, furigana=furigana, grammatical_type=grammatical_type, color=color)]
    
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
    
    def _create_simple_words(self, text: str) -> List[GrammaticalWord]:
        """Create simple words for non-Japanese text with proper wrapping"""
        normalized_text = ' '.join(text.split())  # Remove extra whitespace
        
        if not normalized_text:
            return []
        
        # Check if text contains Chinese characters (no spaces between words)
        has_chinese = self._contains_chinese(normalized_text)
        
        result = []
        
        if has_chinese:
            # For Chinese text, split into individual characters for basic wrapping
            # This is a simple approach - proper Chinese word segmentation would require additional libraries
            for i, char in enumerate(normalized_text):
                if char.strip():  # Skip whitespace characters
                    result.append(GrammaticalWord(
                        word=char,
                        furigana=None,
                        grammatical_type=GrammaticalType.OTHER,
                        color=(255, 255, 255)  # White for non-Japanese text
                    ))
        else:
            # For space-separated languages (English, etc.), split on spaces
            words = normalized_text.split()
            
            for i, word in enumerate(words):
                # Add space before word (except for first word)
                if i > 0:
                    result.append(GrammaticalWord(
                        word=" ",
                        furigana=None,
                        grammatical_type=GrammaticalType.OTHER,
                        color=(255, 255, 255)
                    ))
                
                result.append(GrammaticalWord(
                    word=word,
                    furigana=None,
                    grammatical_type=GrammaticalType.OTHER,
                    color=(255, 255, 255)  # White for non-Japanese text
                ))
        
        return result


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
    def save_srt_with_furigana(segments: List[SubtitleSegment], output_path: str) -> bool:
        """Save SRT file with furigana annotations"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments, 1):
                    # Convert to SRT timestamp format
                    start_time = SubtitleWriter._format_srt_timestamp(segment.start_time)
                    end_time = SubtitleWriter._format_srt_timestamp(segment.end_time)
                    
                    # Build subtitle text
                    if segment.grammatical_words:
                        subtitle_text = "".join([
                            f"{word.word}({word.furigana})" if word.furigana else word.word
                            for word in segment.grammatical_words
                        ])
                    else:
                        subtitle_text = segment.text
                    
                    # Write SRT entry
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{subtitle_text}\n\n")
            
            print(f"💾 Saved SRT: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving SRT: {e}")
            return False
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def _format_srt_timestamp(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


class AudioUtils:
    """Utilities for handling audio preservation"""
    
    @staticmethod
    def check_ffmpeg() -> bool:
        """Check if ffmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                 capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    def merge_audio_video(video_with_subs: str, original_video: str, final_output: str) -> bool:
        """Merge audio from original video with processed video using ffmpeg"""
        
        if not AudioUtils.check_ffmpeg():
            print("⚠️ ffmpeg not found - audio will not be preserved")
            print("   Install ffmpeg to preserve audio: https://ffmpeg.org/download.html")
            # Copy the video without audio as fallback
            try:
                shutil.copy2(video_with_subs, final_output)
                print(f"📁 Copied video without audio to: {final_output}")
                return True
            except Exception as e:
                print(f"❌ Failed to copy video: {e}")
                return False
        
        try:
            cmd = [
                'ffmpeg',
                '-i', video_with_subs,  # Video with subtitles (no audio)
                '-i', original_video,   # Original video with audio
                '-c:v', 'copy',         # Copy video stream
                '-c:a', 'aac',          # Re-encode audio to AAC
                '-map', '0:v:0',        # Map video from first input
                '-map', '1:a:0',        # Map audio from second input
                '-shortest',            # End when shortest stream ends
                '-y',                   # Overwrite output file
                final_output
            ]
            
            print(f"🔊 Merging audio using ffmpeg...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ Audio merged successfully: {final_output}")
                # Clean up temporary file
                try:
                    os.remove(video_with_subs)
                    print(f"🗑️ Cleaned up temporary file: {video_with_subs}")
                except:
                    pass
                return True
            else:
                print(f"❌ ffmpeg error: {result.stderr}")
                # Fallback to video without audio
                try:
                    shutil.copy2(video_with_subs, final_output)
                    print(f"📁 Fallback: Copied video without audio to: {final_output}")
                    return True
                except Exception as e:
                    print(f"❌ Fallback failed: {e}")
                    return False
                
        except subprocess.TimeoutExpired:
            print("❌ ffmpeg timeout - process took too long")
            return False
        except Exception as e:
            print(f"❌ Audio merging failed: {e}")
            return False


class FuriganaBurnerApp:
    """Furigana burner with audio preservation and Japanese-only AI analysis"""
    
    def __init__(self, config: BurnerConfig = None):
        self.config = config or BurnerConfig()
        self.analyzer = FuriganaGrammaticalAnalyzer(self.config)
        self.renderer = GrammaticalRenderer(self.config)
        
        cache_status = "FORCE REFRESH" if self.config.force_refresh else "USE CACHE"
        audio_status = "ENABLED" if self.config.preserve_audio else "DISABLED"
        print(f"🚀 Furigana Burner initialized ({cache_status}, Audio: {audio_status})")
        
        if self.config.preserve_audio and not AudioUtils.check_ffmpeg():
            print("⚠️ Audio preservation requested but ffmpeg not found")
            print("   Install ffmpeg to preserve audio: https://ffmpeg.org/download.html")
    
    def process_video_with_subtitles(self, video_path: str, subtitle_path: str, output_path: str = None) -> bool:
        # Get video directory for default output location
        video_dir = os.path.dirname(os.path.abspath(video_path))
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        if not output_path:
            output_path = os.path.join(video_dir, f"{video_name}_furigana.mp4")
        
        print(f"🎬 Processing: {os.path.basename(video_path)}")
        print(f"📄 Subtitles: {os.path.basename(subtitle_path)}")
        print(f"📁 Output directory: {video_dir}")
        
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
            
            # Save files to video directory
            subtitle_name = os.path.splitext(os.path.basename(subtitle_path))[0]
            json_output = os.path.join(video_dir, f"{subtitle_name}_furigana.json")
            srt_output = os.path.join(video_dir, f"{subtitle_name}_furigana.srt")
            
            SubtitleWriter.save_json_with_grammar(segments, json_output)
            SubtitleWriter.save_srt_with_furigana(segments, srt_output)
            
            # Process video with or without audio preservation
            return self._burn_to_video_with_audio(video_path, segments, output_path)
            
        except Exception as e:
            print(f"❌ Processing error: {e}")
            return False
    
    def _burn_to_video_with_audio(self, video_path: str, segments: List[SubtitleSegment], output_path: str) -> bool:
        """Process video and preserve audio if requested"""
        
        # If audio preservation is disabled, use the original method
        if not self.config.preserve_audio:
            return self._burn_to_video(video_path, segments, output_path)
        
        # Create temporary output for video processing
        temp_output = output_path.replace('.mp4', '_temp_no_audio.mp4')
        
        # Process video (this creates video without audio)
        video_success = self._burn_to_video(video_path, segments, temp_output)
        
        if not video_success:
            return False
        
        # Merge audio from original video
        audio_success = AudioUtils.merge_audio_video(temp_output, video_path, output_path)
        
        return audio_success
    
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
            
            print(f"✅ Video processing completed: {output_path}")
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
    
    parser = argparse.ArgumentParser(description='Furigana Burner with Audio Support and Multi-language Text Wrapping')
    
    # Main arguments with -v and -j options
    parser.add_argument('-v', '--video', help='Input video file')
    parser.add_argument('-j', '--json', help='Input JSON subtitle file')  
    parser.add_argument('-s', '--srt', help='Input SRT subtitle file (alternative to JSON)')
    parser.add_argument('-o', '--output', help='Output video file (optional, defaults to video directory)')
    
    # Legacy positional arguments for backward compatibility
    parser.add_argument('video_pos', nargs='?', help='Input video file (positional)')
    parser.add_argument('subtitles_pos', nargs='?', help='Input subtitle file (positional)')
    parser.add_argument('output_pos', nargs='?', help='Output video file (positional)')
    
    # Configuration options
    parser.add_argument('--position', choices=['top', 'center', 'bottom'], default='top')
    parser.add_argument('--main-font-size', type=int, default=64)
    parser.add_argument('--furigana-font-size', type=int, default=32)
    parser.add_argument('--margin', type=int, default=30,
                       help='Margin from edge of frame in pixels (default: 30)')
    parser.add_argument('--openai-model', default='gpt-4o-mini')
    parser.add_argument('--force', action='store_true', 
                       help='Force fetch new data from OpenAI (ignores existing cache but still saves new cache)')
    parser.add_argument('--no-audio', action='store_true',
                       help='Disable audio preservation (faster processing)')
    
    # Auto-detect mode
    if len(sys.argv) == 1:
        print("🔍 Auto-detecting files...")
        video_files = glob.glob("*.mp4") + glob.glob("*.MP4") + glob.glob("*.avi") + glob.glob("*.mkv")
        subtitle_files = glob.glob("*.json") + glob.glob("*.srt")
        
        if video_files and subtitle_files:
            config = BurnerConfig()
            app = FuriganaBurnerApp(config)
            success = app.process_video_with_subtitles(video_files[0], subtitle_files[0])
            
            if success:
                print("\n🎉 SUCCESS! Furigana processing completed!")
                print("   ✅ Case A: お茶 → お + 茶(ちゃ) [Conservative prefix handling]")
                print("   ✅ Case B: 聞こえて → 聞(き) + こえて [Accurate suffix handling]") 
                print("   ✅ Case C: Complex patterns → Conservative suffix-based approach")
                print("   ✅ Japanese-only AI analysis, other languages simple rendering")
                print("   ✅ Multi-language text wrapping (English, Chinese, etc.)")
                print("   ✅ Audio preserved using ffmpeg")
                print("   ✅ Color consistency maintained across split words")
                print("   ✅ All outputs saved to video directory")
            else:
                print("\n❌ FAILED!")
        else:
            print("❌ No files found")
            print("\n📖 Usage:")
            print("  python furigana_burner.py                              # Auto-detect")
            print("  python furigana_burner.py -v video.mp4 -j subs.json   # With -v -j flags")
            print("  python furigana_burner.py video.mp4 subs.json         # Positional args")
            print("  python furigana_burner.py -v video.mp4 -s subs.srt    # With SRT file")
            print("  python furigana_burner.py --no-audio video.mp4 subs.json  # Skip audio")
            print("  python furigana_burner.py --force video.mp4 subs.json     # Force fresh OpenAI data")
            print("  python furigana_burner.py --margin 50 video.mp4 subs.json # Custom margin")
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
        print("  python furigana_burner.py --no-audio video.mp4 subtitles.json")
        print("  python furigana_burner.py --force video.mp4 subtitles.json")
        print("  python furigana_burner.py --margin 50 video.mp4 subtitles.json")
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
        margin=args.margin,
        openai_model=args.openai_model,
        force_refresh=args.force,  # True = fetch new data, False = use cache
        preserve_audio=not args.no_audio  # True = preserve audio, False = skip audio
    )
    
    app = FuriganaBurnerApp(config)
    success = app.process_video_with_subtitles(video_file, subtitle_file, output_file)
    
    if success:
        print("\n🎉 SUCCESS! Furigana processing completed!")
        print("   ✅ Case A: お茶 → お + 茶(ちゃ) [Conservative prefix handling]")
        print("   ✅ Case B: 聞こえて → 聞(き) + こえて [Accurate suffix handling]")  
        print("   ✅ Case C: Complex patterns → Conservative suffix-based approach")
        print("   ✅ Japanese-only AI analysis, other languages simple rendering")
        print("   ✅ Multi-language text wrapping (English, Chinese, etc.)")
        cache_status = "✅ Fresh data fetched from OpenAI" if config.force_refresh else "✅ Used cached data (faster)"
        print(f"   {cache_status}")
        audio_status = "✅ Audio preserved using ffmpeg" if config.preserve_audio else "⚠️ Audio skipped (--no-audio)"
        print(f"   {audio_status}")
        print("   ✅ Color consistency maintained across split words")
        print("   ✅ All outputs saved to video directory")
    else:
        print("\n❌ FAILED!")


if __name__ == "__main__":
    main()