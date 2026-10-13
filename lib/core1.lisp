
(0011 C1-SECOND
  (0010 (X)
    (100 (011 X))))

(0011 C1-THIRD
  (0010 (X)
    (100 (011 (011 X)))))

(0011 C1-FOURTH
  (0010 (X)
    (100 (011 (011 (011 X))))))

(0011 C1-MAKE-ERROR
  (0010 (KIND DETAIL)
    (111 (001 C1-ERROR)
      (111 KIND
        (111 DETAIL NIL)))))

(0011 C1-ERRORP
  (0010 (VALUE)
    (110
      ((010 VALUE) NIL)
      ((101 (100 VALUE) (001 C1-ERROR)) T)
      ((010 (001 ())) NIL))))

(0011 C1-MAKE-FOUND
  (0010 (VALUE)
    (111 (001 C1-FOUND)
      (111 VALUE NIL))))

(0011 C1-FOUNDP
  (0010 (VALUE)
    (110
      ((010 VALUE) NIL)
      ((101 (100 VALUE) (001 C1-FOUND)) T)
      ((010 (001 ())) NIL))))

(0011 C1-FOUND-VALUE
  (0010 (VALUE)
    (C1-SECOND VALUE)))

(0011 C1-LOOKUP-IN
  (00100 C1-LOOKUP-IN
    (0010 (NAME ENV)
      (110
        ((101 ENV NIL) (001 C1-MISSING))
        ((101 (100 (100 ENV)) NAME)
         (C1-MAKE-FOUND (011 (100 ENV))))
        ((010 (001 ()))
         (C1-LOOKUP-IN NAME (011 ENV)))))))

(0011 C1-ADMITTED-SID-VALUEP
  (0010 (VALUE)
    (110
      ((101 VALUE 001) T)
      ((101 VALUE 010) T)
      ((101 VALUE 101) T)
      ((101 VALUE 111) T)
      ((101 VALUE 100) T)
      ((101 VALUE 011) T)
      ((101 VALUE 110) T)
      ((101 VALUE 0010) T)
      ((101 VALUE 0011) T)
      ((101 VALUE 01010) T)
      ((101 VALUE 01011) T)
      ((101 VALUE 0100) T)
      ((101 VALUE 1110) T)
      ((010 (001 ())) NIL))))

(0011 C1-PRIMITIVE-IDENTITY
  (0010 (NAME)
    (110
      ((101 NAME 010) 010)
      ((101 NAME 101) 101)
      ((101 NAME 111) 111)
      ((101 NAME 100) 100)
      ((101 NAME 011) 011)
      ((101 NAME 0100) 0100)
      ((101 NAME 1110) 1110)
      ((101 NAME (001 ATOM)) 010)
      ((101 NAME (001 atom)) 010)
      ((101 NAME (001 EQ))   101)
      ((101 NAME (001 eq))   101)
      ((101 NAME (001 CONS)) 111)
      ((101 NAME (001 cons)) 111)
      ((101 NAME (001 CAR))  100)
      ((101 NAME (001 car))  100)
      ((101 NAME (001 CDR))  011)
      ((101 NAME (001 cdr))  011)
      ((101 NAME (001 LIST)) 1110)
      ((101 NAME (001 list)) 1110)
      ((101 NAME (001 NOT))  0100)
      ((101 NAME (001 not))  0100)
      ((010 (001 ())) NIL))))

(0011 C1-DEFAULT
  (0010 (NAME)
    ((0010 (IDENTITY)
       (110
         ((101 IDENTITY NIL)
          (C1-MAKE-ERROR (001 UNBOUND) NAME))
         ((010 (001 ())) IDENTITY)))
     (C1-PRIMITIVE-IDENTITY NAME))))

