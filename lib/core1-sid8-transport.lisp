; Core1 SID8 bootstrap transport overlay.
;
; Historical Core1 evaluator source remains unchanged. The SID8-aware S0 can
; already carry exact bare SID8 values. This overlay only supplies an initial
; Core1 global environment in which each admitted compiler-output SID is bound
; to itself, so ordinary C1-LOOKUP returns the exact identity value.
;
; There is no SID predicate, no quoted/string wrapper and no surface-name
; function key after resolution. + and - are present only as compiler-output
; data identities; this does not admit arithmetic execution into Core1.

(DEFINE C1-SID8-BOOTSTRAP-GLOBAL
  (LAMBDA ()
    (CONS (CONS 00000010 00000010)
      (CONS (CONS 00000011 00000011)
        (CONS (CONS 00000100 00000100)
          (CONS (CONS 00000101 00000101)
            (CONS (CONS 00000110 00000110)
              (CONS (CONS 00001100 00001100)
                (CONS (CONS 00001101 00001101)
                  NIL)))))))))

(DEFINE C1-EVAL-PROGRAM-THEN-SID8
  (LAMBDA (FORMS EXPR)
    ((LAMBDA (WORLD)
       (C1-WORLD-VALUE
         (C1-WORLD-EVAL WORLD EXPR)))
     (C1-EVAL-PROGRAM
       FORMS
       (C1-SID8-BOOTSTRAP-GLOBAL)))))
