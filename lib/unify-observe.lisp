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

(00001001 unify-observe
  (00001000 (left right substitution)
    (10011100 ((raw (10000111 left right substitution)))
      (00000111
        ((00000010 raw) 
         (00000111
           ((00000011 raw (00000001 fail)) 
            (00100111
              (00000001 unification-failure)
              left
              right
              substitution))
           ((0100 (00000011 raw (00000001 fail)))
            (00100111 (00000001 unified) raw))))
        ((0100 (00000010 raw))
         (00100111 (00000001 unified) raw))
        ((0100 (00000010 raw))
         (00100111 (00000001 unified) raw))))))
