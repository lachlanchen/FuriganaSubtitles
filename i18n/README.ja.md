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

ffmpeg を使わずに、日本語のふりがな付き字幕を動画に直接焼き込む Python ツールです。

## 特長

- 🎌 **自動ふりがな生成**：MeCab (fugashi) / pykakasi
- 🎨 **高品質レンダリング**：文字とふりがなの間隔を最適化
- 📺 **直接動画処理**：OpenCV でフレーム処理
- 🔤 **自動フォント検出**：日本語フォントを探索
- ⚡ **バッチ処理**：複数動画を一括処理
- 🎯 **位置調整**：字幕位置・余白を設定可能

## インストール

### クイックセットアップ
```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

### 手動インストール
```bash
pip install opencv-python Pillow numpy fugashi unidic pykakasi
python -c "import unidic; unidic.download()"
```

## 使い方

### 1. テスト
```bash
python test_furigana.py
```

### 2. カレントディレクトリを一括処理
```bash
python process_furigana_videos.py
```

### 3. 単体処理
```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. 詳細オプション
```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

## 仕組み

### 1. ふりがな生成
- **優先**：MeCab + fugashi
- **フォールバック**：pykakasi
- **最終手段**：文字単位

### 2. 文字描画
- 文字幅とふりがな幅を計測
- カラム幅を最適化
- 漢字の上にふりがなを配置
- 視認性向上の縁取り

### 3. 動画処理
- OpenCV でフレーム読み込み
- SRT の時間に同期
- RGBA テキストを合成

## 出力例

「今日は空が晴れていて」
```
   きょう   そら    は
   今日  は 空  が 晴れていて
```

## 出力構成

```
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4
├── video_577285345205551192-yFQ1pMPA.srt
├── video_577285345205551192-yFQ1pMPA.json
├── video_577285345205551192-yFQ1pMPA.wav
└── video_577285345205551192-yFQ1pMPA_furigana.mp4
```

## カスタマイズ

- `--main-font-size`：本文サイズ（既定 48）
- `--furigana-font-size`：ふりがなサイズ（既定 24）
- `--position`：`top` / `bottom` / `center`
- `--margin`：余白ピクセル

## トラブルシューティング

### 日本語フォントが見つからない
- macOS：Hiragino Sans
- Linux：fonts-japanese-gothic
- Windows：MS Gothic

### ふりがなが生成されない
1. `python -c "import fugashi; print('OK')"`
2. `python -c "import pykakasi; print('OK')"`
3. `python test_furigana.py`

### 動画処理エラー
- OpenCV が読める形式か確認
- ディスク容量確認
- SRT が UTF-8 か確認

## パフォーマンス

- 解像度と長さに依存
- 一般的に 10–30 fps
- 単一スレッド処理

## 依存関係

- opencv-python
- Pillow
- numpy
- fugashi
- unidic
- pykakasi

## 既知の制限

- CPU 集中（GPU 非対応）
- フォントは自動選択
- 複雑語のふりがなは完全でない場合あり
- 縦書き非対応
- 1 行字幕のみ

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

ふりがな生成の改善や新レイアウトの追加、処理の最適化にご協力ください。
