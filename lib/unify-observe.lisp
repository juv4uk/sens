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
    (110
      ((010 raw)
       (110
         ((101 raw (001 fail))
          (1110 (001 unification-failure) left right substitution))
         ((010 (001 ()))
          (1110 (001 unified) raw))))
      ((010 (001 ()))
       (1110 (001 unified) raw)))))

(0011 unify-observe
  (0010 (left right substitution)
    (уніфікація-спостереження-стан
      (unify left right substitution)
      left right substitution)))
