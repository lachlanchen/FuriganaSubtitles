[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)


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

OpenCV를 사용해 일본어 후리가나와 기타 루비 주석(병음, 로마자, IPA 등)을 비디오 프레임에 직접 렌더링하는 Python 자막 버너입니다. 후리가나 워크플로에 최적화되어 있으면서도, 다국어 루비 스타일 자막까지 유연하게 처리할 수 있습니다.

Built for <a href="https://studio.lazying.art" target="_blank" rel="noreferrer">LazyEdit Studio</a> · <a href="https://github.com/lachlanchen/LazyEdit" target="_blank" rel="noreferrer">GitHub</a>

## 목차

- [개요](#개요)
- [기능](#기능)
- [프로젝트 구조](#프로젝트-구조)
- [사전 요구사항](#사전-요구사항)
- [설치](#설치)
- [사용법](#사용법)
- [설정](#설정)
- [예시](#예시)
- [작동 방식](#작동-방식)
- [개발 노트](#개발-노트)
- [문제 해결](#문제-해결)
- [성능](#성능)
- [의존성](#의존성)
- [알려진 제한 사항](#알려진-제한-사항)
- [로드맵](#로드맵)
- [여러분의 지원으로 가능한 일](#여러분의-지원으로-가능한-일)
- [기여](#기여)
- [라이선스](#라이선스)

## 개요

이 저장소에는 여러 자막 번인 경로가 포함되어 있습니다.

| 경로 | 스크립트 | 적합한 용도 |
|---|---|---|
| 클래식 SRT 후리가나 워크플로 | `process_furigana_videos.py` + `furigana_subtitle_burner.py` | SRT 파일 기반의 일상적인 자막 번인 |
| 독립 실행 워크플로 | `standalone_furigana_burner.py` | 단일 스크립트로 간단 실행 |
| 완전 워크플로 | `complete_furigana_burner.py` | 설정 저장/불러오기 + 프리뷰 모드 |
| 일반화된 루비 엔진 | `subtitles_burner/burner.py` | JSON 기반 다국어 토큰 단위 주석 |

명시적으로 JSON 기반 멀티 슬롯 렌더링이 필요한 경우가 아니라면, 기본 README 흐름은 SRT 기반 파이프라인을 유지합니다.

## 기능

- 🎌 **자동 후리가나 생성**: MeCab(fugashi) 또는 pykakasi를 사용해 한자에 대한 후리가나를 생성
- 🌐 **루비 주석 지원**: 한자/가나 및 기타 스크립트(병음, 로마자, IPA)의 발음 가이드 렌더링
- 🎨 **커스텀 텍스트 렌더링**: 간격, 정렬, 외곽선을 포함한 고품질 루비 텍스트 렌더링
- 📺 **직접 비디오 처리**: OpenCV로 자막을 비디오 프레임에 직접 번인
- 🔤 **스마트 폰트 처리**: CJK 및 라틴 스크립트용 폰트를 자동 탐색 및 적용
- ⚡ **배치 처리**: 여러 비디오를 한 번에 처리
- 🎯 **정밀한 위치 지정**: 자막 위치, 여백, 레이아웃 동작을 설정 가능
- 🧩 **다중 런타임**: classic, standalone, complete, generalized 버너 모듈 중 선택 가능

## 프로젝트 구조

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

## 사전 요구사항

- Python 3.9+ 권장
- 일본어/CJK 텍스트를 렌더링할 수 있는 폰트가 있는 OS
- 프레임 단위 비디오 출력 처리를 위한 충분한 CPU 및 디스크 공간
- UTF-8 인코딩된 입력 자막 파일 권장

## 설치

### 빠른 설정

```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

설정 스크립트는 핵심 패키지를 설치하고, UniDic 다운로드를 시도한 뒤, `test_furigana.py`를 실행합니다.

### 수동 설치

```bash
# Option A: install pinned repo requirements
pip install -r requirements.txt

# Option B: install explicit core packages (as documented in original README)
pip install opencv-python Pillow numpy fugashi unidic pykakasi

# Download Japanese dictionary data
python -c "import unidic; unidic.download()"
```

`subtitles_burner/burner.py`에서 사용하는 선택 패키지(특정 음역 모드에서만 필요):

```bash
pip install phonemizer koroman pypinyin pycantonese
```

`openai_request.py` 헬퍼에서 사용하는 선택 패키지:

```bash
pip install openai pygame
```

## 사용법

### 1. 시스템 테스트

```bash
python test_furigana.py
```

후리가나 생성 기능을 테스트하고 `test_furigana_output.png`를 생성합니다.

### 2. 현재 디렉터리의 모든 비디오 처리

```bash
python process_furigana_videos.py
```

모든 `video_*` 디렉터리를 자동으로 찾아 각 디렉터리에서 첫 번째 `.MP4`와 `.srt`를 처리합니다.

### 3. 단일 비디오 처리

```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. 고급 사용법 (클래식 버너)

```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

### 5. 독립 실행 버너 (자동 감지 모드)

```bash
python standalone_furigana_burner.py
```

인자 없이 실행하면 현재 디렉터리에서 `*.MP4`/`*.mp4`와 `*.srt`를 자동 감지합니다.

### 6. 완전 버너 (설정 + 프리뷰)

```bash
python complete_furigana_burner.py video.mp4 sub.srt out.mp4 --preview
python complete_furigana_burner.py video.mp4 sub.srt out.mp4 --save-config
python complete_furigana_burner.py --config furigana_config.json video.mp4 sub.srt out.mp4
```

### 7. 일반화된 JSON 루비 버너

```bash
python subtitles_burner/burner.py input.mp4 subtitles.json output.mp4 \
  --text-key text \
  --ruby-key ruby \
  --slot 1 \
  --auto-ruby
```

## 설정

### CLI 파라미터 (클래식 `furigana_subtitle_burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--main-font-size` | Size of main Japanese text | `48` |
| `--furigana-font-size` | Size of furigana text | `24` |
| `--position` | `top`, `bottom`, or `center` | `bottom` |
| `--margin` | Distance from edge in pixels | `50` |

### CLI 파라미터 (`standalone_furigana_burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--main-font-size` | Main text size | `64` |
| `--furigana-font-size` | Furigana text size | `32` |
| `--position` | `top`, `bottom`, or `center` | `bottom` |
| `--margin` | Margin from edge | `80` |

### CLI 파라미터 (`complete_furigana_burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--main-font-size` | Main text size | `64` |
| `--furigana-font-size` | Furigana text size | `32` |
| `--position` | `top`, `bottom`, or `center` | `bottom` |
| `--margin` | Margin from edge | `80` |
| `--preview` | Preview mode (first ~10 seconds) | Off |
| `--config <path>` | Load configuration file | `None` |
| `--save-config` | Save current config as default | Off |

### CLI 파라미터 (`subtitles_burner/burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--text-key` | JSON key for base text | `text` |
| `--ruby-key` | JSON key for ruby markup | `None` |
| `--slot` | Slot ID in bottom slot layout | `1` |
| `--auto-ruby` | Auto-generate ruby for Japanese | Off |

### 텍스트 표시

- 가시성을 높이기 위해 흰색 텍스트 + 검은색 외곽선 사용
- 폰트 자동 선택(시스템 일본어 폰트를 우선 시도)
- 문자와 후리가나 사이에 비례 간격 적용

## 예시

### 예시 출력

텍스트 `今日は空が晴れていて`에 대한 출력:

```text
   きょう   そら    は
   今日  は 空  が 晴れていて
```

### 예시 배치 입력/출력 레이아웃

처리 후 디렉터리 구조는 다음과 같습니다.

```text
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4      # Original video
├── video_577285345205551192-yFQ1pMPA.srt      # Subtitle file
├── video_577285345205551192-yFQ1pMPA.json     # Whisper output
├── video_577285345205551192-yFQ1pMPA.wav      # Audio extraction
└── video_577285345205551192-yFQ1pMPA_furigana.mp4  # Output with furigana
```

## 작동 방식

### 1. 후리가나 생성

시스템은 후리가나 생성을 위해 여러 방법을 사용합니다.

- **기본 경로**: fugashi를 통한 MeCab 형태소 분석(정확도 우수)
- **대체 경로**: pykakasi 기반의 기본 한자→히라가나 변환
- **최후 수단**: 문자 단위 분석

### 2. 텍스트 렌더링 전략

- 각 문자와 해당 후리가나를 개별 측정
- 문자별 최적 열 너비 계산
- 대응하는 한자 위에 후리가나를 중앙 정렬
- 가독성을 위해 텍스트 외곽선 추가

### 3. 비디오 처리

- OpenCV로 비디오를 프레임 단위로 읽음
- SRT 타임스탬프 기반으로 자막 타이밍 계산
- 후리가나 텍스트를 RGBA 이미지로 렌더링
- 비디오 프레임에 자막을 알파 블렌딩
- 처리된 프레임을 출력 비디오에 기록

## 개발 노트

- 저장소에는 의도적으로 겹치는 버너 구현이 있으며, 일상 사용에는 SRT 파이프라인이 가장 단순합니다.
- `legacy/`와 `legacy-results/`는 아카이브 용도이며 회귀 비교에 유용합니다.
- 현재 패키징 메타데이터(`pyproject.toml` / `setup.py`)는 없습니다.
- 테스트 커버리지는 정식 프레임워크보다 스크립트 기반(`test_furigana.py`, `simple_test.py`, `font_test.py`)입니다.
- `openai_request.py`는 보조 유틸리티이며 핵심 자막 번인에 필수는 아닙니다.

## 문제 해결

### 일본어 폰트를 찾지 못하는 경우

시스템은 일본어 폰트를 자동으로 찾으려고 시도합니다.

- **macOS**: Hiragino Sans
- **Linux**: `fonts-japanese-gothic`
- **Windows**: MS Gothic

자막이 기본 폰트로 보인다면 일본어 폰트를 설치하세요.

추가 헬퍼:

```bash
python font_test.py
python fix_font_squares.py
```

### 후리가나가 생성되지 않는 경우

1. fugashi/unidic 설치 확인: `python -c "import fugashi; print('OK')"`
2. pykakasi 대체 경로 확인: `python -c "import pykakasi; print('OK')"`
3. 테스트 출력 확인: `python test_furigana.py`
4. 의존성 진단 실행: `python fix_unidic.py` 및 `python debug_japanese.py`

### 비디오 처리 오류

- 입력 비디오를 OpenCV가 읽을 수 있는지 확인
- 출력 파일을 위한 디스크 여유 공간 확인
- SRT 파일 인코딩이 UTF-8인지 확인
- 파이프라인 빠른 검증을 위해 `complete_furigana_burner.py --preview ...` 시도

## 성능

- 처리 속도는 비디오 해상도와 길이에 따라 달라집니다.
- 일반적인 속도: 처리율 10-30 fps
- 메모리 사용량은 비디오 해상도에 비례해 증가합니다.
- 단일 스레드 처리 사용(병렬화 가능)

## 의존성

| Package | Role | Notes |
|---|---|---|
| `opencv-python` | Video processing | Core dependency |
| `Pillow` | Image rendering and text drawing | Core dependency |
| `numpy` | Array operations | Core dependency |
| `fugashi` | Japanese morphological analysis | Optional but recommended |
| `unidic` | Japanese dictionary data | Optional but recommended |
| `pykakasi` | Kanji to hiragana conversion | Fallback path |
| `camel-tools` | Arabic transliteration helpers | Included in `requirements.txt`, used in generalized burner mode |

## 알려진 제한 사항

- 처리가 CPU 집약적입니다(GPU 가속 없음).
- 폰트 선택은 자동이며, 수동 제어 범위가 제한적입니다.
- 복잡한 단어의 후리가나 분배가 완벽하지 않을 수 있습니다.
- 세로쓰기 레이아웃은 지원하지 않습니다.
- 단일 자막 줄만 지원합니다(아직 멀티라인 미지원).

## 로드맵

- 복잡한 다한자 단어의 후리가나 정렬/분배 개선
- 멀티라인 자막 구성 옵션 확장
- classic/standalone/complete/generalized 버너 간 실행 프로필을 더 명확히 제공
- 패키징/테스트 자동화(`pyproject.toml`, CI 스모크 체크) 선택적 추가

## 여러분의 지원으로 가능한 일

- <b>도구를 계속 오픈 상태로 유지</b>: 호스팅, 추론, 데이터 저장소, 커뮤니티 운영.
- <b>더 빠른 출시</b>: EchoMind, LazyEdit, MultilingualWhisper에 집중하는 오픈소스 개발 시간 확보.
- <b>웨어러블 프로토타이핑</b>: IdeasGlass + LightMind를 위한 광학, 센서, 뉴로모픽/엣지 컴포넌트.
- <b>모두를 위한 접근성</b>: 학생, 창작자, 커뮤니티 그룹 대상 보조 배포.

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

## 기여

후리가나 생성 알고리즘 개선, 더 다양한 텍스트 레이아웃 지원, 비디오 처리 파이프라인 최적화 기여를 환영합니다.

변경 사항을 제출할 때는 다음을 포함해 주세요.

- 사용자 관점 영향에 대한 짧은 설명
- 로컬에서 실행한 재현/테스트 명령
- 렌더링에 영향이 있다면 폰트 및 언어 가정에 대한 메모

## 라이선스

현재 이 저장소에는 라이선스 파일이 없습니다.

이 초안의 가정: 유지관리자가 `LICENSE` 파일을 추가하기 전까지 모든 권리 및 사용 조건은 명시되지 않은 상태입니다.
