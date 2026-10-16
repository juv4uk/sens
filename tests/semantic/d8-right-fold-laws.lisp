; D8:10111001 правий REDUCE: D5 REVERSE + D6 FLIP + D6 REDUCE (#3674).
; 4 D1:YES, включно з некомутативним CONS і негативною перестановкою.
; Лише SENS мовна функція: це не direct D8:bits opcode.
(list
  (equal? (згорнути-справа (lambda (left right) (cons left right)) (quote ()) (list (quote ()) (list (quote ())))) (list (quote ()) (list (quote ()))))
  (not? (equal? (згорнути-справа (lambda (left right) (cons left right)) (quote ()) (list (quote ()) (list (quote ())))) (list (list (quote ())) (quote ()))))
  (null? (згорнути-справа (lambda (left right) (cons left right)) (quote ()) (quote ())))
  (equal? (згорнути-справа (lambda (left right) (cons left right)) (quote ()) (list (quote ()))) (list (quote ())))
)
