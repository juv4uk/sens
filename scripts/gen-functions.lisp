;; Live builtin inventory (contract 2.1): every binding whose value prints
;; as #<builtin ...>. Run: ./target/release/my-lisp scripts/gen-functions.lisp
;; Output: one builtin name per line.
(def builtins
  (filter
    (lambda (p) (string-prefix? "#<builtin" (write-to-string (cdr p))))
    (env)))

(def emit-pair
  (lambda (p)
    (princ (car p))))

(def emit
  (lambda (lst)
    (cond
      ((atom? lst) () (quote ()))
      ((atom? lst) (1) (quote ()))
      (t (cons
           (emit-pair (car lst))
           (emit (cdr lst)))))))

(emit builtins)
