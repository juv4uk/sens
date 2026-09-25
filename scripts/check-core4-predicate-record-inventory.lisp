; #1259 — executable observer for the Contract-9 Core4 role inventory.
;
; It validates classification shape only. Function identity is always bare
; exact 8 bits; no surface/name field is admitted as identity.

(def pri-form
  (car (read-all (read-file "knowledge/core4-predicate-record-inventory.lisp"))))
(def pri-schema (car pri-form))
(def pri-sections (cdr pri-form))
(def pri-header (car pri-sections))
(def pri-rows (cdr pri-sections))

(def pri-field-from
  (lambda (name fields)
    (cond
      ((atom? fields) (structural-kind empty-list) (quote missing))
      ((atom? fields) (structural-kind pair)
       (let ((field (car fields)))
         (cond
           ((atom? field) (structural-kind pair)
            (cond
              ((eq? (car field) name) (identity-relation same) (cdr field))
              ((eq? (car field) name) (identity-relation distinct)
               (pri-field-from name (cdr fields)))))
           ((quote pri-next) pri-next
            (pri-field-from name (cdr fields)))))))))

(def pri-field
  (lambda (section name)
    (pri-field-from name section)))

(def pri-row-by-function
  (lambda (function rows)
    (cond
      ((atom? rows) (structural-kind empty-list) (quote missing))
      ((atom? rows) (structural-kind pair)
       (cond
         ((equal? (pri-field (car rows) (quote function)) function)
          (structural-relation same)
          (car rows))
         ((quote pri-next-row) pri-next-row
          (pri-row-by-function function (cdr rows))))))))

(def pri-check
  (lambda (label actual expected)
    (cond
      ((equal? actual expected) (structural-relation same) (quote ()))
      ((quote pri-fail) pri-fail
       (list (quote predicate-record-inventory-mismatch)
             label expected actual)))))

(def pri-first-failure
  (lambda (checks)
    (cond
      ((atom? checks) (structural-kind empty-list) (quote ()))
      ((atom? (car checks)) (structural-kind empty-list)
       (pri-first-failure (cdr checks)))
      ((quote pri-failure) pri-failure (car checks)))))

(def pri-00000010 (pri-row-by-function (quote 00000010) pri-rows))
(def pri-00000011 (pri-row-by-function (quote 00000011) pri-rows))
(def pri-00100010 (pri-row-by-function (quote 00100010) pri-rows))
(def pri-00100011 (pri-row-by-function (quote 00100011) pri-rows))
(def pri-00100100 (pri-row-by-function (quote 00100100) pri-rows))
(def pri-00100110 (pri-row-by-function (quote 00100110) pri-rows))
(def pri-00000111 (pri-row-by-function (quote 00000111) pri-rows))

(def pri-verdict
  (lambda ()
    (let ((failure
            (pri-first-failure
              (list
                (pri-check (quote schema)
                           pri-schema
                           (quote core4-predicate-record-inventory/2))
                (pri-check (quote profile)
                           (pri-field pri-header (quote profile))
                           (quote core4))
                (pri-check (quote identity)
                           (pri-field pri-header (quote function-identity))
                           (quote exact-8-bits-only))
                (pri-check (quote named-ontology)
                           (pri-field pri-header (quote named-function-ontology))
                           (quote forbidden))
                (pri-check (quote no-surface-key-00000010)
                           (pri-field pri-00000010 (quote surface))
                           (quote missing))
                (pri-check (quote role-00000010)
                           (pri-field pri-00000010 (quote current-role))
                           (quote classifier-observer))
                (pri-check (quote target-00000010)
                           (pri-field pri-00000010 (quote target-role))
                           (quote classifier-observer))
                (pri-check (quote role-00000011)
                           (pri-field pri-00000011 (quote current-role))
                           (quote classifier-observer))
                (pri-check (quote target-00000011)
                           (pri-field pri-00000011 (quote target-role))
                           (quote predicate-question))
                (pri-check (quote law-00000011)
                           (pri-field pri-00000011 (quote core4-result-law))
                           (quote ratified-1284))
                (pri-check (quote role-00100010)
                           (pri-field pri-00100010 (quote current-role))
                           (quote predicate-question))
                (pri-check (quote role-00100011)
                           (pri-field pri-00100011 (quote current-role))
                           (quote predicate-question))
                (pri-check (quote role-00100100)
                           (pri-field pri-00100100 (quote current-role))
                           (quote predicate-question))
                (pri-check (quote role-00100110)
                           (pri-field pri-00100110 (quote current-role))
                           (quote predicate-question))
                (pri-check (quote role-00000111)
                           (pri-field pri-00000111 (quote current-role))
                           (quote control-consumer))
                (pri-check (quote compatibility-00000111)
                           (pri-field pri-00000111 (quote compatibility-role))
                           (quote compatibility-only))))))
      (cond
        ((atom? failure) (structural-kind empty-list)
         (quote (core4-predicate-record-inventory-ok)))
        ((quote pri-contract-failure) pri-contract-failure failure)))))

(pri-verdict)
