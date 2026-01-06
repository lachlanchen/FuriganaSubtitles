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

这是一个 Python 工具，可在不使用 ffmpeg 的情况下，把日文假名注音直接烧录到视频里。

## 功能特色

- 🎌 **自动注音生成**：使用 MeCab (fugashi) 或 pykakasi 生成汉字假名
- 🎨 **自定义文本渲染**：正确的对齐与间距
- 📺 **直接视频处理**：OpenCV 逐帧处理
- 🔤 **智能字体选择**：自动查找日文字体
- ⚡ **批量处理**：一次处理多部视频
- 🎯 **精准定位**：可配置字幕位置与边距

## 安装

### 快速安装
```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

### 手动安装
```bash
pip install opencv-python Pillow numpy fugashi unidic pykakasi
python -c "import unidic; unidic.download()"
```

## 使用方式

### 1. 测试系统
```bash
python test_furigana.py
```
会生成示例图片，便于检查注音效果。

### 2. 批量处理当前目录
```bash
python process_furigana_videos.py
```

### 3. 处理单个视频
```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. 高级用法
```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

## 工作原理

### 1. 假名生成
- **主要**：MeCab + fugashi
- **备用**：pykakasi
- **兜底**：逐字处理

### 2. 文本渲染
- 测量字与注音尺寸
- 计算列宽
- 将假名居中于对应汉字上方
- 添加描边提升可读性

### 3. 视频处理
- OpenCV 逐帧读取
- 根据 SRT 时间戳显示
- 生成 RGBA 文字层
- Alpha 混合到视频帧

## 示例输出

文本「今日は空が晴れていて」：
```
   きょう   そら    は
   今日  は 空  が 晴れていて
```

## 文件结构

```
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4
├── video_577285345205551192-yFQ1pMPA.srt
├── video_577285345205551192-yFQ1pMPA.json
├── video_577285345205551192-yFQ1pMPA.wav
└── video_577285345205551192-yFQ1pMPA_furigana.mp4
```

## 可配置项

- `--main-font-size`：主文本大小（默认 48）
- `--furigana-font-size`：假名大小（默认 24）
- `--position`：`top`、`bottom`、`center`
- `--margin`：边距像素

## 故障排查

### 找不到日文字体
- macOS：Hiragino Sans
- Linux：fonts-japanese-gothic
- Windows：MS Gothic

### 无法生成假名
1. `python -c "import fugashi; print('OK')"`
2. `python -c "import pykakasi; print('OK')"`
3. `python test_furigana.py`

### 视频处理错误
- 确保视频可被 OpenCV 读取
- 确保磁盘空间充足
- 确认 SRT 编码为 UTF-8

## 性能

- 速度取决于分辨率和时长
- 常见处理速度 10–30 fps
- 内存随分辨率增大
- 单线程处理

## 依赖

- opencv-python
- Pillow
- numpy
- fugashi（推荐）
- unidic（推荐）
- pykakasi（备用）

## 已知限制

- CPU 密集（无 GPU 加速）
- 字体选择自动化
- 复杂词汇注音可能不完美
- 不支持竖排
- 单行字幕（不支持多行）

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

欢迎改进注音算法、增加排版样式或优化处理流程。
