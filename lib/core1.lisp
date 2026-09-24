
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

(DEFINE C1-ADMITTED-SID-VALUEP
  (LAMBDA (VALUE)
    (COND
      ((EQ VALUE 00000001) T)
      ((EQ VALUE 00000010) T)
      ((EQ VALUE 00000011) T)
      ((EQ VALUE 00000100) T)
      ((EQ VALUE 00000101) T)
      ((EQ VALUE 00000110) T)
      ((EQ VALUE 00000111) T)
      ((EQ VALUE 00001000) T)
      ((EQ VALUE 00001001) T)
      ((EQ VALUE 00001011) T)
      ((EQ VALUE 00001100) T)
      ((EQ VALUE 00001101) T)
      ((EQ VALUE 00100001) T)
      ((EQ VALUE 00100111) T)
      (T NIL))))

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
           ((C1-ADMITTED-SID-VALUEP EXPR) EXPR)
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
