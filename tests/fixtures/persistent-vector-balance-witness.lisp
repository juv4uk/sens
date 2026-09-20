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
(def range-list
  (lambda (n acc)
    (cond
      ((< n 0) 1 acc)
      ((< n 0) 0 (range-list (- n 1) (cons n acc))))))

(def persistent-vector-balance-check
  (lambda ()
    (let* ((v (vec-from-list (range-list 499 (quote ()))))
           (h (vnode-height (vec-tree v)))
           (balanced? (< h 15)))
      (cond
        ((eq balanced? 1) (identity-relation same)
         (quote (persistent-vector-balance-witness (status pass))))
        (t
         (list
           (quote persistent-vector-balance-witness)
           (quote (status fail))
           (list (quote height) h)
           (list (quote balanced) balanced?)))))))

(persistent-vector-balance-check)
