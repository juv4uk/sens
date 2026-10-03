# Dense packing efficiency — #2190

Cachegrind median of 3 paired runs; 65,536 words/case; 4 scans for scan lanes.

Widths are supplied out-of-band to both representations. This measures payload mechanics only; it does not choose #2189 framing.

| case | bits/word | bytes u8 | bytes packed | density | encode I/word | decode-once I/word | scan u8 I/word | scan packed I/word | scan cache I/word | packed/u8 | cache crossover passes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| w1 | 1.000 | 65,536 | 8,192 | x8.000 | 59.760 | 43.009 | 10.001 | 43.000 | 10.000 | x4.300 | 1.30 |
| w2 | 2.000 | 65,536 | 16,384 | x4.000 | 93.510 | 53.009 | 10.001 | 53.000 | 10.000 | x5.299 | 1.23 |
| w3 | 3.000 | 65,536 | 24,576 | x2.667 | 116.269 | 54.009 | 10.001 | 54.000 | 10.000 | x5.399 | 1.23 |
| w4 | 4.000 | 65,536 | 32,768 | x2.000 | 139.009 | 53.009 | 10.001 | 53.000 | 10.000 | x5.299 | 1.23 |
| w5 | 5.000 | 65,536 | 40,960 | x1.600 | 161.687 | 55.009 | 10.001 | 55.000 | 10.000 | x5.499 | 1.22 |
| w6 | 6.000 | 65,536 | 49,152 | x1.333 | 184.375 | 55.009 | 10.001 | 55.000 | 10.000 | x5.499 | 1.22 |
| w7 | 7.000 | 65,536 | 57,344 | x1.143 | 207.098 | 56.009 | 10.001 | 56.000 | 10.000 | x5.599 | 1.22 |
| w8 | 8.000 | 65,536 | 65,536 | x1.000 | 233.824 | 50.009 | 10.001 | 50.000 | 10.000 | x4.999 | 1.25 |
| d1234 | 2.750 | 65,536 | 22,528 | x2.909 | 109.656 | 53.050 | 10.001 | 53.042 | 10.000 | x5.304 | 1.23 |
| mixed18 | 4.500 | 65,536 | 36,864 | x1.778 | 149.432 | 53.134 | 10.001 | 53.125 | 10.000 | x5.312 | 1.23 |

Interpretation:
- bytes u8 is one payload byte per logical word; width schedule is external.
- bytes packed is the production sequential BitPacker payload lower bound.
- encode cost is prepare-packed minus prepare-logical.
- decode-once cost is prepare-cached minus prepare-packed.
- scan costs subtract their representation-specific preparation path.
- cache crossover asks when one packed-to-u8 decode is cheaper than repeatedly bit-reading packed data.
- raw branch counts and all repetitions are in raw.tsv / summary.tsv.
