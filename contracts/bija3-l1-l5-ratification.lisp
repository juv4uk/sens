; contracts/bija3-l1-l5-ratification.lisp
; РАТИФІКОВАНО ВЛАСНИКОМ 2026-10-04 — issue #3202.

(
  (schema . bija3-l1-l5-ratification/1)
  (status . owner-ratified)
  (owner-ratification . #3202)
  (date . "2026-10-04")
  (domain . D3)
  (name . bīja3)

  (bīja3
    . ((D3:000 EMPTY)
       (D3:001 QUOTE)
       (D3:010 ATOM)
       (D3:011 CDR)
       (D3:100 CAR)
       (D3:101 EQ)
       (D3:110 COND)
       (D3:111 CONS)))

  (semantic-duals
    . ((EMPTY CONS)
       (як-є COND)
       (ATOM EQ)
       (CDR CAR)))

  (laws
    . ((L1 . "000 is structural empty ()")
       (L2 . "D3 preserves D2 as exact two-bit prefix fibres plus one child bit")
       (L3 . "one uniform semantic involution covers all four D3 dual pairs")
       (L4 . "dual3(x)=x XOR 111")
       (L5 . "suffix-0 is the evaluator spine: EMPTY -> ATOM -> CAR -> COND")))

  (uk-projection
    . ((EMPTY . ())
       (QUOTE . як-є)
       (ATOM . атом?)
       (CDR . решта)
       (CAR . перше)
       (EQ . тотожне?)
       (COND . за-умовою)
       (CONS . сполучити)))
)
