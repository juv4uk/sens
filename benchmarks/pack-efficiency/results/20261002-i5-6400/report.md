# Dense packing efficiency — #2190

Cachegrind median of 3 paired runs; 65,536 words/case; 4 scans for scan lanes.

Widths are supplied out-of-band to both representations. This measures payload mechanics only; it does not choose #2189 framing.

| case | bits/word | bytes u8 | bytes packed | density | encode I/word | decode-once I/word | scan u8 I/word | scan packed I/word | scan cache I/word | packed/u8 | cache crossover passes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| w1 | 1.000 | 65,536 | 8,192 | x8.000 | 43.760 | 76.009 | 10.001 | 76.000 | 10.000 | x7.599 | 1.15 |
| w2 | 2.000 | 65,536 | 16,384 | x4.000 | 69.510 | 102.009 | 10.001 | 102.000 | 10.000 | x10.199 | 1.11 |
| w3 | 3.000 | 65,536 | 24,576 | x2.667 | 92.269 | 125.009 | 10.001 | 125.000 | 10.000 | x12.499 | 1.09 |
| w4 | 4.000 | 65,536 | 32,768 | x2.000 | 115.008 | 148.009 | 10.001 | 148.000 | 10.000 | x14.798 | 1.07 |
| w5 | 5.000 | 65,536 | 40,960 | x1.600 | 137.687 | 171.009 | 10.001 | 171.000 | 10.000 | x17.098 | 1.06 |
| w6 | 6.000 | 65,536 | 49,152 | x1.333 | 160.374 | 194.009 | 10.001 | 194.000 | 10.000 | x19.398 | 1.05 |
| w7 | 7.000 | 65,536 | 57,344 | x1.143 | 183.098 | 217.009 | 10.001 | 217.000 | 10.000 | x21.697 | 1.05 |
| w8 | 8.000 | 65,536 | 65,536 | x1.000 | 210.824 | 238.009 | 10.001 | 238.000 | 10.000 | x23.797 | 1.04 |
| d1234 | 2.750 | 65,536 | 22,528 | x2.909 | 86.323 | 119.009 | 10.001 | 119.001 | 10.000 | x11.899 | 1.09 |
| mixed18 | 4.500 | 65,536 | 36,864 | x1.778 | 126.556 | 158.884 | 10.001 | 158.875 | 10.000 | x15.886 | 1.07 |

Interpretation:
- bytes u8 is one payload byte per logical word; width schedule is external.
- bytes packed is the production sequential BitPacker payload lower bound.
- encode cost is prepare-packed minus prepare-logical.
- decode-once cost is prepare-cached minus prepare-packed.
- scan costs subtract their representation-specific preparation path.
- cache crossover asks when one packed-to-u8 decode is cheaper than repeatedly bit-reading packed data.
- raw branch counts and all repetitions are in raw.tsv / summary.tsv.
