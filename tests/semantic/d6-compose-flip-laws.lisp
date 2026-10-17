; D6:001011 COMPOSE and D6:101101 FLIP are Lisp-owned D4 LAMBDA derivations.
; These are callable ordinary SENS functions, not direct native D6 opcodes.
; Eight positive/falsifier laws: exact D1:YES iff the order is right.
(list
  ; COMPOSE(f,g)(x) = f(g(x)); CDR then CAR yields the second item.
  (eq? ((скласти-функції
          (lambda (x) (car x))
          (lambda (x) (cdr x)))
        '(ліве праве))
       'праве)
  (not? (eq? ((скласти-функції
                (lambda (x) (car x))
                (lambda (x) (cdr x)))
              '(ліве праве))
            'ліве))
  ; The composed closure captures independently supplied f and g.
  (eq? ((скласти-функції
          (lambda (x) (car x))
          (lambda (x) (cons x '())))
        'значення)
       'значення)
  (not? (eq? ((скласти-функції
                (lambda (x) (car x))
                (lambda (x) (cons x '())))
              'значення)
            'інше))
  ; FLIP(f)(a,b) = f(b,a); result is the reversed two-element list.
  (eq? (car ((поміняти-аргументи
               (lambda (a b) (cons a (cons b '()))))
             'ліве 'праве))
       'праве)
  (eq? (car (cdr ((поміняти-аргументи
                    (lambda (a b) (cons a (cons b '()))))
                  'ліве 'праве))
       'ліве))
  (not? (eq? (car ((поміняти-аргументи
                     (lambda (a b) (cons a (cons b '()))))
                   'ліве 'праве))
             'ліве))
  (not? (eq? (car (cdr ((поміняти-аргументи
                          (lambda (a b) (cons a (cons b '()))))
                        'ліве 'праве))
              'праве))))
