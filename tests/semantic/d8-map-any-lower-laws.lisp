; D8:01000111 MAP-ANY — похідний D1-закон короткого замикання через D6 ANY.
; 8 точних D1 результатів; порожні та асиметричні списки, негатив результату.
(list
  (not? (відобразити-доки-істина (lambda (x) (eq? x (quote є))) (quote ())))
  (відобразити-доки-істина (lambda (x) (eq? x (quote є)))
                           (list (quote нема) (quote є)))
  (not? (відобразити-доки-істина (lambda (x) (eq? x (quote є)))
                                 (list (quote нема) (quote ні))))
  (відобразити-доки-істина (lambda (x) (eq? x (quote є)))
                           (list (quote є) (quote нема)))
  (equal? (відобразити-доки-істина (lambda (x) (eq? x (quote є)))
                                    (list (quote є)))
          (будь-яке? (lambda (x) (eq? x (quote є))) (list (quote є))))
  (equal? (відобразити-доки-істина (lambda (x) (eq? x (quote є))) (quote ()))
          (будь-яке? (lambda (x) (eq? x (quote є))) (quote ())))
  (not? (відобразити-доки-істина (lambda (x) (eq? x (quote є)))
                                 (list (quote ні) (quote ні))))
  (відобразити-доки-істина (lambda (x) (eq? x (quote є)))
                           (list (quote ні) (quote є) (quote ні))))
