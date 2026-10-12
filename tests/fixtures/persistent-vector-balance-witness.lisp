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
(0011 range-list
  (0010 (n acc)
    (110
      ((11010 n 0) acc)
      ((11110111 0 0) (range-list (01011 n 1) (111 n acc))))))

(0011 persistent-vector-balance-check
  (0010 ()
    (001001 ((v (101111011 (range-list 499 (001 ()))))
           (h (vnode-height (vec-tree v)))
           (balanced? (11010 h 15)))
      (110
        ((101 balanced? 1) (1)
         (001 (persistent-vector-balance-witness (status pass))))
        (t
         (1110
           (001 persistent-vector-balance-witness)
           (001 (status fail))
           (1110 (001 height) h)
           (1110 (001 balanced) balanced?)))))))

(persistent-vector-balance-check)
