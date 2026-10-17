; unify-observe — observation boundary for historical unification.
;
; Migrated: COND else (010 ()) → exact D1:1 (010 (001 ())).
; Width is identity. No host truthiness. No crutches.
;
; D4:0011 owns definitions; D4:0010 owns argument binding.
; D3:010 ATOM tests raw shape before D3:101 EQ on the private atom fail.
; Empty substitution () is successful data, never D1:0.
; Surface unify is the existing compatibility mechanism — invoked once.
;
; Reuses: unify, D3 ATOM/EQ/CONS/COND, D4 DEFINE/LAMBDA.
;
; (unify-observe 'radio 'radio '())  → (unified ())
; (unify-observe 'radio 'antenna '()) → (unification-failure radio antenna ())
;
; Binary self-witness: tests/fixtures/unify-observe-d1-witness.lisp

(0011 уніфікація-спостереження-стан
  (0010 (raw left right substitution)
    (за-умовою
      ((атом? raw)
       (за-умовою
         ((тотожне? raw (як-є fail))
          (список (як-є unification-failure) left right substitution))
         ((атом? (як-є ()))
          (список (як-є unified) raw))))
      ((атом? (як-є ()))
       (список (як-є unified) raw)))))

(0011 unify-observe
  (0010 (left right substitution)
    (уніфікація-спостереження-стан
      (unify left right substitution)
      left right substitution)))
