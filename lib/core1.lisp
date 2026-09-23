
(DEFINE C1-SECOND
  (LAMBDA (X)
    (CAR (CDR X))))

(DEFINE C1-THIRD
  (LAMBDA (X)
    (CAR (CDR (CDR X)))))

(DEFINE C1-FOURTH
  (LAMBDA (X)
    (CAR (CDR (CDR (CDR X))))))

(DEFINE C1-MAKE-ERROR
  (LAMBDA (KIND DETAIL)
    (CONS (QUOTE C1-ERROR)
      (CONS KIND
        (CONS DETAIL NIL)))))

(DEFINE C1-ERRORP
  (LAMBDA (VALUE)
    (COND
      ((ATOM VALUE) NIL)
      ((EQ (CAR VALUE) (QUOTE C1-ERROR)) T)
      (T NIL))))

(DEFINE C1-MAKE-FOUND
  (LAMBDA (VALUE)
    (CONS (QUOTE C1-FOUND)
      (CONS VALUE NIL))))

(DEFINE C1-FOUNDP
  (LAMBDA (VALUE)
    (COND
      ((ATOM VALUE) NIL)
      ((EQ (CAR VALUE) (QUOTE C1-FOUND)) T)
      (T NIL))))

(DEFINE C1-FOUND-VALUE
  (LAMBDA (VALUE)
    (C1-SECOND VALUE)))

(DEFINE C1-LOOKUP-IN
  (LABEL C1-LOOKUP-IN
    (LAMBDA (NAME ENV)
      (COND
        ((EQ ENV NIL) (QUOTE C1-MISSING))
        ((EQ (CAR (CAR ENV)) NAME)
         (C1-MAKE-FOUND (CDR (CAR ENV))))
        (T
         (C1-LOOKUP-IN NAME (CDR ENV)))))))

