; D9:000000101/000101100/000010100/000101110 — eight SENS D1 laws.
; One canonical translation/1 envelope, four positive and four wrong-field negatives.
(список
  (equal? (переклад-стан (список (як-є translation/1) (як-є candidate) (як-є clause) "початкове джерело" (як-є твердження))) (як-є candidate))
  (equal? (переклад-вид (список (як-є translation/1) (як-є candidate) (як-є clause) "початкове джерело" (як-є твердження))) (як-є clause))
  (equal? (переклад-джерело (список (як-є translation/1) (як-є candidate) (як-є clause) "початкове джерело" (як-є твердження))) "початкове джерело")
  (equal? (переклад-вміст (список (як-є translation/1) (як-є candidate) (як-є clause) "початкове джерело" (як-є твердження))) (як-є твердження))
  (хибне? (equal? (переклад-стан (список (як-є translation/1) (як-є candidate) (як-є clause) "початкове джерело" (як-є твердження))) (як-є rejected)))
  (хибне? (equal? (переклад-вид (список (як-є translation/1) (як-є candidate) (як-є clause) "початкове джерело" (як-є твердження))) (як-є query)))
  (хибне? (equal? (переклад-джерело (список (як-є translation/1) (як-є candidate) (як-є clause) "початкове джерело" (як-є твердження))) (як-є твердження)))
  (хибне? (equal? (переклад-вміст (список (як-є translation/1) (як-є candidate) (як-є clause) "початкове джерело" (як-є твердження))) "початкове джерело")))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
