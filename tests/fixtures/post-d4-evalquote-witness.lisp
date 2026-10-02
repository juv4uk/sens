; #2279 — ordinary-function EVALQUOTE derivation witness.
;
; Test-only adapter: no SENS identity is assigned here.
; Ordinary EVALQUOTE is reconstructed from existing EVAL + APPLY semantics.
; The later FEXPR/FSUBR staging exception is deliberately out of scope.

(00001001 C1-EVALQUOTE-DERIVED
  (00001000 (FN ARGS)
    (C1-APPLY
      (C1-EVAL FN NIL NIL)
      ARGS
      NIL)))

; One deterministic semantic observation after the helper definition:
; 1. primitive CONS over a value-list;
; 2. nested list data preserved through CAR;
; 3. raw LAMBDA resolved by EVAL then applied as a closure;
; 4. APPLY arity failure propagated unchanged.
(00000100
  (C1-EVALQUOTE-DERIVED (00000001 00000100) (00000001 (A B)))
  (00000100
    (C1-EVALQUOTE-DERIVED (00000001 00000101) (00000001 ((A B))))
    (00000100
      (C1-EVALQUOTE-DERIVED
        (00000001 (00001000 (X Y) (00000100 X Y)))
        (00000001 (A B)))
      (00000100
        (C1-EVALQUOTE-DERIVED
          (00000001 00000101)
          (00000001 ((A B) (C D))))
        NIL))))
