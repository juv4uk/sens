; Core1 SID8 bootstrap transport overlay.
;
; Historical Core1 evaluator source remains unchanged. Compiler source reaches
; C1-EVAL as code-data, so an exact eight-bit source token inside that data is
; still an ordinary source symbol until evaluation. This overlay supplies the
; one explicit resolution boundary:
;
;   exact source-token data -> exact bare runtime SID8
;
; The left side below is source data only; the right side is the function
; identity. C1 QUOTE bypasses lookup, so (QUOTE 00000100) remains data and is
; never auto-promoted. There is no SID -> name -> SID round trip.
;
; + and - are present only as compiler-output data identities. This does not
; admit arithmetic execution into Core1.

(DEFINE C1-SID8-BOOTSTRAP-GLOBAL
  (LAMBDA ()
    (CONS (CONS (QUOTE 00000010) 00000010)
      (CONS (CONS (QUOTE 00000011) 00000011)
        (CONS (CONS (QUOTE 00000100) 00000100)
          (CONS (CONS (QUOTE 00000101) 00000101)
            (CONS (CONS (QUOTE 00000110) 00000110)
              (CONS (CONS (QUOTE 00001100) 00001100)
                (CONS (CONS (QUOTE 00001101) 00001101)
                  NIL)))))))))

(DEFINE C1-EVAL-PROGRAM-THEN-SID8
  (LAMBDA (FORMS EXPR)
    ((LAMBDA (WORLD)
       (C1-WORLD-VALUE
         (C1-WORLD-EVAL WORLD EXPR)))
     (C1-EVAL-PROGRAM
       FORMS
       (C1-SID8-BOOTSTRAP-GLOBAL)))))
