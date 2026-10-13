; #219 — explicit observation boundary for historical unification.
;
; Migrated: two-field COND; canonical exact D1:1 fallback (no computed truth).
; Duplicate arms removed. Failure is positively established data, not host
; truthiness. Width is identity; every bit of the domain address is valued.
;
; Reuses (2000+ surface): unify mechanism 101010000.
;
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

(0011 unify-observe
  (0010 (left right substitution)
    (001000 ((raw (101010000 left right substitution)))
      (110
        ((101 raw (001 fail))
         (1110
           (001 unification-failure)
           left
           right
           substitution))
        (#d1:1
         (1110 (001 unified) raw))))))
