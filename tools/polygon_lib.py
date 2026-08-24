#!/usr/bin/env python3
"""Geometry shared by the ayah-polygon audit and the generator.

Everything here is derived from a page SVG alone: the ۝ end-of-ayah markers drawn in
``<g id="ayah_markers">``, and the page's own ink as rendered by ``rsvg-convert``.  No
function reads the shipped polygons to decide what a polygon should be.

Note what that does *not* mean.  The audit imports ``build_polygons`` from here, so once a
page has been built, the audit's reading-order tier is comparing the generator against
itself: give ``INKCOL`` a wrong value, rebuild, and the audit will call the result clean.
The checks that can genuinely falsify a build are the ones that do not route through this
module's model of a page -- ayah identity, the file derivatives, rect-on-rect overlap, a
marker landing outside its own polygon, the marker centres against the SVG's own
``ayah:x``/``ayah:y``, and the fifteen-line grid.

The model a page follows:

* the page is a grid of equal line bands; markers sit at the middle of a band;
* an ayah occupies an unbroken run of bands, from where the previous ayah ended to its own
  marker, filling whole lines in between;
* reading is right to left, so an ayah's first band starts at the right and its last band
  ends at the left;
* an ayah that ends its line, and the last ayah on a page, run out to the text margin;
* a page can end in the middle of an ayah, in which case the remaining lines belong to the
  ayah whose marker is on the next page and that ayah gets a polygon on both pages.
"""

import os
import re
import subprocess
import tempfile

import numpy as np
from PIL import Image

Z = 4                 # raster scale used for every ink measurement
PITCH = (33.0, 39.0)  # plausible line pitch, in page units, for the full-size pages
NARROW = 0.90         # an unmarked band narrower than this fraction of the text is decoration
JUST = 0.85           # a band at least this wide counts as a justified line
INKCOL = 1            # ink pixels in a column before it counts as ink
FAINT = 0.05          # a band with less than this share of the page's median ink is not a line
EPS = 0.01

_RECT = re.compile(r"M\s*([-\d.]+)\s+([-\d.]+)\s+L\s*([-\d.]+)\s+([-\d.]+)"
                   r"\s+L\s*([-\d.]+)\s+([-\d.]+)\s+L\s*([-\d.]+)\s+([-\d.]+)\s+Z")
# note the \s before d=: without it the non-greedy scan matches the "d=" inside id="…"
_PATH = re.compile(r'<path class="ayahPolygon"([^>]*?)\sd="([^"]*)"([^>]*?)/>')
_ATTR = re.compile(r'(\w[\w-]*)="([^"]*)"')
_MATRIX = re.compile(r'<g transform="matrix\(([-\d.eE ]+)\)"')
_MARKER = re.compile(r'<g transform="translate\(([-\d.eE]+) ([-\d.eE]+)\) '
                     r'scale\(([-\d.eE]+) ([-\d.eE]+)\)">(.*?)</g>', re.S)
_D = re.compile(r'<path d="([^"]*)"')
_TOK = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])|(-?(?:\d+\.?\d*|\.\d+)(?:[eE]-?\d+)?)")
_NARG = dict(M=2, L=2, H=1, V=1, C=6, S=4, Q=4, T=2, A=7, Z=0)


# --------------------------------------------------------------------------- page + markers

def viewbox(svg_text):
    """(min_x, min_y, width, height).  Qalun and Warsh pages use min_x = -6, not 0."""
    v = [float(x) for x in re.search(r'viewBox="([^"]*)"', svg_text).group(1).split()]
    return v[0], v[1], v[2], v[3]


def read_page(svg_path):
    """(svg_text, box, polygons) — polygons in document order, each with its parsed rects."""
    with open(svg_path, encoding="utf-8") as fh:
        text = fh.read()
    box = viewbox(text)
    polys = []
    for m in _PATH.finditer(text):
        attrs = dict(_ATTR.findall(m.group(1) + " " + m.group(3)))
        rects = []
        for r in _RECT.finditer(m.group(2)):
            v = [float(x) for x in r.groups()]
            xs, ys = {v[0], v[2], v[4], v[6]}, {v[1], v[3], v[5], v[7]}
            if len(xs) == 2 and len(ys) == 2:
                rects.append((min(xs), min(ys), max(xs), max(ys)))
        polys.append(dict(span=m.span(), attrs=attrs, d=m.group(2), rects=rects,
                          subpaths=m.group(2).count("Z"),
                          surah=int(attrs.get("surah", -1)), ayah=int(attrs.get("ayah", -1)),
                          key="%s:%s" % (attrs.get("surah"), attrs.get("ayah")),
                          id=attrs.get("id"), number=attrs.get("number")))
    return text, box, polys


