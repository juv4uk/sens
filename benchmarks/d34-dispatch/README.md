# #2209: 8-bit flat-slot dispatch vs ratified D3/D4 prefix dispatch (research harness, not production)

The same six selectors on one address tree (3 levels; every leaf has its own address, so a wrong path is visible):
`101 CAR`, `110 CDR`, `1010 CAAR`, `1011 CADR`, `1100 CDAR`, `1101 CDDR` (D4 word = root `101/110` + one suffix bit; suffix `0` = inner CAR, `1` = inner CDR).

| lane | identity | dispatch |
|---|---|---|
| `u8-flat-ready` | an 8-bit slot | one flat row lookup (row = the recipe, prepared before the calls), then execute it. Deliberately favourable: no human-name lookup |
| `d3d4-prefix-ready` | an exact-width word (3 or 4 bits) | the recipe is derived from the prefix law with shifts and one branch on the width; **no descendant row** |
| `direct-specialized` | compile time | the CAR/CDR chain itself: one fixed loop per selector (lower bound); a minimal `switch` when the stream is mixed |
| `N` (null) | none | only the call loop; subtracted from every lane |

Parity first: all three lanes against an independent classical-name oracle on all six selectors: 0 mismatches. Then Cachegrind
(`--cache-sim=no --branch-sim=yes`, setup vs full, median of 3, 100000 calls), counters from a separate `-DCOUNT` build.

```bash
python3 benchmarks/d34-dispatch/run.py --out docs/research/2209-d34-dispatch-bench.tsv     # gcc, valgrind
```

## Result (one image: Intel i5-6400, gcc 16.1, valgrind 3.27; I refs per call, net of the empty loop)

| workload | u8 flat | d3d4 prefix | direct |
|---|---|---|---|
| CAR (D3, repeated) | 25 | **20** | 3 |
| CDR | 24 | **19** | 3 |
| CAAR (D4, repeated) | 36 | **27** | 6 |
| CADR | 35 | **27** | 6 |
| CDAR | 35 | **26** | 6 |
| CDDR | 34 | **26** | 7 |
| mixed (random of the six) | 31.5 | **24.2** | 18.5 (a switch) |

Table lookups per call: flat 1, prefix 0, direct 0. Bits consumed: prefix 3 (D3) / 4 (D4). Generator applications: 1 (D3), 2 (D4) in every lane
(the semantic path is the same; only the identity mechanism differs). Prepared bytes: flat 768 (a 256-slot row table), prefix 0, direct 0.
Branches per call: D3 flat 6, prefix 6, direct 1; D4 flat 9, prefix 8, direct 2; mixed 8 / 7.3 / 6.5.

## What it says (hypothesis, for this image and this implementation)

1. **Prefix dispatch is cheaper than the flat-slot route** on the same AST: 5 I refs per call for D3 and 8-10 for D4, with no table lookup and no prepared table; the saving is the
   row load and the row's loop.
2. **Both are far above the direct chain** (3 / 6 I refs): the cost of an *identity mechanism* in this C interpreter is 17-21 I refs (prefix) to 22-30 (flat) per selector call. A
   compiler that lowers the word once (#1988's compiled path) pays that decode once; neither lane does that here.
3. In the **mixed** stream the `switch` of the direct lane costs 18.5; prefix is 5.7 above it, flat 13.

## Limits (do not read more into it)

- I refs and Cachegrind's simulated branch counts only; **mispredicts are the simulator's** (about 1 per call for some repeated flat cases, 1.2 for mixed): not a hardware claim.
- The flat lane is *a* favourable baseline, not the best flat design (function pointers or per-slot specialised thunks would drop its row loop); the prefix lane is *a* straightforward decode.
  Both numbers move with the implementation; the sign of the difference should be checked by an independent harness.
- Six selectors, a 3-level tree that stays in cache; no data-cache effects; no CML or FPGA numbers; no other D4 words (they are not selectors).
- Absolute I refs from other hosts or Valgrind images are not comparable (#1987). No wall time. No semantic conclusion from speed.