; The complete exact 8-bit token space is reserved for function identity.
; This recognizes the representation class only; it assigns no operation
; meaning. The nested 16x16 shape keeps each historical Core1 COND bounded.
(DEFINE C1-SID-VALUEP
  (LAMBDA (VALUE)
    (COND
      ((EQ VALUE 00000000) T)
      ((EQ VALUE 00000001) T)
      ((EQ VALUE 00000010) T)
      ((EQ VALUE 00000011) T)
      ((EQ VALUE 00000100) T)
      ((EQ VALUE 00000101) T)
      ((EQ VALUE 00000110) T)
      ((EQ VALUE 00000111) T)
      ((EQ VALUE 00001000) T)
      ((EQ VALUE 00001001) T)
      ((EQ VALUE 00001010) T)
      ((EQ VALUE 00001011) T)
      ((EQ VALUE 00001100) T)
      ((EQ VALUE 00001101) T)
      ((EQ VALUE 00001110) T)
      ((EQ VALUE 00001111) T)
      (T
        (COND
          ((EQ VALUE 00010000) T)
          ((EQ VALUE 00010001) T)
          ((EQ VALUE 00010010) T)
          ((EQ VALUE 00010011) T)
          ((EQ VALUE 00010100) T)
          ((EQ VALUE 00010101) T)
          ((EQ VALUE 00010110) T)
          ((EQ VALUE 00010111) T)
          ((EQ VALUE 00011000) T)
          ((EQ VALUE 00011001) T)
          ((EQ VALUE 00011010) T)
          ((EQ VALUE 00011011) T)
          ((EQ VALUE 00011100) T)
          ((EQ VALUE 00011101) T)
          ((EQ VALUE 00011110) T)
          ((EQ VALUE 00011111) T)
          (T
            (COND
              ((EQ VALUE 00100000) T)
              ((EQ VALUE 00100001) T)
              ((EQ VALUE 00100010) T)
              ((EQ VALUE 00100011) T)
              ((EQ VALUE 00100100) T)
              ((EQ VALUE 00100101) T)
              ((EQ VALUE 00100110) T)
              ((EQ VALUE 00100111) T)
              ((EQ VALUE 00101000) T)
              ((EQ VALUE 00101001) T)
              ((EQ VALUE 00101010) T)
              ((EQ VALUE 00101011) T)
              ((EQ VALUE 00101100) T)
              ((EQ VALUE 00101101) T)
              ((EQ VALUE 00101110) T)
              ((EQ VALUE 00101111) T)
              (T
                (COND
                  ((EQ VALUE 00110000) T)
                  ((EQ VALUE 00110001) T)
                  ((EQ VALUE 00110010) T)
                  ((EQ VALUE 00110011) T)
                  ((EQ VALUE 00110100) T)
                  ((EQ VALUE 00110101) T)
                  ((EQ VALUE 00110110) T)
                  ((EQ VALUE 00110111) T)
                  ((EQ VALUE 00111000) T)
                  ((EQ VALUE 00111001) T)
                  ((EQ VALUE 00111010) T)
                  ((EQ VALUE 00111011) T)
                  ((EQ VALUE 00111100) T)
                  ((EQ VALUE 00111101) T)
                  ((EQ VALUE 00111110) T)
                  ((EQ VALUE 00111111) T)
                  (T
                    (COND
                      ((EQ VALUE 01000000) T)
                      ((EQ VALUE 01000001) T)
                      ((EQ VALUE 01000010) T)
                      ((EQ VALUE 01000011) T)
                      ((EQ VALUE 01000100) T)
                      ((EQ VALUE 01000101) T)
                      ((EQ VALUE 01000110) T)
                      ((EQ VALUE 01000111) T)
                      ((EQ VALUE 01001000) T)
                      ((EQ VALUE 01001001) T)
                      ((EQ VALUE 01001010) T)
                      ((EQ VALUE 01001011) T)
                      ((EQ VALUE 01001100) T)
                      ((EQ VALUE 01001101) T)
                      ((EQ VALUE 01001110) T)
                      ((EQ VALUE 01001111) T)
                      (T
                        (COND
                          ((EQ VALUE 01010000) T)
                          ((EQ VALUE 01010001) T)
                          ((EQ VALUE 01010010) T)
                          ((EQ VALUE 01010011) T)
                          ((EQ VALUE 01010100) T)
                          ((EQ VALUE 01010101) T)
                          ((EQ VALUE 01010110) T)
                          ((EQ VALUE 01010111) T)
                          ((EQ VALUE 01011000) T)
                          ((EQ VALUE 01011001) T)
                          ((EQ VALUE 01011010) T)
                          ((EQ VALUE 01011011) T)
                          ((EQ VALUE 01011100) T)
                          ((EQ VALUE 01011101) T)
                          ((EQ VALUE 01011110) T)
                          ((EQ VALUE 01011111) T)
                          (T
                            (COND
                              ((EQ VALUE 01100000) T)
                              ((EQ VALUE 01100001) T)
                              ((EQ VALUE 01100010) T)
                              ((EQ VALUE 01100011) T)
                              ((EQ VALUE 01100100) T)
                              ((EQ VALUE 01100101) T)
                              ((EQ VALUE 01100110) T)
                              ((EQ VALUE 01100111) T)
                              ((EQ VALUE 01101000) T)
                              ((EQ VALUE 01101001) T)
                              ((EQ VALUE 01101010) T)
                              ((EQ VALUE 01101011) T)
                              ((EQ VALUE 01101100) T)
                              ((EQ VALUE 01101101) T)
                              ((EQ VALUE 01101110) T)
                              ((EQ VALUE 01101111) T)
                              (T
                                (COND
                                  ((EQ VALUE 01110000) T)
                                  ((EQ VALUE 01110001) T)
                                  ((EQ VALUE 01110010) T)
                                  ((EQ VALUE 01110011) T)
                                  ((EQ VALUE 01110100) T)
                                  ((EQ VALUE 01110101) T)
                                  ((EQ VALUE 01110110) T)
                                  ((EQ VALUE 01110111) T)
                                  ((EQ VALUE 01111000) T)
                                  ((EQ VALUE 01111001) T)
                                  ((EQ VALUE 01111010) T)
                                  ((EQ VALUE 01111011) T)
                                  ((EQ VALUE 01111100) T)
                                  ((EQ VALUE 01111101) T)
                                  ((EQ VALUE 01111110) T)
                                  ((EQ VALUE 01111111) T)
                                  (T
                                    (COND
                                      ((EQ VALUE 10000000) T)
                                      ((EQ VALUE 10000001) T)
                                      ((EQ VALUE 10000010) T)
                                      ((EQ VALUE 10000011) T)
                                      ((EQ VALUE 10000100) T)
                                      ((EQ VALUE 10000101) T)
                                      ((EQ VALUE 10000110) T)
                                      ((EQ VALUE 10000111) T)
                                      ((EQ VALUE 10001000) T)
                                      ((EQ VALUE 10001001) T)
                                      ((EQ VALUE 10001010) T)
                                      ((EQ VALUE 10001011) T)
                                      ((EQ VALUE 10001100) T)
                                      ((EQ VALUE 10001101) T)
                                      ((EQ VALUE 10001110) T)
                                      ((EQ VALUE 10001111) T)
                                      (T
                                        (COND
                                          ((EQ VALUE 10010000) T)
                                          ((EQ VALUE 10010001) T)
                                          ((EQ VALUE 10010010) T)
                                          ((EQ VALUE 10010011) T)
                                          ((EQ VALUE 10010100) T)
                                          ((EQ VALUE 10010101) T)
                                          ((EQ VALUE 10010110) T)
                                          ((EQ VALUE 10010111) T)
                                          ((EQ VALUE 10011000) T)
                                          ((EQ VALUE 10011001) T)
                                          ((EQ VALUE 10011010) T)
                                          ((EQ VALUE 10011011) T)
                                          ((EQ VALUE 10011100) T)
                                          ((EQ VALUE 10011101) T)
                                          ((EQ VALUE 10011110) T)
                                          ((EQ VALUE 10011111) T)
                                          (T
                                            (COND
                                              ((EQ VALUE 10100000) T)
                                              ((EQ VALUE 10100001) T)
                                              ((EQ VALUE 10100010) T)
                                              ((EQ VALUE 10100011) T)
                                              ((EQ VALUE 10100100) T)
                                              ((EQ VALUE 10100101) T)
                                              ((EQ VALUE 10100110) T)
                                              ((EQ VALUE 10100111) T)
                                              ((EQ VALUE 10101000) T)
                                              ((EQ VALUE 10101001) T)
                                              ((EQ VALUE 10101010) T)
                                              ((EQ VALUE 10101011) T)
                                              ((EQ VALUE 10101100) T)
                                              ((EQ VALUE 10101101) T)
                                              ((EQ VALUE 10101110) T)
                                              ((EQ VALUE 10101111) T)
                                              (T
                                                (COND
                                                  ((EQ VALUE 10110000) T)
                                                  ((EQ VALUE 10110001) T)
                                                  ((EQ VALUE 10110010) T)
                                                  ((EQ VALUE 10110011) T)
                                                  ((EQ VALUE 10110100) T)
                                                  ((EQ VALUE 10110101) T)
                                                  ((EQ VALUE 10110110) T)
                                                  ((EQ VALUE 10110111) T)
                                                  ((EQ VALUE 10111000) T)
                                                  ((EQ VALUE 10111001) T)
                                                  ((EQ VALUE 10111010) T)
                                                  ((EQ VALUE 10111011) T)
                                                  ((EQ VALUE 10111100) T)
                                                  ((EQ VALUE 10111101) T)
                                                  ((EQ VALUE 10111110) T)
                                                  ((EQ VALUE 10111111) T)
                                                  (T
                                                    (COND
                                                      ((EQ VALUE 11000000) T)
                                                      ((EQ VALUE 11000001) T)
                                                      ((EQ VALUE 11000010) T)
                                                      ((EQ VALUE 11000011) T)
                                                      ((EQ VALUE 11000100) T)
                                                      ((EQ VALUE 11000101) T)
                                                      ((EQ VALUE 11000110) T)
                                                      ((EQ VALUE 11000111) T)
                                                      ((EQ VALUE 11001000) T)
                                                      ((EQ VALUE 11001001) T)
                                                      ((EQ VALUE 11001010) T)
                                                      ((EQ VALUE 11001011) T)
                                                      ((EQ VALUE 11001100) T)
                                                      ((EQ VALUE 11001101) T)
                                                      ((EQ VALUE 11001110) T)
                                                      ((EQ VALUE 11001111) T)
                                                      (T
                                                        (COND
                                                          ((EQ VALUE 11010000) T)
                                                          ((EQ VALUE 11010001) T)
                                                          ((EQ VALUE 11010010) T)
                                                          ((EQ VALUE 11010011) T)
                                                          ((EQ VALUE 11010100) T)
                                                          ((EQ VALUE 11010101) T)
                                                          ((EQ VALUE 11010110) T)
                                                          ((EQ VALUE 11010111) T)
                                                          ((EQ VALUE 11011000) T)
                                                          ((EQ VALUE 11011001) T)
                                                          ((EQ VALUE 11011010) T)
                                                          ((EQ VALUE 11011011) T)
                                                          ((EQ VALUE 11011100) T)
                                                          ((EQ VALUE 11011101) T)
                                                          ((EQ VALUE 11011110) T)
                                                          ((EQ VALUE 11011111) T)
                                                          (T
                                                            (COND
                                                              ((EQ VALUE 11100000) T)
                                                              ((EQ VALUE 11100001) T)
                                                              ((EQ VALUE 11100010) T)
                                                              ((EQ VALUE 11100011) T)
                                                              ((EQ VALUE 11100100) T)
                                                              ((EQ VALUE 11100101) T)
                                                              ((EQ VALUE 11100110) T)
                                                              ((EQ VALUE 11100111) T)
                                                              ((EQ VALUE 11101000) T)
                                                              ((EQ VALUE 11101001) T)
                                                              ((EQ VALUE 11101010) T)
                                                              ((EQ VALUE 11101011) T)
                                                              ((EQ VALUE 11101100) T)
                                                              ((EQ VALUE 11101101) T)
                                                              ((EQ VALUE 11101110) T)
                                                              ((EQ VALUE 11101111) T)
                                                              (T
                                                                (COND
                                                                  ((EQ VALUE 11110000) T)
                                                                  ((EQ VALUE 11110001) T)
                                                                  ((EQ VALUE 11110010) T)
                                                                  ((EQ VALUE 11110011) T)
                                                                  ((EQ VALUE 11110100) T)
                                                                  ((EQ VALUE 11110101) T)
                                                                  ((EQ VALUE 11110110) T)
                                                                  ((EQ VALUE 11110111) T)
                                                                  ((EQ VALUE 11111000) T)
                                                                  ((EQ VALUE 11111001) T)
                                                                  ((EQ VALUE 11111010) T)
                                                                  ((EQ VALUE 11111011) T)
                                                                  ((EQ VALUE 11111100) T)
                                                                  ((EQ VALUE 11111101) T)
                                                                  ((EQ VALUE 11111110) T)
                                                                  ((EQ VALUE 11111111) T)
                                                                  (T NIL))
                                                              ))
                                                          ))
                                                      ))
                                                  ))
                                              ))
                                          ))
                                      ))
                                  ))
                              ))
                          ))
                      ))
                  ))
              ))
          ))
      ))))
