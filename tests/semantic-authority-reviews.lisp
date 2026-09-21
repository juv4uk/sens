; Explicit semantic-authority reviews.
; This file is Lisp-owned policy data consumed by scripts/semantic-authority-guard.lisp.
; Every row is exact-path only: no prefixes, globbing, directories, or wildcards.
;
; #1098 SID-BINARY-IDENTITY-1 is a reviewed representation migration:
; semantic identity changes from host numeric aliases to opaque exact 8-bit Sid8.
; These paths are allowed to change only under that reviewed scope; the guard
; still classifies every other high-risk host file as a violation.

(review "crates/my-lisp/src/eval/builtins.rs" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/eval/canon.rs" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/eval/mod.rs" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/eval/necessary_forms.rs" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/ir.rs" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/language_items.rs" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/lib.rs" issue-1098 sid8-projection-boundary)
(review "crates/my-lisp/src/presentation.rs" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/semantic_registry.rs" issue-1098 sid8-projection-boundary)
(review "crates/my-lisp/src/value.rs" issue-1098 sid8-type-migration)
(review "crates/my-lisp/tests/machine_capability_axis.rs" issue-1098 sid8-witness-migration)
(review "crates/my-lisp/tests/rivnopravnist_mov.rs" issue-1098 sid8-witness-migration)
(review "crates/my-lisp/tests/semantic_coordinate_join.rs" issue-1098 sid8-witness-migration)
(review "crates/my-lisp/tests/semantic_coordinate_join_2.rs" issue-1098 sid8-witness-migration)
(review "crates/my-lisp/tests/semantic_coordinate_law_axis.rs" issue-1098 sid8-witness-migration)
(review "crates/xtask/src/external_oracle.rs" issue-1098 sid8-tooling-migration)
