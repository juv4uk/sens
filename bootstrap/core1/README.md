# Historical bootstrap lane

This directory is the index for the historical/bootstrap evidence formerly
described as **Core1**.

## Authority boundary

```text
lib/core.lisp
  = the one active SENS Core
  = current owner-ratified language law

historical Core1 artifacts
  = bootstrap / derivability / provenance witnesses only
  != peer runtime core
  != alternate semantic profile
```

The historical label `Core1` is retained only where it identifies frozen
evidence or a pinned McCarthy/Lisp-I -> Lisp-1.5 reconstruction step.

## Current executable donor

The executable bootstrap source is still physically stored at:

```text
lib/core1.lisp
```

until every path reference has been classified as either:
- executable bootstrap consumer;
- frozen provenance that must retain the historical path;
- generated/report evidence;
- stale active-profile debt.

Do **not** bulk-rename those references. Frozen evidence must not be rewritten
as if history happened under a different path.

## Bootstrap evidence family

Current historical/bootstrap artifacts include:
- `lib/core1.lisp` — executable historical EVAL/APPLY bootstrap witness;
- `contracts/core1-bootstrap-contract.lisp` — bootstrap boundary;
- `contracts/core1-historical-sid-map.lisp` — one-way historical identity/mechanism map;
- `lib/core1-compiler-prelude.lisp` — compiler/bootstrap donor;
- `lib/core1-compiler-sid-resolver.lisp` — bootstrap resolver donor;
- `lib/core1-sid8-bootstrap-overlay.lisp` — SID8 self-carry experiment;
- post-D4 derivability witnesses that execute the pinned bootstrap.

## Migration rule

A current semantic claim must cite `lib/core.lisp` or current ratified Core
contracts. Historical bootstrap artifacts may prove **derivability,
provenance, or historical mechanism**, but may not override current Core law.

Physical relocation of frozen artifacts is allowed only after executable
consumers and provenance-only references are separated mechanically.
