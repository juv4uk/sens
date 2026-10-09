; #216 — Lisp-owned verdict for exact-Q binary comparison rows.

(def binary-field
  (lambda (row field)
    (let ((found (assoc field row)))
      (cond
        ((atom found) (quote ()))
        (t (cdr found))))))

(def binary-math-verdict
  (lambda (row actual-kind actual-render)
    (cond
      ((not (equal? (binary-field row (quote expected-kind)) actual-kind))
       (list (quote binary-math-result)
             (list (quote status) (quote fail))
             (list (quote detail)
                   (list (quote kind)
                         (binary-field row (quote expected-kind))
                         actual-kind))))
      ((not (equal? (binary-field row (quote expected-render)) actual-render))
       (list (quote binary-math-result)
             (list (quote status) (quote fail))
             (list (quote detail)
                   (list (quote render)
                         (binary-field row (quote expected-render))
                         actual-render))))
      (t
       (list (quote binary-math-result)
             (list (quote status) (quote pass))
             (list (quote detail) (binary-field row (quote decision))))))))
