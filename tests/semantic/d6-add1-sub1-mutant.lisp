; One-bit output mutants for exact D6:001110 and D6:001111.
; Both mistaken results must be rejected by SENS as D1:0.
(list
  (eq? (додати-1 #d24:000000000000000000000000)
       #d24:000000000000000000000000)
  (eq? (відняти-1 #d24:000000000000000000000001)
       #d24:000000000000000000000001))
