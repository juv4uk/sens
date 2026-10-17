; 15 фізичних D1-законів D10:0001100101 SASSOC та сімох en-проєкцій.
; SASSOC = MacLisp EQUAL + нульаргументна запасна дія (не ASSOC/2).
; Тільки процес SENS оцінює ці закони; зовнішні скрипти не визначають семантики.
(list
  (equal? (пошук-асоціації
            (quote а)
            (list (cons (quote а) (quote перше))
                  (cons (quote б) (quote друге)))
            (0010 () (quote немає)))
          (cons (quote а) (quote перше)))
  (equal? (sassoc
            (quote б)
            (list (cons (quote а) (quote перше))
                  (cons (quote б) (quote друге)))
            (quote не-викликати))
          (cons (quote б) (quote друге)))
  (equal? (sassoc
            (quote відсутній)
            (list (cons (quote а) (quote перше)))
            (0010 () (quote резерв)))
          (quote резерв))
  (equal? (sassoc
            (quote порожньо) (quote ())
            (0010 () (quote порожній-резерв)))
          (quote порожній-резерв))
  (equal? (sassoc
            (list (quote складений))
            (list (cons (list (quote складений)) (quote структурний-збіг)))
            (0010 () (quote немає)))
          (cons (list (quote складений)) (quote структурний-збіг)))
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
    (quote (а б)))
  (not? (forall-every-candidate-satisfies?
          (0010 (x) (0101 x))
          (quote (а б)))))
