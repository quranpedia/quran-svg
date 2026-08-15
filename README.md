# Quran SVG

High-quality Quran **SVG pages** with a transparent, clickable **ayah-polygon** layer,
across multiple qiraat and publishers.

Each page is an SVG (plus a Brotli `.svg.br`) whose ayah hit-regions are
`<path class="ayahPolygon" surah=… ayah=… number=…>` and whose text is grouped
**one `<g class="line" data-line="N">` per line**. The `json/` folder holds per-page
polygon metadata plus two indexes: `surah.json` and `markers.json`; `lines/` holds
per-page line geometry.

## Layout

Folders are organised by **qiraa → publisher**:

```
mushafs/<qiraa>/<publisher>/
├── svg/      001.svg …          vector page text + ayah hit-layer
├── svg-br/   001.svg.br …       Brotli-compressed (serve with Content-Encoding: br)
├── json/     001.json …         per-page polygons
│          surah.json            114-surah index (page, juz, names, ayah count)
│          markers.json          ayah medallion centres [{page, ayah, x, y}]
└── lines/    001.json …         per-page line bands, boxes and baselines
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

## Line structure

A page's text is grouped by line inside `#content`, top to bottom:

```xml
<g id="content">
  <g class="line" data-line="1">
    <g transform="translate(152.3 389.27)"><path d="M …" fill="#231f20" fill-rule="evenodd"/></g>
  </g>
  <g class="line" data-line="2"> … </g>
  …
</g>
```

- `data-line` counts from **1 at the top of the rendered page**.
- A standard body page has exactly **15** line groups. Exceptions: pages 1 and 2 (Al-Fatiha
  and the opening of Al-Baqarah) are set on their own spacing and have **7** and **8**.
- A surah-variant page (`106-surah4.svg`) is the whole page under a cropping `viewBox`, so
  it carries all 15 groups and **keeps the parent page's line numbers** — line 8 of
  `106-surah5.svg` is line 8 of page 106, not the first line you can see.
- Highlight a line with `[data-line="7"] { fill: #c8102e }`, or move it with a `transform`
  on the group. Nothing else about the page changed: the ayah polygons, the ayah markers,
  the coordinates and the rendered result are exactly as they were.

`lines/NNN.json` is the same geometry without the SVG — one entry per line, in the page's
own coordinates:

```json
[{"lineNumber": 1, "x": 8.77, "y": 4.53, "width": 321.04, "height": 32.82,
  "top": 4.53, "bottom": 38.54, "baseline": 35.04}]
```

| Field | Meaning |
|---|---|
| `lineNumber` | 1-based, top to bottom — matches `data-line` |
| `x`, `y`, `width`, `height` | tight bounding box of the line's glyphs |
| `top`, `bottom` | the full-width band the line owns; bands tile the page without gaps |
| `baseline` | y the line's letters sit on (absent if it could not be determined) |
| `visible` | `false` only on a variant page, for a line its `viewBox` crops away |

Use `top`/`bottom` to hit-test a touch to a line and to size a highlight; use the box when
you want to fit something to the ink.

## Coordinates & counts

- Coordinates are each mushaf's **native page pixels** (polygons and glyphs share one
  space — no rescaling needed). The Libyan Awqaf mushaf uses `viewBox 0 0 1120 2250`.
- Ayah counts follow **each mushaf's own medallions** and differ between qiraat
  (and occasionally between editions). The mushaf is authoritative.

## Regenerating

`tools/` holds the generator for the line structure. Run it after the pages are
regenerated upstream, or the annotation is lost on the next update:

```bash
tools/add_line_structure.py                    # every edition, refreshes svg-br/ too
tools/add_line_structure.py --mushaf hafs/kfqc
tools/add_line_structure.py --check            # validate only, write nothing
tools/verify_render.py hafs/kfqc --scale 3     # render every page before and after
```

It needs Python 3 and the `brotli` module (`pip install brotli`); `verify_render.py` also
needs `rsvg-convert`, and `numpy`+`pillow` to quantify differences.

Lines are recovered from geometry — there is no markup in the source to group by line, and
a page's whole text is a single `<path>` of up to half a million characters. The generator
fits the page's fixed 15-line grid to the ink profile, then nudges each cut onto the clear
space beside it. **It will not emit a body page that does not segment to 15 lines**; it
reports it instead. Re-running is safe and idempotent: an already-annotated page is
unwrapped and re-derived, and comes out byte-identical.

## Serving Brotli files

```nginx
location ~ \.svg\.br$  { add_header Content-Encoding br; default_type image/svg+xml; }
location ~ \.json\.br$ { add_header Content-Encoding br; default_type application/json; }
```

## License & usage

- **Our own contribution** — the ayah-polygon overlay, the per-line grouping, the JSON
  metadata (`mushafs/**/json/` — per-page polygons, `surah.json`, `markers.json` — and
  `mushafs/**/lines/`), and the repo structure/tooling — is
  **[CC0 1.0](LICENSE)** (public domain): reuse freely, including commercially, no attribution
  required. This is the clean base to build a shared Qur'anic-data standard on.
- **King Fahd Complex editions** (Ḥafṣ, Warsh, Qālūn, Al-Dūrī, Shuʿbah — the `*/kfqc` folders):
  the Complex grants **free use** of its digital Muṣḥaf al-Madinah for personal, business,
  governmental, institutional, printing, digital-publishing, media, website, and software use,
  **worldwide**. The **only** restriction is that **printing physical muṣḥafs for commercial
  sale** is reserved to the Complex (Saudi Royal Decrees). So: free for essentially any
  digital/app/web use — you just can't use it to print-and-sell physical muṣḥafs.
- **Libyan Awqaf edition** (`qalon/libya-awqaf`): **free for non-commercial use only**;
  **commercial use requires prior approval from the Libyan Ministry of Awqaf**.
- **The Qur'anic text itself** is not subject to copyright and may be freely reproduced, but
  must never be altered and its sanctity must be preserved.

See **[NOTICE.md](NOTICE.md)** for full source attribution and the publishers' exact terms.
