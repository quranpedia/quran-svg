# tools

Four scripts and a vendored dataset. They read the page SVGs and nothing else: the shipped
polygons are never used to decide what a polygon *should* be.

**What that does and does not buy you.** The audit does not trust the geometry it is checking
— but it does share `build_polygons` with the generator, so after a build the BREAK tier is
comparing the generator against itself and carries no information. Set `INKCOL` to a wrong
value, rebuild, and the audit will certify the result as clean. The tiers that can actually
falsify a build are IDENTITY, FILES, `OVERLAP`, `STRAY`, `MARKERMETA` (the marker centres
against the SVG's own `ayah:x`/`ayah:y`, which no other code path touches) and `LINES` (a
page must be a fifteen-line grid). Treat a clean BREAK tier as "self-consistent", not as
"correct".

| | |
|---|---|
| `qiraat_map.py` | which counting madhhab each mushaf follows, and each system's per-surah ayah counts |
| `draw_missing_rosettes.py` | draws the ۝ ornament on ayah ends that print only a bare numeral |
| `polygon_lib.py` | the shared geometry: markers, line grid, the generator, the scoring |
| `audit_ayah_polygons.py` | reports violations in four tiers |
| `build_ayah_polygons.py` | regenerates `svg/`, `json/` and `svg-br/` in place |
| `data/qiraat-ayah-map/` | vendored from [quranpedia/qiraat-ayah-map](https://github.com/quranpedia/qiraat-ayah-map) (MIT) — see `SOURCE.md` |

## Ground truth

The ۝ end-of-ayah markers drawn in each page's `<g id="ayah_markers">` give, with no
inference, the line and the x where every ayah finishes. The page's rendered ink gives the
line grid and the whitespace around each medallion. Word-assignment output is not used
anywhere.

Ayah identities come from the polygons' own `surah`/`ayah`/`number` attributes — the
generator never renames an ayah. The counting madhhab is what the *audit* checks those
identities against; it is not an input to the build.

## The model

* a page is a grid of equal line bands, and a marker sits at the middle of a band;
* an ayah occupies an unbroken run of bands, from where the previous ayah ended to its own
  marker, filling whole lines in between;
* reading is right to left: an ayah's first band starts at the right, its last ends at the left;
* an ayah that ends its line runs out to the text margin;
* a page may end mid-ayah, in which case the ayah gets a polygon on both pages;
* a band is a surah header or basmalah only if it carries no marker, is narrower than a
  justified line, and sits where the surah changes;
* a band carrying a trace of ink is not a line — a comb fitted to fifteen lines will happily
  put a sixteenth tooth over the descenders below the last one.

## Running

```sh
python3 tools/qiraat_map.py                              # counting systems, self-checked
python3 tools/audit_ayah_polygons.py                     # all five mushafs, pages 3-604
python3 tools/audit_ayah_polygons.py --mushaf hafs --pages 294,545 --tier geometry
python3 tools/build_ayah_polygons.py --dry-run           # report, write nothing
python3 tools/build_ayah_polygons.py --mushaf warsh      # rewrite svg, json and svg.br
python3 tools/draw_missing_rosettes.py --dry-run         # ayah ends with no ۝ ornament
```

`build_ayah_polygons.py` is idempotent: running it twice produces the same files, because it
sets aside a continuation polygon written by an earlier run before pairing ayat to markers.

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
* Arabic-Indic numerals have gaps between their digits, so measuring one by walking a run of
  ink stops at the first stroke and reports a numeral 1 unit wide.
* Hafs, Douri and Shuʿbah state `markers.json` and `ayah:x`/`ayah:y` in page space. Qālūn and
  Warsh state theirs in a different frame, offset by a translation that varies page to page —
  fit it, never assume it.
