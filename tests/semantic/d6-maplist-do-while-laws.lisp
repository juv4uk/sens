; D6:000101 MAPLIST(list, function) / D6:110010 DO / D6:110011 WHILE — власна SENS семантика.
; Вісім D1:YES: позитивні закони, спростування переставленого хвоста,
; негативне завершення DO і негативний контроль неправильного стану WHILE.
; Не заявляє direct D6:bits callability. Нативний CLI завантажує lib/core4.lisp.
(list
  (equal? (відобразити-залишки (list (quote ()) (list (quote ()))) (lambda (tail) (car tail))) (list (quote ()) (list (quote ()))))
  (not? (equal? (відобразити-залишки (list (quote ()) (list (quote ()))) (lambda (tail) (car tail))) (list (list (quote ())) (quote ()))))
  (null? (відобразити-залишки (quote ()) (lambda (tail) (car tail))))
  (робити (lambda (x) (quote ())) (lambda (x) (null? x)) (lambda (x) (null? x)) (list (quote ())))
  (not? (робити (lambda (x) (quote ())) (lambda (x) (null? x)) (lambda (x) (not? (null? x))) (list (quote ()))))
  (null? (поки (lambda (x) (not? (null? x))) (lambda (x) (quote ())) (list (quote ()))))
  (not? (equal? (поки (lambda (x) (not? (null? x))) (lambda (x) (quote ())) (list (quote ()))) (list (quote ()))))
  (null? (поки (lambda (x) (not? (null? x))) (lambda (x) (quote ())) (quote ())))  ; D6:111100 ANY і D6:111101 ALL — D1-предикати без FILTER.
  (будь-яке? (lambda (x) (null? x))
             (list (list (quote ())) (quote ())))
  (not? (будь-яке? (lambda (x) (null? x))
                   (list (list (quote ())))))
  (усі? (lambda (x) (null? x))
        (list (quote ()) (quote ())))
  (not? (усі? (lambda (x) (null? x))
              (list (quote ()) (list (quote ())))))
  (not? (будь-яке? (lambda (x) (null? x)) (quote ())))
  (усі? (lambda (x) (null? x)) (quote ()))
)
