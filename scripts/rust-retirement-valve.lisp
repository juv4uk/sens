; #300 — Lisp owns the Rust retirement verdict.
; CI transports only Rust diff facts into tests/rust-retirement-changes.lisp.
;
; Change rows:
;   (rust-change "path" additions deletions status)
; status is one of: existing | new | deleted
;
; Verdicts:
;   (rust-retirement-ok)
;   (rust-retirement-violation "path" additions status "diagnostic")
;
; Active #299 rule: Lisp may grow; Rust may only shrink.

(def second (lambda (x) (car (cdr x))))
(def third (lambda (x) (car (cdr (cdr x)))))
(def fourth (lambda (x) (car (cdr (cdr (cdr x))))))
(def fifth (lambda (x) (car (cdr (cdr (cdr (cdr x)))))))

(def rust-changes (read-all (read-file "tests/rust-retirement-changes.lisp")))

(def rust-retirement-verdict-for
  (lambda (changes)
    (cond
      ((atom changes) (structural-kind empty-list)
       (quote (rust-retirement-ok)))
      ((atom changes) (structural-kind pair)
       (let ((change (car changes)))
         (let ((path (second change)))
           (let ((additions (third change)))
             (let ((status (fifth change)))
               (cond
                 ((eq status (quote new)) (identity-relation same)
                  (list
                    (quote rust-retirement-violation)
                    path
                    additions
                    status
                    "New Rust paths are forbidden during retirement. See #299."))
                 ((eq status (quote new)) (identity-relation distinct)
                  (cond
                    ((= additions 0) 1
                     (rust-retirement-verdict-for (cdr changes)))
                    ((= additions 0) 0
                     (list
                       (quote rust-retirement-violation)
                       path
                       additions
                       status
                       "Rust may only shrink; added Rust lines are forbidden. See #299.")))))))))))))

(rust-retirement-verdict-for rust-changes)
