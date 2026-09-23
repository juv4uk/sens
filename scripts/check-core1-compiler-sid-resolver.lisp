; #1180 — Lisp-owned authority check for the Core1 compiler SID8 resolver.
; The checker owns no surface->SID table. It derives every accepted pair from
; contracts/core1-historical-sid-map.lisp and verifies the resolver projection
; stays a one-way, bare-SID8 subset of that authority.

(def core1-sid8-find-section
  (lambda (name sections)
    (cond
      ((atom sections) (structural-kind empty-list) (quote ()))
      ((atom sections) (structural-kind pair)
       (cond
         ((equal? (car (car sections)) name) (structural-relation same)
          (car sections))
         ((equal? (car (car sections)) name) (structural-relation distinct)
          (core1-sid8-find-section name (cdr sections))))))))

(def core1-sid8-authority
  (car (read-all (read-file "contracts/core1-historical-sid-map.lisp"))))

(def core1-sid8-authority-rows
  (cdr
    (core1-sid8-find-section
      (quote rows)
      (cdr core1-sid8-authority))))

(def core1-sid8-resolver
  (car (read-all (read-file "lib/core1-compiler-sid-resolver.lisp"))))

(def core1-sid8-resolver-lambda
  (third core1-sid8-resolver))

(def core1-sid8-resolver-cond
  (third core1-sid8-resolver-lambda))

(def core1-sid8-resolver-clauses
  (cdr core1-sid8-resolver-cond))

(def core1-sid8-authority-row-matches?
  (lambda (surface sid row)
    (cond
      ((equal? (second row) sid) (structural-relation same)
       (cond
         ((equal? (third row) surface) (structural-relation same) (quote yes))
         ((equal? (third row) surface) (structural-relation distinct)
          (cond
            ((equal? (fourth row) surface) (structural-relation same) (quote yes))
            ((equal? (fourth row) surface) (structural-relation distinct) (quote no))))))
      ((equal? (second row) sid) (structural-relation distinct) (quote no)))))

(def core1-sid8-authority-has?
  (lambda (surface sid rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote no))
      ((atom rows) (structural-kind pair)
       (cond
         ((eq (core1-sid8-authority-row-matches? surface sid (car rows)) (quote yes))
          (identity-relation same)
          (quote yes))
         ((eq (core1-sid8-authority-row-matches? surface sid (car rows)) (quote no))
          (identity-relation same)
          (core1-sid8-authority-has? surface sid (cdr rows))))))))

(def core1-sid8-clause-verdict
  (lambda (clause)
    (let* ((query (car clause))
           (result (second clause)))
      (cond
        ((atom query) (structural-kind atom)
         (cond
           ((eq query (quote T)) (identity-relation same)
            (cond
              ((eq result (quote NIL)) (identity-relation same) (quote pass))
              ((eq result (quote NIL)) (identity-relation distinct)
               (list (quote invalid-default-clause) clause))))
           ((eq query (quote T)) (identity-relation distinct)
            (list (quote malformed-query) query))))
        ((atom query) (structural-kind pair)
         (let* ((quoted-surface (third query))
                (surface (second quoted-surface)))
           (cond
             ((eq (car query) (quote EQ)) (identity-relation same)
              (cond
                ((eq (second query) (quote NAME)) (identity-relation same)
                 (cond
                   ((eq (car quoted-surface) (quote QUOTE)) (identity-relation same)
                    (cond
                      ((eq (core1-sid8-authority-has?
                             surface
                             result
                             core1-sid8-authority-rows)
                           (quote yes))
                       (identity-relation same)
                       (quote pass))
                      ((eq (core1-sid8-authority-has?
                             surface
                             result
                             core1-sid8-authority-rows)
                           (quote no))
                       (identity-relation same)
                       (list (quote unauthorized-surface-sid) surface result))))
                   ((eq (car quoted-surface) (quote QUOTE)) (identity-relation distinct)
                    (list (quote malformed-surface-form) quoted-surface))))
                ((eq (second query) (quote NAME)) (identity-relation distinct)
                 (list (quote malformed-query-variable) query))))
             ((eq (car query) (quote EQ)) (identity-relation distinct)
              (list (quote malformed-query) query)))))))))

(def core1-sid8-clauses-verdict
  (lambda (clauses)
    (cond
      ((atom clauses) (structural-kind empty-list)
       (quote (core1-compiler-sid-resolver-check pass)))
      ((atom clauses) (structural-kind pair)
       (let ((verdict (core1-sid8-clause-verdict (car clauses))))
         (cond
           ((eq verdict (quote pass)) (identity-relation same)
            (core1-sid8-clauses-verdict (cdr clauses)))
           ((eq verdict (quote pass)) (identity-relation distinct)
            (list (quote core1-compiler-sid-resolver-check)
                  (quote fail)
                  verdict))))))))

(core1-sid8-clauses-verdict core1-sid8-resolver-clauses)
