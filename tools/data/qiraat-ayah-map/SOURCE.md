# Vendored data

`counting-systems.json`, `qiraat.json` and `book-boundary-primitives.json` are copied
verbatim from [quranpedia/qiraat-ayah-map](https://github.com/quranpedia/qiraat-ayah-map)
(MIT). Commit cb70a73 on branch `fix/madani-first-al-dani`, fetched 2026-08-25.

That branch is **quranpedia/qiraat-ayah-map#10**, not yet merged. It corrects the First
Madinan total from 6214 (which is the *Last* Madinan total) to 6217, the figure al-Dani
states in `al-Bayan`, and drops three boundary points that every madhhab counts and only
Abu Ja'far omits. Re-vendor from `main` once that PR lands; the files should be identical.

They map ayah numbering between the six canonical counting systems. `tools/qiraat_map.py`
uses them to derive each counting system's per-surah ayah counts from the Kufan reference,
so the audit can check that a mushaf's ayah identities match the counting system its
qiraa actually follows.
