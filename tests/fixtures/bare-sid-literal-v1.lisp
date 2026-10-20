; #1096 — bare domain identities as first-class semantic values.
; Semantic authority stays here in Lisp. Host observers may only execute this
; witness and check its named pass/fail envelope.
; Ukrainian projection: decimal arithmetic, no SID8 call heads.

(визначити bare-sid-sum (додати 2 3))
(визначити surface-sum (додати 2 3))

(за-умовою
  ((тотожне? bare-sid-sum surface-sum)
   (як-є (bare-sid-literal-witness (status pass))))
  (так
   (як-є (bare-sid-literal-witness
            (status fail)
            (reason sid-call-surface-parity)))))
