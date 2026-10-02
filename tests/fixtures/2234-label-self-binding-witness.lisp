(C1-EVAL
  (QUOTE
    ((LABEL SELF
       (LAMBDA (XS)
         (COND
           ((EQ XS NIL) (QUOTE DONE))
           (T (SELF (CDR XS))))))
     (QUOTE (A))))
  NIL
  NIL)
