; D10:0010001110 knowledge-proper-list?, D10:0010010110 result-proper-list?.
; Eight exact D1 observations: accepted empty/proper, rejected atom/dotted.
; Expected (1 1 0 0 1 1 0 0); D3:000 is structural NIL, never D1:0.
(list
  (правильний-список-знань? (quote ()))
  (правильний-список-знань? (list (quote а) (quote б)))
  (правильний-список-знань? (quote а))
  (правильний-список-знань? (сполучити (quote а) (quote б)))
  (правильний-список-результатів? (quote ()))
  (правильний-список-результатів? (list (quote а) (quote б)))
  (правильний-список-результатів? (quote а))
  (правильний-список-результатів? (сполучити (quote а) (quote б))))
