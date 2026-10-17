; D9:000000101/000101100/000010100/000101110 — eight SENS D1 laws.
; One canonical translation/1 envelope, four positive and four wrong-field negatives.
(list
  (equal? (переклад-стан (list (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) (quote candidate))
  (equal? (переклад-вид (list (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) (quote clause))
  (equal? (переклад-джерело (list (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) "початкове джерело")
  (equal? (переклад-вміст (list (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) (quote твердження))
  (not? (equal? (переклад-стан (list (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) (quote rejected)))
  (not? (equal? (переклад-вид (list (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) (quote query)))
  (not? (equal? (переклад-джерело (list (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) (quote твердження)))
  (not? (equal? (переклад-вміст (list (quote translation/1) (quote candidate) (quote clause) "початкове джерело" (quote твердження))) "початкове джерело")))