(0011 C1-LOOKUP
  (0010 (NAME ENV GLOBAL)
    ((0010 (LOCAL)
       (110
         ((C1-FOUNDP LOCAL) (C1-FOUND-VALUE LOCAL))
         ((010 (001 ()))
          ((0010 (TOP)
             (110
               ((C1-FOUNDP TOP) (C1-FOUND-VALUE TOP))
               ((010 (001 ())) (C1-DEFAULT NAME))))
           (C1-LOOKUP-IN NAME GLOBAL)))))
     (C1-LOOKUP-IN NAME ENV))))

(0011 C1-FUNARGP
  (0010 (VALUE)
    (110
      ((010 VALUE) NIL)
      ((101 (100 VALUE) (001 FUNARG)) T)
      ((010 (001 ())) NIL))))

(0011 C1-ONE-ARGP
  (0010 (ARGS)
    (110
      ((010 ARGS) NIL)
      ((101 (011 ARGS) NIL) T)
      ((010 (001 ())) NIL))))

(0011 C1-TWO-ARGP
  (0010 (ARGS)
    (110
      ((010 ARGS) NIL)
      ((010 (011 ARGS)) NIL)
      ((101 (011 (011 ARGS)) NIL) T)
      ((010 (001 ())) NIL))))

(0011 C1-BIND
  (00100 C1-BIND
    (0010 (PARAMS ARGS ENV)
      (110
        ((101 PARAMS NIL)
         (110
           ((101 ARGS NIL) ENV)
           ((010 (001 ())) (C1-MAKE-ERROR (001 ARITY) (001 TOO-MANY-ARGUMENTS)))))
        ((101 ARGS NIL)
         (C1-MAKE-ERROR (001 ARITY) (001 TOO-FEW-ARGUMENTS)))
        ((010 (001 ()))
         (C1-BIND
           (011 PARAMS)
           (011 ARGS)
           (111 (111 (100 PARAMS) (100 ARGS)) ENV)))))))

(0011 C1-APPLY-PRIMITIVE
  (0010 (SID ARGS)
    (110
      ((101 SID 1110) ARGS)
      ((101 SID 0100)
       (110
         ((C1-ONE-ARGP ARGS)
          (110
            ((101 (100 ARGS) NIL) T)
            ((010 (001 ())) NIL)))
         ((010 (001 ())) (C1-MAKE-ERROR (001 ARITY) SID))))
      ((101 SID 010)
       (110
         ((C1-ONE-ARGP ARGS) (010 (100 ARGS)))
         ((010 (001 ())) (C1-MAKE-ERROR (001 ARITY) SID))))
      ((101 SID 101)
       (110
         ((C1-TWO-ARGP ARGS) (101 (100 ARGS) (100 (011 ARGS))))
         ((010 (001 ())) (C1-MAKE-ERROR (001 ARITY) SID))))
      ((101 SID 111)
       (110
         ((C1-TWO-ARGP ARGS) (111 (100 ARGS) (100 (011 ARGS))))
         ((010 (001 ())) (C1-MAKE-ERROR (001 ARITY) SID))))
      ((101 SID 100)
       (110
         ((C1-ONE-ARGP ARGS)
          (110
            ((010 (100 ARGS))
             (C1-MAKE-ERROR (001 TYPE) (001 CAR-REQUIRES-PAIR)))
            ((010 (001 ())) (100 (100 ARGS)))))
         ((010 (001 ())) (C1-MAKE-ERROR (001 ARITY) SID))))
      ((101 SID 011)
       (110
         ((C1-ONE-ARGP ARGS)
          (110
            ((010 (100 ARGS))
             (C1-MAKE-ERROR (001 TYPE) (001 CDR-REQUIRES-PAIR)))
            ((010 (001 ())) (011 (100 ARGS)))))
         ((010 (001 ())) (C1-MAKE-ERROR (001 ARITY) SID))))
      ((010 (001 ()))
       (C1-MAKE-ERROR (001 UNSUPPORTED-PRIMITIVE) SID)))))