(DEFINE C1-PRIMITIVE-IDENTITY
  (LAMBDA (NAME)
    (COND
      ((EQ NAME 00000010) 00000010)
      ((EQ NAME 00000011) 00000011)
      ((EQ NAME 00000100) 00000100)
      ((EQ NAME 00000101) 00000101)
      ((EQ NAME 00000110) 00000110)
      ((EQ NAME 00100001) 00100001)
      ((EQ NAME 00100111) 00100111)
      ((EQ NAME (QUOTE ATOM)) 00000010)
      ((EQ NAME (QUOTE atom)) 00000010)
      ((EQ NAME (QUOTE EQ))   00000011)
      ((EQ NAME (QUOTE eq))   00000011)
      ((EQ NAME (QUOTE CONS)) 00000100)
      ((EQ NAME (QUOTE cons)) 00000100)
      ((EQ NAME (QUOTE CAR))  00000101)
      ((EQ NAME (QUOTE car))  00000101)
      ((EQ NAME (QUOTE CDR))  00000110)
      ((EQ NAME (QUOTE cdr))  00000110)
      ((EQ NAME (QUOTE LIST)) 00100111)
      ((EQ NAME (QUOTE list)) 00100111)
      ((EQ NAME (QUOTE NOT))  00100001)
      ((EQ NAME (QUOTE not))  00100001)
      (T NIL))))

