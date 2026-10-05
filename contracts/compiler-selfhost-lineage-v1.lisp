; contracts/compiler-selfhost-lineage-v1.lisp
; sens#3822 / sens#3760 — machine-readable evidence contract for the
; current-domain compiler fixed point.
;
; This file defines evidence shape and acceptance ordering only.
; It does NOT define compiler semantics, backend mechanism, or a self-host PASS.

(
  (schema . compiler-selfhost-lineage/1)
  (status . evidence-contract)
  (issue . #3822)
  (parent . #3760)

  (stages
    . ((C0 . trusted-bootstrap-mechanism)
       (C1 . executable-current-sens-compiler-produced-by-C0)
       (C2 . executable-current-sens-compiler-produced-by-C1)))

  (same-input-law
    . ((compiler-source . identical-required)
       (authority-bundle . identical-required)
       (d8-policy . fail-closed-required)
       (legacy-core1-sid8-substitution . forbidden)))

  (required-provenance
    . (sens-source-sha
       compiler-nucleus-sha256
       language-contract-sha256
       structural-law-projection-sha256
       c0-implementation-sha
       cml-sha
       backend
       target
       abi-profile
       c1-artifact-sha256
       c2-artifact-sha256
       normalized-c1-sha256
       normalized-c2-sha256
       equivalence-method))

  (equivalence-order
    . ((1 . byte-identical-artifact)
       (2 . normalized-ir-or-artifact-identical)
       (3 . canonical-lowering-and-executable-corpus-identical)))

  (downgrade-law
    . ((stronger-failed-weaker-pass . forbidden)
       (stronger-unavailable-weaker-test . allowed-with-explicit-reason)))

  (fresh-bootstrap
    . ((preexisting-c1-read . forbidden)
       (preexisting-c2-read . forbidden)
       (c0-must-produce-c1 . required)
       (c1-must-produce-c2 . required)))

  (failure-categories
    . (semantic-mismatch
       authority-or-provenance-mismatch
       bootstrap-input-mismatch
       backend-mechanism-failure
       toolchain-or-environment-failure
       nondeterministic-artifact
       forbidden-legacy-fallback))

  (acceptance
    . ((c0-produces-executable-c1 . required)
       (c1-compiles-identical-current-source . required)
       (c2-produced . required)
       (declared-equivalence-green . required)
       (fresh-bootstrap-green . required)
       (lineage-report-stored . required)))

  (non-goals
    . (historical-core1-fixed-point
       sid8-selfhost-proof
       behavior-only-smoke-as-fixed-point
       d8-admission
       backend-semantic-authority)))