(0011 C1-EVLIS
  (00100 C1-EVLIS
    (0010 (FORMS ENV GLOBAL)
      (110
        ((101 FORMS NIL) NIL)
        ((010 (001 ()))
         ((0010 (FIRST)
            (110
              ((C1-ERRORP FIRST) FIRST)
              ((010 (001 ()))
               ((0010 (REST)
                  (110
                    ((C1-ERRORP REST) REST)
                    ((010 (001 ())) (111 FIRST REST))))
                (C1-EVLIS (011 FORMS) ENV GLOBAL)))))
          (C1-EVAL (100 FORMS) ENV GLOBAL)))))))

(0011 C1-EVCON
  (00100 C1-EVCON
    (0010 (CLAUSES ENV GLOBAL)
      (110
        ((101 CLAUSES NIL)
         (C1-MAKE-ERROR (001 UNSATISFIED-CONDITIONAL) NIL))
        ((010 (001 ()))
         ((0010 (TEST-VALUE)
            (110
              ((C1-ERRORP TEST-VALUE) TEST-VALUE)
              ((101 TEST-VALUE NIL)
               (C1-EVCON (011 CLAUSES) ENV GLOBAL))
              ((010 (001 ()))
               (C1-EVAL
                 (C1-SECOND (100 CLAUSES))
                 ENV
                 GLOBAL))))
          (C1-EVAL
            (100 (100 CLAUSES))
            ENV
            GLOBAL)))))))

(0011 C1-APPLY
  (0010 (FN ARGS GLOBAL)
    (110
      ((C1-ERRORP FN) FN)
      ((C1-PRIMITIVE-IDENTITY FN)
       (C1-APPLY-PRIMITIVE (C1-PRIMITIVE-IDENTITY FN) ARGS))
      ((C1-FUNARGP FN)
       (FN ARGS GLOBAL))
      ((010 (001 ()))
       (C1-MAKE-ERROR (001 NOT-CALLABLE) FN)))))

(0011 C1-QUOTE-NAMEP
  (0010 (NAME)
    (110
      ((101 NAME 001) T)
      ((101 NAME (001 QUOTE)) T)
      ((101 NAME (001 quote)) T)
      ((010 (001 ())) NIL))))

(0011 C1-COND-NAMEP
  (0010 (NAME)
    (110
      ((101 NAME 110) T)
      ((101 NAME (001 COND)) T)
      ((101 NAME (001 cond)) T)
      ((010 (001 ())) NIL))))

(0011 C1-LAMBDA-NAMEP
  (0010 (NAME)
    (110
      ((101 NAME 0010) T)
      ((101 NAME (001 LAMBDA)) T)
      ((101 NAME (001 lambda)) T)
      ((010 (001 ())) NIL))))

(0011 C1-DEFINE-NAMEP
  (0010 (NAME)
    (110
      ((101 NAME 0011) T)
      ((101 NAME (001 DEFINE)) T)
      ((101 NAME (001 define)) T)
      ((101 NAME (001 def)) T)
      ((010 (001 ())) NIL))))

(0011 C1-LABEL-NAMEP
  (0010 (NAME)
    (110
      ((101 NAME 00100) T)
      ((101 NAME (001 LABEL)) T)
      ((101 NAME (001 label)) T)
      ((010 (001 ())) NIL))))

