#!/usr/bin/env python3
"""Cut each ayah polygon at the line boundaries, so no rectangle spans two lines.

A verse's tap region is stored as a rectilinear polygon covering the words it occupies.
Where a verse runs over several whole lines, that is currently expressed as **one tall
rectangle**: on `hafs/048`, verse 2:282 is three rectangles and the middle one spans all
fifteen lines at once.

That is fine for hit-testing a page drawn exactly as printed, and wrong for anything that
treats a page as lines. A consumer that spreads the lines to fill a screen, highlights a
verse line by line, or reflows the page has to give each rectangle one line's offset — and a
rectangle covering fifteen lines can only be given one. The result is a selection wash that
sits correct in the middle of a long verse and drifts at both ends, which is what
`quranpedia.ios` hit and worked around by clipping every polygon itself.

Now that the pages carry `<g class="line" data-line="N">` the generator knows where the
lines are, so the split belongs here: done once, correctly, for every consumer, instead of
reinvented by each.

## What it does and does not change

It is a pure subdivision. The union of the rectangles a verse covers is identical before and
after — same area, same coverage, no polygon gains or loses a pixel. Only the number of
rectangles changes, and each one afterwards lies inside exactly one line band.

The polygons are rectilinear — verified across all five editions, 6,247 rings, not one edge
off the axes — so slicing them at horizontal cuts is exact rather than an approximation. A
scanline through the middle of each slab recovers the covered x-intervals under the even-odd
rule SVG fills with by default.

Both copies are rewritten: the `<path class="ayahPolygon">` elements in the SVG and the
`polygon` strings in `json/NNN.json`. They are the same geometry and must not diverge.

Usage:

    tools/split_ayah_polygons.py                       # every mushaf
    tools/split_ayah_polygons.py --mushaf hafs/kfqc    # one edition
    tools/split_ayah_polygons.py --check               # verify only, write nothing

`--check` re-derives the union both ways and fails on any disagreement, so a run that
reports nothing has proved the subdivision lossless rather than assumed it.

Re-running is safe: splitting an already-split polygon is a no-op, because every rectangle
already lies within one band and no cut falls inside it.
"""

import argparse
import json
import os
import re
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from add_line_structure import refresh_brotli                             # noqa: E402
from svg_lines import fmt                                                 # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mushafs")

# Coordinates closer than this are the same edge. The polygons are written to two decimals,
# so anything below half a unit in the last place is rounding, not geometry.
EPS = 1e-6

POLYGON_RE = re.compile(r'(<path\b[^>]*\bclass="ayahPolygon"[^>]*\bd=")([^"]*)(")')


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

