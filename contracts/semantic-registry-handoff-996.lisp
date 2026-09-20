; #996 — machine-readable authority handoff policy.
;
; This contract does not duplicate semantic rows. It states how downstream
; consumers such as cml and wsm-my-lisp must pin and verify the canonical
; Lisp-owned registry before lowering or observing it.

(semantic-registry-handoff-contract/1
  (authority "lib/surface/semantic-registry.lisp")
  (authority-owner my-lisp)
  (identity-domain (binary 8))
  (revision-pin git-commit-containing-authority)
  (content-digest sha256-utf8-source)
  (witness semantic-registry-handoff-witness)
  (consumers
    (cml lower-or-observe-only)
    (wsm-my-lisp lower-or-observe-only))
  (forbidden
    decimal-sid-shadow-table
    string-sid-shadow-table
    downstream-semantic-reinterpretation))