def _glyph_bbox(d):
    """Bounding box of a path's ``d``.  Curve control points are included, which is close
    enough for a medallion outline and needs no curve flattening."""
    toks = [(m.group(1), m.group(2)) for m in _TOK.finditer(d)]
    i, cmd, x, y, sx, sy = 0, None, 0.0, 0.0, 0.0, 0.0
    xs, ys = [], []
    while i < len(toks):
        if toks[i][0]:
            cmd = toks[i][0]
            i += 1
            if cmd in "Zz":
                x, y = sx, sy
                continue
        if cmd is None:
            break
        n = _NARG[cmd.upper()]
        a = []
        while len(a) < n and i < len(toks) and toks[i][1] is not None:
            a.append(float(toks[i][1]))
            i += 1
        if len(a) < n:
            break
        rel, c = cmd.islower(), cmd.upper()
        if c == "M":
            x, y = (x + a[0], y + a[1]) if rel else (a[0], a[1])
            sx, sy = x, y
            cmd = "l" if rel else "L"
        elif c == "L":
            x, y = (x + a[0], y + a[1]) if rel else (a[0], a[1])
        elif c == "H":
            x = x + a[0] if rel else a[0]
        elif c == "V":
            y = y + a[0] if rel else a[0]
        elif c in "CSQTA":
            px, py = x, y
            for k in range(0, n - 1, 2):
                if c != "A" or k >= n - 2:
                    xs.append(px + a[k] if rel else a[k])
                    ys.append(py + a[k + 1] if rel else a[k + 1])
            x, y = (px + a[n - 2], py + a[n - 1]) if rel else (a[n - 2], a[n - 1])
        xs.append(x)
        ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def markers(svg_text):
    """[(centre_x, centre_y, half_width)] for every ۝ medallion, de-duplicated.

    The medallion's own outline gives its size, so nothing about the glyph is hard-coded.
    The opening spread draws each marker twice, hence the de-duplication.
    """
    mm = _MATRIX.search(svg_text)
    if not mm:
        return []
    a, b, c, d, e, f = [float(v) for v in mm.group(1).split()]
    k = svg_text.find('<g id="ayah_markers"')
    if k < 0:
        return []
    depth, end = 0, len(svg_text)
    for m in re.finditer(r"<g\b|</g>", svg_text[k:]):
        if m.group(0) == "</g>":
            depth -= 1
            if depth == 0:
                end = k + m.end()
                break
        else:
            depth += 1
    out = {}
    for g in _MARKER.finditer(svg_text[k:end]):
        tx, ty, sx, sy = [float(v) for v in g.groups()[:4]]
        ds = _D.findall(g.group(5))
        if not ds:
            continue
        bb = _glyph_bbox(ds[0])
        if bb is None:
            continue
        gx, gy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
        cx = a * (tx + sx * gx) + c * (ty + sy * gy) + e
        cy = b * (tx + sx * gx) + d * (ty + sy * gy) + f
        out[(round(cx, 3), round(cy, 3))] = round(abs(a * sx * (bb[2] - bb[0])) / 2, 3)
    return [(x, y, hw) for (x, y), hw in sorted(out.items(), key=lambda t: (t[0][1], -t[0][0]))]


def translation_fit(mk, entries, tol=1.5):
    """(matched, dx, dy) — the offset that carries markers.json into page space.

    Hafs, Douri and Shu'bah state their marker coordinates in page space, so the offset is
    zero.  Qalun and Warsh state theirs in a different frame, offset by a translation that
    varies from page to page.  Fit it by consensus rather than assuming either.
    """
    best = (0, 0.0, 0.0)
    for x, y, _ in mk:
        for e in entries:
            dx, dy = e["x"] - x, e["y"] - y
            n = sum(1 for mx, my, _ in mk
                    if any(abs(f["x"] - dx - mx) < tol and abs(f["y"] - dy - my) < tol
                           for f in entries))
            if n > best[0]:
                best = (n, dx, dy)
    return best


