# 2646 — Human-wire ARQ: block framing, CRC and selective retry

Status: research, mechanism only (domain firewall #2508; umbrella #2642). Framing is transport, never semantic identity.

Українська версія: [2646-human-wire-arq.uk.md](2646-human-wire-arq.uk.md).

## Variants
- A: len16 | payload | crc16 (whole message).
- B: fixed blocks `idx8, last1, len9, payload, crc16`.
- C: SYNC `11010011` + B, scan resync.
- D: C with Hamming(7,4) on the block body.

## Results (benchmarks/human-wire-arq)
- 272-bit payload, expected cost with one flip: A 608, B(k=128) 527, C(k=128) 552, D(k=272) 555 bits.
- Single flip always recovers (exhaustive). D: 90-98% zero-retry for flips in the body; flips in the uncoded SYNC still cost one block.
- Insertions/deletions (k=32): B cascades (mean 5.09 of 9 blocks lost, max 9); C and D resync and lose exactly one block.
- Monte Carlo: 0/20000 wrong payloads accepted per variant (bound ~ corrupted_units * 2^-16).
- Scaling vs A (best k): n=2048 B 0.636, C 0.645, D 1.0; n=8192 B 0.590, C 0.598, D 1.01.

## Honest caveats
- At 272 bits the header (26 bits/block + CRC16) swamps the gain; framing pays as messages grow.
- Hamming (D) does not pay on cost (goodput ~0.44-0.49) but gives zero-retry for single flips.
- Scaling grid is capped at k<=256, so best_k=256 sits at the grid edge.
- Retry policy: receiver reports held indices; only gaps/unseen tail are resent; conflicts resend all.

Recommendation for #2644: use C (sync + blocks + CRC) as the default; D only when retry latency dominates.
