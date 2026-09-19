# Узгодження machine-admission: короткий український опис

Цей документ фіксує українською, що історичні machine-admission закони вже мають свідчення у поточному `main`; застарілий код із donor-гілок повторно не вноситься.

# Machine-admission historical reconciliation — 2026-09-20

Parent: #813

This record closes the historical replay audit without copying stale machine
branches. The current main branch already contains the retained laws.

| Retained law | Current-main evidence | Disposition |
| --- | --- | --- |
| Semantic meaning lowers to structured machine forms before execution | `lib/machine/lowering/semantic-x86-64.lisp` | absorbed |
| Closed admission is the only route from structured forms to bytes/host | `lib/machine/admission/x86-64.lisp` + `machine-lowering-boundary.lisp` | absorbed |
| Machine identity cannot allocate or redefine language semantic IDs | `machine-lowering-boundary.lisp` + `crates/my-lisp/tests/machine_lowering_boundary.rs` | absorbed |
| Unadmitted/malformed machine forms fail before host execution | `crates/my-lisp/tests/machine_admission_adversarial.rs` | absorbed |
| Rejected machine forms make zero host executor calls | `crates/my-lisp/tests/machine_admission_adversarial.rs` | absorbed |
| Native admission failure is not silently retried through evaluator | `tests/fixtures/native-first-execution-witness.lisp` + `scripts/test-current-semantic-slice.sh` | absorbed |
| Structured lowering is canonical; bytes are a later target projection | `lib/machine/dispatch/native-first-execute.lisp` + lowering/admission/encoding path | absorbed |

## Historical donors

- `research/machine-inst-semantic-contract`: authority-boundary law is retained, with current main now using the stronger ISA/hardware vertical boundary.
- `feat/machine-admission-1`: closed admission is retained; current main has the expanded canonical admission catalogue.
- `feat/machine-admission-2-structured-lowering`: structured lowering is retained; current main contains the broader lowering profile.
- `test/machine-admission-adversarial-evidence`: negative admission evidence is retained and strengthened by the current adversarial suite.

## Replay decision

No donor implementation is merged wholesale. The historical branch ideas are considered reconciled when every retained law has a current-main executable or contract witness. This record is documentation only; it does not create a second machine-authority table or semantic registry.

## S2 gate

Before the #813 parent merge:

1. verify these witnesses still pass on the exact current main head;
2. verify no new Rust semantic matcher or duplicate admission authority appeared;
3. verify the #504/#508 surfaces remain diagnostic/gateway evidence rather than a second semantic registry.
