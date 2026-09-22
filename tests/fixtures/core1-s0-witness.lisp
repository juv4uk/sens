
(C1-EVAL
  (QUOTE
    (((LAMBDA (X)
        (LAMBDA (Y)
          (CONS X Y)))
      (QUOTE A))
     (QUOTE B)))
  NIL
  NIL)

(C1-WORLD-VALUE
  (C1-EVAL-PROGRAM
    (QUOTE
      ((DEFINE LAST
         (LAMBDA (XS)
           (COND
             ((EQ (CDR XS) NIL) (CAR XS))
             (T (LAST (CDR XS))))))
       (LAST (QUOTE (A B C)))))
    NIL))

(C1-EVAL
  (QUOTE (VECTOR (QUOTE A)))
  NIL
  NIL)
