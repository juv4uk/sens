; Core1 compiler SID resolver.
;
; This is a bootstrap projection, not semantic authority.
; Authority remains:
;   lib/surface/semantic-registry.lisp
;   contracts/core1-historical-sid-map.lisp
;
; It is deliberately separate from lib/core1.lisp so the historical Core1
; seed/pin stays unchanged.  The SID8-aware bootstrap lane loads this file
; only after mccarthy-eval#55, whose reader/evaluator can carry exact bare
; SID8 values without quote/string wrappers.
;
; Result contract:
;   admitted/known compiler surface -> exact bare SID8
;   unknown surface                 -> NIL
;
; The exact bit token is evaluated as a SID8 value by the SID8-aware S0.
; Never wrap these tokens in QUOTE or strings.

(DEFINE C1-COMPILER-SID-FOR-SURFACE
  (LAMBDA (NAME)
    (COND
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
      ((EQ NAME (QUOTE +))    00001100)
      ((EQ NAME (QUOTE -))    00001101)
      ((EQ NAME (QUOTE NOT))  00100001)
      ((EQ NAME (QUOTE not))  00100001)
      ((EQ NAME (QUOTE LIST)) 00100111)
      ((EQ NAME (QUOTE list)) 00100111)
      (T NIL))))
