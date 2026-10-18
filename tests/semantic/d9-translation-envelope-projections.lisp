; D9:000000101/000101100/000010100/000101110 — eight SENS D1 laws.
; One canonical translation/1 envelope, four positive and four wrong-field negatives.
(список
  (equal? (переклад-стан (список (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) (quote candidate))
  (equal? (переклад-вид (список (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) (quote clause))
  (equal? (переклад-джерело (список (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) "початкове джерело")
  (equal? (переклад-вміст (список (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) (quote твердження))
  (хибне? (equal? (переклад-стан (список (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) (quote rejected)))
  (хибне? (equal? (переклад-вид (список (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) (quote query)))
  (хибне? (equal? (переклад-джерело (список (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) (quote твердження)))
  (хибне? (equal? (переклад-вміст (список (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) "початкове джерело")))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
