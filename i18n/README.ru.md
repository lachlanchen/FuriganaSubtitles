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

Python-инструмент для встраивания субтитров, который рендерит японскую фуригану и другие ruby-аннотации (pinyin, romaji, IPA и т.д.) прямо на кадры видео с помощью OpenCV. Проект оптимизирован под сценарии с фуриганой, но при этом остается гибким для многоязычных субтитров в ruby-стиле.

Создано для <a href="https://studio.lazying.art" target="_blank" rel="noreferrer">LazyEdit Studio</a> · <a href="https://github.com/lachlanchen/LazyEdit" target="_blank" rel="noreferrer">GitHub</a>

## Содержание

- [Обзор](#обзор)
- [Возможности](#возможности)
- [Структура проекта](#структура-проекта)
- [Требования](#требования)
- [Установка](#установка)
- [Использование](#использование)
- [Конфигурация](#конфигурация)
- [Примеры](#примеры)
- [Как это работает](#как-это-работает)
- [Примечания по разработке](#примечания-по-разработке)
- [Устранение неполадок](#устранение-неполадок)
- [Производительность](#производительность)
- [Зависимости](#зависимости)
- [Известные ограничения](#известные-ограничения)
- [Планы развития](#планы-развития)
- [Что делает возможной ваша поддержка](#что-делает-возможной-ваша-поддержка)
- [Вклад в проект](#вклад-в-проект)
- [Лицензия](#лицензия)

## Обзор

В этом репозитории есть несколько путей встраивания субтитров:

| Path | Scripts | Best For |
|---|---|---|
| Classic SRT furigana workflow | `process_furigana_videos.py` + `furigana_subtitle_burner.py` | Day-to-day subtitle burning with SRT files |
| Standalone workflow | `standalone_furigana_burner.py` | Simple single-script execution |
| Complete workflow | `complete_furigana_burner.py` | Config save/load + preview mode |
| Generalized ruby engine | `subtitles_burner/burner.py` | JSON-driven multilingual token-level annotation |

По умолчанию README описывает SRT-ориентированный pipeline, если вам явно не нужен JSON-режим с рендерингом нескольких слотов.

## Возможности

- 🎌 **Автоматическая генерация фуриганы**: использует MeCab (fugashi) или pykakasi для генерации фуриганы для кандзи
- 🌐 **Поддержка ruby-аннотаций**: рендер руководств по произношению для кандзи, каны и других систем письма (pinyin, romaji, IPA)
- 🎨 **Гибкий рендер текста**: аккуратный ruby-текст с корректными интервалами, выравниванием и обводкой
- 📺 **Прямая обработка видео**: встраивание субтитров напрямую в видеокадры через OpenCV
- 🔤 **Умная работа со шрифтами**: автоматический поиск и выбор шрифтов для CJK и латиницы
- ⚡ **Пакетная обработка**: обработка нескольких видео за один запуск
- 🎯 **Точное позиционирование**: настраиваемая позиция субтитров, отступы и поведение макета
- 🧩 **Несколько runtime-вариантов**: классический, standalone, complete или generalized модули

## Структура проекта

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

## Требования

- Рекомендуется Python 3.9+
- ОС со шрифтами, которые умеют отображать японский/CJK-текст
- Достаточно CPU и места на диске для покадрового вывода видео
- Входные файлы субтитров в кодировке UTF-8 (рекомендуется)

## Установка

### Быстрая настройка

```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

Скрипт установки ставит основные пакеты, пытается загрузить UniDic и запускает `test_furigana.py`.

### Ручная установка

```bash
# Option A: install pinned repo requirements
pip install -r requirements.txt

# Option B: install explicit core packages (as documented in original README)
pip install opencv-python Pillow numpy fugashi unidic pykakasi

# Download Japanese dictionary data
python -c "import unidic; unidic.download()"
```

Дополнительные пакеты для `subtitles_burner/burner.py` (нужны только для отдельных режимов транслитерации):

```bash
pip install phonemizer koroman pypinyin pycantonese
```

Дополнительные пакеты для вспомогательного `openai_request.py`:

```bash
pip install openai pygame
```

## Использование

### 1. Проверка системы

```bash
python test_furigana.py
```

Проверяет генерацию фуриганы и создает `test_furigana_output.png`.

### 2. Обработать все видео в текущей директории

```bash
python process_furigana_videos.py
```

Автоматически находит все директории `video_*` и обрабатывает первый `.MP4` и `.srt` в каждой.

### 3. Обработать одно видео

```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. Расширенное использование (Classic Burner)

```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

### 5. Standalone Burner (режим автоопределения)

```bash
python standalone_furigana_burner.py
```

Если запустить без аргументов, скрипт автоматически ищет `*.MP4`/`*.mp4` и `*.srt` в текущей директории.

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

## Конфигурация

### CLI-параметры (Classic `furigana_subtitle_burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--main-font-size` | Size of main Japanese text | `48` |
| `--furigana-font-size` | Size of furigana text | `24` |
| `--position` | `top`, `bottom`, or `center` | `bottom` |
| `--margin` | Distance from edge in pixels | `50` |

### CLI-параметры (`standalone_furigana_burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--main-font-size` | Main text size | `64` |
| `--furigana-font-size` | Furigana text size | `32` |
| `--position` | `top`, `bottom`, or `center` | `bottom` |
| `--margin` | Margin from edge | `80` |

### CLI-параметры (`complete_furigana_burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--main-font-size` | Main text size | `64` |
| `--furigana-font-size` | Furigana text size | `32` |
| `--position` | `top`, `bottom`, or `center` | `bottom` |
| `--margin` | Margin from edge | `80` |
| `--preview` | Preview mode (first ~10 seconds) | Off |
| `--config <path>` | Load configuration file | `None` |
| `--save-config` | Save current config as default | Off |

### CLI-параметры (`subtitles_burner/burner.py`)

| Parameter | Description | Default |
|---|---|---|
| `--text-key` | JSON key for base text | `text` |
| `--ruby-key` | JSON key for ruby markup | `None` |
| `--slot` | Slot ID in bottom slot layout | `1` |
| `--auto-ruby` | Auto-generate ruby for Japanese | Off |

### Внешний вид текста

- Белый текст с черной обводкой для максимальной читаемости
- Автоматический выбор шрифта (пытается использовать системные японские шрифты)
- Пропорциональные интервалы между символами и фуриганой

## Примеры

### Пример вывода

Для текста `今日は空が晴れていて`:

```text
   きょう   そら    は
   今日  は 空  が 晴れていて
```

### Пример структуры batch input/output

После обработки директория будет выглядеть так:

```text
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4      # Original video
├── video_577285345205551192-yFQ1pMPA.srt      # Subtitle file
├── video_577285345205551192-yFQ1pMPA.json     # Whisper output
├── video_577285345205551192-yFQ1pMPA.wav      # Audio extraction
└── video_577285345205551192-yFQ1pMPA_furigana.mp4  # Output with furigana
```

## Как это работает

### 1. Генерация фуриганы

Система использует несколько методов генерации фуриганы:

- **Primary**: MeCab с fugashi для точного морфологического анализа
- **Fallback**: pykakasi для базового преобразования кандзи в хирагану
- **Last Resort**: посимвольный анализ

### 2. Стратегия рендера текста

- Измеряет каждый символ и его фуригану отдельно
- Вычисляет оптимальную ширину столбца для каждого символа
- Центрирует фуригану над соответствующим кандзи
- Добавляет обводку текста для лучшей читаемости

### 3. Обработка видео

- Читает видео покадрово с помощью OpenCV
- Рассчитывает тайминг субтитров по временным меткам SRT
- Рендерит текст с фуриганой как RGBA-изображение
- Накладывает субтитры на видеокадр через alpha-blending
- Записывает обработанный кадр в выходное видео

## Примечания по разработке

- В репозитории специально есть несколько перекрывающихся вариантов burner; для повседневной работы проще всего SRT-pipeline.
- `legacy/` и `legacy-results/` архивные, но полезны для регрессионных сравнений.
- Сейчас отсутствуют метаданные packaging (`pyproject.toml` / `setup.py`).
- Тестирование построено на скриптах (`test_furigana.py`, `simple_test.py`, `font_test.py`), а не на формальном test framework.
- `openai_request.py` это вспомогательная утилита и для основного встраивания субтитров не требуется.

## Устранение неполадок

### Не найдены японские шрифты

Система пытается автоматически найти японские шрифты:

- **macOS**: Hiragino Sans
- **Linux**: `fonts-japanese-gothic`
- **Windows**: MS Gothic

Установите японские шрифты, если субтитры отображаются стандартным шрифтом.

Дополнительные утилиты:

```bash
python font_test.py
python fix_font_squares.py
```

### Фуригана не генерируется

1. Проверьте, что fugashi/unidic установлены: `python -c "import fugashi; print('OK')"`
2. Используйте fallback через pykakasi: `python -c "import pykakasi; print('OK')"`
3. Проверьте вывод теста: `python test_furigana.py`
4. Запустите диагностику зависимостей: `python fix_unidic.py` и `python debug_japanese.py`

### Ошибки обработки видео

- Убедитесь, что входное видео читается OpenCV
- Проверьте доступное место на диске для выходного файла
- Убедитесь, что SRT-файл в кодировке UTF-8
- Попробуйте `complete_furigana_burner.py --preview ...`, чтобы быстро проверить pipeline

## Производительность

- Скорость обработки зависит от разрешения и длины видео
- Типичные скорости: 10-30 fps
- Использование памяти масштабируется с разрешением видео
- Используется однопоточная обработка (можно распараллелить)

## Зависимости

| Package | Role | Notes |
|---|---|---|
| `opencv-python` | Video processing | Core dependency |
| `Pillow` | Image rendering and text drawing | Core dependency |
| `numpy` | Array operations | Core dependency |
| `fugashi` | Japanese morphological analysis | Optional but recommended |
| `unidic` | Japanese dictionary data | Optional but recommended |
| `pykakasi` | Kanji to hiragana conversion | Fallback path |
| `camel-tools` | Arabic transliteration helpers | Included in `requirements.txt`, used in generalized burner mode |

## Известные ограничения

- Обработка нагружает CPU (без GPU-ускорения)
- Выбор шрифта автоматический (ограниченный ручной контроль)
- Распределение фуриганы для сложных слов может быть неидеальным
- Нет поддержки вертикальной верстки текста
- Только одна строка субтитров (многострочный режим пока не поддерживается)

## Планы развития

- Улучшить выравнивание/распределение фуриганы для сложных многокандзийных слов
- Расширить возможности компоновки многострочных субтитров
- Добавить более четкие runtime-профили между classic/standalone/complete/generalized burners
- Опционально добавить автоматизацию packaging/тестирования (`pyproject.toml`, CI smoke checks)

## Что делает возможной ваша поддержка

- <b>Поддерживать инструменты открытыми</b>: хостинг, инференс, хранение данных и работа сообщества.
- <b>Быстрее выпускать обновления</b>: недели сфокусированной open-source работы над EchoMind, LazyEdit и MultilingualWhisper.
- <b>Прототипировать wearable-устройства</b>: оптика, сенсоры и neuromorphic/edge-компоненты для IdeasGlass + LightMind.
- <b>Доступ для всех</b>: субсидируемые внедрения для студентов, авторов и локальных сообществ.

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
- Ваша поддержка помогает мне продолжать исследования, разработку и операционную работу, чтобы делиться еще большим числом открытых проектов и улучшений.

## Вклад в проект

Можно улучшать алгоритм генерации фуриганы, добавлять поддержку новых текстовых макетов или оптимизировать pipeline обработки видео.

Если вы отправляете изменения, добавьте:

- Краткое описание пользовательского эффекта
- Команды воспроизведения/тестирования, которые вы запускали локально
- Примечания о шрифтах и языковых допущениях, если изменения влияют на рендер

## Лицензия

В репозитории сейчас отсутствует файл лицензии.

Допущение для этой версии README: все права и условия использования пока не определены до тех пор, пока мейнтейнер не добавит `LICENSE`.
