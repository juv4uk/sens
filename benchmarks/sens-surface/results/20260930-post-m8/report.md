# Post-M8 three-way benchmark (#1665)

Один current-main бінарник, однакові workload-и й oracle:

- **EN text** — людська англійська поверхня, text parse;
- **SENS text** — exact 8-bit reader spelling, text parse;
- **SENS FASL** — exact one-byte function transport, binary decode.

Primary metric: Cachegrind I refs, median repeated runs. Ніякого автоматичного performance verdict/threshold немає.

## Provenance

- git SHA: `786c62b9c9aea167fc5e0dc0e5a541752953b01c`
- host: connector sandbox, Intel Xeon Platinum 8481C @ 2.70GHz
- Valgrind: 3.22.0; rustc 1.98.1; reps=2; repeat_n=3
- **not** Guix-pinned i5-6400 (absolute I-refs not comparable to 20260927 three-way)
- raw: `instructions.tsv` · `environment.tsv` · `summary.json`

## Load / parse / decode

Net instructions = load − empty session.

| workload | EN text | SENS text | SENS FASL | EN/FASL | SENS-text/FASL |
|---|---:|---:|---:|---:|---:|
| ackermann | 199,147 | 196,422 | 42,607 | ×4.674 | ×4.610 |
| assoc | 381,292 | 366,706 | 93,602 | ×4.074 | ×3.918 |
| closures | 196,500 | 187,582 | 45,516 | ×4.317 | ×4.121 |
| evenodd | 198,409 | 190,158 | 41,441 | ×4.788 | ×4.589 |
| fib | 157,725 | 155,439 | 34,455 | ×4.578 | ×4.511 |
| flatten | 328,854 | 312,848 | 84,342 | ×3.899 | ×3.709 |
| lists | 433,244 | 413,056 | 106,063 | ×4.085 | ×3.894 |
| loop | 133,633 | 129,946 | 29,110 | ×4.591 | ×4.464 |
| mapfold | 483,306 | 462,226 | 122,970 | ×3.930 | ×3.759 |
| member | 375,194 | 358,043 | 84,277 | ×4.452 | ×4.248 |
| tree | 224,552 | 215,334 | 55,646 | ×4.035 | ×3.870 |
| **geomean** | | | | **×4.300** | **×4.141** |

## Steady call execution

Per-call = (repeat(N) − ready) / N; load/setup excluded.

| workload | EN text | SENS text | SENS FASL | EN/SENS-text | EN/FASL | SENS-text/FASL |
|---|---:|---:|---:|---:|---:|---:|
| ackermann | 33,344,136 | 33,340,680 | 33,462,697 | ×1.000 | ×0.996 | ×0.996 |
| assoc | 8,733,351 | 8,751,189 | 8,767,921 | ×0.998 | ×0.996 | ×0.998 |
| closures | 88,803,097 | 88,803,485 | 89,033,421 | ×1.000 | ×0.997 | ×0.997 |
| evenodd | 56,951,410 | 56,525,732 | 56,700,955 | ×1.008 | ×1.004 | ×0.997 |
| fib | 45,354,358 | 45,564,410 | 45,501,809 | ×0.995 | ×0.997 | ×1.001 |
| flatten | 30,256,580 | 30,176,698 | 30,293,204 | ×1.003 | ×0.999 | ×0.996 |
| lists | 84,473,803 | 84,253,030 | 84,769,499 | ×1.003 | ×0.997 | ×0.994 |
| loop | 67,898,392 | 67,898,369 | 68,133,369 | ×1.000 | ×0.997 | ×0.997 |
| mapfold | 54,274,567 | 54,136,158 | 54,314,376 | ×1.003 | ×0.999 | ×0.997 |
| member | 78,444,245 | 78,093,478 | 78,477,546 | ×1.004 | ×1.000 | ×0.995 |
| tree | 45,407,214 | 45,361,508 | 45,541,582 | ×1.001 | ×0.997 | ×0.996 |
| **geomean** | | | | **×1.001** | **×0.998** | **×0.997** |

## One-call end-to-end

Net = full − empty; load + setup + one call. Geomean EN/FASL **×1.002**.

## Verdict on hypotheses (#1665)

| hypothesis | result |
|------------|--------|
| EN text execute ≈ SENS text execute after M8 | **supported** — steady geomean EN/SENS-text **×1.001** |
| SENS text execute ≈ SENS FASL execute after load | **supported** — steady geomean SENS-text/FASL **×0.997** |
| EN text load more expensive than SENS FASL load | **supported** — load geomean EN/FASL **×4.30** |

### #1413 residual EN-runtime-name-cost

**Resolved by M8 for steady execution** on this host/commit: no measurable name-tax between EN and SENS-text once lowered (ratios within ~1%).

Historical pre-M8 +16% EN vs SENS execute gap must not be repeated as a *current* claim.

Load-path advantage of binary FASL remains real (~×4.3 vs text parse).

## Interpretation boundary

- Ratios near 1 are measurements, not semantic law.
- Do not edit evaluator/registry to improve this table.
- Absolute I-refs differ from Guix i5-6400 baseline; only within-run ratios are primary.
