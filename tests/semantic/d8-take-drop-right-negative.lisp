; Falsifier: TAKE-right(1, [а, б, в]) != [а]; incorrect left edge is D1:0.
(equal?
  (взяти-справа #d24:000000000000000000000001
    (список (як-є а) (як-є б) (як-є в)))
  (список (як-є а)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
