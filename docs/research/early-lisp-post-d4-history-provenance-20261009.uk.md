# Early Lisp historical ledger — archival provenance and current-domain reconciliation

**Status:** historical ingest only; no new D10 admission.

## Sources and chronology

This ledger preserves 19 operations from the old #2344 branch without importing its unplaced labels or later structural classifications as current truth. Source trail:
- McCarthy's *Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I* (1960), available as a [scan](https://www.cs.cmu.edu/~crary/819-f09/McCarthy60.pdf) and described by the Medley Interlisp bibliography. The paper develops the S-expression/S-function basis and recursive computation model. See the [archived paper scan](https://www.cs.cmu.edu/~crary/819-f09/McCarthy60.pdf) and the [Medley Interlisp bibliography entry](https://interlisp.org/history/bibliography/ufjlxxcl/).
- *LISP 1.5 Programmer's Manual* (1962), [archived scan](https://www.bitsavers.org/pdf/mit/rle_lisp/McCarthy_LISP_1.5_Programmers_Manual_2ed_1985.pdf). The Computer History Museum archive lists the 1962 manual and earlier memos; Appendix A describes the system inventory as of August 1962 and records each object’s property class. See the [archive catalog](https://softwarepreservation.org/projects/LISP/lisp15_family.html) and [manual scan](https://studylib.net/doc/26237227/lisp-1.5-programmers-manual).
- Hart's *MACRO Definitions for LISP*, AI Memo 57 (October 1963), listed in the archive's bibliography. This is after the main 1962 manual cutoff and is intentionally kept as a distinct later attestation. The archive bibliography lists Hart’s October 1963 memo as “MACRO Definitions for LISP.” See the [LISP 1.5 family archive](https://softwarepreservation.org/projects/LISP/lisp15_family.html) and [AI bibliography scan](https://bitsavers.org/pdf/mit/ai/ai_600dpi/AI_191_Bibliography_Jun1976.pdf).

A historical spelling does not by itself establish earliest attestation or current Core ownership.

## Reconciliation against current main

- D1–D9 foundation blob: `09d1d71c39d1484dfd005a5068dbb18b76f0f0d4`
- D10 inventory blob: `73dd518469f972c55411e004b70b054ba8b3ec86`
- Current D10: 625/1024 selected, 0 ratified.

Current exact-name scan across the 19 rows:
- 17 operations overlap the ratified D1–D9 inventory by name;
- 0 overlap selected D10 by name;
- 0 overlap both;
- 2 have no exact-name overlap to either.

This is a lexicographic scan, not a proof of equality or novelty. Historic row claims such as `NEW-OBSERVABLE-CAPABILITY` have been demoted into explicit `original_snapshot` provenance fields; all rows now have `coordinate=null`, `selected_d10_candidate=false`, and `ratified=false`.

## What remains relevant to D10 review (not a promotion request)

1. **SET / SETQ:** reduce the pair to one observable shared-location update law, then compare against current SETQ/binding and D8/D9 reference-cell/binding laws. Quoted-target syntax is not a second root.
2. **RETURN:** historical exit from the most-recent active PROG across an ordinary call boundary is a non-local control rule. Keep control/evaluation ownership with D2; compare it against existing THROW/CATCH/CALL/CC and D10 candidate families before any new Core proposal.
3. **FEXPR / FSUBR:** old FEXPR gets raw operand forms plus explicit caller a-list and returns a direct value; this is not the same three-axis protocol as later Hart MACRO/TRANSFORMER (raw whole form, no caller environment, replacement form reprocessed). Treat as an evaluation/control protocol question for D2, not two names to assign in D10.
4. **TRANSFORMER:** compare raw form, caller environment, and returned-form processing; current D8 already has a TRANSFORMER/Hart-MACRO family. No re-addition by name.
5. **FUNARG / FUNCTION:** historical closure representation versus current LAMBDA/FUNCTION law; provenance only unless an observable residual escapes behavioral dedup.

A fail-closed checker protects the 19-row archival state and recalculates exact-name overlap against current authority hashes.
