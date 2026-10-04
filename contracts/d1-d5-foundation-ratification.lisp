; contracts/d1-d5-foundation-ratification.lisp
; OWNER-RATIFIED 2026-10-05 — issue #3331.
; Single current semantic foundation chain.

(
  (schema . d1-d5-foundation-ratification/1)
  (status . owner-ratified)
  (owner-ratification . #3331)
  (date . "2026-10-05")
  (current-domains . (D1 D2 D3 D4 D5))
  (research-domains . (D6 D7 D8))

  (D1 . ((0 NO) (1 YES)))
  (D2 . ((00 SEPARATOR) (01 CLOSE) (10 OPEN) (11 DOT)))
  (D3 . ((000 EMPTY) (001 QUOTE) (010 ATOM) (011 CDR)
         (100 CAR) (101 EQ) (110 COND) (111 CONS)))
  (D4 . ((0000 APPLY) (0001 EVAL) (0010 LAMBDA) (0011 DEFINE)
         (0100 NOT) (0101 NULL) (0110 CDAR) (0111 CDDR)
         (1000 CAAR) (1001 CADR) (1010 LOOKUP) (1011 BIND)
         (1100 EVCON) (1101 EVLIS) (1110 LIST) (1111 APPEND)))
  (D5 . ((00000 EVALQUOTE) (00001 FUNCTION) (00010 FEXPR) (00011 MACRO)
         (00100 LABEL) (00101 PROG) (00110 SET) (00111 SETQ)
         (01000 ZEROP) (01001 NUMBERP) (01010 PLUS) (01011 DIFFERENCE)
         (01100 CDAAR) (01101 CDADR) (01110 CDDAR) (01111 CDDDR)
         (10000 CAAAR) (10001 CAADR) (10010 CADAR) (10011 CADDR)
         (10100 REVERSE) (10101 REVERSE-ONTO) (10110 TIMES) (10111 QUOTIENT)
         (11000 GO) (11001 RETURN) (11010 LESSP) (11011 GREATERP)
         (11100 ASSOC) (11101 MEMBER) (11110 PAIRLIS) (11111 SUBST)))

  (laws
    . ((identity . "exact bits + exact domain + admitted/proved law")
       (legacy-non-authority . "SID8/Sens8/Function8 coordinates have zero current placement authority")
       (d5-no-duplicate . "D5 has 32 distinct residents and zero lower-domain semantic duplicates")
       (d5-no-global-suffix . "The fifth bit has local family meaning only")
       (d6-boundary . "D6-D8 are research; W6-W8 carrier existence does not grant semantic admission")))

  (supersedes-for-current-authority . (#3327-D3-D5-revocation))
  (preserves-as-research-boundary . (#3327-D6-D8-reset))
)
