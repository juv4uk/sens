; D8:00000100 PROG1 / D8:11001001 PROG2.
; Вісім позитивних перевірок: українська та ASCII-проєкції, 2+ аргументи.
; Результати сформовані тільки за чинними SENS-законами.
(список
  (equal? (повернути-перше (quote a) (quote b)) (quote a))
  (equal? (повернути-перше (quote a) (quote b) (quote c)) (quote a))
  (equal? (послідовність-повернути-перше (quote a) (quote b)) (quote a))
  (equal? (послідовність-повернути-перше (quote a) (quote b) (quote c)) (quote a))
  (equal? (повернути-друге (quote a) (quote b)) (quote b))
  (equal? (повернути-друге (quote a) (quote b) (quote c)) (quote b))
  (equal? (послідовність-повернути-друге (quote a) (quote b) (quote c)) (quote b))
  (equal? (послідовність-повернути-друге (quote a) (quote b) (quote c) (quote d)) (quote b)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити послідовність-повернути-перше prog1)
(визначити послідовність-повернути-друге prog2)
