[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)


<p align="center">
  <img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/logos/banner.png" alt="LazyingArt banner" />
</p>

# أداة حرق الترجمات مع Furigana

<p align="center">
  <img src="../figures/demo.png" alt="Furigana subtitle demo" width="720" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/OpenCV-Video%20Burning-5C3EE8?logo=opencv&logoColor=white" alt="OpenCV" />
  <img src="https://img.shields.io/badge/Status-Active-2ea44f" alt="Status" />
  <img src="https://img.shields.io/badge/Primary%20Flow-SRT%20Pipeline-0ea5e9" alt="Primary Flow" />
  <img src="https://img.shields.io/badge/Extended%20Mode-JSON%20Ruby-f59e0b" alt="Extended Mode" />
</p>

أداة Python لحرق الترجمات تقوم بعرض Furigana اليابانية وتعليقات ruby الأخرى (مثل pinyin وromaji وIPA وغيرها) مباشرة على إطارات الفيديو باستخدام OpenCV. وهي محسّنة لسير عمل furigana مع الحفاظ على مرونة مناسبة للترجمات متعددة اللغات بأسلوب ruby.

مبنيّة لـ <a href="https://studio.lazying.art" target="_blank" rel="noreferrer">LazyEdit Studio</a> · <a href="https://github.com/lachlanchen/LazyEdit" target="_blank" rel="noreferrer">GitHub</a>

## جدول المحتويات

