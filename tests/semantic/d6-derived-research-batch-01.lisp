; D6 batch-01 #5854 — дев'ять SENS власних D1-предикатних законів.
; RASSOC, ANY, ALL: жодного оголошення прямої D6 callability.
(list
  (equal?
    (знайти-за-значенням (quote значення-два)
      (list (cons (quote ключ-один) (quote значення-один))
            (cons (quote ключ-два) (quote значення-два))))
    (cons (quote ключ-два) (quote значення-два)))
  (null? (знайти-за-значенням (quote невідоме)
           (list (cons (quote ключ-один) (quote значення-один)))))
  (null? (знайти-за-значенням (quote ключ-два)
           (list (cons (quote ключ-два) (quote значення-два)))))
  (not? (будь-яке? (lambda (х) (equal? х (quote є))) (quote ())))
  (будь-яке? (lambda (х) (equal? х (quote є)))
             (list (quote нема) (quote є)))
  (not? (будь-яке? (lambda (х) (equal? х (quote є)))
                    (list (quote нема) (quote ні))))
  (усі? (lambda (х) (equal? х (quote є))) (quote ()))
  (усі? (lambda (х) (equal? х (quote є)))
        (list (quote є) (quote є)))
  (not? (усі? (lambda (х) (equal? х (quote є)))
              (list (quote є) (quote нема)))))
