; D10:0010001110 knowledge-proper-list?, D10:0010010110 result-proper-list?.
; Eight exact D1 observations: accepted empty/proper, rejected atom/dotted.
; Expected (1 1 0 0 1 1 0 0); D3:000 is structural NIL, never D1:0.
(список
  (правильний-список-знань? (quote ()))
  (правильний-список-знань? (список (quote а) (quote б)))
  (правильний-список-знань? (quote а))
  (правильний-список-знань? (сполучити (quote а) (quote б)))
  (правильний-список-результатів? (quote ()))
  (правильний-список-результатів? (список (quote а) (quote б)))
  (правильний-список-результатів? (quote а))
  (правильний-список-результатів? (сполучити (quote а) (quote б))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
