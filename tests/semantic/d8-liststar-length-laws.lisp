; D8:00011101 LIST*, 00111110 LENGTH-LIST, 01001111 LIST-LENGTH.
; Вісім явних D1-контролів, структурна пара ≠ правильний список.
(list
  (equal? (неправильний-список (quote а) (quote б))
          (cons (quote а) (quote б)))
  (equal? (неправильний-список (quote а) (quote б) (quote в))
          (cons (quote а) (cons (quote б) (quote в))))
  (equal? (неправильний-список (quote а) (quote ()))
          (list (quote а)))
  (equal? (неправильний-список (quote а)) (quote а))
  (equal? (довжина-списку (quote ()))
          #d24:000000000000000000000000)
  (equal? (довжина-списку (list (quote а) (quote б)))
          #d24:000000000000000000000010)
  (equal? (список-довжина (quote ()))
          #d24:000000000000000000000000)
  (equal? (список-довжина (list (quote а)))
          #d24:000000000000000000000001))
