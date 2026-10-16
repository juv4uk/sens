; D8:10100000 COPY-LIST — вісім D1 точних позитивних і контрастних свідків.
(list
  (null? (копіювати-список (quote ())))
  (equal? (копіювати-список (list (quote а) (quote б)))
          (list (quote а) (quote б)))
  (equal? (копіювати-список (list (list (quote а)) (quote б)))
          (list (list (quote а)) (quote б)))
  (not? (equal? (копіювати-список (list (quote а) (quote б)))
                (list (quote б) (quote а))))
  (equal? (car (копіювати-список (list (quote а) (quote б))))
          (quote а))
  (equal? (cdr (копіювати-список (list (quote а) (quote б))))
          (list (quote б)))
  (equal? (копіювати-список
            (копіювати-список (list (quote а) (quote б))))
          (list (quote а) (quote б)))
  (equal? (копіювати-список (list (quote а) (quote а)))
          (list (quote а) (quote а))))
