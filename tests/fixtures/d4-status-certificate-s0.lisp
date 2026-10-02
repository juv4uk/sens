; #2364 — bounded D4 certificate replay through Core1.
; Loaded after lib/core1.lisp by the dedicated workflow.
;
; One final observation bundles every result so top-level DEFINE return values
; from loading Core1 cannot be confused with certificate outputs.

(CONS
  ; LOOKUP
  (C1-LOOKUP
    (QUOTE X)
    (QUOTE ((X . Y)))
    NIL)

  (CONS
    ; BIND, observed through LOOKUP rather than representation shape.
    (C1-LOOKUP
      (QUOTE Y)
      (C1-BIND
        (QUOTE (X Y))
        (QUOTE (A B))
        NIL)
      NIL)

    (CONS
      ; EVLIS
      (C1-EVLIS
        (QUOTE ((QUOTE A) (QUOTE B)))
        NIL
        NIL)

      (CONS
        ; EVCON: first clause false, second true.
        (C1-EVCON
          (QUOTE
            (((QUOTE NIL) (QUOTE A))
             ((QUOTE T) (QUOTE B))))
          NIL
          NIL)

        (CONS
          ; APPLY over a Lisp-created closure.
          (C1-APPLY
            (C1-EVAL
              (QUOTE (LAMBDA (X) (CONS X NIL)))
              NIL
              NIL)
            (QUOTE (A))
            NIL)

          (CONS
            ; EVAL through primitive CONS + evaluated arguments.
            (C1-EVAL
              (QUOTE (CONS (QUOTE A) (QUOTE (B))))
              NIL
              NIL)

            (CONS
              ; LAMBDA positive control.
              (C1-FUNARGP
                (C1-EVAL
                  (QUOTE (LAMBDA (X) X))
                  NIL
                  NIL))

              (CONS
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
                NIL))))))))
