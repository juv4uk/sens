(C1-EVAL
  (QUOTE
    ((LAMBDA (FIX)
       ((FIX
          (LAMBDA (SELF)
            (LAMBDA (XS)
              (COND
                ((EQ XS NIL) (QUOTE DONE))
                (T (SELF (CDR XS)))))))
        (QUOTE (A))))
     (LAMBDA (F)
       ((LAMBDA (X)
          (F
            (LAMBDA (V)
              ((X X) V))))
        (LAMBDA (X)
          (F
            (LAMBDA (V)
              ((X X) V))))))))
  NIL
  NIL)
