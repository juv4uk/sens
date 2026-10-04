; contracts/d4-bootstrap-ratification.lisp
; FORMER OWNER-RATIFICATION #3272 — revoked by owner reset #3327.
; Preserved as D4 research/provenance evidence; not current semantic authority.

(
  (schema . d4-bootstrap-ratification/1)
  (status . revoked-research-evidence)
  (former-owner-ratification . #3272)
  (revoked-by . #3327)
  (date . "2026-10-04")
  (domain . D4)

  (residents
    . ((D4:0000 APPLY)
       (D4:0001 EVAL)
       (D4:0010 LAMBDA)
       (D4:0011 DEFINE)
       (D4:0100 NOT)
       (D4:0101 NULL)
       (D4:0110 CDAR)
       (D4:0111 CDDR)
       (D4:1000 CAAR)
       (D4:1001 CADR)
       (D4:1010 LOOKUP)
       (D4:1011 BIND)
       (D4:1100 EVCON)
       (D4:1101 EVLIS)
       (D4:1110 LIST)
       (D4:1111 APPEND)))

  (d3-fibres
    . ((D3:000 APPLY EVAL)
       (D3:001 LAMBDA DEFINE)
       (D3:010 NOT NULL)
       (D3:011 CDAR CDDR)
       (D3:100 CAAR CADR)
       (D3:101 LOOKUP BIND)
       (D3:110 EVCON EVLIS)
       (D3:111 LIST APPEND)))

  (classification
    . ((irreducible-bootstrap LAMBDA DEFINE)
       (generated-selectors CAAR CADR CDAR CDDR)
       (derived-bootstrap APPLY EVAL LOOKUP BIND EVCON EVLIS)
       (compact-derived NOT NULL LIST APPEND)))

  (laws
    . ((dense . "all sixteen exact D4 coordinates are occupied")
       (legacy-non-authority . "SID8/Sens8/Function8 and old D4 coordinates have zero placement authority")
       (not-null . "PredicateBit NO is not structural EMPTY; NOT and NULL are distinct residents")
       (list-append . "LIST collects values into a proper list; APPEND combines admitted lists")))

  (evidence . (#2156 #2162 #2287 #3225 #3266))
)
