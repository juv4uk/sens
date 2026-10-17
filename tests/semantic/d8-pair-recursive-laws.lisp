; D8:11111101 PAIR — рекурсивне спарювання двох належних списків.
; Вісім нативних D1 свідків: порядок CAR/CDR, межа NIL і два негативи.
; Без прямого D8 виклику, нових кодів або літералів D7 замість сутностей.
(list
  (equal? (пара (quote ()) (quote ())) (quote ()))
  (equal? (пара (list (quote а)) (list (quote б)))
          (list (cons (quote а) (quote б))))
  (equal? (пара (list (quote а) (quote б))
                 (list (quote в) (quote г)))
          (list (cons (quote а) (quote в))
                (cons (quote б) (quote г))))
  (equal? (пара (list (quote а) (quote б) (quote в))
                 (list (quote г) (quote д) (quote е)))
          (list (cons (quote а) (quote г))
                (cons (quote б) (quote д))
                (cons (quote в) (quote е))))
  (equal? (пара (quote ()) (list (quote а))) (quote ()))
  (equal? (пара (list (quote а)) (quote ())) (quote ()))
  (not? (equal? (пара (list (quote а)) (list (quote б)))
                (list (cons (quote б) (quote а)))))
  (not? (equal? (пара (list (quote а) (quote б))
                       (list (quote в) (quote г)))
                (list (cons (quote б) (quote в))
                      (cons (quote а) (quote г))))))
