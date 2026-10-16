; D6:111000/111001 — шість D1 свідків; останній має точний D1 мутант.
(list
  (equal? (спарувати-послідовності (list (quote а) (quote б)) (list (quote в) (quote г)))
          (list (cons (quote а) (quote в)) (cons (quote б) (quote г))))
  (equal? (розпарувати-пари (list (cons (quote а) (quote в)) (cons (quote б) (quote г))))
          (list (list (quote а) (quote б)) (list (quote в) (quote г))))
  (equal? (розпарувати-пари
            (спарувати-послідовності (list (quote а) (quote б)) (list (quote в) (quote г))))
          (list (list (quote а) (quote б)) (list (quote в) (quote г))))
  (equal? (розпарувати-пари (quote ())) (list (quote ()) (quote ())))
  (not? (equal?
          (спарувати-послідовності (list (quote в) (quote г)) (list (quote а) (quote б)))
          (list (cons (quote а) (quote в)) (cons (quote б) (quote г)))))
  (110 ((101 (null? (розпарувати-пари (quote ()))) #d1:1) #d1:1)
       (#d1:1 (#d1:0))))
