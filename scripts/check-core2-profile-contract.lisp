; #1133 — executable Core2 authority witness.

(def c2-forms (read-all (read-file "contracts/core2-profile-contract.lisp")))
(def c2-contract (car c2-forms))
(def c2-schema (car c2-contract))
(def c2-sections (cdr c2-contract))

(def c2-field-from
  (lambda (name fields)
    (cond
      ((atom fields) (structural-kind empty-list) (quote missing))
      ((atom fields) (structural-kind pair)
       (let ((field (car fields)))
         (cond
           ((atom field) (structural-kind pair)
            (cond
              ((eq (car field) name) (identity-relation same) (cdr field))
              ((eq (car field) name) (identity-relation distinct)
               (c2-field-from name (cdr fields)))))
           ((quote c2-next) c2-next
            (c2-field-from name (cdr fields)))))))))

(def c2-field
  (lambda (section name)
    (c2-field-from name section)))

(def c2-find
  (lambda (wanted sections)
    (cond
      ((atom sections) (structural-kind empty-list) (quote ()))
      ((atom sections) (structural-kind pair)
       (let ((section (car sections)))
         (cond
           ((eq (c2-field section (quote identity)) wanted)
            (identity-relation same)
            section)
           ((quote c2-next) c2-next
            (c2-find wanted (cdr sections)))))))))

(def c2-check
  (lambda (section-name field-name expected)
    (let ((section (c2-find section-name c2-sections)))
      (cond
        ((equal? (c2-field section field-name) expected)
         (structural-relation same)
         (quote ()))
        ((quote c2-fail) c2-fail
         (list (quote mismatch)
               section-name
               field-name
               expected
               (c2-field section field-name)))))))

(def c2-first-failure
  (lambda (checks)
    (cond
      ((atom checks) (structural-kind empty-list) (quote ()))
      ((atom (car checks)) (structural-kind empty-list)
       (c2-first-failure (cdr checks)))
      ((quote c2-failure) c2-failure (car checks)))))

(load "lib/core2.lisp")

(def c2-verdict
  (lambda ()
    (let ((failure
            (c2-first-failure
              (list
                (c2-check (quote authority) (quote profile) (quote core2))
                (c2-check (quote historical-pin) (quote language-contract) (quote (6 0)))
                (c2-check (quote historical-pin) (quote baseline-sha) "35c88142548dad137689cd69ca91c430da148bea")
                (c2-check (quote result-domain) (quote atom-result) (quote historical-t-nil))
                (c2-check (quote conditional) (quote native-clause-shape) (quote two-part))
                (c2-check (quote conditional) (quote selection-rule) (quote historical-truthiness))
                (c2-check (quote conditional) (quote special-form-profile-policy) "contracts/core-special-form-profile-policy.lisp")
                (c2-check (quote acceptance-state) (quote special-form-profile-policy-recorded) (quote yes))
                (c2-check (quote acceptance-state) (quote native-two-part-cond-activation) (quote yes))
                (c2-check (quote acceptance-state) (quote full-profile-special-form-selection) (quote active))))))
      (cond
        ((atom failure) (structural-kind empty-list)
         (cond
           ((eq (core2-atom (quote radio)) (quote t)) (identity-relation same)
            (cond
              ((eq (core2-atom (quote (radio antenna))) (quote ())) (identity-relation same)
               (cond
                 ((eq (core2-eq (quote radio) (quote radio)) (quote t)) (identity-relation same)
                  (cond
                    ((eq (core2-truthy? 0) (quote t)) (identity-relation same)
                     (quote (core2-profile-contract-ok)))
                    ((quote witness-fail) witness-fail
                     (quote (core2-profile-contract-violation zero-truthy)))))
                 ((quote witness-fail) witness-fail
                  (quote (core2-profile-contract-violation eq)))))
              ((quote witness-fail) witness-fail
               (quote (core2-profile-contract-violation atom-pair)))))
           ((quote witness-fail) witness-fail
            (quote (core2-profile-contract-violation atom-symbol)))))
        ((quote c2-contract-fail) c2-contract-fail
         (list (quote core2-profile-contract-violation) failure))))))

(c2-verdict)