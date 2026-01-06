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

Công cụ Python để ghi phụ đề tiếng Nhật kèm furigana trực tiếp lên video mà không cần ffmpeg.

## Tính năng

- 🎌 **Tự động tạo furigana**: MeCab (fugashi) hoặc pykakasi
- 🎨 **Hiển thị đẹp**: căn chỉnh và khoảng cách tốt
- 📺 **Xử lý trực tiếp**: OpenCV theo từng khung hình
- 🔤 **Tự tìm font**: ưu tiên font tiếng Nhật
- ⚡ **Xử lý hàng loạt**: nhiều video cùng lúc
- 🎯 **Định vị chính xác**: tuỳ chỉnh vị trí/biên

## Cài đặt

### Nhanh
```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

### Thủ công
```bash
pip install opencv-python Pillow numpy fugashi unidic pykakasi
python -c "import unidic; unidic.download()"
```

## Cách dùng

### 1. Kiểm tra
```bash
python test_furigana.py
```

### 2. Xử lý thư mục hiện tại
```bash
python process_furigana_videos.py
```

### 3. Xử lý một video
```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. Tuỳ chọn nâng cao
```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

## Cách hoạt động

- Tạo furigana: MeCab → pykakasi → ký tự đơn
- Vẽ chữ: đo kích thước → căn giữa → thêm viền
- Xử lý video: đồng bộ thời gian SRT

## Ví dụ
```
   きょう   そら    は
   今日  は 空  が 晴れていて
```

## Cấu trúc đầu ra

```
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4
├── video_577285345205551192-yFQ1pMPA.srt
├── video_577285345205551192-yFQ1pMPA.json
├── video_577285345205551192-yFQ1pMPA.wav
└── video_577285345205551192-yFQ1pMPA_furigana.mp4
```

## Tuỳ chỉnh

- `--main-font-size` (mặc định 48)
- `--furigana-font-size` (mặc định 24)
- `--position`: top/bottom/center
- `--margin`: pixel biên

## Khắc phục sự cố

- Font Nhật: Hiragino / fonts-japanese-gothic / MS Gothic
- Lỗi furigana: kiểm tra fugashi/pykakasi
- Lỗi video: OpenCV đọc được, SRT UTF-8

## Hiệu năng

- 10–30 fps tuỳ độ phân giải
- Xử lý đơn luồng

## Phụ thuộc

- opencv-python
- Pillow
- numpy
- fugashi
- unidic
- pykakasi

## Hạn chế

- Không có GPU
- Font tự động
- Từ phức tạp có thể sai furigana
- Không hỗ trợ chữ dọc
- Chỉ 1 dòng phụ đề

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

Rất hoan nghênh đóng góp để cải thiện thuật toán furigana và hiệu năng.
