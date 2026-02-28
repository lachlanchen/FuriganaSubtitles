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

OpenCV を使って、日本語のふりがなや各種ルビ注釈（pinyin、romaji、IPA など）を動画フレームへ直接焼き込む Python 製サブタイトルバーナーです。ふりがなワークフロー向けに最適化しつつ、多言語のルビ形式字幕にも柔軟に対応します。

Built for <a href="https://studio.lazying.art" target="_blank" rel="noreferrer">LazyEdit Studio</a> · <a href="https://github.com/lachlanchen/LazyEdit" target="_blank" rel="noreferrer">GitHub</a>

## 目次

- [概要](#概要)
- [機能](#機能)
- [プロジェクト構成](#プロジェクト構成)
- [前提条件](#前提条件)
- [インストール](#インストール)
- [使い方](#使い方)
- [設定](#設定)
- [例](#例)
- [動作の仕組み](#動作の仕組み)
- [開発メモ](#開発メモ)
- [トラブルシューティング](#トラブルシューティング)
- [パフォーマンス](#パフォーマンス)
- [依存関係](#依存関係)
- [既知の制限](#既知の制限)
- [ロードマップ](#ロードマップ)
- [支援で実現できること](#支援で実現できること)
- [コントリビューション](#コントリビューション)
- [ライセンス](#ライセンス)

## 概要

このリポジトリには、複数の字幕焼き込みルートが含まれています。

| ルート | スクリプト | 最適な用途 |
|---|---|---|
| クラシック SRT ふりがなワークフロー | `process_furigana_videos.py` + `furigana_subtitle_burner.py` | 日常的な SRT 字幕焼き込み |
| スタンドアロンワークフロー | `standalone_furigana_burner.py` | 単一スクリプトでシンプルに実行 |
| コンプリートワークフロー | `complete_furigana_burner.py` | 設定の保存/読み込み + プレビューモード |
| 汎用ルビエンジン | `subtitles_burner/burner.py` | JSON 駆動の多言語トークン単位注釈 |

README のデフォルトフローは、明示的に JSON ベースのマルチスロット描画が必要な場合を除き、SRT ベースのパイプラインです。

## 機能

- 🎌 **ふりがなの自動生成**: MeCab（fugashi）または pykakasi を使って漢字のふりがなを生成
- 🌐 **ルビ注釈対応**: 漢字・かな・その他スクリプト（pinyin、romaji、IPA）の発音ガイドを描画
- 🎨 **高品質なテキスト描画**: 適切な間隔・配置・ストロークで美しいルビテキストを描画
- 📺 **動画の直接処理**: OpenCV で字幕を動画フレームへ直接焼き込み
- 🔤 **スマートフォント処理**: CJK とラテン文字向けフォントを自動検出して使用
- ⚡ **バッチ処理**: 複数動画を一括処理
- 🎯 **精密な位置制御**: 字幕位置、余白、レイアウト挙動を設定可能
- 🧩 **複数ランタイム**: classic / standalone / complete / generalized の各モジュールを選択可能

## プロジェクト構成

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

## 前提条件

- Python 3.9+ 推奨
- 日本語/CJK テキストを描画できるフォントがある OS
- フレーム単位の動画出力に十分な CPU とディスク容量
- 入力字幕ファイルは UTF-8 エンコード推奨

## インストール

### クイックセットアップ

```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

セットアップスクリプトは、コアパッケージをインストールし、UniDic のダウンロードを試行し、`test_furigana.py` を実行します。

### 手動インストール

```bash
# Option A: install pinned repo requirements
pip install -r requirements.txt

# Option B: install explicit core packages (as documented in original README)
pip install opencv-python Pillow numpy fugashi unidic pykakasi

# Download Japanese dictionary data
python -c "import unidic; unidic.download()"
```

`subtitles_burner/burner.py` で使うオプションパッケージ（特定の音訳モードでのみ必要）:

```bash
pip install phonemizer koroman pypinyin pycantonese
```

`openai_request.py` ヘルパーで使うオプションパッケージ:

```bash
pip install openai pygame
```

## 使い方

### 1. システムテスト

```bash
python test_furigana.py
```

ふりがな生成をテストし、`test_furigana_output.png` を作成します。

### 2. 現在ディレクトリ内の全動画を処理

```bash
python process_furigana_videos.py
```

すべての `video_*` ディレクトリを自動検出し、それぞれで最初の `.MP4` と `.srt` を処理します。

### 3. 単一動画を処理

```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. 高度な使い方（クラシックバーナー）

```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

### 5. スタンドアロンバーナー（自動検出モード）

```bash
python standalone_furigana_burner.py
```

引数なしで実行すると、現在ディレクトリの `*.MP4`/`*.mp4` と `*.srt` を自動検出します。

### 6. コンプリートバーナー（設定 + プレビュー）

```bash
python complete_furigana_burner.py video.mp4 sub.srt out.mp4 --preview
python complete_furigana_burner.py video.mp4 sub.srt out.mp4 --save-config
python complete_furigana_burner.py --config furigana_config.json video.mp4 sub.srt out.mp4
```

### 7. 汎用 JSON ルビバーナー

```bash
python subtitles_burner/burner.py input.mp4 subtitles.json output.mp4 \
  --text-key text \
  --ruby-key ruby \
  --slot 1 \
  --auto-ruby
```

## 設定

### CLI パラメータ（Classic `furigana_subtitle_burner.py`）

| パラメータ | 説明 | デフォルト |
|---|---|---|
| `--furigana-font-size` | ふりがなテキストのサイズ | `24` |
| `--position` | `top`、`bottom`、`center` | `bottom` |
| `--margin` | 端からの距離（ピクセル） | `50` |

### CLI パラメータ（`standalone_furigana_burner.py`）

| パラメータ | 説明 | デフォルト |
|---|---|---|
| `--main-font-size` | メインテキストサイズ | `64` |
| `--furigana-font-size` | ふりがなサイズ | `32` |
| `--position` | `top`、`bottom`、`center` | `bottom` |
| `--margin` | 端からの余白 | `80` |

### CLI パラメータ（`complete_furigana_burner.py`）

| パラメータ | 説明 | デフォルト |
|---|---|---|
| `--main-font-size` | メインテキストサイズ | `64` |
| `--furigana-font-size` | ふりがなサイズ | `32` |
| `--position` | `top`、`bottom`、`center` | `bottom` |
| `--margin` | 端からの余白 | `80` |
| `--preview` | プレビューモード（先頭約10秒） | Off |
| `--config <path>` | 設定ファイルを読み込み | `None` |
| `--save-config` | 現在設定をデフォルトとして保存 | Off |

### CLI パラメータ（`subtitles_burner/burner.py`）

| パラメータ | 説明 | デフォルト |
|---|---|---|
| `--text-key` | ベーステキスト用 JSON キー | `text` |
| `--ruby-key` | ルビマークアップ用 JSON キー | `None` |
| `--slot` | 下部スロットレイアウトのスロット ID | `1` |

### テキスト表示

- 最大の視認性を得るため、白文字 + 黒ストローク
- 文字とふりがなの間隔はプロポーショナルに調整

## 例

### 出力例

`今日は空が晴れていて` の場合:

```text
   きょう   そら    は
   今日  は 空  が 晴れていて
```

### バッチ入出力レイアウト例

処理後のディレクトリは次のようになります:

```text
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4      # Original video
├── video_577285345205551192-yFQ1pMPA.srt      # Subtitle file
├── video_577285345205551192-yFQ1pMPA.json     # Whisper output
├── video_577285345205551192-yFQ1pMPA.wav      # Audio extraction
└── video_577285345205551192-yFQ1pMPA_furigana.mp4  # Output with furigana
```

## 動作の仕組み

### 1. ふりがな生成

本システムは、ふりがな生成に複数の方式を使用します。

- **Primary**: MeCab + fugashi による高精度な形態素解析
- **Fallback**: pykakasi による基本的な漢字かな変換
- **Last Resort**: 文字単位の解析

### 2. テキスト描画戦略

- 各文字と対応するふりがなを個別に計測
- 各文字に対する最適な列幅を計算
- 対応する漢字の上にふりがなを中央揃えで配置
- 視認性向上のためテキストにストロークを追加

### 3. 動画処理

- OpenCV で動画をフレーム単位に読み込み
- SRT タイムスタンプに基づいて字幕タイミングを計算
- ふりがなテキストを RGBA 画像として描画
- アルファブレンドで字幕を動画フレームへ合成
- 処理済みフレームを出力動画へ書き込み

## 開発メモ

- リポジトリには意図的に重複するバーナー実装があります。日常用途では SRT パイプラインが最もシンプルです。
- `legacy/` と `legacy-results/` はアーカイブで、回帰比較に有用です。
- 現時点でパッケージメタデータ（`pyproject.toml` / `setup.py`）はありません。
- テストカバレッジは正式なテストフレームワークではなく、スクリプトベース（`test_furigana.py`、`simple_test.py`、`font_test.py`）です。
- `openai_request.py` は補助ユーティリティで、コアの字幕焼き込みには必須ではありません。

## トラブルシューティング

### 日本語フォントが見つからない


- **macOS**: Hiragino Sans
- **Linux**: `fonts-japanese-gothic`
- **Windows**: MS Gothic

字幕がデフォルトフォントで表示される場合は、日本語フォントをインストールしてください。

追加ヘルパー:

```bash
python font_test.py
python fix_font_squares.py
```

### ふりがなが生成されない

1. fugashi/unidic の確認: `python -c "import fugashi; print('OK')"`
2. pykakasi フォールバックの確認: `python -c "import pykakasi; print('OK')"`
3. テスト出力の確認: `python test_furigana.py`
4. 依存診断の実行: `python fix_unidic.py` と `python debug_japanese.py`

### 動画処理エラー

- 入力動画が OpenCV で読み取れることを確認
- 出力ファイル用のディスク空き容量を確認
- SRT ファイルのエンコードが UTF-8 であることを確認
- `complete_furigana_burner.py --preview ...` でパイプラインを素早く検証

## パフォーマンス

- 処理速度は動画解像度と長さに依存
- 典型的な処理速度: 10-30 fps
- メモリ使用量は動画解像度に応じて増加
- 単一スレッド処理（並列化は可能）

## 依存関係

| パッケージ | 役割 | 備考 |
|---|---|---|
| `opencv-python` | 動画処理 | コア依存 |
| `Pillow` | 画像描画と文字描画 | コア依存 |
| `numpy` | 配列演算 | コア依存 |
| `pykakasi` | 漢字からひらがなへの変換 | フォールバック経路 |
| `camel-tools` | アラビア語音訳ヘルパー | `requirements.txt` に含まれ、汎用バーナーモードで使用 |

## 既知の制限

- CPU 負荷が高い（GPU アクセラレーションなし）
- フォント選択は自動（手動制御は限定的）
- 複雑な単語ではふりがなの割り当てが完全でない場合がある
- 縦書きレイアウト未対応
- 単一字幕行のみ対応（複数行は未対応）

## ロードマップ

- 複雑な複数字漢字語向けに、ふりがな配置/配分を改善
- 複数行字幕の構成オプションを拡張
- classic / standalone / complete / generalized 間のランタイム特性をより明確化
- 必要に応じてパッケージング/テスト自動化（`pyproject.toml`、CI スモークチェック）を追加

## 支援で実現できること

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

## コントリビューション

ふりがな生成アルゴリズムの改善、より多くのテキストレイアウト対応の追加、動画処理パイプラインの最適化などの貢献を歓迎します。

変更を提出する場合は、次を含めてください。

- ユーザー向け影響の短い説明
- ローカルで実行した再現/テストコマンド
- 描画に影響する変更の場合は、フォントと言語前提に関するメモ

## ライセンス

現在、このリポジトリにはライセンスファイルがありません。

このドラフト時点の前提: メンテナーによって `LICENSE` ファイルが追加されるまでは、権利および利用条件は未規定です。
