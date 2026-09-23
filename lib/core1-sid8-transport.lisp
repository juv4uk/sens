; Core1 SID8 bootstrap transport overlay.
;
; Historical Core1 source remains unchanged. This file is loaded only by the
; SID8-aware bootstrap lane after mccarthy-eval#55. It does not define new
; function meaning; it only lets exact already-authoritative SID8 identity
; values cross the Core1 meta-evaluator lookup boundary without being mistaken
; for ordinary unbound symbols.
;
; + and - appear here as compiler-output data identities only. This does not
; admit arithmetic execution into the Core1 profile.

(DEFINE C1-SID-VALUEP
  (LAMBDA (VALUE)
    (COND
      ((EQ VALUE 00000010) T)
      ((EQ VALUE 00000011) T)
      ((EQ VALUE 00000100) T)
      ((EQ VALUE 00000101) T)
      ((EQ VALUE 00000110) T)
      ((EQ VALUE 00001100) T)
      ((EQ VALUE 00001101) T)
      (T NIL))))

(DEFINE C1-LOOKUP
  (LAMBDA (NAME ENV GLOBAL)
    (COND
      ((C1-SID-VALUEP NAME) NAME)
      (T
       ((LAMBDA (LOCAL)
          (COND
            ((C1-FOUNDP LOCAL) (C1-FOUND-VALUE LOCAL))
            (T
             ((LAMBDA (TOP)
                (COND
                  ((C1-FOUNDP TOP) (C1-FOUND-VALUE TOP))
                  (T (C1-DEFAULT NAME))))
              (C1-LOOKUP-IN NAME GLOBAL)))))
        (C1-LOOKUP-IN NAME ENV))))))
