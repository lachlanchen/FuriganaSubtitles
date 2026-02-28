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

Un quemador de subtítulos en Python que renderiza furigana japonés y otras anotaciones ruby (pinyin, romaji, IPA, etc.) directamente sobre fotogramas de video con OpenCV. Está optimizado para flujos de trabajo con furigana y, al mismo tiempo, mantiene flexibilidad para subtítulos ruby multilingües.

Creado para <a href="https://studio.lazying.art" target="_blank" rel="noreferrer">LazyEdit Studio</a> · <a href="https://github.com/lachlanchen/LazyEdit" target="_blank" rel="noreferrer">GitHub</a>

## Tabla de contenidos

- [Resumen](#resumen)
- [Características](#características)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Configuración](#configuración)
- [Ejemplos](#ejemplos)
- [Cómo funciona](#cómo-funciona)
- [Notas de desarrollo](#notas-de-desarrollo)
- [Solución de problemas](#solución-de-problemas)
- [Rendimiento](#rendimiento)
- [Dependencias](#dependencias)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Hoja de ruta](#hoja-de-ruta)
- [Qué hace posible tu apoyo](#qué-hace-posible-tu-apoyo)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

## Resumen

Este repositorio contiene varias rutas para incrustar subtítulos:

| Ruta | Scripts | Mejor para |
|---|---|---|
| Flujo clásico SRT con furigana | `process_furigana_videos.py` + `furigana_subtitle_burner.py` | Incrustación de subtítulos diaria con archivos SRT |
| Flujo independiente | `standalone_furigana_burner.py` | Ejecución simple con un solo script |
| Flujo completo | `complete_furigana_burner.py` | Guardar/cargar configuración + modo de vista previa |
| Motor ruby generalizado | `subtitles_burner/burner.py` | Anotación multilingüe por token basada en JSON |

El flujo principal documentado en el README sigue siendo el pipeline basado en SRT, salvo que necesites explícitamente renderizado multi-slot basado en JSON.

## Características

- 🎌 **Generación automática de furigana**: Usa MeCab (fugashi) o pykakasi para generar furigana para caracteres kanji
- 🌐 **Compatibilidad con anotaciones ruby**: Renderiza guías de pronunciación para kanji, kana y otros sistemas (pinyin, romaji, IPA)
- 🎨 **Renderizado de texto personalizable**: Dibuja texto ruby con espaciado, alineación y trazo adecuados
- 📺 **Procesamiento directo de video**: Incrusta subtítulos directamente sobre fotogramas usando OpenCV
- 🔤 **Gestión inteligente de fuentes**: Busca y usa automáticamente fuentes para escrituras CJK y latinas
- ⚡ **Procesamiento por lotes**: Procesa múltiples videos a la vez
- 🎯 **Posicionamiento preciso**: Posición, márgenes y comportamiento de diseño configurables
- 🧩 **Múltiples runtimes**: Elige entre módulos classic, standalone, complete o generalized burner

## Estructura del proyecto

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

## Requisitos previos

- Se recomienda Python 3.9+
- Sistema operativo con fuentes capaces de renderizar texto japonés/CJK
- CPU y espacio en disco suficientes para salida de video fotograma a fotograma
- Archivos de subtítulos de entrada codificados en UTF-8 (recomendado)

## Instalación

### Configuración rápida

```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

El script de configuración instala paquetes base, intenta descargar UniDic y ejecuta `test_furigana.py`.

### Instalación manual

```bash
# Option A: install pinned repo requirements
pip install -r requirements.txt

# Option B: install explicit core packages (as documented in original README)
pip install opencv-python Pillow numpy fugashi unidic pykakasi

# Download Japanese dictionary data
python -c "import unidic; unidic.download()"
```

Paquetes opcionales usados por `subtitles_burner/burner.py` (solo necesarios para modos específicos de transliteración):

```bash
pip install phonemizer koroman pypinyin pycantonese
```

Paquetes opcionales usados por la utilidad `openai_request.py`:

```bash
pip install openai pygame
```

## Uso

### 1. Probar el sistema

```bash
python test_furigana.py
```

Esto prueba la generación de furigana y crea `test_furigana_output.png`.

### 2. Procesar todos los videos del directorio actual

```bash
python process_furigana_videos.py
```

Encuentra automáticamente todos los directorios `video_*` y procesa el primer `.MP4` y `.srt` de cada uno.

### 3. Procesar un solo video

```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. Uso avanzado (Classic Burner)

```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

### 5. Standalone Burner (modo auto-detección)

```bash
python standalone_furigana_burner.py
```

Si se ejecuta sin argumentos, detecta automáticamente `*.MP4`/`*.mp4` y `*.srt` en el directorio actual.

### 6. Complete Burner (configuración + vista previa)

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

## Configuración

### Parámetros CLI (Classic `furigana_subtitle_burner.py`)

| Parámetro | Descripción | Predeterminado |
|---|---|---|
| `--main-font-size` | Tamaño del texto japonés principal | `48` |
| `--furigana-font-size` | Tamaño del texto furigana | `24` |
| `--position` | `top`, `bottom` o `center` | `bottom` |
| `--margin` | Distancia al borde en píxeles | `50` |

### Parámetros CLI (`standalone_furigana_burner.py`)

| Parámetro | Descripción | Predeterminado |
|---|---|---|
| `--main-font-size` | Tamaño del texto principal | `64` |
| `--furigana-font-size` | Tamaño del furigana | `32` |
| `--position` | `top`, `bottom` o `center` | `bottom` |
| `--margin` | Margen desde el borde | `80` |

### Parámetros CLI (`complete_furigana_burner.py`)

| Parámetro | Descripción | Predeterminado |
|---|---|---|
| `--main-font-size` | Tamaño del texto principal | `64` |
| `--furigana-font-size` | Tamaño del furigana | `32` |
| `--position` | `top`, `bottom` o `center` | `bottom` |
| `--margin` | Margen desde el borde | `80` |
| `--preview` | Modo vista previa (primeros ~10 segundos) | Off |
| `--config <path>` | Cargar archivo de configuración | `None` |
| `--save-config` | Guardar config actual como predeterminada | Off |

### Parámetros CLI (`subtitles_burner/burner.py`)

| Parámetro | Descripción | Predeterminado |
|---|---|---|
| `--text-key` | Clave JSON para el texto base | `text` |
| `--ruby-key` | Clave JSON para marcado ruby | `None` |
| `--slot` | ID de slot en el diseño de slots inferiores | `1` |
| `--auto-ruby` | Generar ruby automáticamente para japonés | Off |

### Apariencia del texto

- Texto blanco con trazo negro para máxima visibilidad
- Selección automática de fuente (intenta fuentes japonesas del sistema)
- Espaciado proporcional entre caracteres y furigana

## Ejemplos

### Ejemplo de salida

Para el texto `今日は空が晴れていて`:

```text
   きょう   そら    は
   今日  は 空  が 晴れていて
```

### Ejemplo de estructura de entrada/salida por lotes

Después del procesamiento, tu directorio se verá así:

```text
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4      # Original video
├── video_577285345205551192-yFQ1pMPA.srt      # Subtitle file
├── video_577285345205551192-yFQ1pMPA.json     # Whisper output
├── video_577285345205551192-yFQ1pMPA.wav      # Audio extraction
└── video_577285345205551192-yFQ1pMPA_furigana.mp4  # Output with furigana
```

## Cómo funciona

### 1. Generación de furigana

El sistema usa varios métodos para generar furigana:

- **Principal**: MeCab con fugashi para análisis morfológico preciso
- **Alternativa**: pykakasi para conversión básica de kanji a hiragana
- **Último recurso**: análisis carácter por carácter

### 2. Estrategia de renderizado de texto

- Mide cada carácter y su furigana por separado
- Calcula el ancho óptimo de columna para cada carácter
- Centra el furigana sobre el kanji correspondiente
- Agrega trazo al texto para mejor visibilidad

### 3. Procesamiento de video

- Lee el video fotograma a fotograma con OpenCV
- Calcula el timing de subtítulos según marcas de tiempo SRT
- Renderiza texto con furigana como imagen RGBA
- Mezcla subtítulos sobre el fotograma mediante alpha blending
- Escribe el fotograma procesado al video de salida

## Notas de desarrollo

- El repositorio mantiene quemadores superpuestos por diseño; el pipeline SRT es el más simple para uso diario.
- `legacy/` y `legacy-results/` son archivos históricos y útiles para comparar regresiones.
- Actualmente no hay metadatos de empaquetado (`pyproject.toml` / `setup.py`).
- La cobertura de pruebas es basada en scripts (`test_furigana.py`, `simple_test.py`, `font_test.py`) en lugar de un framework de pruebas formal.
- `openai_request.py` es una utilidad auxiliar y no es necesaria para la incrustación de subtítulos principal.

## Solución de problemas

### No se encontraron fuentes japonesas

El sistema intenta encontrar fuentes japonesas automáticamente:

- **macOS**: Hiragino Sans
- **Linux**: `fonts-japanese-gothic`
- **Windows**: MS Gothic

Instala fuentes japonesas si los subtítulos aparecen con la fuente predeterminada.

Utilidades adicionales:

```bash
python font_test.py
python fix_font_squares.py
```

### Furigana no se genera

1. Verifica si fugashi/unidic está instalado: `python -c "import fugashi; print('OK')"`
2. Recurre a pykakasi: `python -c "import pykakasi; print('OK')"`
3. Revisa la salida de prueba: `python test_furigana.py`
4. Ejecuta diagnóstico de dependencias: `python fix_unidic.py` y `python debug_japanese.py`

### Errores en el procesamiento de video

- Asegúrate de que OpenCV pueda leer el video de entrada
- Comprueba el espacio en disco disponible para el archivo de salida
- Verifica que el archivo SRT esté codificado en UTF-8
- Prueba `complete_furigana_burner.py --preview ...` para validar rápido el pipeline

## Rendimiento

- La velocidad de procesamiento depende de la resolución y duración del video
- Velocidades típicas: 10-30 fps de tasa de procesamiento
- El uso de memoria escala con la resolución del video
- Usa procesamiento monohilo (se puede paralelizar)

## Dependencias

| Paquete | Rol | Notas |
|---|---|---|
| `opencv-python` | Procesamiento de video | Dependencia principal |
| `Pillow` | Renderizado de imagen y dibujo de texto | Dependencia principal |
| `numpy` | Operaciones con arrays | Dependencia principal |
| `fugashi` | Análisis morfológico japonés | Opcional pero recomendado |
| `unidic` | Datos de diccionario japonés | Opcional pero recomendado |
| `pykakasi` | Conversión de kanji a hiragana | Ruta alternativa |
| `camel-tools` | Utilidades de transliteración árabe | Incluido en `requirements.txt`, usado en modo generalized burner |

## Limitaciones conocidas

- El procesamiento exige mucha CPU (sin aceleración GPU)
- La selección de fuente es automática (control manual limitado)
- La distribución de furigana para palabras complejas puede no ser perfecta
- No hay soporte para diseño de texto vertical
- Solo una línea de subtítulo (aún sin soporte multilínea)

## Hoja de ruta

- Mejorar alineación/distribución de furigana en palabras complejas de múltiples kanji
- Ampliar opciones de composición de subtítulos multilínea
- Añadir perfiles de ejecución más claros entre burners classic/standalone/complete/generalized
- Añadir opcionalmente automatización de empaquetado/pruebas (`pyproject.toml`, smoke checks en CI)

## Qué hace posible tu apoyo

- <b>Mantener herramientas abiertas</b>: hosting, inferencia, almacenamiento de datos y operaciones de comunidad.
- <b>Entregar más rápido</b>: semanas de tiempo open-source enfocado en EchoMind, LazyEdit y MultilingualWhisper.
- <b>Prototipar wearables</b>: óptica, sensores y componentes neuromórficos/edge para IdeasGlass + LightMind.
- <b>Acceso para todos</b>: despliegues subvencionados para estudiantes, creadores y grupos comunitarios.

### Donar

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
- Tu apoyo sostiene mi investigación, desarrollo y operaciones para que pueda seguir compartiendo más proyectos abiertos y mejoras.

## Contribuir

Siéntete libre de mejorar el algoritmo de generación de furigana, añadir soporte para más diseños de texto u optimizar el pipeline de procesamiento de video.

Si envías cambios, incluye:

- Una explicación breve del impacto para usuarios
- Comandos de reproducción/prueba que ejecutaste en local
- Notas sobre supuestos de fuentes e idiomas si tu cambio afecta el renderizado

## Licencia

Actualmente no hay un archivo de licencia en este repositorio.

Suposición para este borrador: todos los derechos y términos de uso no están especificados hasta que el mantenedor agregue un archivo `LICENSE`.
