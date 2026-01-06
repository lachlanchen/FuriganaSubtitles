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

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        font_paths = [
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
        temp_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(temp_img)

        total_width = 0
        max_height = 0
        for token in tokens:
            main_bbox = draw.textbbox((0, 0), token.text, font=self.main_font)
            main_w = main_bbox[2] - main_bbox[0]
            main_h = main_bbox[3] - main_bbox[1]

            ruby_w = 0
            ruby_h = 0
            if token.ruby:
                ruby_bbox = draw.textbbox((0, 0), token.ruby, font=self.ruby_font)
                ruby_w = ruby_bbox[2] - ruby_bbox[0]
                ruby_h = ruby_bbox[3] - ruby_bbox[1]

            column_w = max(main_w, ruby_w)
            total_width += column_w

            token_height = main_h
            if token.ruby:
                token_height += ruby_h + int(self.style.ruby_font_size * self.style.ruby_spacing)
            max_height = max(max_height, token_height)
        return total_width, max_height

    def render_tokens(self, tokens: list[RubyToken], padding: int = 16) -> Image.Image:
        if not tokens:
            return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

        text_width, text_height = self.measure_tokens(tokens)
        width = max(text_width + padding * 2, 1)
        height = max(text_height + padding * 2, 1)
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        start_x = padding
        start_y = padding
        current_x = start_x

        for token in tokens:
            main_bbox = draw.textbbox((0, 0), token.text, font=self.main_font)
            main_w = main_bbox[2] - main_bbox[0]
            main_h = main_bbox[3] - main_bbox[1]

            ruby_w = 0
            ruby_h = 0
            if token.ruby:
                ruby_bbox = draw.textbbox((0, 0), token.ruby, font=self.ruby_font)
                ruby_w = ruby_bbox[2] - ruby_bbox[0]
                ruby_h = ruby_bbox[3] - ruby_bbox[1]

            column_w = max(main_w, ruby_w)
            main_x = current_x + (column_w - main_w) // 2
            main_y = start_y + (ruby_h + int(self.style.ruby_font_size * self.style.ruby_spacing))

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
                ruby_x = current_x + (column_w - ruby_w) // 2
                ruby_y = start_y
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
        )
        if not segments:
            continue
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
