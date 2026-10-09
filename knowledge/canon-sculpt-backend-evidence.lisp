; #419 backend evidence ledger. Evidence/navigation only.

(canon-sculpt-backend-evidence
  (schema-version 1)
  (law
    (name lowering-is-not-derivation)
    (statement "A native/CML/x86 lowering proves an implementation path, not that a semantic concept is derivable from lower Lisp concepts."))
  (law
    (name shared-truth-not-copied-truth)
    (statement "Backends may consume one Lisp-owned expected corpus; backend manifests must not become a second semantic oracle."))

  (path
    (name native)
    (role execution-consumer)
    (evidence-source tests/fixtures/conformance.lisp)
    (status inspect-current-main))
  (path
    (name meta)
    (role independent-lisp-evaluator-consumer)
    (evidence-source tests/fixtures/conformance.lisp)
    (status inspect-current-main))
  (path
    (name cml)
    (role sibling-compiler-consumer)
    (evidence-source knowledge/lisp-backend-adapters.lisp)
    (status transport-contract-exists))
  (path
    (name x86-machine)
    (role mechanism-lowering)
    (evidence-source lib/machine)
    (status partial-admitted-subset))

  (candidate
    (identity PRIM_COND)
    (backend-note "bounded native lowering evidence exists, but it cannot decide whether cond is fundamental syntax or macro-derivable from a smaller control form"))
  (candidate
    (identity PRIM_CONS)
    (backend-note "machine construction/access lowering can support performance/portability evidence but cannot establish semantic irreducibility"))
  (candidate
    (identity PRIM_ATOM)
    (backend-note "structural classification must not be justified by a host/runtime representation tag"))
  (candidate
    (identity PRIM_EQ)
    (backend-note "identity semantics must not collapse to pointer equality merely because a backend can implement one case that way")))
