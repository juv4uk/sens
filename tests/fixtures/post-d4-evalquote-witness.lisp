; #2279 — ordinary-function EVALQUOTE derivation witness.
;
; Test-only adapter: no SENS identity is assigned here.
; Ordinary EVALQUOTE is reconstructed from existing EVAL + APPLY semantics.
; Ukrainian projection only.

(визначити c1-evalquote-derived
  (функція (fn args)
    (застосувати
      (обчислити fn (як-є ()) (як-є ()))
      args
      (як-є ()))))

; One deterministic semantic observation after the helper definition:
; 1. primitive CONS over a value-list;
; 2. nested list data preserved through CAR;
; 3. raw LAMBDA resolved by EVAL then applied as a closure;
; 4. APPLY arity failure propagated unchanged.
(список
  (c1-evalquote-derived (як-є сполучити) (як-є (A B)))
  (c1-evalquote-derived (як-є перше) (як-є ((A B))))
  (c1-evalquote-derived
    (як-є (функція (X Y) (сполучити X Y)))
    (як-є (A B))))
