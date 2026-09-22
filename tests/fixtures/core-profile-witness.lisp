; #1131 — executable Lisp-owned witness for the four-core profile contract.
; The host only transports contracts/core-profile-contract.lisp as data.

(def core-profile-schema
  (lambda () (car core-profile-document)))

(def core-profile-entries
  (lambda () (cdr core-profile-document)))

(def core-profile-field
  (lambda (entry field)
    (let ((found (assoc field entry)))
      (cond
        ((atom found) (structural-kind empty-list) (quote ()))
        ((quote found) found (cdr found))))))

(def core-profile-find
  (lambda (identity entries)
    (cond
      ((atom entries) (structural-kind empty-list) (quote ()))
      ((eq (core-profile-field (car entries) (quote identity)) identity)
       (identity-relation same)
       (car entries))
      ((quote continue) continue
       (core-profile-find identity (cdr entries))))))

(def core-profile-entry
  (lambda (identity)
    (core-profile-find identity (core-profile-entries))))

(def core-profile-check
  (lambda (identity field expected)
    (let ((entry (core-profile-entry identity)))
      (cond
        ((atom entry) (structural-kind empty-list)
         (list (quote missing-entry) identity))
        ((eq (core-profile-field entry field) expected)
         (identity-relation same)
         (quote ()))
        ((quote mismatch) mismatch
         (list (quote mismatch) identity field expected
               (core-profile-field entry field)))))))

(def core-profile-first-failure
  (lambda (checks)
    (cond
      ((atom checks) (structural-kind empty-list) (quote ()))
      ((atom (car checks)) (structural-kind empty-list)
       (core-profile-first-failure (cdr checks)))
      ((quote failure) failure (car checks)))))

(def core-profile-witness
  (lambda ()
    (let ((failure
            (core-profile-first-failure
              (list
                (core-profile-check
                  (quote authority) (quote owner) (quote my-lisp))
                (core-profile-check
                  (quote authority) (quote canon) (quote single))
                (core-profile-check
                  (quote authority) (quote semantic-registry) (quote single))
                (core-profile-check
                  (quote authority) (quote profiles-may-redefine-meaning) (quote forbidden))
                (core-profile-check
                  (quote core1) (quote role) (quote bootstrap-self-hosting))
                (core-profile-check
                  (quote core1) (quote growth-track) (quote wsm-my-lisp))
                (core-profile-check
                  (quote core1) (quote compiler-witness) (quote cml))
                (core-profile-check
                  (quote core2) (quote role) (quote legacy-my-lisp-compatibility))
                (core-profile-check
                  (quote core2) (quote historical-pin) (quote required-before-activation))
                (core-profile-check
                  (quote core3) (quote role) (quote common-lisp-and-islands))
                (core-profile-check
                  (quote core3) (quote selector-owner) (quote my-lisp))
                (core-profile-check
                  (quote core3) (quote native-observation-preserved) (quote yes))
                (core-profile-check
                  (quote core4) (quote role) (quote current-research))
                (core-profile-check
                  (quote core4) (quote current-default-during-migration) (quote yes))
                (core-profile-check
                  (quote profile-selection) (quote changes-sid-meaning) (quote no))
                (core-profile-check
                  (quote profile-selection) (quote changes-canon-law) (quote no))
                (core-profile-check
                  (quote bootstrap-lineage) (quote generation-provenance) (quote required))
                (core-profile-check
                  (quote bootstrap-lineage) (quote semantic-authority-transfer) (quote forbidden)))))))
      (cond
        ((eq (core-profile-schema) (quote core-profile-contract/1))
         (identity-relation same)
         (cond
           ((atom failure) (structural-kind empty-list)
            (list (quote core-profile-witness)
                  (list (quote status) (quote pass))
                  (list (quote detail) (quote one-authority-four-profiles))))
           ((quote failed) failed
            (list (quote core-profile-witness)
                  (list (quote status) (quote fail))
                  (list (quote detail) failure)))))
        ((quote bad-schema) bad-schema
         (list (quote core-profile-witness)
               (list (quote status) (quote fail))
               (list (quote detail)
                     (list (quote schema) (core-profile-schema)))))))))