(DEFINE C1-DEFAULT
  (LAMBDA (NAME)
    ((LAMBDA (IDENTITY)
       (COND
         ((EQ IDENTITY NIL)
          (C1-MAKE-ERROR (QUOTE UNBOUND) NAME))
         (T IDENTITY)))
     (C1-PRIMITIVE-IDENTITY NAME))))

(DEFINE C1-LOOKUP
  (LAMBDA (NAME ENV GLOBAL)
    ((LAMBDA (LOCAL)
       (COND
         ((C1-FOUNDP LOCAL) (C1-FOUND-VALUE LOCAL))
         (T
          ((LAMBDA (TOP)
             (COND
               ((C1-FOUNDP TOP) (C1-FOUND-VALUE TOP))
               (T (C1-DEFAULT NAME))))
           (C1-LOOKUP-IN NAME GLOBAL)))))
     (C1-LOOKUP-IN NAME ENV))))

(DEFINE C1-FUNARGP
  (LAMBDA (VALUE)
    (COND
      ((ATOM VALUE) NIL)
      ((EQ (CAR VALUE) (QUOTE FUNARG)) T)
      (T NIL))))

(DEFINE C1-ONE-ARGP
  (LAMBDA (ARGS)
    (COND
      ((ATOM ARGS) NIL)
      ((EQ (CDR ARGS) NIL) T)
      (T NIL))))

