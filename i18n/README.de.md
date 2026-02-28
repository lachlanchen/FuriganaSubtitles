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

Ein Python-Subtitle-Burner, der japanisches Furigana und andere Ruby-Anmerkungen (Pinyin, Romaji, IPA usw.) mit OpenCV direkt in Videoframes rendert. Er ist fuer Furigana-Workflows optimiert und bleibt gleichzeitig flexibel fuer mehrsprachige Ruby-Subtitle-Szenarien.

Entwickelt fuer <a href="https://studio.lazying.art" target="_blank" rel="noreferrer">LazyEdit Studio</a> · <a href="https://github.com/lachlanchen/LazyEdit" target="_blank" rel="noreferrer">GitHub</a>

## Inhaltsverzeichnis

- [Ueberblick](#ueberblick)
- [Funktionen](#funktionen)
- [Projektstruktur](#projektstruktur)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Verwendung](#verwendung)
- [Konfiguration](#konfiguration)
- [Beispiele](#beispiele)
- [So funktioniert es](#so-funktioniert-es)
- [Entwicklungshinweise](#entwicklungshinweise)
- [Fehlerbehebung](#fehlerbehebung)
- [Leistung](#leistung)
- [Abhaengigkeiten](#abhaengigkeiten)
- [Bekannte Einschraenkungen](#bekannte-einschraenkungen)
- [Roadmap](#roadmap)
- [Was deine Unterstuetzung ermoeglicht](#was-deine-unterstuetzung-ermoeglicht)
- [Mitwirken](#mitwirken)
- [Lizenz](#lizenz)

## Ueberblick

Dieses Repository enthaelt mehrere Wege zum Einbrennen von Untertiteln:

| Path | Scripts | Best For |
|---|---|---|
| Klassischer SRT-Furigana-Workflow | `process_furigana_videos.py` + `furigana_subtitle_burner.py` | Alltaegliches Einbrennen mit SRT-Dateien |
| Standalone-Workflow | `standalone_furigana_burner.py` | Einfache Ausfuehrung mit nur einem Skript |
| Vollstaendiger Workflow | `complete_furigana_burner.py` | Konfiguration speichern/laden + Vorschau-Modus |
| Generalisierte Ruby-Engine | `subtitles_burner/burner.py` | JSON-gesteuerte, mehrsprachige Annotation auf Token-Ebene |

Der Standardablauf in dieser README bleibt die SRT-basierte Pipeline, sofern du nicht explizit JSON-basiertes Multi-Slot-Rendering benoetigst.

## Funktionen

- 🎌 **Automatische Furigana-Generierung**: Verwendet MeCab (fugashi) oder pykakasi, um Furigana fuer Kanji zu erzeugen
- 🌐 **Unterstuetzung fuer Ruby-Anmerkungen**: Rendert Aussprachehilfen fuer Kanji, Kana und andere Schriftsysteme (Pinyin, Romaji, IPA)
- 🎨 **Anpassbares Text-Rendering**: Rendert gut lesbaren Ruby-Text mit korrektem Abstand, Ausrichtung und Kontur
- 📺 **Direkte Videoverarbeitung**: Brennt Untertitel mit OpenCV direkt in Videoframes ein
- 🔤 **Intelligente Font-Behandlung**: Findet und verwendet automatisch Fonts fuer CJK- und lateinische Schriften
- ⚡ **Batch-Verarbeitung**: Verarbeitet mehrere Videos auf einmal
- 🎯 **Praezise Positionierung**: Konfigurierbare Untertitelposition, Raender und Layout-Verhalten
- 🧩 **Mehrere Laufzeitvarianten**: Wahl zwischen klassischen, standalone, complete oder generalisierten Burner-Modulen

## Projektstruktur

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

## Voraussetzungen

- Python 3.9+ empfohlen
- Betriebssystem mit Fonts, die japanischen/CJK-Text darstellen koennen
- Ausreichend CPU und Speicherplatz fuer framebasierte Videoausgabe
- Eingabe-Untertiteldateien idealerweise in UTF-8 codiert

## Installation

### Schnellstart

```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

Das Setup-Skript installiert Kernpakete, versucht UniDic herunterzuladen und fuehrt `test_furigana.py` aus.

### Manuelle Installation

```bash
# Option A: festgelegte Repo-Abhaengigkeiten installieren
pip install -r requirements.txt

# Option B: explizite Kernpakete installieren (wie in der urspruenglichen README dokumentiert)
pip install opencv-python Pillow numpy fugashi unidic pykakasi

# Japanische Woerterbuchdaten herunterladen
python -c "import unidic; unidic.download()"
```

Optionale Pakete fuer `subtitles_burner/burner.py` (nur fuer bestimmte Transliterationsmodi erforderlich):

```bash
pip install phonemizer koroman pypinyin pycantonese
```

Optionale Pakete fuer das Hilfsskript `openai_request.py`:

```bash
pip install openai pygame
```

## Verwendung

### 1. System testen

```bash
python test_furigana.py
```

Dies testet die Furigana-Generierung und erstellt `test_furigana_output.png`.

### 2. Alle Videos im aktuellen Verzeichnis verarbeiten

```bash
python process_furigana_videos.py
```

Findet automatisch alle `video_*`-Verzeichnisse und verarbeitet jeweils die erste `.MP4`- und `.srt`-Datei.

### 3. Ein einzelnes Video verarbeiten

```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. Erweiterte Verwendung (Classic Burner)

```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

### 5. Standalone Burner (Auto-detect Mode)

```bash
python standalone_furigana_burner.py
```

Ohne Argumente erkennt das Skript im aktuellen Verzeichnis automatisch `*.MP4`/`*.mp4` und `*.srt`.

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

## Konfiguration

### CLI-Parameter (Classic `furigana_subtitle_burner.py`)

| Parameter | Beschreibung | Standard |
|---|---|---|
| `--main-font-size` | Groesse des japanischen Haupttexts | `48` |
| `--furigana-font-size` | Groesse des Furigana-Texts | `24` |
| `--position` | `top`, `bottom` oder `center` | `bottom` |
| `--margin` | Abstand vom Rand in Pixeln | `50` |

### CLI-Parameter (`standalone_furigana_burner.py`)

| Parameter | Beschreibung | Standard |
|---|---|---|
| `--main-font-size` | Groesse des Haupttexts | `64` |
| `--furigana-font-size` | Groesse des Furigana-Texts | `32` |
| `--position` | `top`, `bottom` oder `center` | `bottom` |
| `--margin` | Abstand vom Rand | `80` |

### CLI-Parameter (`complete_furigana_burner.py`)

| Parameter | Beschreibung | Standard |
|---|---|---|
| `--main-font-size` | Groesse des Haupttexts | `64` |
| `--furigana-font-size` | Groesse des Furigana-Texts | `32` |
| `--position` | `top`, `bottom` oder `center` | `bottom` |
| `--margin` | Abstand vom Rand | `80` |
| `--preview` | Vorschau-Modus (erste ~10 Sekunden) | Off |
| `--config <path>` | Konfigurationsdatei laden | `None` |
| `--save-config` | Aktuelle Konfiguration als Standard speichern | Off |

### CLI-Parameter (`subtitles_burner/burner.py`)

| Parameter | Beschreibung | Standard |
|---|---|---|
| `--text-key` | JSON-Key fuer den Basetext | `text` |
| `--ruby-key` | JSON-Key fuer Ruby-Markup | `None` |
| `--slot` | Slot-ID im unteren Slot-Layout | `1` |
| `--auto-ruby` | Ruby fuer Japanisch automatisch erzeugen | Off |

### Textdarstellung

- Weisser Text mit schwarzer Kontur fuer maximale Sichtbarkeit
- Automatische Font-Auswahl (versucht japanische Systemfonts)
- Proportionale Abstaende zwischen Zeichen und Furigana

## Beispiele

### Beispielausgabe

Fuer den Text `今日は空が晴れていて`:

```text
   きょう   そら    は
   今日  は 空  が 晴れていて
```

### Beispiel fuer Batch-Eingabe/-Ausgabe-Struktur

Nach der Verarbeitung sieht dein Verzeichnis so aus:

```text
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4      # Originalvideo
├── video_577285345205551192-yFQ1pMPA.srt      # Untertiteldatei
├── video_577285345205551192-yFQ1pMPA.json     # Whisper-Ausgabe
├── video_577285345205551192-yFQ1pMPA.wav      # Audio-Extraktion
└── video_577285345205551192-yFQ1pMPA_furigana.mp4  # Ausgabe mit Furigana
```

## So funktioniert es

### 1. Furigana-Generierung

Das System nutzt mehrere Methoden zur Furigana-Generierung:

- **Primaer**: MeCab mit fugashi fuer genaue morphologische Analyse
- **Fallback**: pykakasi fuer einfache Kanji-zu-Hiragana-Konvertierung
- **Letzte Option**: Zeichen-fuer-Zeichen-Analyse

### 2. Strategie fuer Text-Rendering

- Misst jedes Zeichen und sein Furigana separat
- Berechnet die optimale Spaltenbreite fuer jedes Zeichen
- Zentriert Furigana ueber dem zugehoerigen Kanji
- Fuegt eine Textkontur fuer bessere Lesbarkeit hinzu

### 3. Videoverarbeitung

- Liest Video Frame fuer Frame mit OpenCV
- Berechnet Untertitel-Timing anhand von SRT-Zeitstempeln
- Rendert Furigana-Text als RGBA-Bild
- Blendet Untertitel per Alpha-Blending auf den Videoframe
- Schreibt den verarbeiteten Frame in das Ausgabevideo

## Entwicklungshinweise

- Das Repository hat absichtlich ueberlappende Burner-Varianten; die SRT-Pipeline ist fuer den Alltag am einfachsten.
- `legacy/` und `legacy-results/` sind Archivbereiche und nuetzlich fuer Regressionsvergleiche.
- Aktuell gibt es keine Packaging-Metadaten (`pyproject.toml` / `setup.py`).
- Testabdeckung ist skriptbasiert (`test_furigana.py`, `simple_test.py`, `font_test.py`) statt eines formalen Test-Frameworks.
- `openai_request.py` ist ein zusaetzliches Utility und fuer das Kern-Subtitle-Burning nicht erforderlich.

## Fehlerbehebung

### Keine japanischen Fonts gefunden

Das System versucht automatisch, japanische Fonts zu finden:

- **macOS**: Hiragino Sans
- **Linux**: `fonts-japanese-gothic`
- **Windows**: MS Gothic

Installiere japanische Fonts, wenn Untertitel in einer Standardschrift erscheinen.

Zusaetzliche Helfer:

```bash
python font_test.py
python fix_font_squares.py
```

### Furigana wird nicht erzeugt

1. Pruefe, ob fugashi/unidic installiert ist: `python -c "import fugashi; print('OK')"`
2. Fallback auf pykakasi: `python -c "import pykakasi; print('OK')"`
3. Testausgabe pruefen: `python test_furigana.py`
4. Abhaengigkeitsdiagnose ausfuehren: `python fix_unidic.py` und `python debug_japanese.py`

### Fehler bei der Videoverarbeitung

- Stelle sicher, dass das Eingabevideo von OpenCV gelesen werden kann
- Pruefe verfuegbaren Speicherplatz fuer die Ausgabedatei
- Verifiziere, dass die SRT-Datei UTF-8 codiert ist
- Nutze `complete_furigana_burner.py --preview ...`, um die Pipeline schnell zu validieren

## Leistung

- Verarbeitungsgeschwindigkeit haengt von Videoaufloesung und Laenge ab
- Typische Geschwindigkeiten: 10-30 fps Verarbeitungsrate
- Speicherverbrauch skaliert mit der Videoaufloesung
- Nutzt Single-Thread-Verarbeitung (kann parallelisiert werden)

## Abhaengigkeiten

| Package | Rolle | Hinweise |
|---|---|---|
| `opencv-python` | Videoverarbeitung | Kernabhaengigkeit |
| `Pillow` | Bild-Rendering und Textzeichnung | Kernabhaengigkeit |
| `numpy` | Array-Operationen | Kernabhaengigkeit |
| `fugashi` | Japanische morphologische Analyse | Optional, aber empfohlen |
| `unidic` | Japanische Woerterbuchdaten | Optional, aber empfohlen |
| `pykakasi` | Kanji-zu-Hiragana-Konvertierung | Fallback-Pfad |
| `camel-tools` | Arabische Transliterations-Helfer | In `requirements.txt` enthalten, genutzt im generalisierten Burner-Modus |

## Bekannte Einschraenkungen

- Verarbeitung ist CPU-intensiv (keine GPU-Beschleunigung)
- Font-Auswahl erfolgt automatisch (begrenzte manuelle Kontrolle)
- Furigana-Verteilung bei komplexen Woertern ist ggf. nicht perfekt
- Keine Unterstuetzung fuer vertikales Textlayout
- Nur eine Untertitelzeile (noch keine Multi-Line-Unterstuetzung)

## Roadmap

- Furigana-Ausrichtung/-Verteilung fuer komplexe Multi-Kanji-Woerter verbessern
- Optionen fuer Multi-Line-Untertitel-Komposition erweitern
- Klarere Laufzeitprofile zwischen classic/standalone/complete/generalized Burnern hinzufuegen
- Optional Packaging/Test-Automatisierung ergaenzen (`pyproject.toml`, CI-Smoke-Checks)

## Was deine Unterstuetzung ermoeglicht

- <b>Tools offen halten</b>: Hosting, Inferenz, Datenspeicherung und Community-Betrieb.
- <b>Schneller liefern</b>: Wochen fokussierter Open-Source-Zeit fuer EchoMind, LazyEdit und MultilingualWhisper.
- <b>Wearables prototypen</b>: Optik, Sensoren und neuromorphe/Edge-Komponenten fuer IdeasGlass + LightMind.
- <b>Zugang fuer alle</b>: Subventionierte Deployments fuer Studierende, Creators und Community-Gruppen.

### Spenden

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

## Mitwirken

Verbesserungen am Furigana-Generierungsalgorithmus, Support fuer weitere Textlayouts oder Optimierungen an der Video-Pipeline sind willkommen.

Wenn du Aenderungen einreichst, fuege bitte hinzu:

- Eine kurze Erklaerung zum sichtbaren Nutzen fuer Anwender
- Reproduktions-/Testbefehle, die du lokal ausgefuehrt hast
- Hinweise zu Font- und Sprachannahmen, falls dein Change das Rendering beeinflusst

## Lizenz

In diesem Repository ist derzeit keine Lizenzdatei vorhanden.

Annahme fuer diesen Entwurf: Alle Rechte und Nutzungsbedingungen sind aktuell nicht spezifiziert, bis der Maintainer eine `LICENSE`-Datei hinzufuegt.
