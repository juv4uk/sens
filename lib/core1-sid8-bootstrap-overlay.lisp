; Core1 bootstrap SID8 self-carry overlay.
;
; This file is NOT the historical Core1 S1 source and is not semantic authority.
; Load lib/core1.lisp first, then this file only on the SID8-aware bootstrap S0.
;
; Purpose:
;   exact typed SID8 compiler-output values -> self-evaluating values in C1-EVAL
;
; No source-name resolution lives here.  No string/quoted SID representation,
; no (SID . SID) bootstrap environment, and no SID -> name -> SID round trip.
; Resolver authority stays in lib/core1-compiler-sid-resolver.lisp.
;
; The admitted set is deliberately the current compiler-emitted primitive-key
; set only.  Expanding it requires an explicit compiler-output witness.

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

; Bootstrap-only replacement for C1-EVAL.  It is byte-for-byte the current
; Core1 evaluator shape except for the first atom-side transport branch:
; a typed, admitted SID8 value carries itself instead of entering lexical
; lookup.  All ordinary Core1 evaluation paths remain unchanged.
(DEFINE C1-EVAL
  (LABEL C1-EVAL
    (LAMBDA (EXPR ENV GLOBAL)
      (COND
        ((ATOM EXPR)
         (COND
           ((C1-SID-VALUEP EXPR) EXPR)
           ((EQ EXPR NIL) NIL)
           ((EQ EXPR (QUOTE nil)) NIL)
           ((EQ EXPR T) T)
           ((EQ EXPR (QUOTE t)) T)
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