(0011 C1-EVAL
  (00100 C1-EVAL
    (0010 (EXPR ENV GLOBAL)
      (110
        ((010 EXPR)
         (110
           ((101 EXPR NIL) NIL)
           ((101 EXPR (001 nil)) NIL)
           ((101 EXPR T) T)
           ((101 EXPR (001 t)) T)
           ((C1-ADMITTED-SID-VALUEP EXPR) EXPR)
           ((010 (001 ())) (C1-LOOKUP EXPR ENV GLOBAL))))
        ((C1-QUOTE-NAMEP (100 EXPR))
         (C1-SECOND EXPR))
        ((C1-COND-NAMEP (100 EXPR))
         (C1-EVCON (011 EXPR) ENV GLOBAL))
        ((C1-LABEL-NAMEP (100 EXPR))
         (C1-EVAL (C1-THIRD EXPR) ENV GLOBAL))
        ((C1-LAMBDA-NAMEP (100 EXPR))
         (FUNCTION
           (0010 (ARGS GLOBAL-AT-CALL)
             ((0010 (BOUND)
                (110
                  ((C1-ERRORP BOUND) BOUND)
                  ((010 (001 ()))
                   (C1-EVAL
                     (C1-THIRD EXPR)
                     BOUND
                     GLOBAL-AT-CALL))))
              (C1-BIND
                (C1-SECOND EXPR)
                ARGS
                ENV)))))
        ((C1-DEFINE-NAMEP (100 EXPR))
         (C1-MAKE-ERROR
           (001 INVALID-FORM)
           (001 DEFINE-IS-TOP-LEVEL-ONLY)))
        ((010 (001 ()))
         ((0010 (FN)
            (110
              ((C1-ERRORP FN) FN)
              ((010 (001 ()))
               ((0010 (ARGS)
                  (110
                    ((C1-ERRORP ARGS) ARGS)
                    ((010 (001 ())) (C1-APPLY FN ARGS GLOBAL))))
                (C1-EVLIS (011 EXPR) ENV GLOBAL)))))
          (C1-EVAL (100 EXPR) ENV GLOBAL)))))))

(0011 C1-MAKE-WORLD
  (0010 (VALUE GLOBAL)
    (111 (001 C1-WORLD)
      (111 VALUE
        (111 GLOBAL NIL)))))

(0011 C1-WORLD-VALUE
  (0010 (WORLD)
    (C1-SECOND WORLD)))

(0011 C1-WORLD-GLOBAL
  (0010 (WORLD)
    (C1-THIRD WORLD)))

(0011 C1-DEFINITIONP
  (0010 (FORM)
    (110
      ((010 FORM) NIL)
      ((C1-DEFINE-NAMEP (100 FORM)) T)
      ((010 (001 ())) NIL))))

(0011 C1-EVAL-PROGRAM
  (00100 C1-EVAL-PROGRAM
    (0010 (FORMS GLOBAL)
      (110
        ((101 FORMS NIL)
         (C1-MAKE-WORLD NIL GLOBAL))
        ((C1-DEFINITIONP (100 FORMS))
         ((0010 (FORM)
            ((0010 (VALUE)
               (110
                 ((C1-ERRORP VALUE)
                  (C1-MAKE-WORLD VALUE GLOBAL))
                 ((010 (001 ()))
                  (C1-EVAL-PROGRAM
                    (011 FORMS)
                    (111
                      (111 (C1-SECOND FORM) VALUE)
                      GLOBAL)))))
             (C1-EVAL (C1-THIRD FORM) NIL GLOBAL)))
          (100 FORMS)))
        ((101 (011 FORMS) NIL)
         (C1-MAKE-WORLD
           (C1-EVAL (100 FORMS) NIL GLOBAL)
           GLOBAL))
        ((010 (001 ()))
         ((0010 (VALUE)
            (110
              ((C1-ERRORP VALUE)
               (C1-MAKE-WORLD VALUE GLOBAL))
              ((010 (001 ()))
               (C1-EVAL-PROGRAM
                 (011 FORMS)
                 GLOBAL))))
          (C1-EVAL (100 FORMS) NIL GLOBAL)))))))

(0011 C1-WORLD-EVAL
  (0010 (WORLD EXPR)
    (C1-MAKE-WORLD
      (C1-EVAL EXPR NIL (C1-WORLD-GLOBAL WORLD))
      (C1-WORLD-GLOBAL WORLD))))

(0011 C1-EVAL-PROGRAM-THEN
  (0010 (FORMS EXPR)
    ((0010 (WORLD)
       (C1-WORLD-VALUE
         (C1-WORLD-EVAL WORLD EXPR)))
     (C1-EVAL-PROGRAM FORMS NIL))))
