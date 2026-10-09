; #229 — current executable Canon laws under layered answer semantics.
; Expected values are Lisp-owned data. No row uses t/() as pass/fail truth.

((expr . "canon-empty-list")
 (expected . ())
 (active . t))

((expr . "(canon-law-empty-list)")
 (expected . (canon-law-result empty-list satisfied))
 (active . t))

((expr . "(canon-law-atom-cons (quote left) (quote right))")
 (expected . (canon-law-result atom-cons satisfied))
 (active . t))

((expr . "(canon-law-car-cons (quote left) (quote right))")
 (expected . (canon-law-result car-cons satisfied))
 (active . t))

((expr . "(canon-law-cdr-cons (quote left) (quote right))")
 (expected . (canon-law-result cdr-cons satisfied))
 (active . t))

((expr . "(canon-law-eq-reflexive-atom (quote left))")
 (expected . (canon-law-result eq-reflexive-atom satisfied))
 (active . t))

((expr . "(canon-law-cdr-dotted)")
 (expected . (canon-law-result cdr-dotted satisfied))
 (active . t))

((expr . "(canon-law-cdr-proper)")
 (expected . (canon-law-result cdr-proper satisfied))
 (active . t))

((expr . "(canon-law-cdr-improper)")
 (expected . (canon-law-result cdr-improper satisfied))
 (active . t))

((expr . "(canon-law-quote-suppresses-evaluation)")
 (expected . (canon-law-result quote-suppresses-evaluation satisfied))
 (active . t))

((expr . "(canon-law-cond-first-match-short-circuit)")
 (expected . (canon-law-result cond-first-match-short-circuit satisfied))
 (active . t))

((expr . "(canon-law-symbolic-surface)")
 (expected . (canon-law-result symbolic-surface satisfied))
 (active . t))

((expr . "(canon-conforms?)")
 (expected . (canon-conformance satisfied))
 (active . t))
