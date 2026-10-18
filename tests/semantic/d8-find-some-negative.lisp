; Wrong-result orientation: FIND 'б' in ('а' 'б') must NOT return 'а'.
(equal?
  (знайти-перший-збіг (quote б) (список (quote а) (quote б)))
  (quote а))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
