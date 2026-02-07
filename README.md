# Quran SVG

High-quality Quran SVG pages with **clickable ayah polygons** for all major Qira'at readings.

## Mushafs Included

| Mushaf | Qira'a | Rawi | Pages | Count System |
|--------|--------|------|-------|--------------|
| Hafs | Asim | Hafs | 604 | Kufi (6,236) |
| Warsh | Nafi' | Warsh | 604 | Madani (6,214) |
| Qalun | Nafi' | Qalun | 604 | Madani (6,214) |
| Douri | Abu Amr | Al-Douri | 604 | Basri (6,205) |
| Shubah | Asim | Shu'bah | 604 | Kufi (6,236) |

## Why SVG?

- **Scalable**: Vector graphics that look crisp at any zoom level
- **Interactive**: Embedded polygon paths enable clickable ayah regions
- **Lightweight**: [Brotli](https://github.com/google/brotli)-compressed versions are ~83% smaller than originals
- **Semantic**: Each ayah has metadata attributes (surah, ayah number, verse ID)

## File Structure

```
mushafs/
├── hafs/
│   ├── svg/           # Uncompressed SVG files (001.svg - 604.svg)
│   ├── svg-br/        # Brotli-compressed SVGs (~83% smaller)
│   └── json/          # Polygon metadata for each page
├── warsh/
├── douri/
├── qalon/
└── shubah/
```

### Special Page Variants

Pages containing multiple surahs have surah-specific variants:

```
106.svg           # Full page (Surah 4 ending + Surah 5 beginning)
106-surah4.svg    # Only Surah An-Nisa (4) portion
106-surah5.svg    # Only Surah Al-Ma'idah (5) portion
```

## SVG Structure

Each SVG contains the Quran text as paths, plus transparent clickable polygons for each ayah:

```xml
<path
  class="ayahPolygon"
  id="verse-1"
  number="001001"        <!-- 6-digit: SSSAAA (surah + ayah) -->
  surah="1"
  ayah="1"
  d="M 5.0 5.75 L 340.0 5.75 L 340.0 43.93 L 5.0 43.93 Z"
  fill-opacity="0"
/>
```

### Recommended CSS

```css
.ayahPolygon {
  fill: transparent;
  fill-opacity: 0;
  cursor: pointer;
  transition: fill-opacity 0.2s ease;
  mix-blend-mode: multiply;
}

.ayahPolygon:hover {
  fill: #f5e6a3;
  fill-opacity: 0.8;
}
```

### JavaScript Click Handler

```javascript
document.querySelectorAll('.ayahPolygon').forEach(polygon => {
  polygon.addEventListener('click', (e) => {
    const surah = e.target.getAttribute('surah');
    const ayah = e.target.getAttribute('ayah');
    console.log(`Clicked: Surah ${surah}, Ayah ${ayah}`);
  });
});
```

## JSON Metadata Format

Each JSON file contains polygon data for its corresponding page:

```json
{
  "page": 3,
  "mushaf_id": 1,
  "polygons": [
    {
      "id": "verse-1",
      "number": "002001",
      "surah": 2,
      "ayah": 1,
      "line": 1,
      "bounds": { "x": 5.0, "y": 5.75, "width": 335.0, "height": 38.18 },
      "path": "M 5.0 5.75 L 340.0 5.75 ..."
    }
  ]
}
```

## Serving Brotli-Compressed Files

[Brotli](https://github.com/google/brotli) is a compression algorithm developed by Google. Learn more about [serving Brotli files](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Encoding).

```nginx
# Nginx
location /quran-svg/ {
  brotli_static on;
  add_header Content-Type image/svg+xml;
}
```

```php
// PHP/Laravel
public function serveSvg(string $mushaf, int $page)
{
    $pageNum = str_pad($page, 3, '0', STR_PAD_LEFT);

    if (str_contains(request()->header('Accept-Encoding', ''), 'br')) {
        $path = "mushafs/{$mushaf}/svg-br/{$pageNum}.svg.br";
        return response(file_get_contents($path))
            ->header('Content-Type', 'image/svg+xml')
            ->header('Content-Encoding', 'br');
    }

    return response(file_get_contents("mushafs/{$mushaf}/svg/{$pageNum}.svg"))
        ->header('Content-Type', 'image/svg+xml');
}
```

---

## ⚠️ Ayah Counting Systems

**Important:** Different Qira'at use different ayah counting systems. The `number` attribute in our SVGs uses each mushaf's **native counting system**.

### Why Counts Differ

The differences arise from scholarly opinions on:
- Whether the Basmala counts as a separate ayah
- Where long passages should be divided
- Treatment of disconnected letters (الحروف المقطعة)

### Example: Surah Al-Fatihah (Ayah 1)

| Mushaf | Ayah 1 Text |
|--------|-------------|
| Hafs | بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ |
| Douri | الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ |

Both have 7 ayahs total, but the numbering is shifted throughout the surah.

### Mapping Recommendation

When building applications supporting multiple Qira'at, maintain a mapping table to convert between counting systems. Store a universal ayah ID (e.g., Hafs-based) in your database and map to other Qira'at for display.

---

## Sources & Credits

### Primary Source

**King Fahd Complex for Printing the Holy Quran**
- https://dm.qurancomplex.gov.sa/
- Original format: Adobe Illustrator (.ai)
- License: Free for Islamic purposes

### Inspiration & Thanks

- **[batoulapps/quran-svg](https://github.com/batoulapps/quran-svg)** - Inspiration for the SVG polygon approach
- **[Itqan.dev](https://itqan.dev/)** - Community support and feedback

## License

The Quran text and its representation are free for all Islamic purposes.

## Contributing

Contributions welcome:
- Bug fixes in polygon positioning
- Additional Qira'at readings
- Documentation improvements

---

Built with ❤️ for the Muslim Ummah by [Quranpedia.net](https://quranpedia.net)
