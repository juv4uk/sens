; D9 SENS result-status algebra: six constructors, three projections, 18 D1 verdicts.
; Negative cases: unfamiliar tag, scalar input, pair-valued head, invalid projections.
(список
  (equal? (результат-стан (створити-доведений (quote факт) (список (quote доказ)))) (quote proved))
  (equal? (результат-стан (створити-невідоме (quote предмет))) (quote unknown))
  (equal? (результат-стан (створити-частковий (quote дані) (quote межа))) (quote partial))
  (equal? (результат-стан (створити-заблокований (quote причина))) (quote blocked))
  (equal? (результат-стан (створити-спірний (quote конфлікт))) (quote disputed))
  (equal? (результат-стан (створити-некоректний (quote причина) (quote вміст))) (quote invalid))
  (equal? (результат-вміст (створити-доведений (quote факт) (список (quote доказ)))) (список (quote факт) (список (quote доказ))))
  (equal? (результат-вміст (створити-невідоме (quote предмет))) (список (quote предмет)))
  (equal? (результат-вміст (створити-частковий (quote дані) (quote межа))) (список (quote дані) (quote межа)))
  (equal? (результат-вміст (створити-заблокований (quote причина))) (список (quote причина)))
  (equal? (результат-вміст (створити-спірний (quote конфлікт))) (список (quote конфлікт)))
  (equal? (результат-вміст (створити-некоректний (quote причина) (quote вміст))) (список (quote причина) (quote вміст)))
  (результат-позначений? (створити-невідоме (quote предмет)))
  (хибне? (результат-позначений? (список (quote not-canonical) (quote дані))))
  (хибне? (результат-позначений? (quote атом)))
  (хибне? (результат-позначений? (список (список (quote unknown)) (quote дані))))
  (equal? (результат-стан (список (quote not-canonical) (quote дані))) (quote ()))
  (equal? (результат-вміст (список (quote not-canonical) (quote дані))) (quote ())))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
