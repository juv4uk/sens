; D8 ASSQ/ASSOC-IF — exact key vs value witnesses, SENS D1 results.
(list
  (equal? (асоціація-тотожна (quote ключ-два)
            (list (cons (quote ключ-один) (quote значення-один))
                  (cons (quote ключ-два) (quote значення-два))))
          (cons (quote ключ-два) (quote значення-два)))
  (null? (асоціація-тотожна (quote немає)
           (list (cons (quote ключ-один) (quote значення-один)))))
  (null? (асоціація-тотожна (quote значення-два)
           (list (cons (quote ключ-два) (quote значення-два)))))
  (equal? (знайти-асоціацію-якщо
            (lambda (x) (equal? x (quote значення-два)))
            (list (cons (quote ключ-один) (quote значення-один))
                  (cons (quote ключ-два) (quote значення-два))))
          (cons (quote ключ-два) (quote значення-два)))
  (null? (знайти-асоціацію-якщо
           (lambda (x) (equal? x (quote немає)))
           (list (cons (quote ключ-два) (quote значення-два)))))
  (null? (знайти-асоціацію-якщо
           (lambda (x) (equal? x (quote ключ-два)))
           (list (cons (quote ключ-два) (quote значення-два)))))
  (null? (знайти-асоціацію-якщо
           (lambda (x) (equal? x (quote будь-що))) (quote ()))))
