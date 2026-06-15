# Quran SVG

High-quality Quran **SVG pages** with a transparent, clickable **ayah-polygon** layer,
across multiple qiraat and publishers.

Each page is an SVG (plus a Brotli `.svg.br`) whose ayah hit-regions are
`<path class="ayahPolygon" surah=… ayah=… number=…>`. The `json/` folder holds
per-page polygon metadata plus two indexes: `surah.json` and `markers.json`.

## Layout

Folders are organised by **qiraa → publisher**:

```
mushafs/<qiraa>/<publisher>/
├── svg/      001.svg …          vector page text + ayah hit-layer
├── svg-br/   001.svg.br …       Brotli-compressed (serve with Content-Encoding: br)
└── json/     001.json …         per-page polygons
           surah.json            114-surah index (page, juz, names, ayah count)
           markers.json          ayah medallion centres [{page, ayah, x, y}]
```

Pages that contain more than one surah also have surah-specific variants, e.g.
`106-surah4.svg` / `106-surah5.svg`.

## Available mushafs

| Qiraa | Rawi | Publisher | Folder | Pages | Ayah count |
|-------|------|-----------|--------|------:|-----------:|
| ʿAsim | Hafs | King Fahd Complex — KFQC | `hafs/kfqc` | 604 | 6236 |
| Nafiʿ | Warsh | King Fahd Complex — KFQC | `warsh/kfqc` | 604 | 6214 |
| Nafiʿ | Qalun | King Fahd Complex — KFQC | `qalon/kfqc` | 604 | 6214 |
| Nafiʿ | Qalun | Libyan Endowments — مصحف الأوقاف الليبي | `qalon/libya-awqaf` | 612 | 6214 |
| Abu ʿAmr | Al-Douri | King Fahd Complex — KFQC | `douri/kfqc` | 604 | 6205 |
| ʿAsim | Shuʿbah | King Fahd Complex — KFQC | `shubah/kfqc` | 604 | 6236 |

## SVG & polygon structure

```xml
<path class="ayahPolygon" id="verse-12" number="002005" surah="2" ayah="5"
      d="M …" fill-opacity="0"/>
```

- `id` — `verse-N`, a global running ayah index over the whole mushaf.
- `number` — `SSSAAA` (surah×1000 + ayah, zero-padded).
- Polygons render first (transparent); page glyphs render on top. Suggested CSS:

```css
.ayahPolygon { fill-opacity: 0; cursor: pointer; }
.ayahPolygon:hover { fill: #f5e6a3; fill-opacity: .5; }
```

Give the glyph paths `pointer-events:none` so the lower polygons receive clicks.

## Coordinates & counts

- Coordinates are each mushaf's **native page pixels** (polygons and glyphs share one
  space — no rescaling needed). The Libyan Awqaf mushaf uses `viewBox 0 0 1120 2250`.
- Ayah counts follow **each mushaf's own medallions** and differ between qiraat
  (and occasionally between editions). The mushaf is authoritative.

## Serving Brotli files

```nginx
location ~ \.svg\.br$  { add_header Content-Encoding br; default_type image/svg+xml; }
location ~ \.json\.br$ { add_header Content-Encoding br; default_type application/json; }
```
