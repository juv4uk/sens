; D6:111000/111001 SENS law, рівнодовгі списки, positive + swapped negative.
(list
  (equal? (спарувати-послідовності (quote ()) (quote ())) (quote ()))
  (equal? (розпарувати-пари (quote ())) (list (quote ()) (quote ())))
  (equal? (спарувати-послідовності (list (quote а) (quote б))
                                  (list (quote в) (quote г)))
          (list (cons (quote а) (quote в)) (cons (quote б) (quote г))))
  (equal? (розпарувати-пари
            (спарувати-послідовності (list (quote а) (quote б))
                                    (list (quote в) (quote г))))
          (list (list (quote а) (quote б)) (list (quote в) (quote г))))
  (not? (equal? (розпарувати-пари
                  (спарувати-послідовності (list (quote а) (quote б))
                                          (list (quote в) (quote г))))
                (list (list (quote в) (quote г)) (list (quote а) (quote б))))))
