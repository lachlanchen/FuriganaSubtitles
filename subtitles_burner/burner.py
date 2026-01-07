#!/usr/bin/env python3
"""
Generalized subtitle burner with ruby (furigana/pinyin) support.
Supports per-token colors and standard subtitle rendering.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    import fugashi
    import unidic

    FUGASHI_AVAILABLE = True
except Exception:
    FUGASHI_AVAILABLE = False

try:
    import pykakasi

    KAKASI_AVAILABLE = True
except Exception:
    KAKASI_AVAILABLE = False

try:
    from phonemizer import phonemize

    PHONEMIZER_AVAILABLE = True
except Exception:
    PHONEMIZER_AVAILABLE = False

try:
    from koroman import romanize as koroman_romanize

    KOROMAN_AVAILABLE = True
except Exception:
    KOROMAN_AVAILABLE = False

try:
    from pypinyin import Style, pinyin as pypinyin

    PINYIN_AVAILABLE = True
except Exception:
    PINYIN_AVAILABLE = False

try:
    from pycantonese import characters_to_jyutping  # type: ignore

    JYUTPING_AVAILABLE = True
except Exception:
    JYUTPING_AVAILABLE = False

try:
    from camel_tools.utils.charmap import CharMapper

    ARABIC_TRANSLIT_AVAILABLE = True
    ARABIC_CHAR_MAPPER = CharMapper.builtin_mapper("ar2bw")
except Exception:
    ARABIC_TRANSLIT_AVAILABLE = False
    ARABIC_CHAR_MAPPER = None

ROMAJI_CONVERTER = None
if KAKASI_AVAILABLE:
    try:
        kakasi = pykakasi.kakasi()
        kakasi.setMode("H", "a")
        kakasi.setMode("K", "a")
        kakasi.setMode("J", "a")
        kakasi.setMode("r", "Hepburn")
        ROMAJI_CONVERTER = kakasi.getConverter()
    except Exception:
        ROMAJI_CONVERTER = None

KANA_ROMAJI_BASE = {
    "あ": "a",
    "い": "i",
    "う": "u",
    "え": "e",
    "お": "o",
    "か": "ka",
    "き": "ki",
    "く": "ku",
    "け": "ke",
    "こ": "ko",
    "さ": "sa",
    "し": "shi",
    "す": "su",
    "せ": "se",
    "そ": "so",
    "た": "ta",
    "ち": "chi",
    "つ": "tsu",
    "て": "te",
    "と": "to",
    "な": "na",
    "に": "ni",
    "ぬ": "nu",
    "ね": "ne",
    "の": "no",
    "は": "ha",
    "ひ": "hi",
    "ふ": "fu",
    "へ": "he",
    "ほ": "ho",
    "ま": "ma",
    "み": "mi",
    "む": "mu",
    "め": "me",
    "も": "mo",
    "や": "ya",
    "ゆ": "yu",
    "よ": "yo",
    "ら": "ra",
    "り": "ri",
    "る": "ru",
    "れ": "re",
    "ろ": "ro",
    "わ": "wa",
    "を": "o",
    "ん": "n",
    "が": "ga",
    "ぎ": "gi",
    "ぐ": "gu",
    "げ": "ge",
    "ご": "go",
    "ざ": "za",
    "じ": "ji",
    "ず": "zu",
    "ぜ": "ze",
    "ぞ": "zo",
    "だ": "da",
    "ぢ": "ji",
    "づ": "zu",
    "で": "de",
    "ど": "do",
    "ば": "ba",
    "び": "bi",
    "ぶ": "bu",
    "べ": "be",
    "ぼ": "bo",
    "ぱ": "pa",
    "ぴ": "pi",
    "ぷ": "pu",
    "ぺ": "pe",
    "ぽ": "po",
    "ぁ": "a",
    "ぃ": "i",
    "ぅ": "u",
    "ぇ": "e",
    "ぉ": "o",
    "ゃ": "ya",
    "ゅ": "yu",
    "ょ": "yo",
}

KANA_ROMAJI_DIGRAPHS = {
    "きゃ": "kya",
    "きゅ": "kyu",
    "きょ": "kyo",
    "ぎゃ": "gya",
    "ぎゅ": "gyu",
    "ぎょ": "gyo",
    "しゃ": "sha",
    "しゅ": "shu",
    "しょ": "sho",
    "じゃ": "ja",
    "じゅ": "ju",
    "じょ": "jo",
    "ちゃ": "cha",
    "ちゅ": "chu",
    "ちょ": "cho",
    "にゃ": "nya",
    "にゅ": "nyu",
    "にょ": "nyo",
    "ひゃ": "hya",
    "ひゅ": "hyu",
    "ひょ": "hyo",
    "みゃ": "mya",
    "みゅ": "myu",
    "みょ": "myo",
    "りゃ": "rya",
    "りゅ": "ryu",
    "りょ": "ryo",
    "びゃ": "bya",
    "びゅ": "byu",
    "びょ": "byo",
    "ぴゃ": "pya",
    "ぴゅ": "pyu",
    "ぴょ": "pyo",
    "ゔぁ": "va",
    "ゔぃ": "vi",
    "ゔぇ": "ve",
    "ゔぉ": "vo",
    "ゔゅ": "vyu",
}

SPEAKER_ICON_PATH = Path(__file__).resolve().parent / "assets" / "speaker.png"


@dataclass
class RubyToken:
    text: str
    ruby: Optional[str] = None
    color: Optional[tuple[int, int, int]] = None
    token_type: Optional[str] = None


@dataclass
class SubtitleSegment:
    start_time: float
    end_time: float
    tokens: list[RubyToken]
    text: str


@dataclass
class TextStyle:
    main_font_size: int = 48
    ruby_font_size: int = 24
    text_color: tuple[int, int, int] = (255, 255, 255)
    stroke_color: tuple[int, int, int] = (0, 0, 0)
    stroke_width: int = 2
    line_spacing: float = 1.2
    ruby_spacing: float = 0.3


@dataclass
class Slot:
    slot_id: int
    x: int
    y: int
    width: int
    height: int
    align: str = "center"


@dataclass
class BurnLayout:
    slots: list[Slot]


@dataclass
class SlotAssignment:
    slot_id: int
    language: str
    json_path: str
    text_key: str
    ruby_key: Optional[str] = None
    tokens_key: str = "tokens"
    pairs_key: str = "furigana_pairs"
    palette: Optional[dict[str, Any]] = None
    style: Optional[TextStyle] = None
    auto_ruby: bool = False
    strip_kana: bool = False
    kana_romaji: bool = False
    pinyin: bool = False
    ipa_lang: Optional[str] = None
    jyutping: bool = False
    korean_romaja: bool = False
    arabic_translit: bool = False


class FuriganaGenerator:
    """Generate ruby for Japanese text using available libraries."""

    def __init__(self) -> None:
        self.tagger = None
        self.kakasi = None

        if FUGASHI_AVAILABLE:
            try:
                self.tagger = fugashi.Tagger()
            except Exception:
                self.tagger = None

        if not self.tagger and KAKASI_AVAILABLE:
            try:
                kakasi = pykakasi.kakasi()
                kakasi.setMode("H", "a")
                kakasi.setMode("K", "a")
                kakasi.setMode("J", "H")
                self.kakasi = kakasi.getConverter()
            except Exception:
                self.kakasi = None

    def generate(self, text: str) -> list[RubyToken]:
        if self.tagger:
            return self._with_fugashi(text)
        if self.kakasi:
            return self._with_kakasi(text)
        return [RubyToken(text=text)]

    def _with_fugashi(self, text: str) -> list[RubyToken]:
        tokens: list[RubyToken] = []
        for word in self.tagger(text):
            surface = word.surface
            reading = word.feature.reading
            if reading and reading != "*":
                reading = self._katakana_to_hiragana(reading)
                tokens.append(RubyToken(text=surface, ruby=reading))
            else:
                tokens.append(RubyToken(text=surface))
        return tokens

    def _with_kakasi(self, text: str) -> list[RubyToken]:
        tokens: list[RubyToken] = []
        conversion = self.kakasi.do(text)
        for item in conversion:
            orig = item.get("orig", "")
            hira = item.get("hira")
            if hira and hira != orig:
                tokens.append(RubyToken(text=orig, ruby=hira))
            else:
                tokens.append(RubyToken(text=orig))
        return tokens

    @staticmethod
    def _katakana_to_hiragana(text: str) -> str:
        result = ""
        for char in text:
            if "\u30a1" <= char <= "\u30f6":
                result += chr(ord(char) - 0x60)
            else:
                result += char
        return result


class RubyRenderer:
    def __init__(self, style: TextStyle) -> None:
        self.style = style
        self.main_font = self._load_font(style.main_font_size)
        self.ruby_font = self._load_font(style.ruby_font_size)

    @staticmethod
    def _measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
        if not text:
            return 0, 0
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    @staticmethod
    def _split_kana_affixes(text: str) -> tuple[str, str, str]:
        prefix = ""
        for char in text:
            if _is_kana(char):
                prefix += char
            else:
                break

        suffix = ""
        for char in reversed(text):
            if _is_kana(char):
                suffix = char + suffix
            else:
                break

        core = text[len(prefix):len(text) - len(suffix) if suffix else len(text)]
        return prefix, core, suffix

    def _build_layout(self, tokens: list[RubyToken]) -> tuple[list[dict[str, Any]], int, int, int]:
        temp_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(temp_img)

        layout: list[dict[str, Any]] = []
        total_width = 0
        max_ruby_h = 0
        max_main_h = 0

        for token in tokens:
            if token.token_type == "speaker":
                icon_size = max(1, int(self.style.main_font_size * 0.9))
                main_w = main_h = icon_size
                ruby_w = ruby_h = 0
                prefix_w = core_w = suffix_w = 0
                column_w = main_w
                total_width += column_w
                max_main_h = max(max_main_h, main_h)
                layout.append(
                    {
                        "main_w": main_w,
                        "main_h": main_h,
                        "ruby_w": ruby_w,
                        "ruby_h": ruby_h,
                        "prefix_w": prefix_w,
                        "core_w": core_w,
                        "suffix_w": suffix_w,
                        "column_w": column_w,
                    }
                )
                continue
            main_w, main_h = self._measure_text(draw, token.text, self.main_font)
            ruby_w, ruby_h = self._measure_text(draw, token.ruby or "", self.ruby_font)

            prefix_w = core_w = suffix_w = 0
            if token.ruby and token.text and _has_kanji(token.text):
                prefix, core, suffix = self._split_kana_affixes(token.text)
                prefix_w, _ = self._measure_text(draw, prefix, self.main_font)
                core_w, _ = self._measure_text(draw, core, self.main_font)
                suffix_w, _ = self._measure_text(draw, suffix, self.main_font)

            column_w = main_w
            if token.ruby:
                if core_w > 0:
                    ruby_span = prefix_w + max(ruby_w, core_w) + suffix_w
                else:
                    ruby_span = ruby_w
                column_w = max(main_w, ruby_span)

            total_width += column_w
            max_ruby_h = max(max_ruby_h, ruby_h)
            max_main_h = max(max_main_h, main_h)

            layout.append(
                {
                    "main_w": main_w,
                    "main_h": main_h,
                    "ruby_w": ruby_w,
                    "ruby_h": ruby_h,
                    "prefix_w": prefix_w,
                    "core_w": core_w,
                    "suffix_w": suffix_w,
                    "column_w": column_w,
                }
            )

        return layout, total_width, max_ruby_h, max_main_h

    @staticmethod
    @lru_cache(maxsize=16)
    def _load_speaker_icon(size: int) -> Optional[Image.Image]:
        if size <= 0 or not SPEAKER_ICON_PATH.exists():
            return None
        try:
            img = Image.open(SPEAKER_ICON_PATH).convert("RGBA")
        except Exception:
            return None
        resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
        return img.resize((size, size), resample)

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        repo_root = Path(__file__).resolve().parents[2]
        local_fonts = [
            repo_root / "fonts" / "arial-unicode-ms.ttf",
            repo_root / "fonts" / "Noto_Sans" / "static" / "NotoSans-Regular.ttf",
            repo_root / "fonts" / "Noto_Sans" / "static" / "NotoSans-Medium.ttf",
        ]
        font_paths = [
            *(str(path) for path in local_fonts if path.exists()),
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
            "/Windows/Fonts/msgothic.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except Exception:
                continue
        return ImageFont.load_default()

    def measure_tokens(self, tokens: list[RubyToken]) -> tuple[int, int]:
        if not tokens:
            return 0, 0
        _, total_width, max_ruby_h, max_main_h = self._build_layout(tokens)
        ruby_row = max_ruby_h + int(self.style.ruby_font_size * self.style.ruby_spacing) if max_ruby_h else 0
        stroke_pad = max(0, int(self.style.stroke_width))
        return total_width + stroke_pad * 2, max_main_h + ruby_row + stroke_pad * 2

    def render_tokens(self, tokens: list[RubyToken], padding: int = 16) -> Image.Image:
        if not tokens:
            return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

        padding = max(padding, int(self.style.stroke_width * 2))
        layout, text_width, max_ruby_h, max_main_h = self._build_layout(tokens)
        ruby_row = max_ruby_h + int(self.style.ruby_font_size * self.style.ruby_spacing) if max_ruby_h else 0
        text_height = max_main_h + ruby_row
        width = max(text_width + padding * 2, 1)
        height = max(text_height + padding * 2, 1)
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        start_x = padding
        start_y = padding
        current_x = start_x

        for token, metrics in zip(tokens, layout):
            main_w = metrics["main_w"]
            main_h = metrics["main_h"]
            ruby_w = metrics["ruby_w"]
            ruby_h = metrics["ruby_h"]
            prefix_w = metrics["prefix_w"]
            core_w = metrics["core_w"]
            column_w = metrics["column_w"]

            main_x = current_x + (column_w - main_w) // 2
            main_y = start_y + ruby_row

            if token.token_type == "speaker":
                icon = self._load_speaker_icon(main_w)
                icon_y = main_y + max(0, (max_main_h - main_h) // 2)
                if icon:
                    img.alpha_composite(icon, (int(main_x), int(icon_y)))
                else:
                    draw.text((main_x, icon_y), token.text or "🔊", font=self.main_font, fill=self.style.text_color)
                current_x += column_w
                continue

            color = token.color or self.style.text_color
            if self.style.stroke_width > 0:
                for dx in range(-self.style.stroke_width, self.style.stroke_width + 1):
                    for dy in range(-self.style.stroke_width, self.style.stroke_width + 1):
                        if dx * dx + dy * dy <= self.style.stroke_width * self.style.stroke_width:
                            draw.text(
                                (main_x + dx, main_y + dy),
                                token.text,
                                font=self.main_font,
                                fill=self.style.stroke_color,
                            )
            draw.text((main_x, main_y), token.text, font=self.main_font, fill=color)

            if token.ruby:
                if core_w > 0:
                    ruby_x = int(main_x + prefix_w + (core_w - ruby_w) / 2)
                else:
                    ruby_x = current_x + (column_w - ruby_w) // 2
                ruby_y = start_y + (max_ruby_h - ruby_h)
                if self.style.stroke_width > 0:
                    for dx in range(-self.style.stroke_width, self.style.stroke_width + 1):
                        for dy in range(-self.style.stroke_width, self.style.stroke_width + 1):
                            if dx * dx + dy * dy <= self.style.stroke_width * self.style.stroke_width:
                                draw.text(
                                    (ruby_x + dx, ruby_y + dy),
                                    token.ruby,
                                    font=self.ruby_font,
                                    fill=self.style.stroke_color,
                                )
                draw.text((ruby_x, ruby_y), token.ruby, font=self.ruby_font, fill=color)

            current_x += column_w

        return img


RENDER_PADDING = 16


def _tokens_fit(tokens: list[RubyToken], slot: Slot, renderer: RubyRenderer) -> bool:
    if not tokens:
        return True
    width, height = renderer.measure_tokens(tokens)
    return (width + RENDER_PADDING * 2) <= slot.width and (height + RENDER_PADDING * 2) <= slot.height


def _tokens_fit_width(tokens: list[RubyToken], slot: Slot, renderer: RubyRenderer) -> bool:
    if not tokens:
        return True
    width, _ = renderer.measure_tokens(tokens)
    return (width + RENDER_PADDING * 2) <= slot.width


def _token_weight(token: RubyToken) -> float:
    text = token.text or ""
    if not text:
        return 0.0
    weight = 0.0
    for char in text:
        if char.isspace():
            continue
        if char.isalnum() or _is_cjk(char) or _is_kana(char) or ("\u0600" <= char <= "\u06FF") or ("\uAC00" <= char <= "\uD7A3"):
            weight += 1.0
        else:
            weight += 0.2
    return weight


def _trim_chunk(chunk: list[RubyToken]) -> list[RubyToken]:
    start = 0
    end = len(chunk)
    while start < end and (chunk[start].text or "").isspace():
        start += 1
    while end > start and (chunk[end - 1].text or "").isspace():
        end -= 1
    return chunk[start:end]


def _split_text_tokens_for_fit(text: str) -> list[RubyToken]:
    if not text:
        return []
    if re.search(r"\s", text):
        return _split_word_tokens(text)
    if any(_is_cjk(char) or _is_kana(char) for char in text):
        return [RubyToken(text=char) for char in text]
    return [RubyToken(text=text)]


def _chunk_tokens_to_fit(tokens: list[RubyToken], slot: Slot, renderer: RubyRenderer) -> list[list[RubyToken]]:
    chunks: list[list[RubyToken]] = []
    current: list[RubyToken] = []
    for token in tokens:
        candidate = current + [token]
        if _tokens_fit(candidate, slot, renderer):
            current = candidate
            continue
        if current:
            cleaned = _trim_chunk(current)
            if cleaned:
                chunks.append(cleaned)
            current = [token]
            if not _tokens_fit(current, slot, renderer):
                cleaned = _trim_chunk(current)
                if cleaned:
                    chunks.append(cleaned)
                current = []
        else:
            cleaned = _trim_chunk([token])
            if cleaned:
                chunks.append(cleaned)
    if current:
        cleaned = _trim_chunk(current)
        if cleaned:
            chunks.append(cleaned)
    return chunks if chunks else [tokens]


def _chunk_tokens_to_fit_width(tokens: list[RubyToken], slot: Slot, renderer: RubyRenderer) -> list[list[RubyToken]]:
    chunks: list[list[RubyToken]] = []
    current: list[RubyToken] = []
    for token in tokens:
        candidate = current + [token]
        if _tokens_fit_width(candidate, slot, renderer):
            current = candidate
            continue
        if current:
            cleaned = _trim_chunk(current)
            if cleaned:
                chunks.append(cleaned)
            current = [token]
            if not _tokens_fit_width(current, slot, renderer):
                cleaned = _trim_chunk(current)
                if cleaned:
                    chunks.append(cleaned)
                current = []
        else:
            cleaned = _trim_chunk([token])
            if cleaned:
                chunks.append(cleaned)
    if current:
        cleaned = _trim_chunk(current)
        if cleaned:
            chunks.append(cleaned)
    return chunks if chunks else [tokens]


def _segment_text_from_tokens(tokens: list[RubyToken]) -> str:
    return "".join(token.text or "" for token in tokens)


def _split_segment_timing(segment: SubtitleSegment, chunks: list[list[RubyToken]]) -> list[SubtitleSegment]:
    if len(chunks) <= 1:
        return [segment]
    start = segment.start_time
    end = segment.end_time
    total_duration = max(0.0, end - start)
    if total_duration <= 0:
        return [segment]
    weights = [sum(_token_weight(token) for token in chunk) for chunk in chunks]
    total_weight = sum(weights)
    if total_weight <= 0:
        weights = [1.0 for _ in chunks]
        total_weight = float(len(chunks))
    new_segments: list[SubtitleSegment] = []
    current_start = start
    for idx, chunk in enumerate(chunks):
        if idx == len(chunks) - 1:
            current_end = end
        else:
            portion = weights[idx] / total_weight
            current_end = current_start + total_duration * portion
            if current_end < current_start:
                current_end = current_start
        new_segments.append(
            SubtitleSegment(
                start_time=current_start,
                end_time=current_end,
                tokens=chunk,
                text=_segment_text_from_tokens(chunk),
            )
        )
        current_start = current_end
    return new_segments


def _auto_split_segments_for_slot(
    segments: list[SubtitleSegment],
    slot: Slot,
    style: TextStyle,
) -> list[SubtitleSegment]:
    renderer = RubyRenderer(style)
    split_segments: list[SubtitleSegment] = []
    for segment in segments:
        if not segment.tokens:
            continue
        tokens = segment.tokens
        width, height = renderer.measure_tokens(tokens)
        if height > slot.height or width <= slot.width * 1.05:
            split_segments.append(segment)
            continue

        split_tokens = tokens
        if len(tokens) == 1 and not tokens[0].ruby:
            text = tokens[0].text or segment.text or ""
            split_tokens = _split_text_tokens_for_fit(text)

        if not _tokens_fit_width(split_tokens, slot, renderer):
            chunks = _chunk_tokens_to_fit_width(split_tokens, slot, renderer)
            if len(chunks) > 1:
                split_segments.extend(_split_segment_timing(segment, chunks))
                continue

        if split_tokens is not tokens:
            split_segments.append(
                SubtitleSegment(
                    start_time=segment.start_time,
                    end_time=segment.end_time,
                    tokens=split_tokens,
                    text=_segment_text_from_tokens(split_tokens),
                )
            )
        else:
            split_segments.append(segment)
    return split_segments


class SubtitleTrack:
    def __init__(self, segments: list[SubtitleSegment], slot: Slot, style: TextStyle) -> None:
        self.segments = sorted(segments, key=lambda seg: seg.start_time)
        self.slot = slot
        self.style = style
        self.renderer = RubyRenderer(style)
        self._segment_index = 0
        self._render_cache: dict[int, Image.Image] = {}

    def active_segment(self, t: float) -> Optional[SubtitleSegment]:
        while self._segment_index < len(self.segments) and self.segments[self._segment_index].end_time < t:
            self._segment_index += 1
        if self._segment_index < len(self.segments):
            seg = self.segments[self._segment_index]
            if seg.start_time <= t <= seg.end_time:
                return seg
        return None

    def render_segment(self, seg: SubtitleSegment) -> Image.Image:
        key = id(seg)
        cached = self._render_cache.get(key)
        if cached is not None:
            return cached

        img = self.renderer.render_tokens(seg.tokens)
        if img.width > self.slot.width or img.height > self.slot.height:
            scale = min(self.slot.width / img.width, self.slot.height / img.height)
            if scale > 0:
                new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
                resample = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
                img = img.resize(new_size, resample)
        self._render_cache[key] = img
        return img


def _parse_timestamp(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    match = re.match(r"^(\d{2}):(\d{2}):(\d{2})[,.](\d{3})$", text)
    if not match:
        return None
    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    millis = int(match.group(4))
    return hours * 3600 + minutes * 60 + seconds + millis / 1000.0


def _is_kana(char: str) -> bool:
    return "\u3040" <= char <= "\u30ff" or char == "\u30fc"


def _has_kanji(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _is_cjk(char: str) -> bool:
    return "\u4e00" <= char <= "\u9fff"


def _to_hiragana(text: str) -> str:
    result = ""
    for char in text:
        if "\u30a1" <= char <= "\u30f6":
            result += chr(ord(char) - 0x60)
        else:
            result += char
    return result


def _is_kana_text(text: str) -> bool:
    return any(_is_kana(char) for char in text) and not _has_kanji(text)


def _kana_to_romaji(text: str) -> Optional[str]:
    if not ROMAJI_CONVERTER:
        return _kana_to_romaji_fallback(text)
    try:
        return ROMAJI_CONVERTER.do(text)
    except Exception:
        return _kana_to_romaji_fallback(text)


def _kana_char_romaji(char: str) -> Optional[str]:
    if not char:
        return None
    if char == "ー":
        return None
    hira = _to_hiragana(char)
    if hira in KANA_ROMAJI_BASE:
        return KANA_ROMAJI_BASE[hira]
    return _kana_to_romaji_fallback(hira)


def _kana_to_romaji_fallback(text: str) -> Optional[str]:
    if not text:
        return None
    hira = _to_hiragana(text)
    result = ""
    i = 0
    while i < len(hira):
        char = hira[i]
        if char == "っ":
            if i + 1 < len(hira):
                next_char = hira[i + 1]
                next_pair = hira[i + 1 : i + 3] if i + 2 < len(hira) else ""
                next_romaji = KANA_ROMAJI_DIGRAPHS.get(next_pair) or KANA_ROMAJI_BASE.get(next_char, "")
                if next_romaji:
                    result += next_romaji[0]
            i += 1
            continue
        if char == "ー":
            if result and result[-1] in "aeiou":
                result += result[-1]
            i += 1
            continue
        pair = hira[i : i + 2]
        if pair in KANA_ROMAJI_DIGRAPHS:
            result += KANA_ROMAJI_DIGRAPHS[pair]
            i += 2
            continue
        result += KANA_ROMAJI_BASE.get(char, char)
        i += 1
    return result.strip() or None


def _apply_kana_romaji(tokens: list[RubyToken]) -> None:
    for token in tokens:
        if token.ruby:
            continue
        if not token.text:
            continue
        if not _is_kana_text(token.text):
            continue
        if len(token.text) == 1:
            romaji = _kana_char_romaji(token.text)
        else:
            romaji = _kana_to_romaji(token.text)
        if romaji and romaji != token.text:
            token.ruby = romaji


def _split_kana_affixes_text(text: str) -> tuple[str, str, str]:
    if not text or not _has_kanji(text):
        return "", text, ""
    prefix = ""
    for char in text:
        if _is_kana(char):
            prefix += char
        else:
            break
    suffix = ""
    for char in reversed(text):
        if _is_kana(char):
            suffix = char + suffix
        else:
            break
    core = text[len(prefix):len(text) - len(suffix) if suffix else len(text)]
    return prefix, core, suffix


def _expand_kana_affixes(tokens: list[RubyToken], add_romaji: bool) -> list[RubyToken]:
    expanded: list[RubyToken] = []
    for token in tokens:
        if not token.text:
            continue
        if not _has_kanji(token.text):
            if add_romaji and _is_kana_text(token.text):
                for char in token.text:
                    romaji = _kana_char_romaji(char) if add_romaji else None
                    expanded.append(
                        RubyToken(
                            text=char,
                            ruby=romaji,
                            color=token.color,
                            token_type=token.token_type,
                        )
                    )
            else:
                expanded.append(token)
            continue
        prefix, core, suffix = _split_kana_affixes_text(token.text)
        if prefix:
            if add_romaji:
                for char in prefix:
                    expanded.append(
                        RubyToken(
                            text=char,
                            ruby=_kana_char_romaji(char),
                            color=token.color,
                            token_type=token.token_type,
                        )
                    )
            else:
                expanded.append(
                    RubyToken(
                        text=prefix,
                        ruby=None,
                        color=token.color,
                        token_type=token.token_type,
                )
            )
        if core:
            if prefix or suffix:
                expanded.append(
                    RubyToken(
                        text=core,
                        ruby=token.ruby,
                        color=token.color,
                        token_type=token.token_type,
                    )
                )
        if suffix:
            if add_romaji:
                for char in suffix:
                    expanded.append(
                        RubyToken(
                            text=char,
                            ruby=_kana_char_romaji(char),
                            color=token.color,
                            token_type=token.token_type,
                        )
                    )
            else:
                expanded.append(
                    RubyToken(
                        text=suffix,
                        ruby=None,
                        color=token.color,
                        token_type=token.token_type,
                )
            )
        if not (prefix or suffix):
            expanded.append(token)
    return expanded


def _split_word_tokens(text: str) -> list[RubyToken]:
    if not text:
        return []
    parts = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+|\s+|[^\w\s]", text)
    tokens: list[RubyToken] = []
    for part in parts:
        tokens.append(RubyToken(text=part))
    return tokens


def _normalize_speaker_tokens(tokens: list[RubyToken]) -> list[RubyToken]:
    if not tokens or tokens[0].token_type != "speaker":
        return tokens
    rest = tokens[1:]
    if len(rest) != 1:
        return tokens
    candidate = rest[0]
    if candidate.ruby or not candidate.text:
        return tokens
    if re.search(r"\s", candidate.text):
        split_tokens = _split_word_tokens(candidate.text)
        return [tokens[0]] + split_tokens
    return tokens


def _phonemize_word(word: str, lang: str) -> Optional[str]:
    if not PHONEMIZER_AVAILABLE:
        return None
    try:
        result = phonemize(
            word,
            language=lang,
            backend="espeak",
            strip=True,
            preserve_punctuation=True,
            with_stress=False,
            njobs=1,
        )
    except Exception:
        return None
    cleaned = result.strip()
    if not cleaned or cleaned == word:
        return None
    return cleaned


def _apply_ipa(tokens: list[RubyToken], lang: str) -> list[RubyToken]:
    if not tokens:
        return tokens
    updated: list[RubyToken] = []
    for token in tokens:
        if token.ruby or not token.text:
            updated.append(token)
            continue
        if not re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ]", token.text):
            updated.append(token)
            continue
        ipa = _phonemize_word(token.text, lang)
        if ipa:
            token.ruby = ipa
        updated.append(token)
    return updated


def _tokens_with_pinyin(text: str) -> list[RubyToken]:
    if not PINYIN_AVAILABLE:
        return [RubyToken(text=text)]
    items = pypinyin(text, style=Style.TONE, errors=lambda x: [x])
    tokens: list[RubyToken] = []
    for char, py in zip(text, items):
        reading = py[0] if py else ""
        if _is_cjk(char) and reading and reading != char:
            tokens.append(RubyToken(text=char, ruby=reading))
        else:
            tokens.append(RubyToken(text=char))
    return tokens


def _apply_pinyin(tokens: list[RubyToken]) -> list[RubyToken]:
    if not PINYIN_AVAILABLE:
        return tokens
    expanded: list[RubyToken] = []
    for token in tokens:
        if token.ruby or not token.text:
            expanded.append(token)
            continue
        if any(_is_cjk(char) for char in token.text):
            expanded.extend(_tokens_with_pinyin(token.text))
        else:
            expanded.append(token)
    return expanded


def _apply_jyutping(text: str) -> list[RubyToken]:
    if not JYUTPING_AVAILABLE:
        return [RubyToken(text=text)]
    try:
        jyut_list = characters_to_jyutping(text)
    except Exception:
        return [RubyToken(text=text)]

    tokens: list[RubyToken] = []
    for item in jyut_list:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            segment, jyut = item
            segment_text = str(segment)
            if not segment_text:
                continue
            if jyut:
                tokens.append(RubyToken(text=segment_text, ruby=str(jyut)))
            else:
                tokens.append(RubyToken(text=segment_text))
        else:
            tokens.append(RubyToken(text=str(item)))
    return tokens


def _romanize_korean(text: str) -> Optional[str]:
    if not KOROMAN_AVAILABLE:
        return None
    try:
        return koroman_romanize(text, use_pronunciation_rules=True)
    except Exception:
        return None


def _split_korean_tokens(text: str) -> list[RubyToken]:
    if not text:
        return []
    parts = re.findall(r"[가-힣]+|[A-Za-zÀ-ÖØ-öø-ÿ']+|\\d+|\\s+|[^\\w\\s]", text)
    tokens: list[RubyToken] = []
    for part in parts:
        tokens.append(RubyToken(text=part))
    return tokens


def _apply_korean_romaja(tokens: list[RubyToken]) -> list[RubyToken]:
    if not tokens:
        return tokens
    updated: list[RubyToken] = []
    for token in tokens:
        if token.ruby or not token.text:
            updated.append(token)
            continue
        if not re.search(r"[가-힣]", token.text):
            updated.append(token)
            continue
        romaja = _romanize_korean(token.text)
        if romaja:
            token.ruby = romaja
        updated.append(token)
    return updated


_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")


def _arabic_transliterate(text: str) -> Optional[str]:
    if not ARABIC_TRANSLIT_AVAILABLE or not text:
        return None
    if not ARABIC_CHAR_MAPPER:
        return None
    try:
        mapped = ARABIC_CHAR_MAPPER(text)
    except Exception:
        return None
    cleaned = str(mapped).strip()
    if not cleaned or cleaned == text:
        return None
    return cleaned


def _split_arabic_tokens(text: str) -> list[RubyToken]:
    if not text:
        return []
    parts = re.findall(r"[\u0600-\u06FF]+|\s+|[^\s\u0600-\u06FF]+", text)
    return [RubyToken(text=part) for part in parts]


def _apply_arabic_translit(tokens: list[RubyToken]) -> list[RubyToken]:
    if not tokens:
        return tokens
    updated: list[RubyToken] = []
    for token in tokens:
        if token.ruby or not token.text:
            updated.append(token)
            continue
        if not _ARABIC_RE.search(token.text):
            updated.append(token)
            continue
        translit = _arabic_transliterate(token.text)
        if translit:
            token.ruby = translit
        updated.append(token)
    return updated


def _strip_kana_affixes(text: str, ruby: Optional[str]) -> Optional[str]:
    if not ruby:
        return ruby
    if not text or not _has_kanji(text):
        return None

    ruby_h = _to_hiragana(ruby)
    prefix = ""
    for char in text:
        if _is_kana(char):
            prefix += char
        else:
            break
    suffix = ""
    for char in reversed(text):
        if _is_kana(char):
            suffix = char + suffix
        else:
            break

    prefix_h = _to_hiragana(prefix)
    suffix_h = _to_hiragana(suffix)
    trimmed = ruby_h
    if prefix_h and trimmed.startswith(prefix_h):
        trimmed = trimmed[len(prefix_h):]
    if suffix_h and trimmed.endswith(suffix_h):
        trimmed = trimmed[: -len(suffix_h)]
    trimmed = trimmed.strip()
    if not trimmed:
        return None
    if trimmed == _to_hiragana(text):
        return None
    return trimmed


def _hex_to_rgb(value: str) -> Optional[tuple[int, int, int]]:
    text = value.strip().lstrip("#")
    if len(text) == 3:
        text = "".join([c * 2 for c in text])
    if len(text) != 6:
        return None
    try:
        return tuple(int(text[i : i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return None


def _resolve_token_color(token: dict, palette: Optional[dict[str, Any]]) -> Optional[tuple[int, int, int]]:
    color_value = token.get("color")
    if isinstance(color_value, str):
        return _hex_to_rgb(color_value)

    token_type = token.get("type") or token.get("pos") or token.get("tag")
    if token_type and palette:
        entry = palette.get("types", {}).get(token_type) or palette.get(token_type)
        if isinstance(entry, dict) and "color" in entry:
            return _hex_to_rgb(str(entry["color"]))
        if isinstance(entry, str):
            return _hex_to_rgb(entry)
    return None


def _tokens_from_pairs(pairs: Iterable) -> list[RubyToken]:
    tokens: list[RubyToken] = []
    for pair in pairs:
        if not isinstance(pair, (list, tuple)) or len(pair) < 1:
            continue
        text = str(pair[0] or "")
        if not text:
            continue
        ruby = str(pair[1]) if len(pair) > 1 and pair[1] is not None else None
        tokens.append(RubyToken(text=text, ruby=ruby))
    return tokens


def _tokens_from_ruby_markup(text: str) -> list[RubyToken]:
    tokens: list[RubyToken] = []
    pattern = re.compile(r"<([^>]+)>\[([^\]]+)\]")
    cursor = 0
    for match in pattern.finditer(text):
        if match.start() > cursor:
            plain = text[cursor:match.start()]
            if plain:
                tokens.append(RubyToken(text=plain))
        tokens.append(RubyToken(text=match.group(1), ruby=match.group(2)))
        cursor = match.end()
    if cursor < len(text):
        tail = text[cursor:]
        if tail:
            tokens.append(RubyToken(text=tail))
    return tokens if tokens else [RubyToken(text=text)]


def load_segments_from_json(
    json_path: str,
    text_key: Optional[str] = None,
    ruby_key: Optional[str] = None,
    tokens_key: str = "tokens",
    pairs_key: str = "furigana_pairs",
    palette: Optional[dict[str, Any]] = None,
    auto_ruby: bool = False,
    strip_kana: bool = False,
    kana_romaji: bool = False,
    pinyin: bool = False,
    ipa_lang: Optional[str] = None,
    jyutping: bool = False,
    korean_romaja: bool = False,
    arabic_translit: bool = False,
) -> list[SubtitleSegment]:
    with open(json_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if isinstance(payload, dict):
        items = payload.get("items") or payload.get("subtitles") or payload.get("segments") or []
    elif isinstance(payload, list):
        items = payload
    else:
        items = []

    generator = FuriganaGenerator() if auto_ruby else None
    segments: list[SubtitleSegment] = []

    for item in items:
        if not isinstance(item, dict):
            continue
        start = _parse_timestamp(item.get("start"))
        end = _parse_timestamp(item.get("end"))
        if start is None or end is None:
            continue

        base_text = None
        if text_key:
            base_text = item.get(text_key)
        if base_text is None:
            base_text = item.get("text")
        base_text = "" if base_text is None else str(base_text)

        tokens_payload = item.get(tokens_key) if tokens_key else None
        tokens: list[RubyToken] = []

        if isinstance(tokens_payload, list) and tokens_payload:
            for token in tokens_payload:
                if not isinstance(token, dict):
                    continue
                token_text = token.get("text") or token.get("word") or token.get("token")
                if not token_text:
                    continue
                token_ruby = token.get("ruby") or token.get("reading") or token.get("furigana")
                token_color = _resolve_token_color(token, palette)
                tokens.append(
                    RubyToken(
                        text=str(token_text),
                        ruby=str(token_ruby) if token_ruby is not None else None,
                        color=token_color,
                        token_type=str(token.get("type")) if token.get("type") else None,
                    )
                )
        elif pairs_key and item.get(pairs_key):
            tokens = _tokens_from_pairs(item.get(pairs_key))
        elif ruby_key and item.get(ruby_key):
            tokens = _tokens_from_ruby_markup(str(item.get(ruby_key)))
        elif generator and base_text:
            tokens = generator.generate(base_text)
        else:
            tokens = [RubyToken(text=base_text)] if base_text else []

        if tokens and tokens[0].token_type == "speaker":
            tokens = _normalize_speaker_tokens(tokens)

        if strip_kana and tokens:
            for token in tokens:
                token.ruby = _strip_kana_affixes(token.text, token.ruby)

        if tokens and (strip_kana or kana_romaji):
            tokens = _expand_kana_affixes(tokens, kana_romaji)

        if kana_romaji and tokens:
            _apply_kana_romaji(tokens)

        if pinyin and tokens:
            tokens = _apply_pinyin(tokens)

        if jyutping:
            tokens = _apply_jyutping(base_text)

        if korean_romaja:
            if len(tokens) == 1 and tokens[0].text and not tokens[0].ruby and " " in tokens[0].text:
                tokens = _split_korean_tokens(tokens[0].text)
            tokens = _apply_korean_romaja(tokens)

        if ipa_lang:
            if len(tokens) == 1 and tokens[0].text and not tokens[0].ruby and " " in tokens[0].text:
                tokens = _split_word_tokens(tokens[0].text)
            tokens = _apply_ipa(tokens, ipa_lang)

        if arabic_translit:
            if len(tokens) == 1 and tokens[0].text and not tokens[0].ruby:
                tokens = _split_arabic_tokens(tokens[0].text)
            tokens = _apply_arabic_translit(tokens)

        segments.append(
            SubtitleSegment(
                start_time=start,
                end_time=end,
                tokens=tokens,
                text=base_text,
            )
        )

    return segments


def build_bottom_slot_layout(
    frame_width: int,
    frame_height: int,
    rows: int = 2,
    cols: int = 2,
    height_ratio: float = 0.28,
    margin: int = 24,
    gutter: int = 12,
    lift_slots: int = 1,
) -> BurnLayout:
    bottom_height = int(frame_height * height_ratio)
    slot_height = max(1, (bottom_height - gutter * (rows - 1)) // rows)
    lift_slots = max(0, int(lift_slots))
    lift_pixels = (slot_height + gutter) * lift_slots
    top_y = max(0, frame_height - bottom_height - lift_pixels)
    slot_width = max(1, (frame_width - gutter * (cols - 1) - margin * 2) // cols)

    slots: list[Slot] = []
    slot_id = 1
    for row in range(rows):
        for col in range(cols):
            x = margin + col * (slot_width + gutter)
            y = top_y + row * (slot_height + gutter)
            slots.append(Slot(slot_id=slot_id, x=x, y=y, width=slot_width, height=slot_height))
            slot_id += 1
    return BurnLayout(slots=slots)


def burn_subtitles_with_layout(
    video_path: str,
    output_path: str,
    layout: BurnLayout,
    assignments: list[SlotAssignment],
    fps_override: Optional[float] = None,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> None:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = fps_override or cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    slot_map = {slot.slot_id: slot for slot in layout.slots}
    tracks: list[SubtitleTrack] = []

    for assignment in assignments:
        slot = slot_map.get(assignment.slot_id)
        if not slot:
            continue
        style = assignment.style or TextStyle()
        segments = load_segments_from_json(
            assignment.json_path,
            text_key=assignment.text_key,
            ruby_key=assignment.ruby_key,
            tokens_key=assignment.tokens_key,
            pairs_key=assignment.pairs_key,
            palette=assignment.palette,
            auto_ruby=assignment.auto_ruby,
            strip_kana=assignment.strip_kana,
            kana_romaji=assignment.kana_romaji,
            pinyin=assignment.pinyin,
            ipa_lang=assignment.ipa_lang,
            jyutping=assignment.jyutping,
            korean_romaja=assignment.korean_romaja,
            arabic_translit=assignment.arabic_translit,
        )
        if not segments:
            continue
        segments = _auto_split_segments_for_slot(segments, slot, style)
        tracks.append(SubtitleTrack(segments=segments, slot=slot, style=style))

    ext = os.path.splitext(output_path)[1].lower()
    if ext == ".avi":
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
    else:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_idx = 0
    last_reported = -1
    if progress_callback and total_frames:
        progress_callback(0)
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            t = frame_idx / fps if fps else 0
            for track in tracks:
                seg = track.active_segment(t)
                if not seg:
                    continue
                img = track.render_segment(seg)
                frame = _overlay_image(frame, img, track.slot)

            out.write(frame)
            frame_idx += 1
            if total_frames:
                progress = int(min(100, (frame_idx / total_frames) * 100))
                if progress_callback and progress != last_reported and (progress == 100 or progress % 2 == 0):
                    progress_callback(progress)
                    last_reported = progress
    finally:
        cap.release()
        out.release()


def _overlay_image(frame: np.ndarray, img: Image.Image, slot: Slot) -> np.ndarray:
    overlay = cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGRA)
    h, w = overlay.shape[:2]

    if slot.align == "left":
        x = slot.x
    elif slot.align == "right":
        x = slot.x + max(slot.width - w, 0)
    else:
        x = slot.x + max((slot.width - w) // 2, 0)
    y = slot.y + max((slot.height - h) // 2, 0)

    x = max(0, min(x, frame.shape[1] - w))
    y = max(0, min(y, frame.shape[0] - h))

    alpha = overlay[:, :, 3] / 255.0
    alpha = np.stack([alpha] * 3, axis=2)

    region = frame[y : y + h, x : x + w]
    blended = region * (1 - alpha) + overlay[:, :, :3] * alpha
    frame[y : y + h, x : x + w] = blended.astype(np.uint8)
    return frame


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Burn subtitles with ruby support")
    parser.add_argument("video", help="Input video")
    parser.add_argument("json", help="Subtitle JSON file")
    parser.add_argument("output", help="Output video")
    parser.add_argument("--text-key", default="text", help="JSON key for base text")
    parser.add_argument("--ruby-key", default=None, help="JSON key for ruby markup")
    parser.add_argument("--slot", type=int, default=1, help="Slot id")
    parser.add_argument("--auto-ruby", action="store_true", help="Auto-generate ruby for Japanese")

    args = parser.parse_args()

    cap = cv2.VideoCapture(args.video)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    layout = build_bottom_slot_layout(width, height)
    assignments = [
        SlotAssignment(
            slot_id=args.slot,
            language=args.text_key,
            json_path=args.json,
            text_key=args.text_key,
            ruby_key=args.ruby_key,
            auto_ruby=args.auto_ruby,
        )
    ]

    burn_subtitles_with_layout(args.video, args.output, layout, assignments)
