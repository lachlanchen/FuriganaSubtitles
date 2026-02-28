[English](../README.md) · [العربية](README.ar.md) · [Español](README.es.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [中文 (简体)](README.zh-Hans.md) · [中文（繁體）](README.zh-Hant.md) · [Deutsch](README.de.md) · [Русский](README.ru.md)


<p align="center">
  <img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/logos/banner.png" alt="Bannière LazyingArt" />
</p>

# Furigana Subtitle Burner

<p align="center">
  <img src="figures/demo.png" alt="Démo de sous-titres furigana" width="720" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/OpenCV-Video%20Burning-5C3EE8?logo=opencv&logoColor=white" alt="OpenCV" />
  <img src="https://img.shields.io/badge/Status-Active-2ea44f" alt="Statut" />
  <img src="https://img.shields.io/badge/Primary%20Flow-SRT%20Pipeline-0ea5e9" alt="Flux principal" />
  <img src="https://img.shields.io/badge/Extended%20Mode-JSON%20Ruby-f59e0b" alt="Mode étendu" />
</p>

Un générateur de sous-titres Python qui rend les furigana japonais et d’autres annotations ruby (pinyin, romaji, API/IPA, etc.) directement sur les frames vidéo avec OpenCV. Il est optimisé pour les workflows furigana tout en restant flexible pour des sous-titres de style ruby multilingues.

Conçu pour <a href="https://studio.lazying.art" target="_blank" rel="noreferrer">LazyEdit Studio</a> · <a href="https://github.com/lachlanchen/LazyEdit" target="_blank" rel="noreferrer">GitHub</a>

## Table des matières

- [Vue d’ensemble](#vue-densemble)
- [Fonctionnalités](#fonctionnalités)
- [Structure du projet](#structure-du-projet)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Configuration](#configuration)
- [Exemples](#exemples)
- [Fonctionnement](#fonctionnement)
- [Notes de développement](#notes-de-développement)
- [Dépannage](#dépannage)
- [Performances](#performances)
- [Dépendances](#dépendances)
- [Limites connues](#limites-connues)
- [Feuille de route](#feuille-de-route)
- [Ce que votre soutien rend possible](#ce-que-votre-soutien-rend-possible)
- [Contribution](#contribution)
- [Licence](#licence)

## Vue d’ensemble

Ce dépôt contient plusieurs parcours de rendu de sous-titres :

| Parcours | Scripts | Idéal pour |
|---|---|---|
| Workflow furigana SRT classique | `process_furigana_videos.py` + `furigana_subtitle_burner.py` | Rendu de sous-titres au quotidien avec des fichiers SRT |
| Workflow autonome | `standalone_furigana_burner.py` | Exécution simple avec un seul script |
| Workflow complet | `complete_furigana_burner.py` | Sauvegarde/chargement de configuration + mode aperçu |
| Moteur ruby généralisé | `subtitles_burner/burner.py` | Annotation multilingue au niveau token pilotée par JSON |

Le flux README par défaut reste le pipeline basé sur SRT, sauf si vous avez explicitement besoin d’un rendu multi-emplacements basé sur JSON.

## Fonctionnalités

- 🎌 **Génération automatique de furigana** : utilise MeCab (fugashi) ou pykakasi pour générer des furigana pour les caractères kanji
- 🌐 **Prise en charge des annotations ruby** : rend des guides de prononciation pour kanji, kana et d’autres écritures (pinyin, romaji, IPA)
- 🎨 **Rendu de texte personnalisable** : produit un texte ruby lisible avec espacement, alignement et contour appropriés
- 📺 **Traitement vidéo direct** : incruste les sous-titres directement sur les frames vidéo avec OpenCV
- 🔤 **Gestion intelligente des polices** : trouve et utilise automatiquement des polices pour les écritures CJK et latines
- ⚡ **Traitement par lots** : traite plusieurs vidéos en une fois
- 🎯 **Positionnement précis** : position des sous-titres, marges et comportement de mise en page configurables
- 🧩 **Plusieurs runtimes** : choix entre les modules classic, standalone, complete ou generalized burner

## Structure du projet

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

## Prérequis

- Python 3.9+ recommandé
- OS avec des polices capables de rendre du texte japonais/CJK
- CPU et espace disque suffisants pour une sortie vidéo frame par frame
- Fichiers de sous-titres d’entrée encodés en UTF-8 (recommandé)

## Installation

### Configuration rapide

```bash
chmod +x setup_furigana.sh
./setup_furigana.sh
```

Le script d’installation installe les paquets principaux, tente le téléchargement de UniDic, puis exécute `test_furigana.py`.

### Installation manuelle

```bash
# Option A: install pinned repo requirements
pip install -r requirements.txt

# Option B: install explicit core packages (as documented in original README)
pip install opencv-python Pillow numpy fugashi unidic pykakasi

# Download Japanese dictionary data
python -c "import unidic; unidic.download()"
```

Paquets optionnels utilisés par `subtitles_burner/burner.py` (nécessaires uniquement pour certains modes de translittération) :

```bash
pip install phonemizer koroman pypinyin pycantonese
```

Paquets optionnels utilisés par l’utilitaire `openai_request.py` :

```bash
pip install openai pygame
```

## Utilisation

### 1. Tester le système

```bash
python test_furigana.py
```

Cela teste la génération de furigana et crée `test_furigana_output.png`.

### 2. Traiter toutes les vidéos du répertoire courant

```bash
python process_furigana_videos.py
```

Détecte automatiquement tous les dossiers `video_*` et traite le premier `.MP4` et `.srt` de chacun.

### 3. Traiter une seule vidéo

```bash
python process_furigana_videos.py input_video.mp4 subtitles.srt output_video.mp4
```

### 4. Utilisation avancée (Classic Burner)

```bash
python furigana_subtitle_burner.py video.mp4 subtitles.srt output.mp4 \
    --main-font-size 64 \
    --furigana-font-size 32 \
    --position bottom \
    --margin 80
```

### 5. Standalone Burner (mode auto-détection)

```bash
python standalone_furigana_burner.py
```

Exécuté sans arguments, il détecte automatiquement `*.MP4`/`*.mp4` et `*.srt` dans le répertoire courant.

### 6. Complete Burner (config + aperçu)

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

## Configuration

### Paramètres CLI (Classic `furigana_subtitle_burner.py`)

| Paramètre | Description | Par défaut |
|---|---|---|
| `--main-font-size` | Taille du texte japonais principal | `48` |
| `--furigana-font-size` | Taille du texte furigana | `24` |
| `--position` | `top`, `bottom` ou `center` | `bottom` |
| `--margin` | Distance au bord en pixels | `50` |

### Paramètres CLI (`standalone_furigana_burner.py`)

| Paramètre | Description | Par défaut |
|---|---|---|
| `--main-font-size` | Taille du texte principal | `64` |
| `--furigana-font-size` | Taille du furigana | `32` |
| `--position` | `top`, `bottom` ou `center` | `bottom` |
| `--margin` | Marge par rapport au bord | `80` |

### Paramètres CLI (`complete_furigana_burner.py`)

| Paramètre | Description | Par défaut |
|---|---|---|
| `--main-font-size` | Taille du texte principal | `64` |
| `--furigana-font-size` | Taille du furigana | `32` |
| `--position` | `top`, `bottom` ou `center` | `bottom` |
| `--margin` | Marge par rapport au bord | `80` |
| `--preview` | Mode aperçu (premières ~10 secondes) | Off |
| `--config <path>` | Charger un fichier de configuration | `None` |
| `--save-config` | Sauvegarder la configuration actuelle par défaut | Off |

### Paramètres CLI (`subtitles_burner/burner.py`)

| Paramètre | Description | Par défaut |
|---|---|---|
| `--text-key` | Clé JSON pour le texte de base | `text` |
| `--ruby-key` | Clé JSON pour le marquage ruby | `None` |
| `--slot` | ID du slot dans la disposition des slots bas | `1` |
| `--auto-ruby` | Génération automatique du ruby pour le japonais | Off |

### Apparence du texte

- Texte blanc avec contour noir pour une visibilité maximale
- Sélection automatique de police (essaie les polices japonaises système)
- Espacement proportionnel entre caractères et furigana

## Exemples

### Sortie d’exemple

Pour le texte `今日は空が晴れていて` :

```text
   きょう   そら    は
   今日  は 空  が 晴れていて
```

### Exemple de structure d’entrée/sortie en lot

Après traitement, votre dossier ressemblera à ceci :

```text
video_577285345205551192-yFQ1pMPA/
├── video_577285345205551192-yFQ1pMPA.MP4      # Original video
├── video_577285345205551192-yFQ1pMPA.srt      # Subtitle file
├── video_577285345205551192-yFQ1pMPA.json     # Whisper output
├── video_577285345205551192-yFQ1pMPA.wav      # Audio extraction
└── video_577285345205551192-yFQ1pMPA_furigana.mp4  # Output with furigana
```

## Fonctionnement

### 1. Génération des furigana

Le système utilise plusieurs méthodes pour générer les furigana :

- **Principal** : MeCab avec fugashi pour une analyse morphologique précise
- **Fallback** : pykakasi pour une conversion kanji-vers-hiragana de base
- **Dernier recours** : analyse caractère par caractère

### 2. Stratégie de rendu du texte

- Mesure chaque caractère et son furigana séparément
- Calcule la largeur de colonne optimale pour chaque caractère
- Centre le furigana au-dessus du kanji correspondant
- Ajoute un contour de texte pour une meilleure lisibilité

### 3. Traitement vidéo

- Lit la vidéo frame par frame avec OpenCV
- Calcule le timing des sous-titres à partir des timestamps SRT
- Rend le texte furigana en image RGBA
- Applique un alpha-blending du sous-titre sur la frame vidéo
- Écrit la frame traitée dans la vidéo de sortie

## Notes de développement

- Le dépôt contient volontairement des burners qui se chevauchent ; le pipeline SRT est le plus simple pour l’usage quotidien.
- `legacy/` et `legacy-results/` sont archivés et utiles pour des comparaisons de régression.
- Aucun metadata de packaging (`pyproject.toml` / `setup.py`) n’est actuellement présent.
- La couverture de test est basée sur des scripts (`test_furigana.py`, `simple_test.py`, `font_test.py`) plutôt que sur un framework de tests formel.
- `openai_request.py` est un utilitaire auxiliaire et n’est pas requis pour le rendu principal des sous-titres.

## Dépannage

### Aucune police japonaise trouvée

Le système essaie de trouver automatiquement des polices japonaises :

- **macOS** : Hiragino Sans
- **Linux** : `fonts-japanese-gothic`
- **Windows** : MS Gothic

Installez des polices japonaises si les sous-titres apparaissent avec la police par défaut.

Aides supplémentaires :

```bash
python font_test.py
python fix_font_squares.py
```

### Les furigana ne sont pas générés

1. Vérifier si fugashi/unidic est installé : `python -c "import fugashi; print('OK')"`
2. Utiliser le fallback pykakasi : `python -c "import pykakasi; print('OK')"`
3. Vérifier la sortie de test : `python test_furigana.py`
4. Exécuter le diagnostic des dépendances : `python fix_unidic.py` et `python debug_japanese.py`

### Erreurs de traitement vidéo

- Vérifier que la vidéo d’entrée est lisible par OpenCV
- Vérifier l’espace disque disponible pour le fichier de sortie
- Vérifier que l’encodage du fichier SRT est UTF-8
- Essayer `complete_furigana_burner.py --preview ...` pour valider rapidement le pipeline

## Performances

- La vitesse de traitement dépend de la résolution et de la durée de la vidéo
- Vitesses typiques : cadence de traitement de 10 à 30 fps
- L’utilisation mémoire augmente avec la résolution vidéo
- Utilise un traitement mono-thread (peut être parallélisé)

## Dépendances

| Package | Rôle | Notes |
|---|---|---|
| `opencv-python` | Traitement vidéo | Dépendance principale |
| `Pillow` | Rendu d’image et dessin de texte | Dépendance principale |
| `numpy` | Opérations sur tableaux | Dépendance principale |
| `fugashi` | Analyse morphologique du japonais | Optionnel mais recommandé |
| `unidic` | Données de dictionnaire japonais | Optionnel mais recommandé |
| `pykakasi` | Conversion kanji vers hiragana | Chemin de fallback |
| `camel-tools` | Aides de translittération arabe | Inclus dans `requirements.txt`, utilisé en mode generalized burner |

## Limites connues

- Le traitement est intensif en CPU (pas d’accélération GPU)
- La sélection de police est automatique (contrôle manuel limité)
- La distribution des furigana pour des mots complexes peut ne pas être parfaite
- Pas de prise en charge de la mise en page verticale
- Une seule ligne de sous-titre (pas encore de support multi-lignes)

## Feuille de route

- Améliorer l’alignement/la distribution des furigana pour les mots complexes multi-kanji
- Étendre les options de composition de sous-titres multi-lignes
- Ajouter des profils d’exécution plus clairs entre les burners classic/standalone/complete/generalized
- Ajouter éventuellement l’automatisation packaging/tests (`pyproject.toml`, smoke checks CI)

## Ce que votre soutien rend possible

- <b>Garder les outils ouverts</b> : hébergement, inférence, stockage de données et opérations communautaires.
- <b>Livrer plus vite</b> : des semaines de temps open source concentré sur EchoMind, LazyEdit et MultilingualWhisper.
- <b>Prototyper des wearables</b> : optique, capteurs et composants neuromorphiques/edge pour IdeasGlass + LightMind.
- <b>Accès pour tous</b> : déploiements subventionnés pour les étudiants, créateurs et groupes communautaires.

### Faire un don

<div align="center">
<table style="margin:0 auto; text-align:center; border-collapse:collapse;">
  <tr>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;">
      <a href="https://chat.lazying.art/donate">https://chat.lazying.art/donate</a>
    </td>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;">
      <a href="https://chat.lazying.art/donate"><img src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/figs/donate_button.svg" alt="Faire un don" height="44"></a>
    </td>
  </tr>
  <tr>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;">
      <a href="https://paypal.me/RongzhouChen">
        <img src="https://img.shields.io/badge/PayPal-Donate-003087?logo=paypal&logoColor=white" alt="Faire un don avec PayPal">
      </a>
    </td>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;">
      <a href="https://buy.stripe.com/aFadR8gIaflgfQV6T4fw400">
        <img src="https://img.shields.io/badge/Stripe-Donate-635bff?logo=stripe&logoColor=white" alt="Faire un don avec Stripe">
      </a>
    </td>
  </tr>
  <tr>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;"><strong>WeChat</strong></td>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;"><strong>Alipay</strong></td>
  </tr>
  <tr>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;"><img alt="QR WeChat" src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/figs/donate_wechat.png" width="240"/></td>
    <td style="text-align:center; vertical-align:middle; padding:6px 12px;"><img alt="QR Alipay" src="https://raw.githubusercontent.com/lachlanchen/lachlanchen/main/figs/donate_alipay.png" width="240"/></td>
  </tr>
</table>
</div>

**支援 / Donate**

- ご支援は研究・開発と運用の継続に役立ち、より多くのオープンなプロジェクトを皆さんに届ける力になります。
- 你的支持将用于研发与运维，帮助我持续公开分享更多项目与改进。
- Your support sustains my research, development, and ops so I can keep sharing more open projects and improvements.

## Contribution

N’hésitez pas à améliorer l’algorithme de génération de furigana, à ajouter la prise en charge de nouvelles mises en page de texte, ou à optimiser le pipeline de traitement vidéo.

Si vous proposez des changements, incluez :

- Une brève explication de l’impact côté utilisateur
- Les commandes de reproduction/test exécutées en local
- Des notes sur les hypothèses de police et de langue si votre changement affecte le rendu

## Licence

Aucun fichier de licence n’est actuellement présent dans ce dépôt.

Hypothèse pour ce brouillon : tous les droits et conditions d’utilisation sont actuellement non spécifiés tant qu’un fichier `LICENSE` n’est pas ajouté par le mainteneur.