(DEFINE C1-TWO-ARGP
  (LAMBDA (ARGS)
    (COND
      ((ATOM ARGS) NIL)
      ((ATOM (CDR ARGS)) NIL)
      ((EQ (CDR (CDR ARGS)) NIL) T)
      (T NIL))))

(DEFINE C1-BIND
  (LABEL C1-BIND
    (LAMBDA (PARAMS ARGS ENV)
      (COND
        ((EQ PARAMS NIL)
         (COND
           ((EQ ARGS NIL) ENV)
           (T (C1-MAKE-ERROR (QUOTE ARITY) (QUOTE TOO-MANY-ARGUMENTS)))))
        ((EQ ARGS NIL)
         (C1-MAKE-ERROR (QUOTE ARITY) (QUOTE TOO-FEW-ARGUMENTS)))
        (T
         (C1-BIND
           (CDR PARAMS)
           (CDR ARGS)
           (CONS (CONS (CAR PARAMS) (CAR ARGS)) ENV)))))))

(DEFINE C1-APPLY-PRIMITIVE
  (LAMBDA (SID ARGS)
    (COND
      ((EQ SID 00100111) ARGS)
      ((EQ SID 00100001)
       (COND
         ((C1-ONE-ARGP ARGS)
          (COND
            ((EQ (CAR ARGS) NIL) T)
            (T NIL)))
         (T (C1-MAKE-ERROR (QUOTE ARITY) SID))))
      ((EQ SID 00000010)
       (COND
         ((C1-ONE-ARGP ARGS) (ATOM (CAR ARGS)))
         (T (C1-MAKE-ERROR (QUOTE ARITY) SID))))
      ((EQ SID 00000011)
       (COND
         ((C1-TWO-ARGP ARGS) (EQ (CAR ARGS) (CAR (CDR ARGS))))
         (T (C1-MAKE-ERROR (QUOTE ARITY) SID))))
      ((EQ SID 00000100)
       (COND
         ((C1-TWO-ARGP ARGS) (CONS (CAR ARGS) (CAR (CDR ARGS))))
         (T (C1-MAKE-ERROR (QUOTE ARITY) SID))))
      ((EQ SID 00000101)
       (COND
         ((C1-ONE-ARGP ARGS)
          (COND
            ((ATOM (CAR ARGS))
             (C1-MAKE-ERROR (QUOTE TYPE) (QUOTE CAR-REQUIRES-PAIR)))
            (T (CAR (CAR ARGS)))))
         (T (C1-MAKE-ERROR (QUOTE ARITY) SID))))
      ((EQ SID 00000110)
       (COND
         ((C1-ONE-ARGP ARGS)
          (COND
            ((ATOM (CAR ARGS))
             (C1-MAKE-ERROR (QUOTE TYPE) (QUOTE CDR-REQUIRES-PAIR)))
            (T (CDR (CAR ARGS)))))
         (T (C1-MAKE-ERROR (QUOTE ARITY) SID))))
      (T
       (C1-MAKE-ERROR (QUOTE UNSUPPORTED-PRIMITIVE) SID)))))

