; #1259 — executable observer for the Contract-9 Core4 role inventory.
;
; It validates classification shape only. Function identity is always bare
; exact 8 bits; no surface/name field is admitted as identity.

(00001001 pri-form
  (00000101 (01001011 (10100110 "knowledge/core4-predicate-record-inventory.lisp"))))
(00001001 pri-schema (00000101 pri-form))
(00001001 pri-sections (00000110 pri-form))
(00001001 pri-header (00000101 pri-sections))
(00001001 pri-rows (00000110 pri-sections))

(00001001 pri-field-from
  (00001000 (name fields)
    (00000111
      ((00000010 fields) () (00000001 missing))
      ((00000010 fields) (0)
       (10011100 ((field (00000101 fields)))
         (00000111
           ((00000010 field) (0)
            (00000111
              ((00000011 (00000101 field) name) (1) (00000110 field))
              ((00000011 (00000101 field) name) (0)
               (pri-field-from name (00000110 fields)))))
           ((00000001 pri-next) pri-next
            (pri-field-from name (00000110 fields)))))))))

(00001001 pri-field
  (00001000 (section name)
    (pri-field-from name section)))

(00001001 pri-row-by-function
  (00001000 (function rows)
    (00000111
      ((00000010 rows) () (00000001 missing))
      ((00000010 rows) (0)
       (00000111
         ((00100010 (pri-field (00000101 rows) (00000001 function)) function)
          (1)
          (00000101 rows))
         ((00000001 pri-next-row) pri-next-row
          (pri-row-by-function function (00000110 rows))))))))

(00001001 pri-check
  (00001000 (label actual expected)
    (00000111
      ((00100010 actual expected) (1) (00000001 ()))
      ((00000001 pri-fail) pri-fail
       (00100111 (00000001 predicate-record-inventory-mismatch)
             label expected actual)))))

(00001001 pri-first-failure
  (00001000 (checks)
    (00000111
      ((00000010 checks) () (00000001 ()))
      ((00000010 (00000101 checks)) ()
       (pri-first-failure (00000110 checks)))
      ((00000001 pri-failure) pri-failure (00000101 checks)))))

(00001001 pri-00000010 (pri-row-by-function (00000001 00000010) pri-rows))
(00001001 pri-00000011 (pri-row-by-function (00000001 00000011) pri-rows))
(00001001 pri-00100010 (pri-row-by-function (00000001 00100010) pri-rows))
(00001001 pri-00100011 (pri-row-by-function (00000001 00100011) pri-rows))
(00001001 pri-00100100 (pri-row-by-function (00000001 00100100) pri-rows))
(00001001 pri-00100110 (pri-row-by-function (00000001 00100110) pri-rows))
(00001001 pri-00000111 (pri-row-by-function (00000001 00000111) pri-rows))

(00001001 pri-verdict
  (00001000 ()
    (10011100 ((failure
            (pri-first-failure
              (00100111
                (pri-check (00000001 schema)
                           pri-schema
                           (00000001 core4-predicate-record-inventory/2))
                (pri-check (00000001 profile)
                           (pri-field pri-header (00000001 profile))
                           (00000001 core4))
                (pri-check (00000001 identity)
                           (pri-field pri-header (00000001 function-identity))
                           (00000001 exact-8-bits-only))
                (pri-check (00000001 named-ontology)
                           (pri-field pri-header (00000001 named-function-ontology))
                           (00000001 forbidden))
                (pri-check (00000001 no-surface-key-00000010)
                           (pri-field pri-00000010 (00000001 surface))
                           (00000001 missing))
                (pri-check (00000001 role-00000010)
                           (pri-field pri-00000010 (00000001 current-role))
                           (00000001 classifier-observer))
                (pri-check (00000001 target-00000010)
                           (pri-field pri-00000010 (00000001 target-role))
                           (00000001 classifier-observer))
                (pri-check (00000001 role-00000011)
                           (pri-field pri-00000011 (00000001 current-role))
                           (00000001 classifier-observer))
                (pri-check (00000001 target-00000011)
                           (pri-field pri-00000011 (00000001 target-role))
                           (00000001 predicate-question))
                (pri-check (00000001 law-00000011)
                           (pri-field pri-00000011 (00000001 core4-result-law))
                           (00000001 ratified-1284))
                (pri-check (00000001 role-00100010)
                           (pri-field pri-00100010 (00000001 current-role))
                           (00000001 predicate-question))
                (pri-check (00000001 role-00100011)
                           (pri-field pri-00100011 (00000001 current-role))
                           (00000001 predicate-question))
                (pri-check (00000001 role-00100100)
                           (pri-field pri-00100100 (00000001 current-role))
                           (00000001 predicate-question))
                (pri-check (00000001 role-00100110)
                           (pri-field pri-00100110 (00000001 current-role))
                           (00000001 predicate-question))
                (pri-check (00000001 role-00000111)
                           (pri-field pri-00000111 (00000001 current-role))
                           (00000001 control-consumer))
                (pri-check (00000001 compatibility-00000111)
                           (pri-field pri-00000111 (00000001 compatibility-role))
                           (00000001 compatibility-only))))))
      (00000111
        ((00000010 failure) ()
         (00000001 (core4-predicate-record-inventory-ok)))
        ((00000001 pri-contract-failure) pri-contract-failure failure)))))

(pri-verdict)
