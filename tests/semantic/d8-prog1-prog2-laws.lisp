; D8:00000100 PROG1 / D8:11001001 PROG2.
; Вісім позитивних перевірок: українська та ASCII-проєкції, 2+ аргументи.
; Результати сформовані тільки за чинними SENS-законами.
(list
  (equal? (повернути-перше (quote a) (quote b)) (quote a))
  (equal? (повернути-перше (quote a) (quote b) (quote c)) (quote a))
  (equal? (prog1 (quote a) (quote b)) (quote a))
  (equal? (prog1 (quote a) (quote b) (quote c)) (quote a))
  (equal? (повернути-друге (quote a) (quote b)) (quote b))
  (equal? (повернути-друге (quote a) (quote b) (quote c)) (quote b))
  (equal? (prog2 (quote a) (quote b) (quote c)) (quote b))
  (equal? (prog2 (quote a) (quote b) (quote c) (quote d)) (quote b)))
