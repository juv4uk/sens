; #305 — persistent-vector AVL-balance law is owned by Lisp.
; Inserting ascending keys into an empty vector must produce an AVL-balanced
; tree whose height remains logarithmic (< 15 for 500 items), not O(n).
; Comparison `<` evaluates in the exact arithmetic domain and produces 1.
; The shell observes only this witness's named envelope.

(load "lib/core.lisp")
(load "lib/persistent-vector.lisp")

; #613 migrated lib sites to canonical three-part cond but left this
; witness's two-part gate: (< n 0) answers exact-Q 0 for n >= 0, and 0 is
; truthy -- so range-list returned the empty accumulator immediately.
; E1 (#216): explicit expected-result domains under the current 1/0 answers.
(00001001 range-list
  (00001000 (n acc)
    (00000111
      ((00011010 n 0) acc)
      ((00011100 0 0) (range-list (00001101 n 1) (00000100 n acc))))))

(00001001 persistent-vector-balance-check
  (00001000 ()
    (10011101 ((v (01110110 (range-list 499 (00000001 ()))))
           (h (vnode-height (vec-tree v)))
           (balanced? (00011010 h 15)))
      (00000111
        ((00000011 balanced? 1) (1)
         (00000001 (persistent-vector-balance-witness (status pass))))
        (t
         (00100111
           (00000001 persistent-vector-balance-witness)
           (00000001 (status fail))
           (00100111 (00000001 height) h)
           (00100111 (00000001 balanced) balanced?)))))))

(persistent-vector-balance-check)