- [نظرة عامة](#نظرة-عامة)
- [الميزات](#الميزات)
- [هيكل المشروع](#هيكل-المشروع)
- [المتطلبات المسبقة](#المتطلبات-المسبقة)
- [التثبيت](#التثبيت)
- [الاستخدام](#الاستخدام)
- [الإعدادات](#الإعدادات)
- [أمثلة](#أمثلة)
- [آلية العمل](#آلية-العمل)
- [ملاحظات التطوير](#ملاحظات-التطوير)
- [استكشاف الأخطاء وإصلاحها](#استكشاف-الأخطاء-وإصلاحها)
- [الأداء](#الأداء)
- [الاعتماديات](#الاعتماديات)
- [القيود المعروفة](#القيود-المعروفة)
- [خارطة الطريق](#خارطة-الطريق)
- [ما الذي يتيحه دعمك](#ما-الذي-يتيحه-دعمك)
- [المساهمة](#المساهمة)
- [الترخيص](#الترخيص)

## نظرة عامة

يحتوي هذا المستودع على عدة مسارات لحرق الترجمات:

| المسار | السكربتات | الأنسب لـ |
|---|---|---|
| سير عمل furigana الكلاسيكي عبر SRT | `process_furigana_videos.py` + `furigana_subtitle_burner.py` | الاستخدام اليومي لحرق الترجمات بملفات SRT |
| سير العمل المستقل | `standalone_furigana_burner.py` | تنفيذ بسيط عبر سكربت واحد |
| سير العمل الكامل | `complete_furigana_burner.py` | حفظ/تحميل الإعدادات + وضع المعاينة |
| محرّك ruby المعمّم | `subtitles_burner/burner.py` | تعليقات متعددة اللغات على مستوى الرموز انطلاقًا من JSON |

يبقى مسار README الافتراضي هو خط أنابيب SRT، إلا إذا كنت تحتاج صراحةً إلى عرض متعدد الخانات قائم على JSON.

## الميزات

- 🎌 **توليد Furigana تلقائيًا**: يستخدم MeCab (fugashi) أو pykakasi لتوليد furigana لأحرف kanji
- 🌐 **دعم تعليقات Ruby**: عرض أدلة النطق لـ kanji وkana وأنظمة كتابة أخرى (pinyin وromaji وIPA)
- 🎨 **تصيير نص مخصص**: إخراج ruby جميل مع تباعد ومحاذاة وحدود (stroke) مناسبة
- 📺 **معالجة فيديو مباشرة**: حرق الترجمات مباشرة على إطارات الفيديو عبر OpenCV
- 🔤 **إدارة ذكية للخطوط**: العثور تلقائيًا على الخطوط المناسبة لنصوص CJK واللاتينية
- ⚡ **معالجة دفعية**: معالجة عدة فيديوهات دفعة واحدة
- 🎯 **تموضع دقيق**: إعداد موضع الترجمة والهوامش وسلوك التخطيط
- 🧩 **تشغيلات متعددة**: اختر بين وحدات الكلاسيكي أو المستقل أو الكامل أو المعمّم

## هيكل المشروع

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

## المتطلبات المسبقة

- يوصى باستخدام Python 3.9+
- نظام تشغيل يتضمن خطوطًا قادرة على عرض النص الياباني/‏CJK
- موارد CPU ومساحة قرص كافية لإخراج الفيديو إطارًا بإطار
- يُنصح بأن تكون ملفات الترجمة المُدخلة بترميز UTF-8

## التثبيت

### إعداد سريع

```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

يقوم سكربت الإعداد بتثبيت الحزم الأساسية، ويحاول تنزيل UniDic، ثم يشغّل `test_furigana.py`.

### التثبيت اليدوي

```bash
# Option A: install pinned repo requirements
pip install -r requirements.txt

# Option B: install explicit core packages (as documented in original README)
pip install opencv-python Pillow numpy fugashi unidic pykakasi

# Download Japanese dictionary data
python -c "import unidic; unidic.download()"
```

حزم اختيارية يستخدمها `subtitles_burner/burner.py` (مطلوبة فقط لبعض أوضاع التحويل الصوتي):

```bash
pip install phonemizer koroman pypinyin pycantonese
```

حزم اختيارية يستخدمها المساعد `openai_request.py`:

```bash
pip install openai pygame
```

## الاستخدام

### 1. اختبار النظام

```bash
python test_furigana.py
```

يختبر هذا توليد furigana وينشئ الملف `test_furigana_output.png`.

### 2. معالجة جميع الفيديوهات في المجلد الحالي

```bash
python process_furigana_videos.py
```

يعثر تلقائيًا على جميع مجلدات `video_*` ويعالج أول ملف `.MP4` و`.srt` في كل مجلد.

### 3. معالجة فيديو واحد

```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. استخدام متقدم (المحرّك الكلاسيكي)

```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

### 5. المحرّك المستقل (وضع الاكتشاف التلقائي)

```bash
python standalone_furigana_burner.py
```

عند تشغيله دون معاملات، يكتشف تلقائيًا ملفات `*.MP4`/`*.mp4` و`*.srt` في المجلد الحالي.

### 6. المحرّك الكامل (إعدادات + معاينة)

```bash
python complete_furigana_burner.py video.mp4 sub.srt out.mp4 --preview
python complete_furigana_burner.py video.mp4 sub.srt out.mp4 --save-config
python complete_furigana_burner.py --config furigana_config.json video.mp4 sub.srt out.mp4
```

### 7. محرّك JSON Ruby المعمّم

```bash
python subtitles_burner/burner.py input.mp4 subtitles.json output.mp4 \
  --text-key text \
  --ruby-key ruby \
  --slot 1 \
  --auto-ruby
```

## الإعدادات

### معاملات CLI (الكلاسيكي `furigana_subtitle_burner.py`)

| المعامل | الوصف | الافتراضي |
|---|---|---|
| `--main-font-size` | حجم النص الياباني الرئيسي | `48` |
| `--furigana-font-size` | حجم نص furigana | `24` |
| `--position` | `top` أو `bottom` أو `center` | `bottom` |
| `--margin` | المسافة عن الحافة بالبكسل | `50` |

### معاملات CLI (`standalone_furigana_burner.py`)

| المعامل | الوصف | الافتراضي |
|---|---|---|
| `--main-font-size` | حجم النص الرئيسي | `64` |
| `--furigana-font-size` | حجم furigana | `32` |
| `--position` | `top` أو `bottom` أو `center` | `bottom` |
| `--margin` | الهامش عن الحافة | `80` |

### معاملات CLI (`complete_furigana_burner.py`)

| المعامل | الوصف | الافتراضي |
|---|---|---|
| `--main-font-size` | حجم النص الرئيسي | `64` |
| `--furigana-font-size` | حجم furigana | `32` |
| `--position` | `top` أو `bottom` أو `center` | `bottom` |
| `--margin` | الهامش عن الحافة | `80` |
| `--preview` | وضع المعاينة (أول ~10 ثوانٍ) | Off |
| `--config <path>` | تحميل ملف إعدادات | `None` |
| `--save-config` | حفظ الإعدادات الحالية كافتراضية | Off |

### معاملات CLI (`subtitles_burner/burner.py`)

| المعامل | الوصف | الافتراضي |
|---|---|---|
| `--text-key` | مفتاح JSON للنص الأساسي | `text` |
| `--ruby-key` | مفتاح JSON لوسم ruby | `None` |
| `--slot` | معرّف الخانة في تخطيط الخانات السفلية | `1` |
| `--auto-ruby` | توليد ruby تلقائيًا لليابانية | Off |

### مظهر النص

- نص أبيض مع حد أسود لأعلى وضوح
- اختيار تلقائي للخط (يحاول استخدام خطوط يابانية من النظام)
- تباعد تناسبي بين الأحرف وfurigana

## أمثلة

### مثال على الناتج

للنص `今日は空が晴れていて`:

```text
   きょう   そら    は
   今日  は 空  が 晴れていて
```

### مثال لتخطيط الإدخال/الإخراج في المعالجة الدفعية

بعد المعالجة، سيصبح مجلدك بالشكل التالي:

```text
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4      # Original video
├── video_577285345205551192-yFQ1pMPA.srt      # Subtitle file
├── video_577285345205551192-yFQ1pMPA.json     # Whisper output
├── video_577285345205551192-yFQ1pMPA.wav      # Audio extraction
└── video_577285345205551192-yFQ1pMPA_furigana.mp4  # Output with furigana
```

## آلية العمل

### 1. توليد Furigana

يستخدم النظام عدة طرق لتوليد furigana:

- **الطريقة الأساسية**: MeCab مع fugashi لتحليل صرفي دقيق
- **البديل الاحتياطي**: pykakasi لتحويل أساسي من kanji إلى hiragana
- **الخيار الأخير**: تحليل حرف-بحرف

### 2. استراتيجية تصيير النص

- قياس كل حرف وfurigana الخاص به بشكل منفصل
- حساب عرض العمود الأنسب لكل حرف
- توسيط furigana فوق kanji المقابل
- إضافة حد للنص لتحسين الوضوح

### 3. معالجة الفيديو

- قراءة الفيديو إطارًا بإطار باستخدام OpenCV
- حساب توقيت الترجمة استنادًا إلى طوابع SRT الزمنية
- تصيير نص furigana كصورة RGBA
- مزج الترجمة مع إطار الفيديو عبر Alpha-blending
- كتابة الإطار المعالج إلى فيديو الإخراج

## ملاحظات التطوير

- يتضمن المستودع عدة محرّكات متداخلة عن قصد؛ ومسار SRT هو الأبسط للاستخدام اليومي.
- `legacy/` و`legacy-results/` أرشيفيان ومفيديان لمقارنات الانحدار (regression).
- لا توجد حاليًا بيانات حزم (`pyproject.toml` / `setup.py`).
- تغطية الاختبارات معتمدة على السكربتات (`test_furigana.py` و`simple_test.py` و`font_test.py`) بدل إطار اختبارات رسمي.
- `openai_request.py` أداة مساعدة إضافية وليست مطلوبة لحرق الترجمات الأساسي.

## استكشاف الأخطاء وإصلاحها

### لم يتم العثور على خطوط يابانية

يحاول النظام إيجاد خطوط يابانية تلقائيًا:

- **macOS**: Hiragino Sans
- **Linux**: `fonts-japanese-gothic`
- **Windows**: MS Gothic

قم بتثبيت خطوط يابانية إذا ظهرت الترجمات بخط افتراضي.

أدوات مساعدة إضافية:

```bash
python font_test.py
python fix_font_squares.py
```

### لا يتم توليد Furigana

1. تحقّق من تثبيت fugashi/unidic: `python -c "import fugashi; print('OK')"`
2. استخدم مسار fallback عبر pykakasi: `python -c "import pykakasi; print('OK')"`
3. افحص ناتج الاختبار: `python test_furigana.py`
4. شغّل تشخيص الاعتماديات: `python fix_unidic.py` و`python debug_japanese.py`

### أخطاء معالجة الفيديو

- تأكد أن OpenCV قادر على قراءة فيديو الإدخال
- تحقق من توفر مساحة قرص كافية لملف الإخراج
- تحقّق من أن ترميز ملف SRT هو UTF-8
- جرّب `complete_furigana_burner.py --preview ...` للتحقق السريع من خط الأنابيب

## الأداء

- تعتمد سرعة المعالجة على دقة الفيديو وطوله
- السرعات النموذجية: معدل معالجة 10-30 fps
- يزداد استهلاك الذاكرة بارتفاع دقة الفيديو
- المعالجة أحادية الخيط (يمكن موازاتها)

## الاعتماديات

| الحزمة | الدور | ملاحظات |
|---|---|---|
| `opencv-python` | معالجة الفيديو | اعتماد أساسي |
| `Pillow` | تصيير الصور ورسم النص | اعتماد أساسي |
| `numpy` | عمليات المصفوفات | اعتماد أساسي |
| `fugashi` | التحليل الصرفي الياباني | اختياري لكن موصى به |
| `unidic` | بيانات القاموس الياباني | اختياري لكن موصى به |
| `pykakasi` | تحويل kanji إلى hiragana | مسار احتياطي |
| `camel-tools` | أدوات مساعدة للنقل الصوتي العربي | موجودة في `requirements.txt` وتُستخدم في وضع المحرّك المعمّم |

## القيود المعروفة

- المعالجة كثيفة على CPU (لا يوجد تسريع GPU)
- اختيار الخطوط تلقائي (تحكم يدوي محدود)
- توزيع furigana للكلمات المعقدة قد لا يكون مثاليًا
- لا يوجد دعم لتخطيط النص العمودي
- سطر ترجمة واحد فقط (لا يوجد دعم متعدد الأسطر بعد)

## خارطة الطريق

- تحسين محاذاة/توزيع furigana للكلمات المعقدة متعددة kanji
- توسيع خيارات تركيب الترجمات متعددة الأسطر
- إضافة ملفات تعريف تشغيل أوضح بين المحرّكات: الكلاسيكي/المستقل/الكامل/المعمّم
- إضافة تغليف/أتمتة اختبارات اختياريًا (`pyproject.toml`، وفحوصات CI أساسية)

## ما الذي يتيحه دعمك

- <b>إبقاء الأدوات مفتوحة</b>: الاستضافة، والاستدلال، وتخزين البيانات، وعمليات المجتمع.
- <b>تسريع الإطلاق</b>: أسابيع من وقت المصدر المفتوح المركّز على EchoMind وLazyEdit وMultilingualWhisper.
- <b>نمذجة الأجهزة القابلة للارتداء</b>: البصريات، والمستشعرات، ومكوّنات neuromorphic/edge لمشاريع IdeasGlass + LightMind.
- <b>إتاحة الوصول للجميع</b>: نشرات مدعومة للطلاب والمبدعين ومجموعات المجتمع.

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

## المساهمة

يمكنك تحسين خوارزمية توليد furigana، أو إضافة دعم لمزيد من تخطيطات النص، أو تحسين أداء خط أنابيب معالجة الفيديو.

إذا أرسلت تغييرات، أضف ما يلي:

- شرحًا مختصرًا للتأثير على المستخدم
- أوامر إعادة الإنتاج/الاختبار التي شغّلتها محليًا
- ملاحظات عن افتراضات الخطوط واللغات إذا كان التغيير يؤثر على التصيير

## الترخيص

لا يوجد حاليًا ملف ترخيص في هذا المستودع.

الافتراض في هذه المسودة: جميع الحقوق وشروط الاستخدام غير محددة حاليًا إلى أن يضيف المشرف ملف `LICENSE`.