def rings(polygon):
    """`M x y L … Z` groups as vertex lists, in the order they were written."""
    out = []
    for body in re.findall(r"M([^MZ]+)Z", polygon):
        nums = [float(v) for v in re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", body)]
        pts = list(zip(nums[0::2], nums[1::2]))
        if len(pts) >= 3:
            out.append(pts)
    return out


def is_rectilinear(pts):
    """Every edge axis-aligned. True of every ring in the corpus; asserted, not assumed."""
    for i, (x0, y0) in enumerate(pts):
        x1, y1 = pts[(i + 1) % len(pts)]
        if abs(x0 - x1) > EPS and abs(y0 - y1) > EPS:
            return False
    return True


def spans_at(all_rings, y):
    """The x-intervals the polygon covers at height `y`, under the even-odd rule.

    Only vertical edges can cross a horizontal ray on a rectilinear polygon, so this is an
    exact crossing count rather than a sampled one. Half-open in y (`y0 <= y < y1`) so a
    vertex shared by two edges is counted once.
    """
    xs = []
    for pts in all_rings:
        for i, (x0, y0) in enumerate(pts):
            x1, y1 = pts[(i + 1) % len(pts)]
            if abs(x0 - x1) > EPS:
                continue                      # horizontal edge, cannot cross the ray
            lo, hi = (y0, y1) if y0 <= y1 else (y1, y0)
            if lo - EPS <= y < hi - EPS:
                xs.append(x0)
    xs.sort()
    out = []
    for i in range(0, len(xs) - 1, 2):
        if xs[i + 1] - xs[i] > EPS:
            out.append((xs[i], xs[i + 1]))
    return merge(out)


def merge(intervals):
    """Coalesce touching or overlapping x-intervals."""
    if not intervals:
        return []
    intervals = sorted(intervals)
    out = [list(intervals[0])]
    for lo, hi in intervals[1:]:
        if lo <= out[-1][1] + EPS:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return [tuple(v) for v in out]


def split_polygon(polygon, cuts):
    """Subdivide at every horizontal `cut` that crosses the polygon.

    Returns rectangles as `(x0, y0, x1, y1)`, top to bottom then left to right, so the
    output order is stable and a consumer reading it sequentially reads the verse in
    reading order.
    """
    all_rings = rings(polygon)
    if not all_rings:
        return []
    for pts in all_rings:
        if not is_rectilinear(pts):
            raise ValueError("polygon is not rectilinear; slab decomposition would be lossy")

    ys = {y for pts in all_rings for _, y in pts}
    lo, hi = min(ys), max(ys)
    ys.update(c for c in cuts if lo + EPS < c < hi - EPS)
    edges = sorted(ys)

    rects = []
    for y0, y1 in zip(edges, edges[1:]):
        if y1 - y0 <= EPS:
            continue
        for x0, x1 in spans_at(all_rings, (y0 + y1) / 2):
            rects.append((x0, y0, x1, y1))
    return rects


def to_path(rects):
    """Rectangles back to the `M … Z` form the files already use."""
    return " ".join(
        "M {} {} L {} {} L {} {} L {} {} Z".format(
            fmt(x0), fmt(y0), fmt(x1), fmt(y0), fmt(x1), fmt(y1), fmt(x0), fmt(y1)
        )
        for x0, y0, x1, y1 in rects
    )


def coverage(polygon):
    """A canonical description of the filled region, for proving nothing moved.

    Slabs keyed by their y-range, each holding merged x-intervals. Two polygons covering the
    same area produce the same structure however they are cut up, which is what makes this a
    proof of equality rather than a comparison of the text.
    """
    all_rings = rings(polygon)
    if not all_rings:
        return []
    edges = sorted({y for pts in all_rings for _, y in pts})
    out = []
    for y0, y1 in zip(edges, edges[1:]):
        if y1 - y0 <= EPS:
            continue
        spans = spans_at(all_rings, (y0 + y1) / 2)
        if spans:
            out.append((round(y0, 4), round(y1, 4),
                        tuple((round(a, 4), round(b, 4)) for a, b in spans)))
    return merge_slabs(out)


def merge_slabs(slabs):
    """Join vertically adjacent slabs with identical x-intervals, so the form is canonical."""
    out = []
    for y0, y1, spans in slabs:
        if out and abs(out[-1][1] - y0) <= EPS and out[-1][2] == spans:
            out[-1] = (out[-1][0], y1, spans)
        else:
            out.append((y0, y1, spans))
    return out


# ---------------------------------------------------------------------------
# One page
# ---------------------------------------------------------------------------

def line_cuts(lines_path):
    """The horizontal boundaries between lines, from the generated line bands."""
    if not os.path.exists(lines_path):
        return None
    bands = json.load(open(lines_path, encoding="utf-8"))
    if len(bands) < 2:
        return None
    # Interior boundaries only: a cut at the top of the first line or the bottom of the last
    # would slice off a sliver above or below the text rather than separate two lines.
    return [b["top"] for b in bands[1:]]


def process_page(args):
    svg_path, json_path, lines_path, check = args
    name = os.path.basename(svg_path)
    cuts = line_cuts(lines_path)
    if cuts is None:
        return {"file": name, "skipped": "no line bands"}

    try:
        entries = json.load(open(json_path, encoding="utf-8")) if os.path.exists(json_path) else []
    except (OSError, ValueError) as exc:
        return {"file": name, "error": str(exc)}

    svg = open(svg_path, encoding="utf-8").read()

    before = after = 0
    changed_json = False
    mismatches = []

    for entry in entries:
        original = entry.get("polygon", "")
        if not original:
            continue
        try:
            rects = split_polygon(original, cuts)
        except ValueError as exc:
            return {"file": name, "error": str(exc)}
        rebuilt = to_path(rects)
        before += len(rings(original))
        after += len(rects)
        if coverage(original) != coverage(rebuilt):
            mismatches.append("%d:%d" % (entry.get("surahNumber"), entry.get("ayahNumber")))
        if rebuilt != original:
            changed_json = True
            if not check:
                entry["polygon"] = rebuilt

    # The SVG carries the same polygons; they must not drift apart from the JSON.
    svg_changed = False

    def replace(m):
        nonlocal svg_changed, mismatches
        head, d, tail = m.groups()
        try:
            rebuilt = to_path(split_polygon(d, cuts))
        except ValueError:
            return m.group(0)
        if coverage(d) != coverage(rebuilt):
            mismatches.append("svg")
            return m.group(0)
        if rebuilt != d:
            svg_changed = True
        return head + rebuilt + tail

    new_svg = POLYGON_RE.sub(replace, svg)

    if mismatches:
        return {"file": name, "error": "coverage changed for " + ", ".join(sorted(set(mismatches))[:6])}

    if not check:
        if changed_json:
            with open(json_path, "w", encoding="utf-8") as fh:
                json.dump(entries, fh, ensure_ascii=False)
        if svg_changed:
            with open(svg_path, "w", encoding="utf-8") as fh:
                fh.write(new_svg)

    return {"file": name, "before": before, "after": after,
            "changed": changed_json or svg_changed}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def editions(only):
    out = []
    for mushaf in sorted(os.listdir(ROOT)):
        mdir = os.path.join(ROOT, mushaf)
        if not os.path.isdir(mdir):
            continue
        for pub in sorted(os.listdir(mdir)):
            rel = "%s/%s" % (mushaf, pub)
            if only and rel != only:
                continue
            if os.path.isdir(os.path.join(mdir, pub, "svg")):
                out.append(rel)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mushaf", help="only this edition, e.g. hafs/kfqc")
    ap.add_argument("--check", action="store_true", help="verify only, write nothing")
    ap.add_argument("--no-brotli", action="store_true", help="do not refresh svg-br/")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    args = ap.parse_args()

    failures = 0
    for rel in editions(args.mushaf):
        base = os.path.join(ROOT, rel)
        tasks = []
        for name in sorted(os.listdir(os.path.join(base, "svg"))):
            if not name.endswith(".svg") or re.search(r"\d+-surah", name):
                continue
            stem = os.path.splitext(name)[0]
            tasks.append((
                os.path.join(base, "svg", name),
                os.path.join(base, "json", stem + ".json"),
                os.path.join(base, "lines", stem + ".json"),
                args.check,
            ))

        with Pool(args.jobs) as pool:
            results = pool.map(process_page, tasks)

        errors = [r for r in results if "error" in r]
        skipped = [r for r in results if "skipped" in r]
        done = [r for r in results if "before" in r]
        before = sum(r["before"] for r in done)
        after = sum(r["after"] for r in done)
        changed = sum(1 for r in done if r["changed"])

        print("%-16s pages %3d   rectangles %5d -> %5d   pages changed %3d%s%s" % (
            rel, len(done), before, after, changed,
            "   skipped %d" % len(skipped) if skipped else "",
            "   ERRORS %d" % len(errors) if errors else "",
        ))
        for r in errors[:5]:
            print("     %s: %s" % (r["file"], r["error"]))
        failures += len(errors)

        # `svg-br/` is a compressed copy of `svg/`; leaving it stale would serve the
        # unsplit polygons to anyone reading the Brotli files. Same helper and same
        # settings as the line generator, so an untouched page still round-trips.
        if not args.check and not args.no_brotli and not errors:
            touched = [r["file"] for r in done if r["changed"]]
            if touched:
                refresh_brotli(base, touched, args.jobs)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
