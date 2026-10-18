; D8:00010011 MAPLIST-right. Law #3744; exact result (1 1 0).
; Positive: asymmetric three-element left prefixes in longest-first order.
; Positive empty list; negative: reversing only source omits callback conjugation.
(список
  (equal?
    (залишки-справа
      (список (quote а) (quote б) (quote в))
      (функція (хвіст) хвіст))
    (список
      (список (quote а) (quote б) (quote в))
      (список (quote а) (quote б))
      (список (quote а))))
  (equal?
    (залишки-справа (список) (функція (хвіст) хвіст))
    (список))
  (equal?
    (залишки-справа
      (список (quote а) (quote б))
      (функція (хвіст) хвіст))
    (відобразити-залишки
      (зворот (список (quote а) (quote б)))
      (функція (хвіст) хвіст))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
