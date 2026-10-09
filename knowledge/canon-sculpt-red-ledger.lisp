; #419 RED ledger. Research evidence only.

(canon-sculpt-red-ledger
  (schema-version 1)
  (experiment
    (candidate PRIM_QUOTE)
    (hypothesis "quote is derivable as an ordinary eager Lisp function")
    (fixture tests/fixtures/canon-sculpt-quote-ordinary-function-red.lisp)
    (required-observation "an unbound symbol supplied as source data must reach the function body without ordinary argument evaluation")
    (predicted-current-result "RED: eager argument evaluation attempts to resolve the symbol before the ordinary function body")
    (interpretation
      "If observed, this falsifies only ordinary-function derivation. It does not prove quote irreducible: quote may still be derivable from a smaller explicitly declared evaluation-control mechanism.")))
