# #2000 — first unbounded-width scaling smoke

Research-only. No production carrier or semantic migration.

## What was tested

The C carrier structs have no language-level maximum width. The smoke selected:

```text
64, 65, 128, 255, 256, 257, 1024, 4096 bits
```

`4096` is only a test point.

Every invocation first checked:
- exact-width equality;
- equal numeric zero at adjacent widths remains a different identity;
- append(bit) followed by parent restores the original;
- original word remains an exact prefix of its appended child;
- leading width information survives.

All checks passed.

## First semantic result

No semantic cliff was observed at:

```text
64 -> 65
255 -> 256 -> 257
1024 -> 4096
```

The small-inline+spill carrier has a physical 64->65 transition, but the identity law does not change.

## Representative Cachegrind I refs/op

### Equality

```text
width    heap-bytes    small-inline+spill
64          71.5              52.4
65          71.5              76.4
128         71.4              76.4
255         69.4              74.4
256         69.4              74.4
257         69.4              74.4
1024        81.4              86.5
4096       141.4             146.5
```

### Prefix

```text
width    heap-bytes    small-inline+spill
64        1423.5             1804.5
65        1443.5             2415.5
128       2703.5             4620.5
255       5243.5             9065.5
256       5263.5             9100.5
257       5283.5             9135.5
1024     20623.4            35980.4
4096     82063.4           143500.4
```

### Append one bit

```text
width    heap-bytes    small-inline+spill
64        2208.6             2219.7
65        2234.6             2440.7
128       3870.6             4265.6
255       7173.6             7949.7
256       7199.6             7978.7
257       7225.6             8007.7
1024     27209.7            30292.6
4096    107152.7           119451.7
```

The long-word prefix/append reference implementations intentionally walk bits one by one. Their large slopes are therefore a mechanism falsifier, not a semantic objection.

## Allocation result

For heap/spilled append, the first implementation allocates one new payload per operation:

```text
64   -> 9 bytes
128  -> 17 bytes
256  -> 33 bytes
1024 -> 129 bytes
4096 -> 513 bytes
```

Equality and prefix allocate zero in the measured loop.

## Interpretation

The first important claim survives:

> longer bounded words are mechanically more expensive, but do not cross a semantic width cliff.

The next carrier question is not “should long meanings be forbidden?” but:

> which chunked/bytewise representation makes parent/prefix/append scale better?

## Next falsifier

Add a chunk-aware candidate that:
- compares aligned prefix bytes before tail bits;
- appends without rebuilding every prior bit;
- shares/copies chunks or uses amortized storage;
- preserves exact width and leading zeros.

If that candidate removes the current O(width)-per-bit overhead while preserving all identity properties, the present slope is confirmed as prototype-algorithm cost rather than language-law cost.

Raw evidence: `docs/research/2000-unbounded-width.tsv`.
