; D8:11011100 RASSQ — D3 EQ над CDR, не над ключем.
; D8:11011101 UNTIL — дуальність D6 WHILE під D4 NOT.
; 8 точних відповідей D1:YES; негативні значення мають лишатися NO.
(list
  (equal?
    (асоціація-решта (quote значення-б)
      (list (cons (quote ключ-а) (quote значення-а))
            (cons (quote ключ-б) (quote значення-б))))
    (cons (quote ключ-б) (quote значення-б)))
  (null? (асоціація-решта (quote ключ-б)
           (list (cons (quote ключ-б) (quote значення-б)))))
  (null? (асоціація-решта (quote значення-а) (quote ())))
  (equal?
    (асоціація-решта (quote значення-а)
      (list (cons (quote ключ-а) (quote значення-а))
            (cons (quote ключ-б) (quote значення-б))))
    (cons (quote ключ-а) (quote значення-а)))
  (equal?
    (поки-не
      (lambda (s) (null? (cdr s)))
      (lambda (s) (cdr s))
      (list (quote а) (quote б) (quote в)))
    (list (quote в)))
  (equal?
    (поки-не (lambda (s) (null? s))
             (lambda (s) (cdr s))
             (quote ()))
    (quote ()))
  (equal?
    (поки-не (lambda (s) (null? s))
             (lambda (s) (cdr s))
             (list (quote а) (quote б)))
    (quote ()))
  (not? (equal?
    (поки-не
      (lambda (s) (null? (cdr s)))
      (lambda (s) (cdr s))
      (list (quote а) (quote б) (quote в)))
    (list (quote а) (quote б) (quote в)))))
