(C1-EVAL
  (QUOTE
    (((LAMBDA (MARK)
        ((LAMBDA (FIX)
           (FIX
             (LAMBDA (RECUR)
               (LAMBDA (XS)
                 (COND
                   ((EQ XS NIL) MARK)
                   (T (RECUR (CDR XS))))))))
         (LAMBDA (F)
           ((LAMBDA (X)
              (F
                (LAMBDA (V)
                  ((X X) V))))
            (LAMBDA (X)
              (F
                (LAMBDA (V)
                  ((X X) V))))))))
      (QUOTE CAPTURED))
     (QUOTE (A B))))
  NIL
  NIL)
