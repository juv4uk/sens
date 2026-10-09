# D8 historical full-map and D9 overflow — provenance archive, not current placement authority

**Status:** archive-only; no current D8/D9/D10 placement, no new D10 candidate selection.

## Why selective preservation instead of merging old maps

The old D8 full-map tranche (#2934, branch feat/d8-historical-full-occupancy) kept 64 admitted-by-selector-law rows and 192 attested-not-admitted candidates. Crucially, that old report itself says the “four historical capabilities per D6 parent” rule was falsified and demoted. Its 64 selector coordinates cite obsolete D3 roots 101=CAR and 110=CDR; current canonical D3 is 100=CAR and 011=CDR. Do not merge the old map as a live placement table. The current D8 authority is knowledge/d8-ratified.json, owner-ratified 256/256.

The old D9 overflow report is also a snapshot from when D9 was still unratified. It contains 34 entries: 20 old SELECT-D9-CANDIDATE, 11 HOLD, and 3 exact lower-domain rejections. Current D1–D9 are now ratified, so preserve the old decisions only as historical records and recompute overlap against current authorities.

## Primary-source web checks

The LISP 1.5 Programmer's Manual Appendix A explicitly describes a snapshot of the Lisp system as of August 1962 and records object names, property classes (EXPR/FEXPR/SUBR/FSUBR/APVAL), and function definitions. This is a catalogue of one historical system, not current SENS placement authority. See the [manual's archived scan](https://studylib.net/doc/26237227/lisp-1.5-programmers-manual) and the [Computer History Museum LISP History Collection](https://softwarepreservation.computerhistory.org/LISP/). The ANSI Common Lisp HyperSpec defines WITH-OPEN-FILE as opening a file stream, binding it for a dynamic extent, and closing it when control exits normally or abnormally. Stream resource behavior is concrete, but external-file effects must not be conflated with pure parsing/string IO. See [CLHS WITH-OPEN-FILE](https://clhs.lisp.se/Body/m_w_open.htm) and [CLHS open/closed stream concepts](https://www.lispworks.com/documentation/HyperSpec/Body/21_ac.htm).

## Current-main exact-name check

Authority snapshot:
- D1–D9 blob: 09d1d71c39d1484dfd005a5068dbb18b76f0f0d4
- D8 ratification blob: 43ac2620661dc5af40fe7e7ca8b39b89c9aee094
- D10 inventory blob: 73dd518469f972c55411e004b70b054ba8b3ec86
- D10: 625/1024 selected; 0 ratified.

The machine ledger recomputes names separately for the 192 D8-history rows and 34 D9-overflow rows. Each record retains original coordinate/decision only under historical_snapshot. Every current row has coordinate=null, selected_d10_candidate=false, ratified=false. Exact-name overlap is not behavior proof; exact-name absence is not a D10 admission rule.

## D10 propositions to review next (not auto-selected)

1. **Stream lifetime family:** test OPEN, CLOSE and WITH-OPEN-FILE against current D9 stream laws. Positive witness: stream opens in scope, reads/writes expected data, and closes on normal and nonlocal exit; falsifier: resource remains open on exit. Keep file-system effects distinct from pure parsing/string IO.
2. **Resource ownership family:** DEFRESOURCE, ALLOCATE-RESOURCE, DEALLOCATE-RESOURCE, USING-RESOURCE, MAP-RESOURCE and DEALLOCATE-WHOLE-RESOURCE from later Lisp Machine documentation. A possible universal law is pool accounting/reuse plus guaranteed return on dynamic-scope exit; do not select unless primary manual and witnesses establish exact behavior, including allocation failure and double release.
3. **Foreign-call family:** FFI-CALL is not a new identity solely because a historical candidate says so. Require a portable argument/result/ownership/error contract independent of a specific ABI or pointer representation. Likely island/substrate boundary unless a universal result law is proven.
4. **Sequence/set operations:** NUNION and NRECONC were old D9 proposals; compare their destructive alias-visible mutation with ratified D8 mutable-pair/list laws. The name or historical selection is not enough to create a new D10 candidate.
5. **Compiler/metadata proposals:** COMPILE-FILE, MACRO-FUNCTION, COMPILER-MACRO, SYMBOL-MACRO, DEFINE-COMPILER-MACRO, DEFSTRUCT, DEFTYPE, DEFINE-CONDITION and DEHANDLER need a result contract separated from host tooling, expansion/control flow, and package mechanisms; many may be covered by other domain/package laws.

The archival checker compares source authority hashes against current files and fails closed if any row is accidentally given a current coordinate, selection or ratification.
