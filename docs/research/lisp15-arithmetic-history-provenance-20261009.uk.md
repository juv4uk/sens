# LISP 1.5 arithmetic — historical carrier evidence, not D10 selection

**Status:** archival numeric-provenance ledger; no D10 slots, coordinates or ratification.

## Primary source

The source ledger names *LISP 1.5 Programmer's Manual*, Chapter IV §4.2, printed pages 25–27 and Appendix A pages 63–64. A source-preserved scan is available at [Bitsavers](https://www.bitsavers.org/pdf/mit/rle_lisp/McCarthy_LISP_1.5_Programmers_Manual_2ed_1985.pdf); the [Computer History Museum Software Preservation Group catalog](https://softwarepreservation.computerhistory.org/LISP/lisp15_family.html) tracks LISP 1.5 editions and earlier memos. The manual is an attestation of that described system, not a proof that every behavior was the earliest implementation.

## Reconciliation against current main

Machine snapshot:
- D1–D9 foundation blob: `09d1d71c39d1484dfd005a5068dbb18b76f0f0d4`
- D10 inventory blob: `73dd518469f972c55411e004b70b054ba8b3ec86`
- D10: 625/1024 selected, 0 ratified.

Normalized exact-name scan across 26 historical operations finds:
- 21 rows with an exact name in ratified D1–D9;
- 0 exact-name overlaps with selected D10;
- 5 rows without an exact-name overlap to either set (MINUS, FIXP, FLOATP, LOGOR, LEFTSHIFT).

Exact-name overlap is not a semantic equivalence proof. Exact-name absence is not a D10 promotion rule.

## Why this matters for Core-Math and D10

The old ledger explicitly records fixed-point, floating-point, near-zero/near-one tolerances, and 36-bit logical-word behavior. Those historical carriers cannot be silently reinterpreted as current exact-Q laws. For example, the old ledger says fixed-point `RECIP` returns zero, and `ZEROP` uses a documented tolerance of (3\times10^{-6}); current D6/D5 identities should be compared using the current numeric contract, not copy-pasted from this manual.

No D10 semantic residents are proposed by this archival move. Priority is to preserve exact evidence and let Core-Math/type-carrier review resolve the old-vs-current law differences. All 26 rows remain `selected_d10_candidate=false`, `coordinate=null`, `ratified=false`.

## Research priority after preservation

1. Compare historical FIXP/FLOATP and the numeric result carrier against current numeric type laws; absence of those spellings is not enough to create D10.
2. Compare RECIP, ZEROP and ONEP tolerance/negative-zero cases against exact-Q semantics; record divergence instead of harmonizing silently.
3. Keep LOGOR/LOGAND/LOGXOR/LEFTSHIFT's 36-bit word laws as machine-carrier evidence until a width-independent semantic law is independently proved.
4. Keep DIVIDE's two-element `[quotient,remainder]` result shape distinct from arithmetic quotient alone, but dedup against existing D8/D5 composition before proposing any new identity.

The archival ledger's own checker recomputes current exact-name overlap and fails closed on stale authority hashes, invented selection, coordinates or ratification.
