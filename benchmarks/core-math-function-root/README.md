# Core-Math function-root probe (#3023)

This benchmark tests the proposed coordinate law

```text
E(G ∘ G) = E(G)^2
```

without allowing coordinate arithmetic to define semantics.

Current authority is **#3331**: D1-D5 are ratified/current; D6-D8 are research.
The probe therefore scans the complete current 62-resident D1-D5 foundation.

## Run

```bash
python3 benchmarks/core-math-function-root/probe.py
```

The output is machine-readable JSON.

## Current result

The exhaustive coordinate pre-scan contains:

- 62 current domain-qualified residents;
- 17 perfect-square source coordinates;
- 76 domain-qualified root candidates.

For the selector family, where independent self-composition semantics are
already admitted:

```text
CAR ∘ CAR = CAAR
CDR ∘ CDR = CDDR
```

the square-coordinate hypothesis gets **0/2** matches:

```text
E(CAR)=4,  4²=16 -> D5:CAAAR, but CAR∘CAR = D4:CAAR (8)
E(CDR)=3,  3²=9  -> D4:CADR,  but CDR∘CDR = D4:CDDR (7)
```

So the sqrt/self-composition law is **FALSIFIED for the selector family**.

The positive control is the already-earned affine append law:

```text
child(parent,A) = 2*E(parent)+0
child(parent,D) = 2*E(parent)+1
```

It matches all 12 current D3→D4 and D4→D5 selector descendants.

Exact random-placement controls:

```text
both primitive square hits: 1 / 1,120
all four D3→D4 append hits: 1 / 43,680
all eight D4→D5 append hits: 1 / 424,097,856,000
```

This is deliberately a bounded falsification/positive-control result, not a
claim that every non-selector perfect-square candidate has been semantically
tested.  Candidates lacking an independent composition certificate stay
UNTESTED.