(DEFINE C1-EVLIS
  (LABEL C1-EVLIS
    (LAMBDA (FORMS ENV GLOBAL)
      (COND
        ((EQ FORMS NIL) NIL)
        (T
         ((LAMBDA (FIRST)
            (COND
              ((C1-ERRORP FIRST) FIRST)
              (T
               ((LAMBDA (REST)
                  (COND
                    ((C1-ERRORP REST) REST)
                    (T (CONS FIRST REST))))
                (C1-EVLIS (CDR FORMS) ENV GLOBAL)))))
          (C1-EVAL (CAR FORMS) ENV GLOBAL)))))))

(DEFINE C1-EVCON
  (LABEL C1-EVCON
    (LAMBDA (CLAUSES ENV GLOBAL)
      (COND
        ((EQ CLAUSES NIL)
         (C1-MAKE-ERROR (QUOTE UNSATISFIED-CONDITIONAL) NIL))
        (T
         ((LAMBDA (TEST-VALUE)
            (COND
              ((C1-ERRORP TEST-VALUE) TEST-VALUE)
              ((EQ TEST-VALUE NIL)
               (C1-EVCON (CDR CLAUSES) ENV GLOBAL))
              (T
               (C1-EVAL
                 (C1-SECOND (CAR CLAUSES))
                 ENV
                 GLOBAL))))
          (C1-EVAL
            (CAR (CAR CLAUSES))
            ENV
            GLOBAL)))))))

(DEFINE C1-APPLY
  (LAMBDA (FN ARGS GLOBAL)
    (COND
      ((C1-ERRORP FN) FN)
      ((C1-PRIMITIVE-IDENTITY FN)
       (C1-APPLY-PRIMITIVE (C1-PRIMITIVE-IDENTITY FN) ARGS))
      ((C1-FUNARGP FN)
       (FN ARGS GLOBAL))
      (T
       (C1-MAKE-ERROR (QUOTE NOT-CALLABLE) FN)))))

(DEFINE C1-QUOTE-NAMEP
  (LAMBDA (NAME)
    (COND
      ((EQ NAME (QUOTE QUOTE)) T)
      ((EQ NAME (QUOTE quote)) T)
      (T NIL))))

(DEFINE C1-COND-NAMEP
  (LAMBDA (NAME)
    (COND
      ((EQ NAME (QUOTE COND)) T)
      ((EQ NAME (QUOTE cond)) T)
      (T NIL))))

(DEFINE C1-LAMBDA-NAMEP
  (LAMBDA (NAME)
    (COND
      ((EQ NAME (QUOTE LAMBDA)) T)
      ((EQ NAME (QUOTE lambda)) T)
      (T NIL))))

(DEFINE C1-DEFINE-NAMEP
  (LAMBDA (NAME)
    (COND
      ((EQ NAME (QUOTE DEFINE)) T)
      ((EQ NAME (QUOTE define)) T)
      ((EQ NAME (QUOTE def)) T)
      (T NIL))))

