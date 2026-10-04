; contracts/bija3-l1-l5-ratification.lisp
; OWNER-RATIFIED 2026-10-04 — issue #3202.
; This is current D3 semantic authority together with language-contract.lisp.

(
  (schema . bija3-l1-l5-ratification/1)
  (status . owner-ratified)
  (owner-ratification . #3202)
  (date . "2026-10-04")
  (domain . D3)
  (name . bīja3)

  (map
    . ((000 EMPTY)
       (001 QUOTE)
       (010 ATOM)
       (011 CDR)
       (100 CAR)
       (101 EQ)
       (110 COND)
       (111 CONS)))

  (d2-prefix-fibres
    . ((00 EMPTY QUOTE)
       (01 ATOM CDR)
       (10 CAR EQ)
       (11 COND CONS)))

  (semantic-duals
    . ((EMPTY CONS)
       (QUOTE COND)
       (ATOM EQ)
       (CDR CAR)))

  (laws
    . ((L1 . "000 is structural empty ()")
       (L2 . "D3 preserves D2 as exact two-bit prefix fibres plus one child bit")
       (L3 . "one uniform semantic involution covers all four D3 dual pairs")
       (L4 . "dual3(x)=x XOR 111; recursive geometry matches D1 XOR 1 and D2 XOR 11")
       (L5 . "suffix-0 is the evaluator/metalinguistic spine: EMPTY -> ATOM -> CAR -> COND")))

  (evidence . (#3194 #3196 #3200))
  (implementation-cutover . (#3203 #2055 #3205 #3206))
  (superseded-current-order
    . ((011 COND)
       (100 CONS)
       (101 CAR)
       (110 CDR)
       (111 EQ)))
)
