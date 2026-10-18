; One-bit output mutants for exact D6:001110 and D6:001111.
; Both mistaken results must be rejected by SENS as D1:0.
(список
  (тотожне? (додати-1 #d24:000000000000000000000000)
       #d24:000000000000000000000000)
  (тотожне? (відняти-1 #d24:000000000000000000000001)
       #d24:000000000000000000000001))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити тотожне? eq?)
(визначити список list)