(DEFINE C1-EVAL
  (LABEL C1-EVAL
    (LAMBDA (EXPR ENV GLOBAL)
      (COND
        ((ATOM EXPR)
         (COND
           ((EQ EXPR NIL) NIL)
           ((EQ EXPR (QUOTE nil)) NIL)
           ((EQ EXPR T) T)
           ((EQ EXPR (QUOTE t)) T)
           ((C1-SID-VALUEP EXPR) EXPR)
           (T (C1-LOOKUP EXPR ENV GLOBAL))))
        ((C1-QUOTE-NAMEP (CAR EXPR))
         (C1-SECOND EXPR))
        ((C1-COND-NAMEP (CAR EXPR))
         (C1-EVCON (CDR EXPR) ENV GLOBAL))
        ((C1-LAMBDA-NAMEP (CAR EXPR))
         (FUNCTION
           (LAMBDA (ARGS GLOBAL-AT-CALL)
             ((LAMBDA (BOUND)
                (COND
                  ((C1-ERRORP BOUND) BOUND)
                  (T
                   (C1-EVAL
                     (C1-THIRD EXPR)
                     BOUND
                     GLOBAL-AT-CALL))))
              (C1-BIND
                (C1-SECOND EXPR)
                ARGS
                ENV)))))
        ((C1-DEFINE-NAMEP (CAR EXPR))
         (C1-MAKE-ERROR
           (QUOTE INVALID-FORM)
           (QUOTE DEFINE-IS-TOP-LEVEL-ONLY)))
        (T
         ((LAMBDA (FN)
            (COND
              ((C1-ERRORP FN) FN)
              (T
               ((LAMBDA (ARGS)
                  (COND
                    ((C1-ERRORP ARGS) ARGS)
                    (T (C1-APPLY FN ARGS GLOBAL))))
                (C1-EVLIS (CDR EXPR) ENV GLOBAL)))))
          (C1-EVAL (CAR EXPR) ENV GLOBAL)))))))

(DEFINE C1-MAKE-WORLD
  (LAMBDA (VALUE GLOBAL)
    (CONS (QUOTE C1-WORLD)
      (CONS VALUE
        (CONS GLOBAL NIL)))))

(DEFINE C1-WORLD-VALUE
  (LAMBDA (WORLD)
    (C1-SECOND WORLD)))

(DEFINE C1-WORLD-GLOBAL
  (LAMBDA (WORLD)
    (C1-THIRD WORLD)))

(DEFINE C1-DEFINITIONP
  (LAMBDA (FORM)
    (COND
      ((ATOM FORM) NIL)
      ((C1-DEFINE-NAMEP (CAR FORM)) T)
      (T NIL))))

(DEFINE C1-EVAL-PROGRAM
  (LABEL C1-EVAL-PROGRAM
    (LAMBDA (FORMS GLOBAL)
      (COND
        ((EQ FORMS NIL)
         (C1-MAKE-WORLD NIL GLOBAL))
        ((C1-DEFINITIONP (CAR FORMS))
         ((LAMBDA (FORM)
            ((LAMBDA (VALUE)
               (COND
                 ((C1-ERRORP VALUE)
                  (C1-MAKE-WORLD VALUE GLOBAL))
                 (T
                  (C1-EVAL-PROGRAM
                    (CDR FORMS)
                    (CONS
                      (CONS (C1-SECOND FORM) VALUE)
                      GLOBAL)))))
             (C1-EVAL (C1-THIRD FORM) NIL GLOBAL)))
          (CAR FORMS)))
        ((EQ (CDR FORMS) NIL)
         (C1-MAKE-WORLD
           (C1-EVAL (CAR FORMS) NIL GLOBAL)
           GLOBAL))
        (T
         ((LAMBDA (VALUE)
            (COND
              ((C1-ERRORP VALUE)
               (C1-MAKE-WORLD VALUE GLOBAL))
              (T
               (C1-EVAL-PROGRAM
                 (CDR FORMS)
                 GLOBAL))))
          (C1-EVAL (CAR FORMS) NIL GLOBAL)))))))

(DEFINE C1-WORLD-EVAL
  (LAMBDA (WORLD EXPR)
    (C1-MAKE-WORLD
      (C1-EVAL EXPR NIL (C1-WORLD-GLOBAL WORLD))
      (C1-WORLD-GLOBAL WORLD))))

(DEFINE C1-EVAL-PROGRAM-THEN
  (LAMBDA (FORMS EXPR)
    ((LAMBDA (WORLD)
       (C1-WORLD-VALUE
         (C1-WORLD-EVAL WORLD EXPR)))
     (C1-EVAL-PROGRAM FORMS NIL))))
