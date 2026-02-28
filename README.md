[English](README.md) · [العربية](i18n/README.ar.md) · [Español](i18n/README.es.md) · [Français](i18n/README.fr.md) · [日本語](i18n/README.ja.md) · [한국어](i18n/README.ko.md) · [Tiếng Việt](i18n/README.vi.md) · [中文 (简体)](i18n/README.zh-Hans.md) · [中文（繁體）](i18n/README.zh-Hant.md) · [Deutsch](i18n/README.de.md) · [Русский](i18n/README.ru.md)

<p align="center">
  <img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/logos/banner.png" alt="LazyingArt banner" />
</p>


# Furigana Subtitle Burner

<p align="center">
  <img src="figures/demo.png" alt="Furigana subtitle demo" width="720" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/OpenCV-Video%20Burning-5C3EE8?logo=opencv&logoColor=white" alt="OpenCV" />
  <img src="https://img.shields.io/badge/Status-Active-2ea44f" alt="Status" />
  <img src="https://img.shields.io/badge/Primary%20Flow-SRT%20Pipeline-0ea5e9" alt="Primary Flow" />
  <img src="https://img.shields.io/badge/Extended%20Mode-JSON%20Ruby-f59e0b" alt="Extended Mode" />
</p>

A Python subtitle burner that renders Japanese furigana and other ruby annotations (pinyin, romaji, IPA, etc.) directly onto video frames with OpenCV. It is optimized for furigana workflows while remaining flexible for multilingual ruby-style subtitles.

