# #2715 — Memo 24 arithmetic chronology

This sidecar compares Michael Levin's **April 28, 1961 Memo 24,
_Arithmetic in LISP 1.5_** directly against the merged 1962 arithmetic ledger
from #2709 / PR #2710.

It is chronology/provenance evidence only. It does not allocate Core D5/D6
coordinates and does not import Core-Math exact-Q laws into historical Lisp.

Current bounded result:

- 21 / 26 later-ledger rows are directly attested in Memo 24;
- 5 are not attested in Memo 24: QUOTIENT, REMAINDER, DIVIDE, EXPT, LEFTSHIFT;
- 4 directly attested predicate laws changed by the 1962 manual:
  LESSP, GREATERP, ONEP, EQUAL;
- ZEROP and FLOATP remain conservative UNRESOLVED comparisons because the
  primary scan/OCR is ambiguous or internally self-contradictory at the exact
  wording level.

The important rule is:

```text
earlier name attestation != unchanged semantic law
```

All rows remain `current_domain_candidate=unresolved` and
`binary_object=UNPLACED`.
