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

Một công cụ burn phụ đề bằng Python có thể render furigana tiếng Nhật và các chú thích ruby khác (pinyin, romaji, IPA, v.v.) trực tiếp lên từng khung hình video bằng OpenCV. Dự án được tối ưu cho quy trình furigana nhưng vẫn linh hoạt cho phụ đề kiểu ruby đa ngôn ngữ.

Được xây dựng cho <a href="https://studio.lazying.art" target="_blank" rel="noreferrer">LazyEdit Studio</a> · <a href="https://github.com/lachlanchen/LazyEdit" target="_blank" rel="noreferrer">GitHub</a>

## Mục lục

- [Tổng quan](#tổng-quan)
- [Tính năng](#tính-năng)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Điều kiện tiên quyết](#điều-kiện-tiên-quyết)
- [Cài đặt](#cài-đặt)
- [Cách sử dụng](#cách-sử-dụng)
- [Cấu hình](#cấu-hình)
- [Ví dụ](#ví-dụ)
- [Cơ chế hoạt động](#cơ-chế-hoạt-động)
- [Ghi chú phát triển](#ghi-chú-phát-triển)
- [Khắc phục sự cố](#khắc-phục-sự-cố)
- [Hiệu năng](#hiệu-năng)
- [Phụ thuộc](#phụ-thuộc)
- [Hạn chế đã biết](#hạn-chế-đã-biết)
- [Lộ trình](#lộ-trình)
- [Sự hỗ trợ của bạn giúp thực hiện điều gì](#sự-hỗ-trợ-của-bạn-giúp-thực-hiện-điều-gì)
- [Đóng góp](#đóng-góp)
- [Giấy phép](#giấy-phép)

## Tổng quan

Kho này bao gồm nhiều luồng burn phụ đề:

| Luồng | Script | Phù hợp nhất cho |
|---|---|---|
| Luồng furigana SRT cổ điển | `process_furigana_videos.py` + `furigana_subtitle_burner.py` | Burn phụ đề hằng ngày với tệp SRT |
| Luồng độc lập | `standalone_furigana_burner.py` | Chạy đơn giản bằng một script |
| Luồng đầy đủ | `complete_furigana_burner.py` | Lưu/tải cấu hình + chế độ xem trước |
| Ruby engine tổng quát | `subtitles_burner/burner.py` | Chú thích cấp token đa ngôn ngữ điều khiển bằng JSON |

Luồng mặc định trong README vẫn là pipeline dựa trên SRT, trừ khi bạn cần render nhiều slot dựa trên JSON.

## Tính năng

- 🎌 **Tạo Furigana Tự động**: Dùng MeCab (fugashi) hoặc pykakasi để tạo furigana cho chữ kanji
- 🌐 **Hỗ trợ Chú thích Ruby**: Render hướng dẫn phát âm cho kanji, kana và các hệ chữ khác (pinyin, romaji, IPA)
- 🎨 **Render Văn bản Tùy chỉnh**: Render chữ ruby đẹp, khoảng cách, căn chỉnh và viền hợp lý
- 📺 **Xử lý Video Trực tiếp**: Burn phụ đề trực tiếp lên từng khung hình bằng OpenCV
- 🔤 **Xử lý Font Thông minh**: Tự động tìm và dùng font cho CJK và chữ Latin
- ⚡ **Xử lý hàng loạt**: Xử lý nhiều video cùng lúc
- 🎯 **Định vị Chính xác**: Cấu hình vị trí phụ đề, lề và hành vi bố cục
- 🧩 **Nhiều Runtime**: Chọn giữa các module classic, standalone, complete hoặc generalized burner

## Cấu trúc dự án

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

## Điều kiện tiên quyết

- Khuyến nghị Python 3.9+
- Hệ điều hành có font có thể render chữ Nhật/CJK
- Đủ CPU và dung lượng đĩa cho xuất video theo từng khung hình
- Tệp phụ đề đầu vào mã hóa UTF-8 (khuyến nghị)

## Cài đặt

### Thiết lập nhanh

```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

Script thiết lập sẽ cài các gói cốt lõi, thử tải UniDic và chạy `test_furigana.py`.

### Cài đặt thủ công

```bash
# Option A: install pinned repo requirements
pip install -r requirements.txt

# Option B: install explicit core packages (as documented in original README)
pip install opencv-python Pillow numpy fugashi unidic pykakasi

# Download Japanese dictionary data
python -c "import unidic; unidic.download()"
```

Các gói tùy chọn dùng bởi `subtitles_burner/burner.py` (chỉ cần cho một số chế độ chuyển tự cụ thể):

```bash
pip install phonemizer koroman pypinyin pycantonese
```

Các gói tùy chọn dùng bởi tiện ích `openai_request.py`:

```bash
pip install openai pygame
```

## Cách sử dụng

### 1. Kiểm tra hệ thống

```bash
python test_furigana.py
```

Lệnh này kiểm tra tạo furigana và tạo `test_furigana_output.png`.

### 2. Xử lý tất cả video trong thư mục hiện tại

```bash
python process_furigana_videos.py
```

Tự động tìm tất cả thư mục `video_*` và xử lý tệp `.MP4` và `.srt` đầu tiên trong mỗi thư mục.

### 3. Xử lý một video đơn

```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. Cách dùng nâng cao (Classic Burner)

```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

### 5. Standalone Burner (Chế độ tự phát hiện)

```bash
python standalone_furigana_burner.py
```

Nếu chạy không có tham số, script sẽ tự phát hiện `*.MP4`/`*.mp4` và `*.srt` trong thư mục hiện tại.

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

## Cấu hình

### Tham số CLI (Classic `furigana_subtitle_burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--main-font-size` | Cỡ chữ tiếng Nhật chính | `48` |
| `--furigana-font-size` | Cỡ chữ furigana | `24` |
| `--position` | `top`, `bottom`, hoặc `center` | `bottom` |
| `--margin` | Khoảng cách tới mép (pixel) | `50` |

### Tham số CLI (`standalone_furigana_burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--main-font-size` | Cỡ chữ chính | `64` |
| `--furigana-font-size` | Cỡ chữ furigana | `32` |
| `--position` | `top`, `bottom`, hoặc `center` | `bottom` |
| `--margin` | Lề so với mép | `80` |

### Tham số CLI (`complete_furigana_burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--main-font-size` | Cỡ chữ chính | `64` |
| `--furigana-font-size` | Cỡ chữ furigana | `32` |
| `--position` | `top`, `bottom`, hoặc `center` | `bottom` |
| `--margin` | Lề so với mép | `80` |
| `--preview` | Chế độ xem trước (khoảng 10 giây đầu) | Off |
| `--config <path>` | Tải tệp cấu hình | `None` |
| `--save-config` | Lưu cấu hình hiện tại làm mặc định | Off |

### Tham số CLI (`subtitles_burner/burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--text-key` | JSON key cho văn bản gốc | `text` |
| `--ruby-key` | JSON key cho ruby markup | `None` |
| `--slot` | Slot ID trong bố cục slot dưới | `1` |
| `--auto-ruby` | Tự sinh ruby cho tiếng Nhật | Off |

### Hiển thị văn bản

- Chữ trắng viền đen để tăng khả năng nhìn rõ
- Tự động chọn font (ưu tiên thử các font tiếng Nhật trong hệ thống)
- Khoảng cách tỉ lệ giữa ký tự và furigana

## Ví dụ

### Ví dụ đầu ra

Với văn bản `今日は空が晴れていて`:

```text
   きょう   そら    は
   今日  は 空  が 晴れていて
```

### Ví dụ bố cục đầu vào/đầu ra hàng loạt

Sau khi xử lý, thư mục của bạn sẽ có dạng:

```text
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4      # Original video
├── video_577285345205551192-yFQ1pMPA.srt      # Subtitle file
├── video_577285345205551192-yFQ1pMPA.json     # Whisper output
├── video_577285345205551192-yFQ1pMPA.wav      # Audio extraction
└── video_577285345205551192-yFQ1pMPA_furigana.mp4  # Output with furigana
```

## Cơ chế hoạt động

### 1. Tạo Furigana

Hệ thống dùng nhiều phương pháp để tạo furigana:

- **Primary**: MeCab với fugashi để phân tích hình thái chính xác
- **Fallback**: pykakasi để chuyển kanji sang hiragana cơ bản
- **Last Resort**: Phân tích từng ký tự

### 2. Chiến lược render văn bản

- Đo riêng từng ký tự và furigana tương ứng
- Tính độ rộng cột tối ưu cho từng ký tự
- Căn giữa furigana phía trên kanji tương ứng
- Thêm viền chữ để tăng độ rõ

### 3. Xử lý video

- Đọc video theo từng khung hình bằng OpenCV
- Tính thời điểm hiển thị phụ đề theo mốc thời gian SRT
- Render văn bản furigana dưới dạng ảnh RGBA
- Alpha-blend phụ đề lên khung hình video
- Ghi khung hình đã xử lý ra video đầu ra

## Ghi chú phát triển

- Kho có các burner chồng lấn theo chủ ý; pipeline SRT là lựa chọn đơn giản nhất cho nhu cầu hằng ngày.
- `legacy/` và `legacy-results/` là dữ liệu lưu trữ và hữu ích cho so sánh hồi quy.
- Hiện chưa có metadata đóng gói (`pyproject.toml` / `setup.py`).
- Độ phủ kiểm thử ở dạng script (`test_furigana.py`, `simple_test.py`, `font_test.py`), chưa phải framework test chính thức.
- `openai_request.py` là tiện ích phụ trợ, không bắt buộc cho burn phụ đề cốt lõi.

## Khắc phục sự cố

### Không tìm thấy font tiếng Nhật

Hệ thống sẽ cố tự tìm font tiếng Nhật:

- **macOS**: Hiragino Sans
- **Linux**: `fonts-japanese-gothic`
- **Windows**: MS Gothic

Hãy cài font tiếng Nhật nếu phụ đề hiển thị bằng font mặc định.

Công cụ hỗ trợ thêm:

```bash
python font_test.py
python fix_font_squares.py
```

### Không tạo được Furigana

1. Kiểm tra fugashi/unidic đã cài chưa: `python -c "import fugashi; print('OK')"`
2. Dùng đường dự phòng pykakasi: `python -c "import pykakasi; print('OK')"`
3. Kiểm tra kết quả test: `python test_furigana.py`
4. Chạy chẩn đoán phụ thuộc: `python fix_unidic.py` và `python debug_japanese.py`

### Lỗi xử lý video

- Đảm bảo OpenCV đọc được video đầu vào
- Kiểm tra dung lượng đĩa còn trống cho tệp đầu ra
- Xác minh tệp SRT dùng mã hóa UTF-8
- Thử `complete_furigana_burner.py --preview ...` để kiểm chứng pipeline nhanh

## Hiệu năng

- Tốc độ xử lý phụ thuộc vào độ phân giải và độ dài video
- Tốc độ điển hình: 10-30 fps
- Mức dùng bộ nhớ tăng theo độ phân giải video
- Dùng xử lý đơn luồng (có thể song song hóa)

## Phụ thuộc

| Package | Vai trò | Ghi chú |
|---|---|---|
| `opencv-python` | Xử lý video | Phụ thuộc cốt lõi |
| `Pillow` | Render ảnh và vẽ văn bản | Phụ thuộc cốt lõi |
| `numpy` | Thao tác mảng | Phụ thuộc cốt lõi |
| `fugashi` | Phân tích hình thái tiếng Nhật | Tùy chọn nhưng khuyến nghị |
| `unidic` | Dữ liệu từ điển tiếng Nhật | Tùy chọn nhưng khuyến nghị |
| `pykakasi` | Chuyển kanji sang hiragana | Đường dự phòng |
| `camel-tools` | Tiện ích chuyển tự tiếng Ả Rập | Có trong `requirements.txt`, dùng ở chế độ generalized burner |

## Hạn chế đã biết

- Xử lý tốn CPU (không có tăng tốc GPU)
- Chọn font tự động (khả năng điều khiển thủ công còn hạn chế)
- Phân bổ furigana cho từ phức tạp có thể chưa hoàn hảo
- Chưa hỗ trợ bố cục văn bản dọc
- Chỉ hỗ trợ một dòng phụ đề (chưa hỗ trợ nhiều dòng)

## Lộ trình

- Cải thiện căn chỉnh/phân bổ furigana cho các từ đa-kanji phức tạp
- Mở rộng tùy chọn dựng phụ đề nhiều dòng
- Bổ sung profile runtime rõ ràng hơn giữa classic/standalone/complete/generalized burners
- Tùy chọn thêm tự động hóa đóng gói/kiểm thử (`pyproject.toml`, CI smoke checks)

## Sự hỗ trợ của bạn giúp thực hiện điều gì

- <b>Duy trì công cụ mở</b>: hosting, suy luận, lưu trữ dữ liệu và vận hành cộng đồng.
- <b>Ra mắt nhanh hơn</b>: nhiều tuần tập trung mã nguồn mở cho EchoMind, LazyEdit và MultilingualWhisper.
- <b>Thử nghiệm thiết bị đeo</b>: quang học, cảm biến và thành phần neuromorphic/edge cho IdeasGlass + LightMind.
- <b>Tiếp cận cho mọi người</b>: triển khai trợ cấp cho sinh viên, nhà sáng tạo và các nhóm cộng đồng.

### Ủng hộ

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

## Đóng góp

Bạn có thể cải thiện thuật toán tạo furigana, bổ sung hỗ trợ cho nhiều kiểu bố cục văn bản hơn, hoặc tối ưu pipeline xử lý video.

Nếu gửi thay đổi, vui lòng kèm:

- Mô tả ngắn về tác động đối với người dùng
- Lệnh tái hiện/test bạn đã chạy cục bộ
- Ghi chú về giả định font và ngôn ngữ nếu thay đổi của bạn ảnh hưởng việc render

## Giấy phép

Hiện chưa có tệp giấy phép trong kho này.

Giả định cho bản nháp này: mọi quyền và điều khoản sử dụng hiện chưa được chỉ định cho đến khi maintainer thêm tệp `LICENSE`.
