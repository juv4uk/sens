# #2190 Pack vs box (research)

**Agent:** grok-xai  
**Question:** when does sequential bit packing repay itself vs one-byte-per-word boxes?

```sh
python3 benchmarks/pack-vs-box/pack_vs_box.py
```

## Density (authoritative here)

| kind | density gain (box bytes / pack bytes) |
|------|--------------------------------------:|
| D1 (1-bit) | **×8** |
| D2 (2-bit) | **×4** |
| D3 (3-bit) | **×2.67** |
| mixed D1/D2/D3 | **~×4** |
| Bit8 | **×1** (no win) |

Utilization stays ≥93% even on short mixed streams (tail padding only).

## Wall time (diagnostic only — not Cachegrind)

Python bit-loop model on connector sandbox. Order of magnitude only.

At n=1024: pack costs scale roughly with bit count; Bit8 pack ≈ box size so packing buys nothing.

## Threshold sketch (hypothesis for #2190, not production law)

```text
hot scalar runtime     → box (Bits<N> as u8) — avoid pack/unpack per op
cold AST / wire / FPGA → pack — D1–D3 density ×2.7–8
Bit8 bulk              → box and pack equivalent density
hot repeated bulk      → measure decode-once cache (not in this slice)
```

## Non-claims

- no semantic role assignment
- no replacement of Rust `Bits<N>` / #2188 packer
- no global "always pack" recommendation
- Cachegrind I-ref follow-up still needed on pinned host
