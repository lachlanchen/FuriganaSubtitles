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

أداة Python لحرق ترجمات يابانية مع الفوريغانا مباشرة داخل الفيديو بدون ffmpeg.

## الميزات

- 🎌 **توليد فوريغانا تلقائي**: باستخدام MeCab (fugashi) أو pykakasi
- 🎨 **رسم نص متقن**: محاذاة ومسافات دقيقة
- 📺 **معالجة مباشرة للفيديو**: عبر OpenCV إطارًا بإطار
- 🔤 **اختيار خطوط تلقائي**: يبحث عن خطوط يابانية
- ⚡ **معالجة دفعات**: عدة فيديوهات دفعة واحدة
- 🎯 **تحكم بالموقع**: ضبط المكان والهوامش

## التثبيت

```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

أو يدويًا:
```bash
pip install opencv-python Pillow numpy fugashi unidic pykakasi
python -c "import unidic; unidic.download()"
```

## الاستخدام

```bash
python test_furigana.py
python process_furigana_videos.py
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

## مثال
```
   きょう   そら    は
   今日  は 空  が 晴れていて
```

## التخصيص

- `--main-font-size` حجم النص الرئيسي
- `--furigana-font-size` حجم الفوريغانا
- `--position` الموقع
- `--margin` الهوامش

## القيود

- معالجة CPU فقط
- خطوط تلقائية
- لا يدعم الكتابة العمودية
- سطر واحد فقط

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

نرحب بالمساهمات لتحسين توليد الفوريغانا والأداء.
