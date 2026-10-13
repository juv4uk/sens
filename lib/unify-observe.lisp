; #219 — explicit observation boundary for historical unification.
; `unify` remains the compatibility mechanism: it yields a substitution or the
; private-by-convention atom `fail`. This wrapper does not reinterpret either
; as generic truth and does not invent a failure cause that `unify` did not
; preserve.
;
; A successful empty substitution is data, not Canon-0 no-answer:
;   (unify-observe 'radio 'radio '()) => (unified ())
;
; A completed mismatch is a positively established algorithmic outcome:
;   (unify-observe 'radio 'antenna '())
;     => (unification-failure radio antenna ())

; Розділяємо результат уніфікації та керування: атом fail — невдача;
; кожна інша підстановка, зокрема порожня (), — успішні дані.
; Лише D3 COND/ATOM/EQ і D4 DEFINE/LAMBDA; D9:101010000 — запис, не дозвіл.
(0011 уніфікація-спостереження-стан
  (0010 (raw left right substitution)
    (110
      ((010 raw)
       (110
         ((101 raw (001 fail))
          (1110 (001 unification-failure) left right substitution))
         ((010 ())
          (1110 (001 unified) raw))))
      ((010 ())
       (1110 (001 unified) raw)))))

(0011 unify-observe
  (0010 (left right substitution)
    (уніфікація-спостереження-стан
      (unify left right substitution)
      left right substitution)))
