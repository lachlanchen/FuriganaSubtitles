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

這是一個 Python 工具，可在不使用 ffmpeg 的情況下，將日文假名註音（ふりがな）直接燒錄到影片中。

## 功能特色

- 🎌 **自動注音生成**：使用 MeCab (fugashi) 或 pykakasi 生成漢字假名
- 🎨 **自訂文字渲染**：良好對齊與間距的假名渲染
- 📺 **直接影片處理**：使用 OpenCV 逐幀處理
- 🔤 **智慧字型選擇**：自動找尋日文字型
- ⚡ **批次處理**：可一次處理多部影片
- 🎯 **精準定位**：可調整字幕位置與邊距

## 安裝

### 快速安裝
```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

### 手動安裝
```bash
# 安裝必要套件
pip install opencv-python Pillow numpy fugashi unidic pykakasi

# 下載日文字典
python -c "import unidic; unidic.download()"
```

## 使用方式

### 1. 測試系統
```bash
python test_furigana.py
```
會產生示範圖片，用於檢查注音效果。

### 2. 批次處理當前目錄影片
```bash
python process_furigana_videos.py
```

### 3. 處理單一影片
```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. 進階參數
```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

## 原理說明

### 1. 生成假名
- **主要方式**：MeCab + fugashi（較準確）
- **備援方式**：pykakasi（較簡單）
- **最後手段**：逐字處理

### 2. 文字渲染
- 測量每個字與假名尺寸
- 計算最佳欄寬
- 將假名置於對應漢字上方
- 加上描邊提高可讀性

### 3. 影片處理
- 使用 OpenCV 逐幀讀取
- 依 SRT 時間戳控制顯示
- 產生 RGBA 文字圖層
- Alpha 混合至原影片

## 範例輸出

文字「今日は空が晴れていて」：
```
   きょう   そら    は
   今日  は 空  が 晴れていて
```

## 輸出結構

```
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4
├── video_577285345205551192-yFQ1pMPA.srt
├── video_577285345205551192-yFQ1pMPA.json
├── video_577285345205551192-yFQ1pMPA.wav
└── video_577285345205551192-yFQ1pMPA_furigana.mp4
```

## 自訂選項

- `--main-font-size`：主文字大小（預設 48）
- `--furigana-font-size`：假名大小（預設 24）
- `--position`：`top`、`bottom`、`center`
- `--margin`：距離邊緣像素

## 疑難排解

### 找不到日文字型
- macOS：Hiragino Sans
- Linux：fonts-japanese-gothic
- Windows：MS Gothic

### 無法產生假名
1. `python -c "import fugashi; print('OK')"`
2. `python -c "import pykakasi; print('OK')"`
3. `python test_furigana.py`

### 影片處理錯誤
- 確認影片可被 OpenCV 讀取
- 確認磁碟空間
- 確認 SRT 編碼為 UTF-8

## 效能

- 速度與解析度、影片長度相關
- 典型速度約 10–30 fps
- 記憶體隨解析度增加
- 單執行緒處理

## 相依套件

- opencv-python
- Pillow
- numpy
- fugashi（建議）
- unidic（建議）
- pykakasi（備援）

## 已知限制

- CPU 密集（無 GPU 加速）
- 字型選擇較自動化
- 複雜詞彙的假名分配仍可能不完美
- 不支援直排
- 單行字幕（未支援多行）

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

歡迎改善假名生成、加入新排版或優化影片處理流程。
