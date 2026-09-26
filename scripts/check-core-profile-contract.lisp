; #1131 — executable my-lisp witness for contracts/core-profile-contract.lisp.
;
; Цей файл не визначає профільні закони. Він читає authority-документ як
; Lisp-дані та перевіряє лише критичні інваріанти four-core boundary.
;
; Успіх:
;   (core-profile-contract-ok)
;
; Порушення:
;   (core-profile-contract-violation ...)

(def cp-contract-forms
  (read-all (read-file "contracts/core-profile-contract.lisp")))

(def cp-contract (car cp-contract-forms))
(def cp-schema (car cp-contract))
(def cp-sections (cdr cp-contract))

(def cp-field-from
  (lambda (name fields)
    (cond
      ((atom? fields) () (quote missing))
      ((atom? fields) (0)
       (let ((field (car fields)))
         (cond
           ((atom? field) (0)
            (cond
              ((eq? (car field) name) (1) (cdr field))
              ((eq? (car field) name) (0)
               (cp-field-from name (cdr fields)))))
           ((atom? field) (1)
            (cp-field-from name (cdr fields)))
           ((atom? field) ()
            (cp-field-from name (cdr fields)))))))))

(def cp-field
  (lambda (section name)
    (cp-field-from name section)))

(def cp-find-section
  (lambda (wanted sections)
    (cond
      ((atom? sections) () (quote ()))
      ((atom? sections) (0)
       (let ((section (car sections)))
         (cond
           ((eq? (cp-field section (quote identity)) wanted)
            (1)
            section)
           ((eq? (cp-field section (quote identity)) wanted)
            (0)
            (cp-find-section wanted (cdr sections)))))))))

(def cp-check
  (lambda (section-name field-name expected)
    (let ((section (cp-find-section section-name cp-sections)))
      (cond
        ((atom? section) ()
         (list (quote missing-section) section-name))
        ((atom? section) (0)
         (let ((actual (cp-field section field-name)))
           (cond
             ((equal? actual expected) (1)
              (quote ()))
             ((equal? actual expected) (0)
              (list (quote mismatch)
                    section-name
                    field-name
                    expected
                    actual)))))))))

(def cp-first-failure
  (lambda (checks)
    (cond
      ((atom? checks) () (quote ()))
      ((atom? checks) (0)
       (let ((check (car checks)))
         (cond
           ((atom? check) ()
            (cp-first-failure (cdr checks)))
           ((atom? check) (0)
            check)
           ((atom? check) (1)
            (list (quote malformed-check) check))))))))

(def cp-contract-verdict
  (lambda ()
    (cond
      ((eq? cp-schema (quote core-profile-contract/2))
       (1)
       (let ((failure
               (cp-first-failure
                 (list
                   (cp-check (quote authority) (quote owner) (quote my-lisp))
                   (cp-check (quote authority) (quote sid-identity) (quote shared))
                   (cp-check (quote authority) (quote canon-identity) (quote shared))
                   (cp-check (quote authority) (quote semantic-registry) (quote shared))
                   (cp-check (quote authority) (quote profile-law-selection) (quote required))
                   (cp-check (quote authority) (quote profile-may-mint-sid) (quote forbidden))
                   (cp-check (quote authority) (quote profile-may-renumber-sid) (quote forbidden))
                   (cp-check (quote authority) (quote backend-may-own-sid-meaning) (quote forbidden))
                   (cp-check (quote authority) (quote single-law-for-all-profiles) (quote forbidden))

                   (cp-check (quote core1) (quote profile-number) 1)
                   (cp-check (quote core1) (quote role) (quote bootstrap-historical-root))
                   (cp-check (quote core1) (quote execution-source) "lib/core1.lisp")
                   (cp-check (quote core1) (quote status) (quote admitted))

                   (cp-check (quote core2) (quote profile-number) 2)
                   (cp-check (quote core2) (quote role) (quote frozen-legacy-compatibility))
                   (cp-check (quote core2) (quote historical-contract) (quote (6 0)))
                   (cp-check (quote core2) (quote status) (quote admitted))

                   (cp-check (quote core3) (quote profile-number) 3)
                   (cp-check (quote core3) (quote role) (quote experimental-kernel-laboratory))
                   (cp-check (quote core3) (quote status) (quote partial-native-observation-admitted-canon-operation-pending))
                   (cp-check (quote core3) (quote law-source) "contracts/core3-profile-contract.lisp")
                   (cp-check (quote core3) (quote execution-source) "lib/core3.lisp")
                   (cp-check (quote core3) (quote historical-contract) (quote (7 0)))
                   (cp-check (quote core3) (quote selector-owner) (quote my-lisp))
                   (cp-check (quote core3) (quote lowering-owner) (quote my-lisp))
                   (cp-check (quote core3) (quote native-observation-is-language-law) (quote no))

                   (cp-check (quote core4) (quote profile-number) 4)
                   (cp-check (quote core4) (quote role) (quote current-creative-language))
                   (cp-check (quote core4) (quote historical-contract) (quote (8 0)))
                   (cp-check (quote core4) (quote execution-source) "lib/core4.lisp")
                   (cp-check (quote core4) (quote fasl-source) "lib/core4.lisp.fasl")
                   (cp-check (quote core4) (quote compatibility-donor) "lib/core.lisp")
                   (cp-check (quote core4) (quote status) (quote admitted))

                   (cp-check
                     (quote profile-selection)
                     (quote same-sid-across-profiles)
                     (quote required))
                   (cp-check
                     (quote profile-selection)
                     (quote same-sid-may-select-profile-specific-law)
                     (quote yes))
                   (cp-check
                     (quote profile-selection)
                     (quote same-sid-may-select-profile-specific-result-domain)
                     (quote yes))
                   (cp-check
                     (quote profile-selection)
                     (quote profile-selection-precedes-mechanism-selection)
                     (quote yes))
                   (cp-check
                     (quote profile-selection)
                     (quote mechanism-selection-may-ratify-language-law)
                     (quote no))
                   (cp-check
                     (quote profile-selection)
                     (quote implicit-fallback-to-another-profile)
                     (quote forbidden))

                   (cp-check
                     (quote migration-state)
                     (quote core2-source)
                     (quote admitted))
                   (cp-check
                     (quote migration-state)
                     (quote core4-source)
                     (quote admitted))
                   (cp-check (quote migration-state) (quote core3-source) (quote partial))
                   (cp-check
                     (quote migration-state)
                     (quote current-lib-core-role)
                     (quote core4-compatibility-donor))
                   (cp-check
                     (quote migration-state)
                     (quote current-lib-core-is-core1)
                     (quote no))
                   (cp-check
                     (quote migration-state)
                     (quote copy-current-core-four-times)
                     (quote forbidden))))))
         (cond
           ((atom? failure) ()
            (list (quote core-profile-contract-ok)))
           ((atom? failure) (0)
            (list (quote core-profile-contract-violation) failure)))))
      ((eq? cp-schema (quote core-profile-contract/2))
       (0)
       (list
         (quote core-profile-contract-violation)
         (list (quote schema) (quote core-profile-contract/2) cp-schema))))))

(cp-contract-verdict)
