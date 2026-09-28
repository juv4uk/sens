; #1131 — executable SENS witness for contracts/core-profile-contract.lisp.
;
; Цей файл не визначає профільні закони. Він читає authority-документ як
; Lisp-дані та перевіряє лише критичні інваріанти four-core boundary.
;
; Успіх:
;   (core-profile-contract-ok)
;
; Порушення:
;   (core-profile-contract-violation ...)

(00001001 cp-contract-forms
  (01001011 (10100110 "contracts/core-profile-contract.lisp")))

(00001001 cp-contract (00000101 cp-contract-forms))
(00001001 cp-schema (00000101 cp-contract))
(00001001 cp-sections (00000110 cp-contract))

(00001001 cp-field-from
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
               (cp-field-from name (00000110 fields)))))
           ((00000010 field) (1)
            (cp-field-from name (00000110 fields)))
           ((00000010 field) ()
            (cp-field-from name (00000110 fields)))))))))

(00001001 cp-field
  (00001000 (section name)
    (cp-field-from name section)))

(00001001 cp-find-section
  (00001000 (wanted sections)
    (00000111
      ((00000010 sections) () (00000001 ()))
      ((00000010 sections) (0)
       (10011100 ((section (00000101 sections)))
         (00000111
           ((00000011 (cp-field section (00000001 identity)) wanted)
            (1)
            section)
           ((00000011 (cp-field section (00000001 identity)) wanted)
            (0)
            (cp-find-section wanted (00000110 sections)))))))))

(00001001 cp-check
  (00001000 (section-name field-name expected)
    (10011100 ((section (cp-find-section section-name cp-sections)))
      (00000111
        ((00000010 section) ()
         (00100111 (00000001 missing-section) section-name))
        ((00000010 section) (0)
         (10011100 ((actual (cp-field section field-name)))
           (00000111
             ((00100010 actual expected) (1)
              (00000001 ()))
             ((00100010 actual expected) (0)
              (00100111 (00000001 mismatch)
                    section-name
                    field-name
                    expected
                    actual)))))))))

(00001001 cp-first-failure
  (00001000 (checks)
    (00000111
      ((00000010 checks) () (00000001 ()))
      ((00000010 checks) (0)
       (10011100 ((check (00000101 checks)))
         (00000111
           ((00000010 check) ()
            (cp-first-failure (00000110 checks)))
           ((00000010 check) (0)
            check)
           ((00000010 check) (1)
            (00100111 (00000001 malformed-check) check))))))))

