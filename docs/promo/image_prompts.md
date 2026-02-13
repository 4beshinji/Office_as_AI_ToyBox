# SOMS 画像生成AIプロンプト集

スライド・記事・ウェブサイト用のビジュアル素材を生成するためのプロンプト集。
DALL-E 3 / Midjourney / Stable Diffusion 向けに最適化。

---

## 1. ヒーローイメージ (スライド表紙 / 記事アイキャッチ)

**用途**: `slides_tech.md` スライド1, `slides_pitch.md` スライド1, `article.md` アイキャッチ

### DALL-E 3 / ChatGPT

```
A futuristic open-plan office interior at dusk, bathed in deep blue ambient light.
Golden luminous particles flow through the air like a neural network, connecting
small glowing sensor nodes mounted on walls and desks to a central crystalline
structure that pulses with warm golden light. A few people work comfortably at
standing desks, with holographic task cards floating near them showing gold reward
badges. The atmosphere is calm, intelligent, and alive — as if the room itself
is thinking. Photorealistic, cinematic lighting, wide angle, 16:9 aspect ratio.
```

### Midjourney

```
/imagine futuristic office interior, deep blue ambient lighting, golden neural
network particles connecting wall-mounted IoT sensors to a glowing central brain
node, people working comfortably at standing desks, holographic task cards with
gold badges floating nearby, photorealistic, cinematic, wide angle --ar 16:9
--v 6.1 --style raw
```

### Stable Diffusion (SDXL)

```
Prompt: futuristic smart office, deep blue ambient light, golden particles flowing
like neural pathways connecting IoT sensor nodes, crystalline AI core glowing warmly,
people working at ergonomic desks, holographic UI elements, photorealistic,
cinematic lighting
Negative: cartoon, anime, low quality, blurry, distorted faces
Steps: 30, CFG: 7, Size: 1920x1080
```

---

## 2. 有機体メタファー図 (アーキテクチャ説明)

**用途**: `slides_tech.md` スライド4-5, `slides_pitch.md` スライド4

### DALL-E 3 / ChatGPT

```
A semi-transparent human silhouette standing in a modern office, viewed from the side.
Inside the silhouette, a glowing golden brain represents the LLM, with blue neural
pathways (MQTT) extending down through the body. The eyes glow with a camera lens
overlay (computer vision). The hands extend outward and connect to small ESP32
circuit boards and sensor devices via golden threads. Around the figure, floating
icons represent: a microphone (voice), a dashboard screen (human interface), and
sensor modules. The background is dark navy blue (#0a1628). Clean, technical
illustration style with subtle glow effects. Labeled diagram aesthetic.
```

### Midjourney

```
/imagine semi-transparent human body silhouette, glowing golden brain inside the head
representing AI, blue neural pathways extending through the body as data connections,
camera lens eyes for computer vision, hands connected to small IoT circuit boards via
golden threads, floating icons around the figure showing sensors microphone and
dashboard screen, dark navy background, technical illustration, subtle glow effects
--ar 16:9 --v 6.1
```

---

## 3. 嵐のプロトコル (シナリオ説明)

**用途**: `slides_tech.md` スライド12, `article.md` シナリオセクション

### DALL-E 3 / ChatGPT

```
A dramatic scene viewed through a rain-streaked office window at twilight. Heavy rain
falls outside, visible through the glass. In the foreground, a person's hand holds a
smartphone displaying a task notification card with a glowing gold reward badge
showing "5000" points and a red "URGENT" label. The phone screen has a dark UI with
blue and gold accents. On the window sill, a small ESP32 sensor device with a green
LED blinks. The office interior is warmly lit with blue-tinted smart lighting.
Cinematic, moody atmosphere, shallow depth of field focusing on the phone screen.
```

### Midjourney

```
/imagine dramatic rainy office window at twilight, person holding smartphone showing
task notification with gold reward badge "5000" and red urgent label, dark UI with
blue and gold accents, ESP32 sensor on windowsill with green LED, warm interior
lighting, rain drops on glass, cinematic shallow depth of field, moody atmosphere
--ar 16:9 --v 6.1 --style raw
```

---

## 4. データ主権ビジュアル (都市ビジョン)

**用途**: `slides_tech.md` スライド17, `slides_pitch.md` スライド9

### DALL-E 3 / ChatGPT

```
An aerial view of a modern city at night, rendered in dark blue tones. Each building
has a warm golden pillar of light emanating upward from its rooftop, representing
local data processing. The pillars of light do NOT connect to any cloud above —
instead, they pulse independently, each building self-contained. Thin golden lines
connect neighboring buildings at ground level, representing minimal data exchange.
The sky above is clear and dark, deliberately empty of any cloud infrastructure
symbols. A subtle "50,000:1" text floats in the corner. Isometric or bird's eye
perspective, clean vector-like aesthetic with glow effects.
```

