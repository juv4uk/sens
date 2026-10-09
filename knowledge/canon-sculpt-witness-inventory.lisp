; #419 witness inventory. Navigation/provenance only: expected semantic truth stays in the referenced Lisp corpora.

(canon-sculpt-witness-inventory
  (schema-version 1)
  (rule (no-copied-expected-values))

  (witness
    (candidate PRIM_ATOM)
    (source tests/fixtures/structural-observation-v1.lisp)
    (coverage structural-kind)
    (authority lisp-owned)
    (status inspect-current-main))

  (witness
    (candidate PRIM_EQ)
    (source tests/fixtures/structural-observation-v1.lisp)
    (coverage identity-relation)
    (authority lisp-owned)
    (status inspect-current-main))

  (witness
    (candidate PRIM_CONS)
    (source tests/fixtures/conformance.lisp)
    (coverage construction-and-observation)
    (authority lisp-owned)
    (status inspect-current-main))

  (witness
    (candidate PRIM_CAR)
    (source tests/fixtures/conformance.lisp)
    (coverage first-component)
    (authority lisp-owned)
    (status inspect-current-main))

  (witness
    (candidate PRIM_CDR)
    (source tests/fixtures/conformance.lisp)
    (coverage second-component)
    (authority lisp-owned)
    (status inspect-current-main))

  (witness
    (candidate PRIM_COND)
    (source tests/fixtures/conformance.lisp)
    (coverage conditional-evaluation)
    (authority lisp-owned)
    (status inspect-current-main))

  (witness
    (candidate cross-backend-shared-truth)
    (source knowledge/lisp-backend-adapters.lisp)
    (coverage native-meta-cml-transport)
    (authority transport-only)
    (status inspect-current-main))

  (gap
    (candidate PRIM_QUOTE)
    (status insufficient-inventory-evidence)
    (next "locate an active Lisp-owned quote/evaluation-control witness before making a reducibility claim")))
