# tools

Three scripts and a vendored dataset. They read the page SVGs and nothing else; the shipped
polygons are never used to decide what a polygon should be, so the audit's verdict is
independent of the data it checks.

| | |
|---|---|
| `qiraat_map.py` | which counting madhhab each mushaf follows, and each system's per-surah ayah counts |
| `polygon_lib.py` | the shared geometry: markers, line grid, the generator, the scoring |
| `audit_ayah_polygons.py` | reports violations in four tiers |
| `build_ayah_polygons.py` | regenerates `svg/`, `json/` and `svg-br/` in place |
| `data/qiraat-ayah-map/` | vendored from [quranpedia/qiraat-ayah-map](https://github.com/quranpedia/qiraat-ayah-map) (MIT) — see `SOURCE.md` |

## Ground truth

The ۝ end-of-ayah markers drawn in each page's `<g id="ayah_markers">` give, with no
inference, the line and the x where every ayah finishes. The page's rendered ink gives the
line grid and the whitespace around each medallion. The counting madhhab gives the ayah
identities. Word-assignment output is not used anywhere.

## The model

* a page is a grid of equal line bands, and a marker sits at the middle of a band;
* an ayah occupies an unbroken run of bands, from where the previous ayah ended to its own
  marker, filling whole lines in between;
* reading is right to left: an ayah's first band starts at the right, its last ends at the left;
* an ayah that ends its line runs out to the text margin;
* a page may end mid-ayah, in which case the ayah gets a polygon on both pages;
* a band is a surah header or basmalah only if it carries no marker, is narrower than a
  justified line, and sits where the surah changes.

## Running

```sh
python3 tools/qiraat_map.py                              # counting systems, self-checked
python3 tools/audit_ayah_polygons.py                     # all five mushafs, pages 3-604
python3 tools/audit_ayah_polygons.py --mushaf hafs --pages 294,545 --tier geometry
python3 tools/build_ayah_polygons.py --dry-run           # report, write nothing
python3 tools/build_ayah_polygons.py --mushaf warsh      # rewrite svg, json and svg.br
```

Needs `rsvg-convert` on PATH, plus `numpy`, `Pillow` and `brotli`.

Pages 1–2 are out of scope everywhere: the ornate opening spread uses one staircase polygon
per ayah instead of a stack of rectangles, and was corrected by hand.

## Gotchas worth knowing

* Qālūn and Warsh pages use `viewBox="-6 0 345 550"`. Any measurement taken from a raster has
  to be mapped through the viewBox origin or it lands 6 units off.
* An `id="verse-13"` attribute contains the substring `d="`, so a non-greedy scan for the
  polygon's `d` attribute must require whitespace before it.
* Medallions frequently touch the neighbouring letters, so a scan looking for the whitespace
  beside a medallion must never cross ink.