Built for <a href="https://studio.lazying.art" target="_blank" rel="noreferrer">LazyEdit Studio</a> · <a href="https://github.com/lachlanchen/LazyEdit" target="_blank" rel="noreferrer">GitHub</a>

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Examples](#examples)
- [How It Works](#how-it-works)
- [Development Notes](#development-notes)
- [Troubleshooting](#troubleshooting)
- [Performance](#performance)
- [Dependencies](#dependencies)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [What your support makes possible](#what-your-support-makes-possible)
- [Contributing](#contributing)
- [License](#license)

## Overview

This repository contains multiple subtitle burning paths:

| Path | Scripts | Best For |
|---|---|---|
| Classic SRT furigana workflow | `process_furigana_videos.py` + `furigana_subtitle_burner.py` | Day-to-day subtitle burning with SRT files |
| Standalone workflow | `standalone_furigana_burner.py` | Simple single-script execution |
| Complete workflow | `complete_furigana_burner.py` | Config save/load + preview mode |
| Generalized ruby engine | `subtitles_burner/burner.py` | JSON-driven multilingual token-level annotation |

Default README flow remains the SRT-based pipeline unless you explicitly need JSON-based multi-slot rendering.

## Features

- 🎌 **Automatic Furigana Generation**: Uses MeCab (fugashi) or pykakasi to generate furigana for kanji characters
- 🌐 **Ruby Annotation Support**: Render pronunciation guides for kanji, kana, and other scripts (pinyin, romaji, IPA)
- 🎨 **Custom Text Rendering**: Renders beautiful ruby text with proper spacing, alignment, and stroke
- 📺 **Direct Video Processing**: Burns subtitles directly onto video frames using OpenCV
- 🔤 **Smart Font Handling**: Automatically finds and uses fonts for CJK and Latin scripts
- ⚡ **Batch Processing**: Process multiple videos at once
- 🎯 **Precise Positioning**: Configurable subtitle position, margins, and layout behavior
- 🧩 **Multiple Runtimes**: Choose between classic, standalone, complete, or generalized burner modules

## Project Structure

```text
FuriganaSubtitles/
├── README.md
├── requirements.txt
├── setup_furigana.sh
├── process_furigana_videos.py
├── furigana_subtitle_burner.py
├── standalone_furigana_burner.py
├── complete_furigana_burner.py
├── subtitles_burner/
│   ├── __init__.py
│   ├── burner.py
│   └── assets/
│       └── speaker.png
├── i18n/
│   ├── README.ar.md
│   ├── README.es.md
│   ├── README.fr.md
│   ├── README.ja.md
│   ├── README.ko.md
│   ├── README.vi.md
│   ├── README.zh-Hans.md
│   └── README.zh-Hant.md
├── figures/
│   └── demo.png
├── .github/
│   └── FUNDING.yml
├── legacy/
├── legacy-results/
├── test_furigana.py
├── simple_test.py
├── font_test.py
├── fix_font_squares.py
├── fix_unidic.py
├── debug_japanese.py
└── openai_request.py
```

## Prerequisites

- Python 3.9+ recommended
- OS with fonts that can render Japanese/CJK text
- Enough CPU and disk for frame-by-frame video output
- Input subtitle files encoded as UTF-8 (recommended)

## Installation

### Quick Setup

```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

The setup script installs core packages, attempts UniDic download, and runs `test_furigana.py`.

### Manual Installation

```bash
# Option A: install pinned repo requirements
pip install -r requirements.txt

# Option B: install explicit core packages (as documented in original README)
pip install opencv-python Pillow numpy fugashi unidic pykakasi

# Download Japanese dictionary data
python -c "import unidic; unidic.download()"
```

Optional packages used by `subtitles_burner/burner.py` (only needed for specific transliteration modes):

```bash
pip install phonemizer koroman pypinyin pycantonese
```

Optional packages used by `openai_request.py` helper:

```bash
pip install openai pygame
```

## Usage

### 1. Test the System

```bash
python test_furigana.py
```

This tests furigana generation and creates `test_furigana_output.png`.

### 2. Process All Videos in Current Directory

```bash
python process_furigana_videos.py
```

Automatically finds all `video_*` directories and processes the first `.MP4` and `.srt` in each.

### 3. Process a Single Video

```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. Advanced Usage (Classic Burner)

```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

### 5. Standalone Burner (Auto-detect Mode)

```bash
python standalone_furigana_burner.py
```

If run with no args, it auto-detects `*.MP4`/`*.mp4` and `*.srt` in the current directory.

### 6. Complete Burner (Config + Preview)

```bash
python complete_furigana_burner.py video.mp4 sub.srt out.mp4 --preview
python complete_furigana_burner.py video.mp4 sub.srt out.mp4 --save-config
python complete_furigana_burner.py --config furigana_config.json video.mp4 sub.srt out.mp4
```

### 7. Generalized JSON Ruby Burner

```bash
python subtitles_burner/burner.py input.mp4 subtitles.json output.mp4 \
  --text-key text \
  --ruby-key ruby \
  --slot 1 \
  --auto-ruby
```

## Configuration

### CLI Parameters (Classic `furigana_subtitle_burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--main-font-size` | Size of main Japanese text | `48` |
| `--furigana-font-size` | Size of furigana text | `24` |
| `--position` | `top`, `bottom`, or `center` | `bottom` |
| `--margin` | Distance from edge in pixels | `50` |

### CLI Parameters (`standalone_furigana_burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--main-font-size` | Main text size | `64` |
| `--furigana-font-size` | Furigana text size | `32` |
| `--position` | `top`, `bottom`, or `center` | `bottom` |
| `--margin` | Margin from edge | `80` |

### CLI Parameters (`complete_furigana_burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--main-font-size` | Main text size | `64` |
| `--furigana-font-size` | Furigana text size | `32` |
| `--position` | `top`, `bottom`, or `center` | `bottom` |
| `--margin` | Margin from edge | `80` |
| `--preview` | Preview mode (first ~10 seconds) | Off |
| `--config <path>` | Load configuration file | `None` |
| `--save-config` | Save current config as default | Off |

### CLI Parameters (`subtitles_burner/burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--text-key` | JSON key for base text | `text` |
| `--ruby-key` | JSON key for ruby markup | `None` |
| `--slot` | Slot ID in bottom slot layout | `1` |
| `--auto-ruby` | Auto-generate ruby for Japanese | Off |

### Text Appearance

- White text with black stroke for maximum visibility
- Automatic font selection (tries system Japanese fonts)
- Proportional spacing between characters and furigana

## Examples

### Example Output

For the text `今日は空が晴れていて`:

```text
   きょう   そら    は
   今日  は 空  が 晴れていて
```

### Example Batch Input/Output Layout

After processing, your directory will look like:

```text
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4      # Original video
├── video_577285345205551192-yFQ1pMPA.srt      # Subtitle file
├── video_577285345205551192-yFQ1pMPA.json     # Whisper output
├── video_577285345205551192-yFQ1pMPA.wav      # Audio extraction
└── video_577285345205551192-yFQ1pMPA_furigana.mp4  # Output with furigana
```

## How It Works

### 1. Furigana Generation

The system uses multiple methods to generate furigana:

- **Primary**: MeCab with fugashi for accurate morphological analysis
- **Fallback**: pykakasi for basic kanji-to-hiragana conversion
- **Last Resort**: Character-by-character analysis

### 2. Text Rendering Strategy

- Measures each character and its furigana separately
- Calculates optimal column width for each character
- Centers furigana above corresponding kanji
- Adds text stroke for better visibility

### 3. Video Processing

- Reads video frame by frame using OpenCV
- Calculates subtitle timing based on SRT timestamps
- Renders furigana text as RGBA image
- Alpha-blends subtitle onto video frame
- Writes processed frame to output video

## Development Notes

- Repository has overlapping burners by design; the SRT pipeline is simplest for day-to-day use.
- `legacy/` and `legacy-results/` are archival and useful for regression comparisons.
- No packaging metadata (`pyproject.toml` / `setup.py`) is currently present.
- Test coverage is script-based (`test_furigana.py`, `simple_test.py`, `font_test.py`) rather than a formal test framework.
- `openai_request.py` is an auxiliary utility and not required for core subtitle burning.

## Troubleshooting

### No Japanese Fonts Found

The system tries to find Japanese fonts automatically:

- **macOS**: Hiragino Sans
- **Linux**: `fonts-japanese-gothic`
- **Windows**: MS Gothic

Install Japanese fonts if subtitles appear in default font.

Additional helpers:

```bash
python font_test.py
python fix_font_squares.py
```

### Furigana Not Generated

1. Check if fugashi/unidic is installed: `python -c "import fugashi; print('OK')"`
2. Fallback to pykakasi: `python -c "import pykakasi; print('OK')"`
3. Check test output: `python test_furigana.py`
4. Run dependency diagnostics: `python fix_unidic.py` and `python debug_japanese.py`

### Video Processing Errors

- Ensure input video is readable by OpenCV
- Check available disk space for output file
- Verify SRT file encoding is UTF-8
- Try `complete_furigana_burner.py --preview ...` to validate pipeline quickly

## Performance

- Processing speed depends on video resolution and length
- Typical speeds: 10-30 fps processing rate
- Memory usage scales with video resolution
- Uses single-threaded processing (can be parallelized)

## Dependencies

| Package | Role | Notes |
|---|---|---|
| `opencv-python` | Video processing | Core dependency |
| `Pillow` | Image rendering and text drawing | Core dependency |
| `numpy` | Array operations | Core dependency |
| `fugashi` | Japanese morphological analysis | Optional but recommended |
| `unidic` | Japanese dictionary data | Optional but recommended |
| `pykakasi` | Kanji to hiragana conversion | Fallback path |
| `camel-tools` | Arabic transliteration helpers | Included in `requirements.txt`, used in generalized burner mode |

## Known Limitations

- Processing is CPU-intensive (no GPU acceleration)
- Font selection is automatic (limited manual control)
- Furigana distribution for complex words may not be perfect
- No support for vertical text layout
- Single subtitle line only (no multi-line support yet)

## Roadmap

- Improve furigana alignment/distribution for complex multi-kanji words
- Expand multi-line subtitle composition options
- Add clearer runtime profiles between classic/standalone/complete/generalized burners
- Optionally add packaging/test automation (`pyproject.toml`, CI smoke checks)

## What your support makes possible

- <b>Keep tools open</b>: hosting, inference, data storage, and community ops.
- <b>Ship faster</b>: weeks of focused open-source time on EchoMind, LazyEdit, and MultilingualWhisper.
- <b>Prototype wearables</b>: optics, sensors, and neuromorphic/edge components for IdeasGlass + LightMind.
- <b>Access for all</b>: subsidized deployments for students, creators, and community groups.

### Donate

<div align="center">
<table style="margin:0 auto; text-align:center; border-collapse:collapse;">
  <tr>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;">
      <a href="https://chat.lazying.art/donate">https://chat.lazying.art/donate</a>
    </td>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;">
      <a href="https://chat.lazying.art/donate"><img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/figs/donate_button.svg" alt="Donate" height="44"></a>
    </td>
  </tr>
  <tr>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;">
      <a href="https://paypal.me/RongzhouChen">
        <img src="https://img.shields.io/badge/PayPal-Donate-003087?logo=paypal&logoColor=white" alt="Donate with PayPal">
      </a>
    </td>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;">
      <a href="https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400">
        <img src="https://img.shields.io/badge/Stripe-Donate-635bff?logo=stripe&logoColor=white" alt="Donate with Stripe">
      </a>
    </td>
  </tr>
  <tr>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;"><strong>WeChat</strong></td>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;"><strong>Alipay</strong></td>
  </tr>
  <tr>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;"><img alt="WeChat QR" src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/figs/donate_wechat.png" width="240"/></td>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;"><img alt="Alipay QR" src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/figs/donate_alipay.png" width="240"/></td>
  </tr>
</table>
</div>

**支援 / Donate**

- ご支援は研究・開発と運用の継続に役立ち、より多くのオープンなプロジェクトを皆さんに届ける力になります。
- 你的支持将用于研发与运维，帮助我持续公开分享更多项目与改进。
- Your support sustains my research, development, and ops so I can keep sharing more open projects and improvements.

## Contributing

Feel free to improve the furigana generation algorithm, add support for more text layouts, or optimize the video processing pipeline.

If you submit changes, include:

- A short explanation of the user-facing impact
- Reproduction/test commands you ran locally
- Notes about font and language assumptions if your change affects rendering

## License

No license file is currently present in this repository.

Assumption for this draft: all rights and usage terms are currently unspecified until a `LICENSE` file is added by the maintainer.
