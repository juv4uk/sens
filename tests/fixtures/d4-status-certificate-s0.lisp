; #2364 — bounded D4 certificate replay through Core1.
; Loaded after lib/core1.lisp by the dedicated workflow.

; LOOKUP
(C1-LOOKUP
  (QUOTE X)
  (QUOTE ((X . Y)))
  NIL)

; BIND, observed through LOOKUP rather than representation shape.
(C1-LOOKUP
  (QUOTE Y)
  (C1-BIND
    (QUOTE (X Y))
    (QUOTE (A B))
    NIL)
  NIL)

; EVLIS
(C1-EVLIS
  (QUOTE ((QUOTE A) (QUOTE B)))
  NIL
  NIL)

; EVCON: first clause false, second true.
(C1-EVCON
  (QUOTE
    (((QUOTE NIL) (QUOTE A))
     ((QUOTE T) (QUOTE B))))
  NIL
  NIL)

; APPLY over a Lisp-created closure.
(C1-APPLY
  (C1-EVAL
    (QUOTE (LAMBDA (X) (CONS X NIL)))
    NIL
    NIL)
  (QUOTE (A))
  NIL)

; EVAL through primitive CONS + evaluated arguments.
(C1-EVAL
  (QUOTE (CONS (QUOTE A) (QUOTE (B))))
  NIL
  NIL)

; LAMBDA positive control.
(C1-FUNARGP
  (C1-EVAL
    (QUOTE (LAMBDA (X) X))
    NIL
    NIL))

; DEFINE positive control with recursion.
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