def recover_markers(mk, entries, tol=1.5):
    """(markers, recovered) — ayah ends whose ۝ rosette was never drawn.

    A few Qalun pages print an ayah end as a bare numeral with no rosette, so the glyph is
    absent from ``<g id="ayah_markers">`` even though the number is on the page.  Their
    ``markers.json`` states every ayah end but in a different coordinate frame, offset by a
    translation that varies from page to page.  Fit that translation by consensus and take
    only the entries it leaves unmatched.  The fit has to explain *every* rosette the page
    does draw, or it is not trusted and nothing is recovered.
    """
    if not mk or not entries:
        return mk, []
    n, dx, dy = translation_fit(mk, entries, tol)
    if n < len(mk):
        return mk, []
    half = sorted(t[2] for t in mk)[len(mk) // 2]
    added = [(round(e["x"] - dx, 3), round(e["y"] - dy, 3), half) for e in entries
             if not any(abs(e["x"] - dx - x) < 2.0 and abs(e["y"] - dy - y) < 2.0
                        for x, y, _ in mk)]
    return sorted(mk + added, key=lambda t: (t[1], -t[0])), added


# --------------------------------------------------------------------------- ink + line grid

def ink_mask(svg_path, z=Z):
    """Boolean mask of the page's ink, rendered at ``z`` pixels per page unit."""
    tmp = tempfile.mktemp(suffix=".png")
    try:
        subprocess.run(["rsvg-convert", "-z", str(z), svg_path, "-o", tmp], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return np.array(Image.open(tmp).convert("RGBA"))[..., 3] > 40
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def line_grid(mask, marker_ys, box, pitch=PITCH, z=Z):
    """(pitch, bands) — a uniform comb fitted to the ink and phase-locked to the markers,
    with every boundary then snapped to the ink minimum between its two lines."""
    x0, y0, _, _ = box
    prof = mask.sum(1).astype(float)
    ys = np.arange(len(prof)) / z + y0
    inked = ys[prof > 0]
    top, bot = inked.min(), inked.max()
    m = np.asarray(sorted(marker_ys), float)
    best = None
    for h in np.arange(pitch[0], pitch[1] + 1e-9, 0.02):
        coherence = abs(np.exp(1j * 2 * np.pi * (m % h) / h).mean()) if len(m) >= 2 else 1.0
        v = (prof * np.exp(1j * 2 * np.pi * (ys % h) / h)).sum() / max(prof.sum(), 1)
        s = coherence + 0.6 * abs(v)
        if best is None or s > best[0]:
            best = (s, h, v)
    _, h, v = best
    ang = np.angle(np.exp(1j * 2 * np.pi * (m % h) / h).mean()) if len(m) else np.angle(v)
    c0 = (ang % (2 * np.pi)) / (2 * np.pi) * h
    centres = [c0 + h * k for k in range(int(np.floor((top - c0) / h)),
                                         int(np.ceil((bot - c0) / h)) + 1)]
    centres = [c for c in centres if top - 0.55 * h < c < bot + 0.55 * h]
    edges = ([centres[0] - h / 2]
             + [(a + b) / 2 for a, b in zip(centres, centres[1:])]
             + [centres[-1] + h / 2])
    snapped = [edges[0]]
    for e in edges[1:-1]:
        lo = max(0, int((e - y0 - 0.28 * h) * z))
        hi = min(len(prof), int((e - y0 + 0.28 * h) * z))
        snapped.append((lo + int(np.argmin(prof[lo:hi]))) / z + y0 if hi > lo else e)
    snapped.append(edges[-1])
    snapped = [min(max(e, y0), y0 + box[3]) for e in snapped]      # never leave the page
    bands = []
    for a, b in zip(snapped, snapped[1:]):
        sl = mask[max(0, int((a - y0) * z)):int((b - y0) * z)]
        col = sl.sum(0)
        cols = np.where(col > INKCOL)[0]
        if not len(cols):
            continue
        bands.append(dict(top=a, bot=b, x0=cols.min() / z + x0, x1=cols.max() / z + x0,
                          ink=int(sl.sum()), col=col))
    # A comb fitted to 15 lines can put an extra tooth over the descenders hanging below the
    # last line -- a kasra under the final word is enough to inject a phantom sixteenth band,
    # which then reads as "the page ends mid-ayah".  Real lines carry at least a fifth of the
    # page's median ink; these specks carry well under a hundredth.
    if bands:
        floor = FAINT * float(np.median([b["ink"] for b in bands]))
        bands = [b for b in bands if b["ink"] >= floor]
    return h, bands


def text_margins(bands, box):
    """(left, right) — the justified block, padded on both sides by the smaller real margin."""
    x0, _, width, _ = box
    widest = max(b["x1"] - b["x0"] for b in bands)
    just = [b for b in bands if b["x1"] - b["x0"] >= JUST * widest] or bands
    lo, hi = min(b["x0"] for b in just), max(b["x1"] for b in just)
    pad = min(lo - x0, x0 + width - hi)
    return max(x0, lo - pad), min(x0 + width, hi + pad)


def decoration(bands, marker_bands, ayahs):
    """Bands that carry a surah header or a basmalah rather than ayah text.

    Such a band has no marker, is narrower than a justified line, and sits where the surah
    changes.  Warsh basmalahs reach 0.77 of the text width against 0.57 in Hafs, so the
    width test alone is not enough — the surah change is what makes it safe.
    """
    widest = max(b["x1"] - b["x0"] for b in bands)
    marked = set(marker_bands)
    decor = set()
    for i, (surah, ayah) in enumerate(ayahs):
        starts_surah = (i == 0 and ayah == 1) or (i > 0 and ayahs[i - 1][0] != surah)
        if not starts_surah:
            continue
        for j in range(0 if i == 0 else marker_bands[i - 1], marker_bands[i] + 1):
            if j in marked:
                continue
            if bands[j]["x1"] - bands[j]["x0"] < NARROW * widest:
                decor.add(j)
            else:
                break
    return decor


# --------------------------------------------------------------------------- the generator

def build_polygons(bands, mk, ayahs, box, tail_key=None, z=Z):
    """{key: [rect]} for one page, plus the margins, the decoration bands and any notes."""
    x0, _, width, _ = box

    def band_of(y):
        for i, b in enumerate(bands):
            if b["top"] <= y < b["bot"]:
                return i
        return min(range(len(bands)), key=lambda i: abs((bands[i]["top"] + bands[i]["bot"]) / 2 - y))

    marks = sorted(mk, key=lambda m: (band_of(m[1]), -m[0]))
    ends = [band_of(m[1]) for m in marks]
    left, right = text_margins(bands, box)
    decor = decoration(bands, ends, ayahs)
    text = [i for i in range(len(bands)) if i not in decor]
    if not text:
        raise ValueError("no text bands on this page")

    def ayah_end(band, centre, half):
        """Where the ayah's highlight ends: the midpoint of the whitespace immediately left
        of its medallion, or the medallion's own edge when the next glyph touches it.  The
        scan never crosses ink — medallions frequently touch the neighbouring letters, and
        skipping ink would swallow the next ayah's first word.  None means the line ends."""
        col = bands[band]["col"]
        edge = centre - half
        i = min(int((edge - x0 - 0.5) * z), len(col) - 1)
        if i < 0:
            return None
        if col[i] > INKCOL:
            return edge
        first_empty = i
        while i >= 0 and col[i] <= INKCOL:
            i -= 1
        return None if i < 0 else ((first_empty + i) / 2 + 0.5) / z + x0

    out, notes = {}, []
    band, cursor = text[0], right
    for i, key in enumerate(ayahs):
        end = max(ends[i], band)
        if ends[i] < band:
            notes.append("%d:%d marker sits above the previous ayah" % key)
        gap = ayah_end(end, marks[i][0], marks[i][2])
        ends_line = gap is None
        stop = left if ends_line else max(left, gap)
        rects = []
        run = [j for j in text if band <= j <= end]
        for j in run:
            hi = cursor if j == run[0] else right
            lo = stop if j == end else left
            if hi - lo > EPS:
                rects.append([lo, bands[j]["top"], hi, bands[j]["bot"]])
        if ends_line and rects:
            rects[-1][0] = left
        out["%d:%d" % key] = rects
        if ends_line:
            later = [j for j in text if j > end]
            band, cursor = (later[0] if later else end + 1), right
        else:
            band, cursor = end, stop

    tail = []
    if cursor > left + EPS and band in text:
        tail.append([left, bands[band]["top"], cursor, bands[band]["bot"]])
    tail += [[left, bands[j]["top"], right, bands[j]["bot"]] for j in text if j > band]
    if tail:
        if tail_key:
            out[tail_key] = tail
        else:
            notes.append("page ends mid-ayah but the continuing ayah is unknown")
    return out, (left, right), decor, notes, bool(tail)


def merge_rects(rects):
    """Merge vertically adjacent rects of equal width, as the shipped files do."""
    out = []
    for r in rects:
        if (out and abs(out[-1][3] - r[1]) < EPS
                and abs(out[-1][0] - r[0]) < EPS and abs(out[-1][2] - r[2]) < EPS):
            out[-1][3] = r[3]
        else:
            out.append(list(r))
    return out


def _num(v):
    return ("%.2f" % v).rstrip("0").rstrip(".") if abs(v - round(v, 1)) > 1e-9 else "%.1f" % v


def path_d(rects):
    """The ``d`` attribute for a stack of rects, in the shipped files' own style."""
    return " ".join("M %s %s L %s %s L %s %s L %s %s Z"
                    % (_num(r[0]), _num(r[1]), _num(r[2]), _num(r[1]),
                       _num(r[2]), _num(r[3]), _num(r[0]), _num(r[3])) for r in rects)


# --------------------------------------------------------------------------- scoring

def band_spans(rects, top, bot):
    """The x-intervals a rect list claims on one band.  A rect counts only when it covers
    more than half the band, so a vertical offset between two data sets cannot file the
    same rect under two bands."""
    height = bot - top
    intervals = sorted((r[0], r[2]) for r in rects
                       if min(r[3], bot) - max(r[1], top) > 0.5 * height)
    out = []
    for a, b in intervals:
        if out and a <= out[-1][1] + EPS:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def score(polygons, bands, decor, mask, mk, box, ordered_keys=None, z=Z):
    """The four invariants, as numbers: unowned ink, overlap, and stray markers."""
    x0, y0, _, _ = box
    covered = np.zeros(mask.shape, bool)
    for rects in polygons.values():
        for r in rects:
            covered[max(0, int((r[1] - y0) * z)):int((r[3] - y0) * z),
                    max(0, int((r[0] - x0) * z)):int((r[2] - x0) * z)] = True
    keep = np.zeros(mask.shape, bool)
    for i, b in enumerate(bands):
        if i in decor:
            continue
        keep[max(0, int((b["top"] - y0) * z)):int((b["bot"] - y0) * z)] = True
    uncovered = int((mask & keep & ~covered).sum())

    flat = [(k, r) for k, rects in polygons.items() for r in rects]
    area, pairs = 0.0, 0
    for i in range(len(flat)):
        ka, ra = flat[i]
        for j in range(i + 1, len(flat)):
            kb, rb = flat[j]
            if ka == kb:
                continue
            ox = min(ra[2], rb[2]) - max(ra[0], rb[0])
            oy = min(ra[3], rb[3]) - max(ra[1], rb[1])
            if ox > 0.05 and oy > 0.05:
                area += ox * oy
                pairs += 1

    stray = 0
    keys = [k for k in (ordered_keys or list(polygons)) if k in polygons]
    if len(mk) == len(keys):
        def nearest(y):
            return min(range(len(bands)),
                       key=lambda i: abs((bands[i]["top"] + bands[i]["bot"]) / 2 - y))
        for key, m in zip(keys, sorted(mk, key=lambda t: (nearest(t[1]), -t[0]))):
            if not any(r[0] - EPS <= m[0] <= r[2] + EPS and r[1] - EPS <= m[1] <= r[3] + EPS
                       for r in polygons[key]):
                stray += 1
    return dict(uncovered_ink=uncovered, overlap_area=round(area, 1),
                overlap_pairs=pairs, stray_markers=stray)
