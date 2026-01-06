<p align="center">
  <img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/logos/banner.png" alt="LazyingArt banner" />
</p>

<p>
  <b>Languages:</b>
  <a href="../README.md">English</a>
  · <a href="README.zh-Hant.md">中文（繁體）</a>
  · <a href="README.zh-Hans.md">中文 (简体)</a>
  · <a href="README.ja.md">日本語</a>
  · <a href="README.ko.md">한국어</a>
  · <a href="README.vi.md">Tiếng Việt</a>
  · <a href="README.ar.md">العربية</a>
  · <a href="README.fr.md">Français</a>
  · <a href="README.es.md">Español</a>
</p>

# Furigana Subtitle Burner

ffmpeg 없이 일본어 후리가나(발음 표기) 자막을 영상에 직접 굽는 Python 도구입니다.

## 기능

- 🎌 **자동 후리가나 생성**: MeCab(fugashi) 또는 pykakasi 사용
- 🎨 **고급 렌더링**: 후리가나 정렬/간격 최적화
- 📺 **직접 영상 처리**: OpenCV 프레임 처리
- 🔤 **자동 폰트 감지**: 일본어 폰트 탐색
- ⚡ **배치 처리**: 다수 영상 처리
- 🎯 **정밀 위치**: 위치/여백 설정

## 설치

### 빠른 설치
```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

### 수동 설치
```bash
pip install opencv-python Pillow numpy fugashi unidic pykakasi
python -c "import unidic; unidic.download()"
```

## 사용법

### 1. 테스트
```bash
python test_furigana.py
```

### 2. 현재 폴더 일괄 처리
```bash
python process_furigana_videos.py
```

### 3. 단일 영상 처리
```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. 고급 옵션
```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

## 동작 방식

- 후리가나 생성: MeCab → pykakasi → 문자 단위
- 텍스트 렌더링: 글자 크기 측정 → 정렬 → 스트로크 적용
- 영상 처리: SRT 시간에 맞춰 프레임 합성

## 예시 출력

```
   きょう   そら    は
   今日  は 空  が 晴れていて
```

## 출력 구조

```
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4
├── video_577285345205551192-yFQ1pMPA.srt
├── video_577285345205551192-yFQ1pMPA.json
├── video_577285345205551192-yFQ1pMPA.wav
└── video_577285345205551192-yFQ1pMPA_furigana.mp4
```

## 설정

- `--main-font-size` (기본 48)
- `--furigana-font-size` (기본 24)
- `--position`: top/bottom/center
- `--margin`: 여백(px)

## 문제 해결

- 일본어 폰트: Hiragino / fonts-japanese-gothic / MS Gothic
- 후리가나 생성 실패: fugashi/pykakasi 설치 확인
- 영상 오류: OpenCV 지원 형식, 디스크 용량, SRT UTF-8 확인

## 성능

- 해상도/길이에 따라 10–30 fps
- 단일 스레드 처리

## 의존성

- opencv-python
- Pillow
- numpy
- fugashi
- unidic
- pykakasi

## 제한 사항

- GPU 가속 없음
- 자동 폰트 선택
- 복잡한 단어의 후리가나 오차 가능
- 세로쓰기 미지원
- 단일 자막 라인

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

후리가나 생성/레이아웃/성능 개선에 기여해 주세요.
