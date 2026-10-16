; Чотирнадцять незалежних scalar D1:YES свідків функцій D6.
; Кожний наступний рядок — одна повна програма SENS для native CLI.
; Спеціальні неправильні результати й перестановки перевіряються всередині SENS через NOT/EQ.
(equal? (відобразити-залишки (list (quote ()) (list (quote ()))) (lambda (tail) (car tail))) (list (quote ()) (list (quote ()))))
(not? (equal? (відобразити-залишки (list (quote ()) (list (quote ()))) (lambda (tail) (car tail))) (list (list (quote ())) (quote ()))))
(null? (відобразити-залишки (quote ()) (lambda (tail) (car tail))))
(робити (lambda (x) (quote ())) (lambda (x) (null? x)) (lambda (x) (null? x)) (list (quote ())))
(not? (робити (lambda (x) (quote ())) (lambda (x) (null? x)) (lambda (x) (not? (null? x))) (list (quote ()))))
(null? (поки (lambda (x) (not? (null? x))) (lambda (x) (quote ())) (list (quote ()))))
(not? (equal? (поки (lambda (x) (not? (null? x))) (lambda (x) (quote ())) (list (quote ()))) (list (quote ()))))
(null? (поки (lambda (x) (not? (null? x))) (lambda (x) (quote ())) (quote ())))
(будь-яке? (lambda (x) (null? x)) (list (list (quote ())) (quote ())))
(not? (будь-яке? (lambda (x) (null? x)) (list (list (quote ())))))
(усі? (lambda (x) (null? x)) (list (quote ()) (quote ())))
(not? (усі? (lambda (x) (null? x)) (list (quote ()) (list (quote ())))))
(not? (будь-яке? (lambda (x) (null? x)) (quote ())))
(усі? (lambda (x) (null? x)) (quote ()))
