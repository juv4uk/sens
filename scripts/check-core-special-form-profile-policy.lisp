; #1133 — executable witness for Lisp-owned special-form profile policy.

(def csp-policy
  (car
    (read-all
      (read-file "contracts/core-special-form-profile-policy.lisp"))))

(def csp-rows (cdr csp-policy))

(def csp-find
  (lambda (name rows)
    (cond
      ((atom? rows)
       ()
       (quote ()))
      ((atom? rows)
       (0)
       (cond
         ((eq? (car (car rows)) name)
          (1)
          (car rows))
         ((eq? (car (car rows)) name)
          (0)
          (csp-find name (cdr rows))))))))

(def csp-row-check
  (lambda (name expected)
    (let ((actual (csp-find name csp-rows)))
      (cond
        ((equal? actual expected)
         (1)
         (quote ()))
        ((equal? actual expected)
         (0)
         (list (quote mismatch) name expected actual))))))

(def csp-first-failure
  (lambda (checks)
    (cond
      ((atom? checks)
       ()
       (quote ()))
      ((atom? (car checks))
       ()
       (csp-first-failure (cdr checks)))
      ((atom? (car checks))
       (0)
       (car checks))
      ((atom? (car checks))
       (1)
       (car checks)))))

(def csp-verdict
  (lambda ()
    (let ((failure
            (csp-first-failure
              (list
                (csp-row-check
                  (quote owner)
                  (quote (owner my-lisp)))
                (csp-row-check
                  (quote cond-sid)
                  (quote (cond-sid 00000111)))
                (csp-row-check
                  (quote identity)
                  (quote (identity shared-across-profiles)))
                (csp-row-check
                  (quote selection-order)
                  (quote (selection-order profile-before-special-form-mechanism)))
                (csp-row-check
                  (quote core2)
                  (quote
                    (core2
                      clause-family two-part
                      selection-rule historical-truthiness
                      exhaustion-result ()
                      contract (6 0)
                      law-source contracts/core2-profile-contract.lisp
                      activation runtime-profile-hook-required)))
                (csp-row-check
                  (quote core3)
                  (quote
                    (core3
                      clause-family two-part
                      selection-rule historical-truthiness
                      exhaustion-result ()
                      contract (7 0)
                      law-source contracts/core3-profile-contract.lisp
                      activation experimental-profile)))
                (csp-row-check
                  (quote core4)
                  (quote
                    (core4
                      clause-family three-part
                      selection-rule explicit-result-match
                      exhaustion-result UnsatisfiedConditional
                      contract (8 0)
                      law-source language-contract.lisp
                      activation current)))
                (csp-row-check
                  (quote implicit-profile-selection)
                  (quote (implicit-profile-selection forbidden)))
                (csp-row-check
                  (quote host-profile-law-table)
                  (quote (host-profile-law-table forbidden)))
                (csp-row-check
                  (quote runtime-profile-selector)
                  (quote
                    (runtime-profile-selector
                      owner my-lisp
                      state active-mechanical-hook)))))))
      (cond
        ((atom? failure)
         ()
         (quote (core-special-form-profile-policy-ok)))
        ((atom? failure)
         (0)
         (list
           (quote core-special-form-profile-policy-violation)
           failure))
        ((atom? failure)
         (1)
         (list
           (quote core-special-form-profile-policy-violation)
           failure))))))

(csp-verdict)