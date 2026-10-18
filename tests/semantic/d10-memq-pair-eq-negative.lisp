; D10 MEMQ: EQ is only admitted on atoms, no pair structural equality.
(входження-тотожність (список (як-є а))
  (список (список (як-є а))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити входження-тотожність memq)
