; #1180 — Lisp-owned checker for the Core1 compiler SID8 resolver.

(def c1r-resolver-form
  (car (read-all (read-file "lib/core1-compiler-sid-resolver.lisp"))))

(def c1r-expected-resolver-form
  (quote
    (DEFINE C1-COMPILER-SID-FOR-SURFACE
      (LAMBDA (NAME)
        (C1-PRIMITIVE-IDENTITY NAME)))))

(def c1r-find-section
  (lambda (name sections)
    (cond
      ((atom? sections) (structural-kind empty-list) (quote ()))
      ((atom? sections) (structural-kind pair)
       (cond
         ((eq? (car (car sections)) name) (identity-relation same)
          (car sections))
         ((eq? (car (car sections)) name) (identity-relation distinct)
          (c1r-find-section name (cdr sections))))))))

(def c1r-authority
  (car (read-all (read-file "contracts/core1-historical-sid-map.lisp"))))

(def c1r-authority-rows
  (cdr (c1r-find-section (quote rows) (cdr c1r-authority))))

(def c1r-seventh
  (lambda (row)
    (car (cdr (cdr (cdr (cdr (cdr (cdr row)))))))))

(def c1r-row-status
  (lambda (surface sid rows)
    (cond
      ((atom? rows) (structural-kind empty-list) (quote missing))
      ((atom? rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((equal? (second row) sid) (structural-relation same)
            (cond
              ((equal? (fourth row) surface) (structural-relation same)
               (c1r-seventh row))
              ((equal? (fourth row) surface) (structural-relation distinct)
               (c1r-row-status surface sid (cdr rows)))))
           ((equal? (second row) sid) (structural-relation distinct)
            (c1r-row-status surface sid (cdr rows)))))))))

(def c1r-check-required
  (lambda (pairs)
    (cond
      ((atom? pairs) (structural-kind empty-list) (quote ()))
      ((atom? pairs) (structural-kind pair)
       (let* ((pair (car pairs))
              (surface (car pair))
              (sid (second pair))
              (status (c1r-row-status surface sid c1r-authority-rows)))
         (cond
           ((eq? status (quote admitted)) (identity-relation same)
            (c1r-check-required (cdr pairs)))
           ((quote c1r-required-fail) c1r-required-fail
            (list (quote required-row-not-admitted) surface sid status))))))))

(def c1r-first-failure
  (lambda (checks)
    (cond
      ((atom? checks) (structural-kind empty-list) (quote ()))
      ((atom? (car checks)) (structural-kind empty-list)
       (c1r-first-failure (cdr checks)))
      ((quote c1r-failure) c1r-failure (car checks)))))

(def c1r-verdict
  (lambda ()
    (let ((failure
            (c1r-first-failure
              (list
                (cond
                  ((equal? c1r-resolver-form c1r-expected-resolver-form)
                   (structural-relation same)
                   (quote ()))
                  ((quote c1r-shape-fail) c1r-shape-fail
                   (list (quote resolver-must-delegate-without-table)
                         c1r-resolver-form)))
                (c1r-check-required
                  (quote
                    ((ATOM 00000010)
                     (EQ 00000011)
                     (CONS 00000100)
                     (CAR 00000101)
                     (CDR 00000110)
                     (NOT 00100001)
                     (LIST 00100111))))
                (cond
                  ((eq?
                     (c1r-row-status
                       (quote PLUS) 00001100 c1r-authority-rows)
                     (quote available-not-admitted))
                   (identity-relation same)
                   (quote ()))
                  ((quote c1r-plus-fail) c1r-plus-fail
                   (quote (plus-must-remain-not-admitted))))
                (cond
                  ((eq?
                     (c1r-row-status
                       (quote DIFFERENCE) 00001101 c1r-authority-rows)
                     (quote available-not-admitted))
                   (identity-relation same)
                   (quote ()))
                  ((quote c1r-minus-fail) c1r-minus-fail
                   (quote (minus-must-remain-not-admitted))))))))
      (cond
        ((atom? failure) (structural-kind empty-list)
         (quote (core1-compiler-sid-resolver-check pass)))
        ((quote c1r-contract-fail) c1r-contract-fail
         (list (quote core1-compiler-sid-resolver-check)
               (quote fail)
               failure))))))

(c1r-verdict)
