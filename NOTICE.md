# NOTICE — Sources, Attribution & Usage Terms

This repository contains vector (SVG) renderings of Qur'an mushaf pages together with a
transparent, clickable ayah‑polygon layer and per‑page JSON metadata. Please read the
following before using the material.

## 1. The Qur'anic text itself

The text of the Holy Qur'an (the ʿUthmānī rasm) is the revealed Word of Allah. It is **not
subject to copyright** and may be freely reproduced. However, it **must never be altered,
truncated, or misrepresented**, and it must be handled with the respect (ḥurmah) due to it
under Islamic rulings. Any use that distorts the text or is disrespectful to it is not
permitted.

## 2. Mushaf sources (page layouts & calligraphy)

While the *text* is free, each mushaf's **page composition, calligraphy/typeface, and layout**
are the work of its publisher. The pages in this repository are derived from the following
editions:

| Qiraa'a | Rawi | Publisher / Edition | Folder |
|---------|------|---------------------|--------|
| ʿĀṣim | Ḥafṣ | King Fahd Glorious Qur'an Printing Complex, Madinah (KFQC) — مجمع الملك فهد لطباعة المصحف الشريف | `mushafs/hafs/kfqc` |
| Nāfiʿ | Warsh | King Fahd Glorious Qur'an Printing Complex, Madinah (KFQC) | `mushafs/warsh/kfqc` |
| Nāfiʿ | Qālūn | King Fahd Glorious Qur'an Printing Complex, Madinah (KFQC) | `mushafs/qalon/kfqc` |
| Nāfiʿ | Qālūn | Libyan Ministry of Endowments (Awqaf) — مصحف الأوقاف الليبي | `mushafs/qalon/libya-awqaf` |
| Abū ʿAmr | Al‑Dūrī | King Fahd Glorious Qur'an Printing Complex, Madinah (KFQC) | `mushafs/douri/kfqc` |
| ʿĀṣim | Shuʿbah | King Fahd Glorious Qur'an Printing Complex, Madinah (KFQC) | `mushafs/shubah/kfqc` |

All rights in the original mushaf editions remain with their respective publishers.

## 3. Usage terms

### Non‑commercial use — permitted, free
All of the mushafs included here are **free to use for non‑commercial purposes** — such as
personal study, teaching, daʿwah, research, and free (non‑paid) software and websites —
**in a manner that does not conflict with the rulings of Islam** and that preserves the
integrity and sanctity of the Qur'anic text. The publishers make these mushafs available for
the benefit of Muslims worldwide on this basis.

### Commercial use — check with each publisher first
For **any commercial use** (selling, bundling into a paid product, printing for sale,
advertising‑driven distribution, etc.), the mushaf editions are **not automatically licensed**.
You **must obtain permission directly from the publisher of each mushaf you intend to use**:

- **King Fahd Glorious Qur'an Printing Complex (KFQC), Madinah** — <https://qurancomplex.gov.sa>
  (contact the Complex for reproduction/commercial‑use permissions).
- **Libyan Ministry of Endowments and Islamic Affairs (Awqaf)** — for the Libyan Qālūn mushaf.

The maintainers of this repository cannot grant commercial rights over the underlying mushaf
editions; only each publisher can.

## 4. This repository's own contribution (dual‑licensed)

- **Numbering & boundary data** — everything under `mushafs/**/json/` (per‑page polygons,
  `surah.json`, `markers.json`): the per‑riwaya ayah counts, ayah↔page mapping, and
  hit‑region coordinates are **facts** about the mushaf and are dedicated to the public
  domain under **CC0 1.0** (see `DATA-LICENSE`). Reuse freely — including commercially, with
  no attribution required — so this data can serve as a clean foundation for an open,
  shared Qur'anic‑data standard.
- **Rendered page art** — the SVG page glyphs and their Brotli copies under `svg/` and
  `svg-br/` derive from the publishers' mushaf editions and are licensed under
  **CC BY‑NC‑SA 4.0** (see `LICENSE`), consistent with the non‑commercial terms of those
  sources. Attribution to *Quranpedia — quran‑svg* is appreciated.

## 5. Disclaimer

The material is provided "as is", for the service of the Book of Allah. If you find any error
in a page or its metadata, please open an issue so it can be corrected promptly.
