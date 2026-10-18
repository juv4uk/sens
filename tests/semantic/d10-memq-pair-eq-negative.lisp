; D10 MEMQ: EQ is only admitted on atoms, no pair structural equality.
(входження-тотожність (список (quote а))
  (список (список (quote а))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити входження-тотожність memq)
