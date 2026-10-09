; #419 PRE-1.0 Canon sculpture audit
; Evidence map only. This file does not define language semantics.
; Classification is intentionally provisional and falsifiable.

(canon-sculpt-audit
  (schema-version 1)
  (freeze-status pre-1.0-unfrozen)
  (classification-vocabulary
    (ground-value
     syntax-rule-candidate
     irreducible-candidate
     derivable-candidate
     value-domain
     insufficient-evidence))

  (candidate
    (identity CANON_EMPTY_LIST)
    (surface ()))
    (category ground-value)
    (observable-laws
      (ground-object)
      (proper-list-terminator)
      (unspecialized-no-answer-where-explicitly-contracted))
    (lower-concepts ())
    (classification ground-value)
    (falsification-question
      "Can every current use of Canon 0 be replaced by a derived value without introducing a second ground identity?"))

  (candidate
    (identity PRIM_QUOTE)
    (category evaluation-control)
    (observable-laws (return-form-without-ordinary-evaluation))
    (classification syntax-rule-candidate)
    (falsification-question
      "Can quote be defined as an ordinary callable Lisp function without already possessing a mechanism that suppresses argument evaluation?"))

  (candidate
    (identity PRIM_ATOM)
    (category structural-observation)
    (observable-laws
      ((atom ()) (structural-kind empty-list))
      ((atom pair) (structural-kind pair))
      ((atom non-pair-non-empty) (structural-kind atom)))
    (classification insufficient-evidence)
    (falsification-question
      "Can structural-kind be derived without calling atom, an alias of atom, a host representation tag, or an equivalent primitive structural classifier?"))

  (candidate
    (identity PRIM_EQ)
    (category identity-observation)
    (observable-laws
      (returns-identity-relation-result-not-generic-truth))
    (classification insufficient-evidence)
    (falsification-question
      "Can identity-relation be derived from lower Lisp concepts without importing pointer/host equality or recursively invoking eq through another surface?"))

  (candidate
    (identity PRIM_CONS)
    (category structure-construction)
    (observable-laws (construct-pair))
    (classification irreducible-candidate)
    (falsification-question
      "Can a pair be constructed without already having a pair constructor or a stronger aggregate constructor in the semantic ground?"))

  (candidate
    (identity PRIM_CAR)
    (category structure-observation)
    (observable-laws (observe-first-component-of-pair))
    (classification insufficient-evidence)
    (falsification-question
      "Can first-component observation be derived from cons plus other lower concepts without smuggling in pair destructuring?"))

  (candidate
    (identity PRIM_CDR)
    (category structure-observation)
    (observable-laws (observe-second-component-of-pair))
    (classification insufficient-evidence)
    (falsification-question
      "Can second-component observation be derived from cons plus other lower concepts without smuggling in pair destructuring?"))

  (candidate
    (identity PRIM_COND)
    (category evaluation-control)
    (observable-laws
      (ordered-clause-selection)
      (evaluate-selected-consequent-only))
    (classification syntax-rule-candidate)
    (falsification-question
      "Can cond be macro-derived from a smaller evaluation-control form while preserving observable evaluation order and without making that smaller form an undeclared semantic primitive?"))

  (audit-law
    (name no-historical-privilege)
    (statement "Being named primitive in an earlier contract is evidence to inspect, not proof of irreducibility."))
  (audit-law
    (name no-host-proof)
    (statement "A Rust implementation, runtime tag, pointer identity, or backend shortcut cannot by itself prove semantic irreducibility."))
  (audit-law
    (name preserve-before-delete)
    (statement "No candidate may be removed until its observable laws are preserved by independent Lisp-owned witnesses and a non-circular derivation is demonstrated.")))
