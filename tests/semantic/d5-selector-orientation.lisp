; D5:01100..01111,10000..10011 — 8 позитивних та 8 негативних SENS свідків.
; Пряма D5 викличність не відкривається: тестуються мовні D4:0011 визначення.
; Негатив: одна заміна бітового CAR/CDR в селекторному ланцюгу.
(list
  (eq? (р-п-п (cons (cons (cons (quote хиба-0) (quote ціль)) (quote хиба-1)) (quote хиба-2))) (quote ціль))
  (not? (eq? (car (car (car (cons (cons (cons (quote хиба-0) (quote ціль)) (quote хиба-1)) (quote хиба-2))))) (quote ціль)))
  (eq? (р-п-р (cons (quote хиба-2) (cons (cons (quote хиба-0) (quote ціль)) (quote хиба-1)))) (quote ціль))
  (not? (eq? (car (car (cdr (cons (quote хиба-2) (cons (cons (quote хиба-0) (quote ціль)) (quote хиба-1)))))) (quote ціль)))
  (eq? (р-р-п (cons (cons (quote хиба-1) (cons (quote хиба-0) (quote ціль))) (quote хиба-2))) (quote ціль))
  (not? (eq? (car (cdr (car (cons (cons (quote хиба-1) (cons (quote хиба-0) (quote ціль))) (quote хиба-2))))) (quote ціль)))
  (eq? (р-р-р (cons (quote хиба-2) (cons (quote хиба-1) (cons (quote хиба-0) (quote ціль))))) (quote ціль))
  (not? (eq? (car (cdr (cdr (cons (quote хиба-2) (cons (quote хиба-1) (cons (quote хиба-0) (quote ціль))))))) (quote ціль)))
  (eq? (п-п-п (cons (cons (cons (quote ціль) (quote хиба-0)) (quote хиба-1)) (quote хиба-2))) (quote ціль))
  (not? (eq? (cdr (car (car (cons (cons (cons (quote ціль) (quote хиба-0)) (quote хиба-1)) (quote хиба-2))))) (quote ціль)))
  (eq? (п-п-р (cons (quote хиба-2) (cons (cons (quote ціль) (quote хиба-0)) (quote хиба-1)))) (quote ціль))
  (not? (eq? (cdr (car (cdr (cons (quote хиба-2) (cons (cons (quote ціль) (quote хиба-0)) (quote хиба-1)))))) (quote ціль)))
  (eq? (п-р-п (cons (cons (quote хиба-1) (cons (quote ціль) (quote хиба-0))) (quote хиба-2))) (quote ціль))
  (not? (eq? (cdr (cdr (car (cons (cons (quote хиба-1) (cons (quote ціль) (quote хиба-0))) (quote хиба-2))))) (quote ціль)))
  (eq? (п-р-р (cons (quote хиба-2) (cons (quote хиба-1) (cons (quote ціль) (quote хиба-0))))) (quote ціль))
  (not? (eq? (cdr (cdr (cdr (cons (quote хиба-2) (cons (quote хиба-1) (cons (quote ціль) (quote хиба-0))))))) (quote ціль)))
)
