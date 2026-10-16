; D8:00010011 MAPLIST-right. Law #3744; exact result (1 1 0).
; Positive: asymmetric three-element left prefixes in longest-first order.
; Positive empty list; negative: reversing only source omits callback conjugation.
(list
  (equal?
    (залишки-справа
      (list (quote а) (quote б) (quote в))
      (функція (хвіст) хвіст))
    (list
      (list (quote а) (quote б) (quote в))
      (list (quote а) (quote б))
      (list (quote а))))
  (equal?
    (залишки-справа (list) (функція (хвіст) хвіст))
    (list))
  (equal?
    (залишки-справа
      (list (quote а) (quote б))
      (функція (хвіст) хвіст))
    (відобразити-залишки
      (зворот (list (quote а) (quote б)))
      (функція (хвіст) хвіст))))
