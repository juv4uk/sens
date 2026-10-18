; Wrong-result orientation: FIND 'б' in ('а' 'б') must NOT return 'а'.
(equal?
  (знайти-перший-збіг (як-є б) (список (як-є а) (як-є б)))
  (як-є а))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
