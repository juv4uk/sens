; contracts/d5-ratification.lisp
; OWNER-RATIFIED 2026-10-04 — issue #3305.
; Current D5 semantic residency authority.

(
  (schema . d5-ratification/1)
  (status . owner-ratified)
  (owner-ratification . #3305)
  (date . "2026-10-04")
  (domain . D5)
  (width . 5)
  (capacity . 32)
  (occupancy . 32)

  (residents
    . ((D5:00000 EVALQUOTE)
       (D5:00001 FUNCTION)
       (D5:00010 FEXPR)
       (D5:00011 MACRO)
       (D5:00100 LABEL)
       (D5:00101 PROG)
       (D5:00110 SET)
       (D5:00111 SETQ)
       (D5:01000 ZEROP)
       (D5:01001 NUMBERP)
       (D5:01010 PLUS)
       (D5:01011 DIFFERENCE)
       (D5:01100 CDAAR)
       (D5:01101 CDADR)
       (D5:01110 CDDAR)
       (D5:01111 CDDDR)
       (D5:10000 CAAAR)
       (D5:10001 CAADR)
       (D5:10010 CADAR)
       (D5:10011 CADDR)
       (D5:10100 REVERSE)
       (D5:10101 REVERSE-ONTO)
       (D5:10110 TIMES)
       (D5:10111 QUOTIENT)
       (D5:11000 GO)
       (D5:11001 RETURN)
       (D5:11010 LESSP)
       (D5:11011 GREATERP)
       (D5:11100 ASSOC)
       (D5:11101 MEMBER)
       (D5:11110 PAIRLIS)
       (D5:11111 SUBST)))

  (relation-classes
    . ((semantic-generator . 5)
       (local-algebra . 5)
       (multi-delta-family . 2)
       (coordinate-historical . 4)))

  (laws
    . ((no-global-fifth-bit . "The fifth bit has local family meaning only; there is no universal D5 suffix semantics.")
       (no-lower-duplicate . "A D5 resident must not duplicate an already-admitted lower-domain semantic identity merely to fill capacity.")
       (selector-family . "The eight depth-3 selector residents follow the proved CAR/CDR composition law under D4 selector parents.")
       (reverse-onto . "REVERSE(x)=REVERSE-ONTO(x,()); REVERSE-ONTO(x,y)=APPEND(REVERSE(x),y); APPEND(x,y)=REVERSE-ONTO(REVERSE(x),y).")
       (runtime-separation . "Ratified residency does not promise a callable mechanism. Missing resident mechanisms fail closed.")))

  (supersedes . (#3278-D5-revocation OD-005-pre-reset #3297-research-shadow))
  (preserves . (#3278-D6-revocation #3278-D8-revocation))
)
