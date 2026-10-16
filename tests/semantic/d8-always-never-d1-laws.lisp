; D8:10101110 ALWAYS / D8:11001010 NEVER, поверхні лише D1.
; Вісім точних D1:YES, зокрема фальсифікатори одного D1:NO та YES.
(list
  (усі-істинні? (quote ()))
  (жодне-істинне? (quote ()))
  (усі-істинні?
    (list (null? (quote ())) (null? (quote ()))))
  (not? (усі-істинні?
    (list (null? (quote ())) (null? (list (quote ()))))))
  (жодне-істинне?
    (list (null? (list (quote ()))) (null? (list (quote ())))))
  (not? (жодне-істинне?
    (list (null? (list (quote ()))) (null? (quote ())))))
  (not? (усі-істинні?
    (list (null? (list (quote ()))))))
  (not? (жодне-істинне?
    (list (null? (quote ()))))))
