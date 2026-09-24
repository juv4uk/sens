; #1258 — first vertical slice of the Core4 predicate-answer model.
;
; `eq` (Rust builtin, SID 00000011) is historical Core1 mechanism and stays
; completely unchanged: it still returns `(identity-relation same|distinct)`
; and still errors on a non-atom argument. `eq?` is a new, separate,
; Lisp-owned wrapper that answers with the Core4 predicate-answer spelling
; from #1255's table (level 1: "1" for a fully-determined yes, "0" for a
; fully-determined no) instead of the structural record. No weaker level
; (11/00/...) is assigned here — #1258 explicitly forbids inventing those
; without a separate law/proof.
;
; SID identity plays no role in this answer: `eq?` is pure Lisp composition
; over the existing `eq` builtin, never a new semantic identity of its own.

(def eq?
  (lambda (a b)
    (cond
      ((eq a b) (identity-relation same) "1")
      ((eq a b) (identity-relation distinct) "0"))))
