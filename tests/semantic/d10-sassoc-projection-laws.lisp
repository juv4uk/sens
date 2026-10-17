; 12 незалежних фізичних позитивів D10 SASSOC та en-проєкцій.
; Всі результати обчислює SENS через власний reader/eval.
(list
  (equal? (пошук-асоціації
            (quote а)
            (list (cons (quote а) (quote перше))
                  (cons (quote б) (quote друге))))
          (cons (quote а) (quote перше)))
  (equal? (sassoc
            (quote б)
            (list (cons (quote а) (quote перше))
                  (cons (quote б) (quote друге))))
          (cons (quote б) (quote друге)))
  (equal? (sassoc
            (quote відсутній)
            (list (cons (quote а) (quote перше))))
          (quote ()))
  (empty-queue? (quote ()))
  (not? (empty-queue? (quote (а))))
  (equal? (sortcar
            (list (list (довжина (quote (а б))) (quote друге))
                  (list (довжина (quote (а))) (quote перше))))
          (list (list (довжина (quote (а))) (quote перше))
                (list (довжина (quote (а б))) (quote друге))))
  (equal? (result-count (quote (а б)))
          (довжина (quote (а б))))
  (knowledge-proper-list? (quote (а б)))
  (not? (knowledge-proper-list? (cons (quote а) (quote б))))
  (result-proper-list? (quote (а б)))
  (not? (result-proper-list? (cons (quote а) (quote б))))
  (forall-every-candidate-satisfies?
    (0010 (x) (not? (0101 x)))
    (quote (а б))))
