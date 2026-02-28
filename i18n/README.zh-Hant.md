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

這是一個 Python 字幕燒錄工具，使用 OpenCV 直接在影片影格上渲染日文振假名（furigana）以及其他 ruby 註音（如拼音、羅馬字、IPA 等）。它針對振假名流程做了最佳化，同時保有多語言 ruby 風格字幕的彈性。

Built for <a href="https://studio.lazying.art" target="_blank" rel="noreferrer">LazyEdit Studio</a> · <a href="https://github.com/lachlanchen/LazyEdit" target="_blank" rel="noreferrer">GitHub</a>

## 目錄

- [概覽](#概覽)
- [功能特色](#功能特色)
- [專案結構](#專案結構)
- [先決條件](#先決條件)
- [安裝](#安裝)
- [使用方式](#使用方式)
- [設定](#設定)
- [範例](#範例)
- [運作原理](#運作原理)
- [開發備註](#開發備註)
- [疑難排解](#疑難排解)
- [效能](#效能)
- [相依套件](#相依套件)
- [已知限制](#已知限制)
- [路線圖](#路線圖)
- [你的支持將帶來什麼](#你的支持將帶來什麼)
- [貢獻](#貢獻)
- [授權](#授權)

## 概覽

此儲存庫包含多種字幕燒錄流程：

| 路徑 | 腳本 | 最適合用途 |
|---|---|---|
| 經典 SRT 振假名流程 | `process_furigana_videos.py` + `furigana_subtitle_burner.py` | 日常以 SRT 檔案進行字幕燒錄 |
| 獨立流程 | `standalone_furigana_burner.py` | 單一腳本的簡單執行 |
| 完整流程 | `complete_furigana_burner.py` | 設定儲存/載入 + 預覽模式 |
| 泛化 ruby 引擎 | `subtitles_burner/burner.py` | 以 JSON 驅動的多語言、token 級註解 |

除非你明確需要以 JSON 為基礎的多槽位渲染，README 預設流程仍是 SRT 管線。

## 功能特色

- 🎌 **自動產生振假名**：使用 MeCab（fugashi）或 pykakasi，為漢字自動產生振假名
- 🌐 **Ruby 註解支援**：可渲染漢字、假名與其他文字系統的讀音標註（拼音、羅馬字、IPA）
- 🎨 **可自訂文字渲染**：提供合適間距、對齊與描邊的美觀 ruby 文字渲染
- 📺 **直接影片處理**：透過 OpenCV 直接把字幕燒錄到影片影格
- 🔤 **智慧字型處理**：自動尋找並使用 CJK 與拉丁字元字型
- ⚡ **批次處理**：可一次處理多部影片
- 🎯 **精準定位**：可設定字幕位置、邊距與版面行為
- 🧩 **多種執行模式**：可在 classic、standalone、complete 或 generalized 模組間切換

## 專案結構

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

## 先決條件

- 建議使用 Python 3.9+
- 作業系統需具備可渲染日文/CJK 文字的字型
- 需有足夠 CPU 與磁碟空間進行逐影格影片輸出
- 建議輸入字幕檔採用 UTF-8 編碼

## 安裝

### 快速安裝

```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

安裝腳本會安裝核心套件、嘗試下載 UniDic，並執行 `test_furigana.py`。

### 手動安裝

```bash
# Option A: install pinned repo requirements
pip install -r requirements.txt

# Option B: install explicit core packages (as documented in original README)
pip install opencv-python Pillow numpy fugashi unidic pykakasi

# Download Japanese dictionary data
python -c "import unidic; unidic.download()"
```

`subtitles_burner/burner.py` 使用的可選套件（僅在特定轉寫模式需要）：

```bash
pip install phonemizer koroman pypinyin pycantonese
```

`openai_request.py` 輔助工具使用的可選套件：

```bash
pip install openai pygame
```

## 使用方式

### 1. 測試系統

```bash
python test_furigana.py
```

此指令會測試振假名生成功能，並建立 `test_furigana_output.png`。

### 2. 處理目前目錄中的所有影片

```bash
python process_furigana_videos.py
```

會自動尋找所有 `video_*` 目錄，並處理每個目錄中的第一個 `.MP4` 與 `.srt`。

### 3. 處理單一影片

```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. 進階用法（Classic Burner）

```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

### 5. Standalone Burner（自動偵測模式）

```bash
python standalone_furigana_burner.py
```

若不帶參數執行，會在目前目錄自動偵測 `*.MP4`/`*.mp4` 與 `*.srt`。

### 6. Complete Burner（設定 + 預覽）

```bash
python complete_furigana_burner.py video.mp4 sub.srt out.mp4 --preview
python complete_furigana_burner.py video.mp4 sub.srt out.mp4 --save-config
python complete_furigana_burner.py --config furigana_config.json video.mp4 sub.srt out.mp4
```

### 7. 泛化 JSON Ruby Burner

```bash
python subtitles_burner/burner.py input.mp4 subtitles.json output.mp4 \
  --text-key text \
  --ruby-key ruby \
  --slot 1 \
  --auto-ruby
```

## 設定

### CLI 參數（Classic `furigana_subtitle_burner.py`）

| 參數 | 說明 | 預設值 |
|---|---|---|
| `--main-font-size` | 主要日文文字大小 | `48` |
| `--furigana-font-size` | 振假名文字大小 | `24` |
| `--position` | `top`、`bottom` 或 `center` | `bottom` |
| `--margin` | 與邊緣距離（像素） | `50` |

### CLI 參數（`standalone_furigana_burner.py`）

| 參數 | 說明 | 預設值 |
|---|---|---|
| `--main-font-size` | 主要文字大小 | `64` |
| `--furigana-font-size` | 振假名文字大小 | `32` |
| `--position` | `top`、`bottom` 或 `center` | `bottom` |
| `--margin` | 與邊緣距離 | `80` |

### CLI 參數（`complete_furigana_burner.py`）

| 參數 | 說明 | 預設值 |
|---|---|---|
| `--main-font-size` | 主要文字大小 | `64` |
| `--furigana-font-size` | 振假名文字大小 | `32` |
| `--position` | `top`、`bottom` 或 `center` | `bottom` |
| `--margin` | 與邊緣距離 | `80` |
| `--preview` | 預覽模式（前約 10 秒） | Off |
| `--config <path>` | 載入設定檔 | `None` |
| `--save-config` | 將目前設定存為預設值 | Off |

### CLI 參數（`subtitles_burner/burner.py`）

| 參數 | 說明 | 預設值 |
|---|---|---|
| `--text-key` | JSON 中基礎文字的 key | `text` |
| `--ruby-key` | JSON 中 ruby 標記的 key | `None` |
| `--slot` | 底部槽位版面的槽位 ID | `1` |
| `--auto-ruby` | 自動為日文產生 ruby | Off |

### 文字外觀

- 白字黑邊，以提升可讀性
- 自動選擇字型（會嘗試系統日文字型）
- 在字元與振假名之間使用等比例間距

## 範例

### 範例輸出

對於文字 `今日は空が晴れていて`：

```text
   きょう   そら    は
   今日  は 空  が 晴れていて
```

### 範例批次輸入/輸出目錄結構

處理完成後，目錄會像這樣：

```text
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4      # Original video
├── video_577285345205551192-yFQ1pMPA.srt      # Subtitle file
├── video_577285345205551192-yFQ1pMPA.json     # Whisper output
├── video_577285345205551192-yFQ1pMPA.wav      # Audio extraction
└── video_577285345205551192-yFQ1pMPA_furigana.mp4  # Output with furigana
```

## 運作原理

### 1. 振假名生成

系統使用多種方法產生振假名：

- **Primary**：使用 MeCab 搭配 fugashi，提供準確的形態學分析
- **Fallback**：使用 pykakasi 進行基本漢字轉平假名
- **Last Resort**：逐字分析

### 2. 文字渲染策略

- 分別量測每個字元及其振假名
- 計算每個字元的最佳欄寬
- 將振假名置中於對應漢字上方
- 加上文字描邊以提升可視性

### 3. 影片處理

- 使用 OpenCV 逐影格讀取影片
- 依 SRT 時間戳計算字幕顯示時機
- 將振假名文字渲染成 RGBA 影像
- 以 alpha 混合方式疊加字幕到影格
- 將處理後影格寫入輸出影片

## 開發備註

- 儲存庫刻意保留多個重疊的 burner；日常使用最簡單的是 SRT 管線。
- `legacy/` 與 `legacy-results/` 為封存資料，適合做回歸比較。
- 目前沒有封裝中繼資料（`pyproject.toml` / `setup.py`）。
- 測試覆蓋以腳本為主（`test_furigana.py`、`simple_test.py`、`font_test.py`），不是正式測試框架。
- `openai_request.py` 是輔助工具，核心字幕燒錄不依賴它。

## 疑難排解

### 找不到日文字型

系統會自動嘗試尋找日文字型：

- **macOS**：Hiragino Sans
- **Linux**：`fonts-japanese-gothic`
- **Windows**：MS Gothic

若字幕顯示為預設字型，請安裝日文字型。

其他輔助工具：

```bash
python font_test.py
python fix_font_squares.py
```

### 無法產生振假名

1. 檢查是否已安裝 fugashi/unidic：`python -c "import fugashi; print('OK')"`
2. 改用 pykakasi 後備路徑：`python -c "import pykakasi; print('OK')"`
3. 檢查測試輸出：`python test_furigana.py`
4. 執行相依性診斷：`python fix_unidic.py` 與 `python debug_japanese.py`

### 影片處理錯誤

- 確認 OpenCV 可讀取輸入影片
- 檢查輸出檔案所需的磁碟空間
- 確認 SRT 檔案編碼為 UTF-8
- 可先用 `complete_furigana_burner.py --preview ...` 快速驗證流程

## 效能

- 處理速度取決於影片解析度與長度
- 常見速度：約 10-30 fps
- 記憶體使用量會隨影片解析度增加
- 目前使用單執行緒處理（可再平行化）

## 相依套件

| 套件 | 角色 | 備註 |
|---|---|---|
| `opencv-python` | 影片處理 | 核心相依 |
| `Pillow` | 影像渲染與文字繪製 | 核心相依 |
| `numpy` | 陣列運算 | 核心相依 |
| `fugashi` | 日文形態學分析 | 可選但建議安裝 |
| `unidic` | 日文詞典資料 | 可選但建議安裝 |
| `pykakasi` | 漢字轉平假名 | 後備路徑 |
| `camel-tools` | 阿拉伯文轉寫輔助 | 已包含於 `requirements.txt`，用於 generalized burner 模式 |

## 已知限制

- 處理流程吃 CPU（無 GPU 加速）
- 字型選擇為自動模式（手動控制有限）
- 複雜詞彙的振假名分配可能不完美
- 不支援直排文字版面
- 目前僅支援單行字幕（尚未支援多行）

## 路線圖

- 改善複雜多漢字詞彙的振假名對齊/分配
- 擴充多行字幕排版選項
- 讓 classic/standalone/complete/generalized 各執行模式的定位更清晰
- 視需要加入封裝/測試自動化（`pyproject.toml`、CI smoke checks）

## 你的支持將帶來什麼

- <b>維持工具開放</b>：支撐託管、推論、資料儲存與社群營運。
- <b>加速交付</b>：投入數週完整開源開發時間於 EchoMind、LazyEdit 與 MultilingualWhisper。
- <b>穿戴式原型</b>：用於 IdeasGlass + LightMind 的光學、感測器與類神經/邊緣元件。
- <b>普及可及性</b>：為學生、創作者與社群團體提供補助部署。

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

## 貢獻

歡迎你改進振假名生成演算法、加入更多文字版面支援，或優化影片處理管線。

如果你要提交變更，請附上：

- 對使用者可見影響的簡短說明
- 你在本機執行的重現/測試指令
- 若變更影響渲染，請補充字型與語言假設

## 授權

此儲存庫目前尚未提供授權檔案。

此草稿的假設：在維護者新增 `LICENSE` 檔案前，所有權利與使用條款目前皆未明確指定。
