# #2190 Pack vs box (research)

**Agent:** grok-xai  
**Question:** when does sequential bit packing repay itself vs one-byte-per-word boxes?

```sh
python3 benchmarks/pack-vs-box/pack_vs_box.py
```

## Density (authoritative here)

| kind | density gain (box / pack bytes) |
|------|--------------------------------:|
| D1 (1-bit) | **×8** |
| D2 (2-bit) | **×4** |
| D3 (3-bit) | **×2.67** |
| mixed D1/D2/D3 | **~×4** |
| Bit8 | **×1** (no win) |

## Threshold sketch (not production law)

```text
hot scalar runtime     → box (Bits<N> as u8)
cold AST / wire / FPGA → pack for D1–D3
Bit8 bulk              → packing free lunch absent
```

Wall µs are diagnostic only. Does not own #2208 BitPacker adapter or D5 research.
