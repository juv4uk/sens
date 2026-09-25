; #211 — replaceability witness.
; CI runs this after physically moving lib/machine out of the checkout.
; The expected answers live here in Lisp; the shell observes only the named
; pass envelope. Removing a backend may remove execution capability, never
; the meaning of these already-ratified language forms.

(load "lib/core.lisp")

(def machine-replaceability-rows
  (quote
    ((add
       (+ 2 3)
       5)
     (eq-cond
       (cond
         ((eq? 2 2) (identity-relation same) 111)
         ((eq? 2 2) (identity-relation distinct) 222))
       111)
     (car-cons
       (car (cons 2 3))
       2))))

(def machine-replaceability-run
  (lambda (rows)
    (cond
      ((atom? rows) (structural-kind empty-list)
       (quote (machine-replaceability-witness (status pass))))
      ((atom? rows) (structural-kind atom)
       (list
         (quote machine-replaceability-witness)
         (quote (status fail))
         (list (quote case) (quote malformed-row-tail))))
      ((atom? rows) (structural-kind pair)
       (let* ((row (car rows))
              (name (car row))
              (actual (eval (second row)))
              (expected (third row)))
         (cond
           ((equal? actual expected) (structural-relation same)
            (machine-replaceability-run (cdr rows)))
           ((equal? actual expected) (structural-relation distinct)
            (list
              (quote machine-replaceability-witness)
              (quote (status fail))
              (list (quote case) name)
              (list (quote expected) expected)
              (list (quote actual) actual)))))))))

(machine-replaceability-run machine-replaceability-rows)
