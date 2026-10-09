; #1096 — bare 8-bit tokens are first-class Canon semantic identities.
; Semantic authority stays here in Lisp. Host observers may only execute this
; witness and check its named pass/fail envelope.
;
; Exactly eight bare 0/1 digits name a SID. Numeric binary interpretation is a
; separate explicit facility; this witness does not reinterpret SID bits as a
; decimal value.

(00001001 bare-sid-sum (00001100 2 3))
(00001001 surface-sum (00001100 2 3))

(00000111
  ((00011100 bare-sid-sum surface-sum) 1
   (00000111
     ; Exact D1 EQUAL produces a one-bit predicate, not legacy list (1).
     ; Select directly on D1:1; retain the negative fail envelope below.
     ((00100010 (01001100 00000000) "00000000")
      (00000001 (bare-sid-literal-witness (status pass))))
     (t t
      (00000001 (bare-sid-literal-witness
               (status fail)
               (reason sid-zero-print-roundtrip))))))
  (t t
   (00000001 (bare-sid-literal-witness
            (status fail)
            (reason sid-call-surface-parity)))))
