; D8:10111001 правий REDUCE: D5 REVERSE + D6 FLIP + D6 REDUCE (#3674).
; 4 D1:YES, включно з некомутативним CONS і негативною перестановкою.
; Лише SENS мовна функція: це не direct D8:bits opcode.
(список
  (equal? (згорнути-справа (lambda (left right) (сполучити left right)) (quote ()) (список (quote ()) (список (quote ())))) (список (quote ()) (список (quote ()))))
  (хибне? (equal? (згорнути-справа (lambda (left right) (сполучити left right)) (quote ()) (список (quote ()) (список (quote ())))) (список (список (quote ())) (quote ()))))
  (порожній? (згорнути-справа (lambda (left right) (сполучити left right)) (quote ()) (quote ())))
  (equal? (згорнути-справа (lambda (left right) (сполучити left right)) (quote ()) (список (quote ()))) (список (quote ())))
)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити сполучити cons)
(визначити список list)
(визначити хибне? not?)
(визначити порожній? null?)
