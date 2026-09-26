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

(def unify-observe
  (lambda (left right substitution)
    (let ((raw (unify left right substitution)))
      (cond
        ((atom? raw) (1)
         (cond
           ((eq? raw (quote fail)) (1)
            (list
              (quote unification-failure)
              left
              right
              substitution))
           ((eq? raw (quote fail)) (0)
            (list (quote unified) raw))))
        ((atom? raw) ()
         (list (quote unified) raw))
        ((atom? raw) (0)
         (list (quote unified) raw))))))