### Midjourney

```
/imagine aerial view of a modern city at night, dark blue tones, each building with
a warm golden pillar of light from rooftop representing local AI processing, no
cloud connections above, thin golden lines between buildings at ground level for
minimal data exchange, clear dark sky without cloud symbols, isometric perspective,
clean vector aesthetic with glow effects --ar 16:9 --v 6.1
```

---

## 5. ダッシュボードモックアップ (プロダクト紹介)

**用途**: `slides_tech.md` スライド14, `slides_pitch.md` スライド5

### DALL-E 3 / ChatGPT

```
A sleek dark-mode dashboard UI displayed on a large wall-mounted monitor in a modern
office. The screen shows 3 task cards arranged vertically, each with:
- A Japanese title in white text
- A location badge in blue
- A gold circular reward badge showing point values (1500, 2000, 3000)
- Colored urgency indicators (green, orange, red)
- Three action buttons: "受諾" (accept), "完了" (complete), "無視" (ignore)
The background of the UI is deep navy (#0a1628). One card is highlighted with a
subtle golden glow indicating selection. The overall aesthetic is clean,
gamified, and futuristic. The monitor sits in a minimalist office setting.
Photorealistic rendering, slight perspective angle.
```

### Midjourney

```
/imagine sleek dark mode dashboard UI on wall monitor, 3 task cards with Japanese
text titles, gold reward badges showing points, colored urgency indicators in green
orange red, action buttons labeled in Japanese, deep navy background, gamified
futuristic clean aesthetic, one card highlighted with golden glow, minimalist
office setting, photorealistic slight angle --ar 16:9 --v 6.1
```

---

## 6. エッジデバイス (ハードウェア紹介)

**用途**: `slides_tech.md` スライド19 (技術スタック), 記事内挿絵

### DALL-E 3 / ChatGPT

```
A close-up product photography style shot of a small IoT sensor node on a clean
white surface. The device consists of:
- A tiny ESP32-C6 microcontroller board (Seeed XIAO, about 2cm square)
- Connected to a BME680 environmental sensor (small silver square module)
- Connected to a MH-Z19C CO2 sensor (green rectangular module, about 3cm)
- Minimal clean wiring with thin colored jumper cables
- A small 3D-printed translucent white enclosure partially visible
The lighting is soft and even, studio quality. The background is pure white with
subtle shadows. The components are arranged neatly in an exploded view style,
showing how they connect. Technical product photography, shallow depth of field,
macro lens aesthetic.
```

### Midjourney

```
/imagine close-up product photography, small ESP32-C6 microcontroller connected
to BME680 sensor module and MH-Z19C CO2 sensor, minimal clean wiring with colored
jumper cables, translucent white 3D printed enclosure, pure white background,
soft studio lighting, exploded view arrangement, macro lens shallow depth of field,
technical product photo --ar 16:9 --v 6.1 --style raw
```

---

## スタイルガイドライン (共通)

### カラーパレット

プロンプトに含める色指定:

| 用途 | 色 | Hex |
|---|---|---|
| 背景 (ダーク) | ディープネイビー | `#0a1628` |
| アクセント (ゴールド) | ゴールド | `#FFD700` |
| テキスト / セカンダリ | ライトブルー | `#90CAF9` |
| プライマリ | ブルー | `#2196F3` |
| 成功 | グリーン | `#4CAF50` |
| 警告 | オレンジ | `#FF9800` |
| エラー / 緊急 | レッド | `#F44336` |

### トーン & ムード

- **フューチャリスティック** だが **温かみ** がある (冷たいSFではない)
- **人間中心**: AIが支配するのではなく、人間と協働するイメージ
- **ローカル**: クラウドの存在を示唆しない
- **有機的**: 機械的な直線より、神経系のような曲線と光の粒子

### 解像度

| 用途 | 推奨サイズ |
|---|---|
| スライド背景 | 1920 x 1080 (16:9) |
| 記事アイキャッチ | 1200 x 630 (OGP) |
| 記事内挿絵 | 1200 x 800 |
| ウェブサイトヒーロー | 1920 x 1080 |

### ネガティブプロンプト (共通)

Stable Diffusion 向け:
```
cartoon, anime, low quality, blurry, distorted faces, text, watermark,
signature, oversaturated, cloud computing symbols, AWS/Azure/GCP logos
```