(00001001 cp-contract-verdict
  (00001000 ()
    (00000111
      ((00000011 cp-schema (00000001 core-profile-contract/2))
       (1)
       (10011100 ((failure
               (cp-first-failure
                 (00100111
                   (cp-check (00000001 authority) (00000001 owner) (00000001 sens))
                   (cp-check (00000001 authority) (00000001 sid-identity) (00000001 shared))
                   (cp-check (00000001 authority) (00000001 canon-identity) (00000001 shared))
                   (cp-check (00000001 authority) (00000001 semantic-registry) (00000001 shared))
                   (cp-check (00000001 authority) (00000001 profile-law-selection) (00000001 required))
                   (cp-check (00000001 authority) (00000001 profile-may-mint-sid) (00000001 forbidden))
                   (cp-check (00000001 authority) (00000001 profile-may-renumber-sid) (00000001 forbidden))
                   (cp-check (00000001 authority) (00000001 backend-may-own-sid-meaning) (00000001 forbidden))
                   (cp-check (00000001 authority) (00000001 single-law-for-all-profiles) (00000001 forbidden))

                   (cp-check (00000001 core1) (00000001 profile-number) 1)
                   (cp-check (00000001 core1) (00000001 role) (00000001 bootstrap-historical-root))
                   (cp-check (00000001 core1) (00000001 execution-source) "lib/core1.lisp")
                   (cp-check (00000001 core1) (00000001 status) (00000001 admitted))

                   (cp-check (00000001 core2) (00000001 profile-number) 2)
                   (cp-check (00000001 core2) (00000001 role) (00000001 frozen-legacy-compatibility))
                   (cp-check (00000001 core2) (00000001 historical-contract) (00000001 (6 0)))
                   (cp-check (00000001 core2) (00000001 status) (00000001 admitted))

                   (cp-check (00000001 core3) (00000001 profile-number) 3)
                   (cp-check (00000001 core3) (00000001 role) (00000001 experimental-kernel-laboratory))
                   (cp-check (00000001 core3) (00000001 status) (00000001 partial-native-observation-admitted-canon-operation-pending))
                   (cp-check (00000001 core3) (00000001 law-source) "contracts/core3-profile-contract.lisp")
                   (cp-check (00000001 core3) (00000001 execution-source) "lib/core3.lisp")
                   (cp-check (00000001 core3) (00000001 historical-contract) (00000001 (7 0)))
                   (cp-check (00000001 core3) (00000001 selector-owner) (00000001 sens))
                   (cp-check (00000001 core3) (00000001 lowering-owner) (00000001 sens))
                   (cp-check (00000001 core3) (00000001 native-observation-is-language-law) (00000001 no))

                   (cp-check (00000001 core4) (00000001 profile-number) 4)
                   (cp-check (00000001 core4) (00000001 role) (00000001 current-creative-language))
                   (cp-check (00000001 core4) (00000001 historical-contract) (00000001 (8 0)))
                   (cp-check (00000001 core4) (00000001 execution-source) "lib/core4.lisp")
                   (cp-check (00000001 core4) (00000001 fasl-source) "lib/core4.lisp.fasl")
                   (cp-check (00000001 core4) (00000001 compatibility-donor) "lib/core.lisp")
                   (cp-check (00000001 core4) (00000001 status) (00000001 admitted))

                   (cp-check
                     (00000001 profile-selection)
                     (00000001 same-sid-across-profiles)
                     (00000001 required))
                   (cp-check
                     (00000001 profile-selection)
                     (00000001 same-sid-may-select-profile-specific-law)
                     (00000001 yes))
                   (cp-check
                     (00000001 profile-selection)
                     (00000001 same-sid-may-select-profile-specific-result-domain)
                     (00000001 yes))
                   (cp-check
                     (00000001 profile-selection)
                     (00000001 profile-selection-precedes-mechanism-selection)
                     (00000001 yes))
                   (cp-check
                     (00000001 profile-selection)
                     (00000001 mechanism-selection-may-ratify-language-law)
                     (00000001 no))
                   (cp-check
                     (00000001 profile-selection)
                     (00000001 implicit-fallback-to-another-profile)
                     (00000001 forbidden))

                   (cp-check
                     (00000001 migration-state)
                     (00000001 core2-source)
                     (00000001 admitted))
                   (cp-check
                     (00000001 migration-state)
                     (00000001 core4-source)
                     (00000001 admitted))
                   (cp-check (00000001 migration-state) (00000001 core3-source) (00000001 partial))
                   (cp-check
                     (00000001 migration-state)
                     (00000001 current-lib-core-role)
                     (00000001 core4-compatibility-donor))
                   (cp-check
                     (00000001 migration-state)
                     (00000001 current-lib-core-is-core1)
                     (00000001 no))
                   (cp-check
                     (00000001 migration-state)
                     (00000001 copy-current-core-four-times)
                     (00000001 forbidden))))))
         (00000111
           ((00000010 failure) ()
            (00100111 (00000001 core-profile-contract-ok)))
           ((00000010 failure) (0)
            (00100111 (00000001 core-profile-contract-violation) failure)))))
      ((00000011 cp-schema (00000001 core-profile-contract/2))
       (0)
       (00100111
         (00000001 core-profile-contract-violation)
         (00100111 (00000001 schema) (00000001 core-profile-contract/2) cp-schema))))))

(cp-contract-verdict)
