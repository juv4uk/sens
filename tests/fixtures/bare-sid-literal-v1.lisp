; #1096 — bare 8-bit tokens are first-class Canon semantic identities.
; Semantic authority stays here in Lisp. Host observers may only execute this
; witness and check its named pass/fail envelope.
;
; Exactly eight bare 0/1 digits name a SID. Numeric binary interpretation is a
; separate explicit facility; this witness does not reinterpret SID bits as a
; decimal value.

(def bare-sid-sum (00001100 2 3))
(def surface-sum (+ 2 3))

(cond
  ((= bare-sid-sum surface-sum) 1
   (cond
     ((equal? (write-to-string 00000000) "00000000")
      (1)
      (quote (bare-sid-literal-witness (status pass))))
     (t t
      (quote (bare-sid-literal-witness
               (status fail)
               (reason sid-zero-print-roundtrip))))))
  (t t
   (quote (bare-sid-literal-witness
            (status fail)
            (reason sid-call-surface-parity)))))
