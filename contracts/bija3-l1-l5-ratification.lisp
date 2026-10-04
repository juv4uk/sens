; contracts/bija3-l1-l5-ratification.lisp
; FORMER OWNER-RATIFICATION #3202 — revoked by owner reset #3327.
; Preserved as D3 research/provenance evidence; not current semantic authority.

(
  (schema . bija3-l1-l5-ratification/1)
  (status . revoked-research-evidence)
  (former-owner-ratification . #3202)
  (revoked-by . #3327)
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

  (d2-prefix-fibres
    . ((D2:00 EMPTY QUOTE)
       (D2:01 ATOM CDR)
       (D2:10 CAR EQ)
       (D2:11 COND CONS)))

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
    . ((D3:011 COND)
       (D3:100 CONS)
       (D3:101 CAR)
       (D3:110 CDR)
       (D3:111 EQ)))
)
