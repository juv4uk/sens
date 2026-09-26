; #1133 — executable Core2 authority witness.

(00001001 c2-forms (01001011 (10100110 "contracts/core2-profile-contract.lisp")))
(00001001 c2-contract (00000101 c2-forms))
(00001001 c2-schema (00000101 c2-contract))
(00001001 c2-sections (00000110 c2-contract))

(00001001 c2-field-from
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
               (c2-field-from name (00000110 fields)))))
           ((00000001 c2-next) c2-next
            (c2-field-from name (00000110 fields)))))))))

(00001001 c2-field
  (00001000 (section name)
    (c2-field-from name section)))

(00001001 c2-find
  (00001000 (wanted sections)
    (00000111
      ((00000010 sections) () (00000001 ()))
      ((00000010 sections) (0)
       (10011100 ((section (00000101 sections)))
         (00000111
           ((00000011 (c2-field section (00000001 identity)) wanted)
            (1)
            section)
           ((00000001 c2-next) c2-next
            (c2-find wanted (00000110 sections)))))))))

(00001001 c2-check
  (00001000 (section-name field-name expected)
    (10011100 ((section (c2-find section-name c2-sections)))
      (00000111
        ((00100010 (c2-field section field-name) expected)
         (1)
         (00000001 ()))
        ((00000001 c2-fail) c2-fail
         (00100111 (00000001 mismatch)
               section-name
               field-name
               expected
               (c2-field section field-name)))))))

(00001001 c2-first-failure
  (00001000 (checks)
    (00000111
      ((00000010 checks) () (00000001 ()))
      ((00000010 (00000101 checks)) ()
       (c2-first-failure (00000110 checks)))
      ((00000001 c2-failure) c2-failure (00000101 checks)))))

(load "lib/core2.lisp")

(00001001 c2-verdict
  (00001000 ()
    (10011100 ((failure
            (c2-first-failure
              (00100111
                (c2-check (00000001 authority) (00000001 profile) (00000001 core2))
                (c2-check (00000001 historical-pin) (00000001 language-contract) (00000001 (6 0)))
                (c2-check (00000001 historical-pin) (00000001 baseline-sha) "35c88142548dad137689cd69ca91c430da148bea")
                (c2-check (00000001 result-domain) (00000001 atom-result) (00000001 historical-t-nil))
                (c2-check (00000001 conditional) (00000001 native-clause-shape) (00000001 two-part))
                (c2-check (00000001 conditional) (00000001 selection-rule) (00000001 historical-truthiness))
                (c2-check (00000001 conditional) (00000001 special-form-profile-policy) "contracts/core-special-form-profile-policy.lisp")
                (c2-check (00000001 acceptance-state) (00000001 special-form-profile-policy-recorded) (00000001 yes))
                (c2-check (00000001 acceptance-state) (00000001 native-two-part-cond-activation) (00000001 yes))
                (c2-check (00000001 acceptance-state) (00000001 full-profile-special-form-selection) (00000001 active))))))
      (00000111
        ((00000010 failure) ()
         (00000111
           ((00000011 (core2-atom (00000001 radio)) (00000001 t)) (1)
            (00000111
              ((00000011 (core2-atom (00000001 (radio antenna))) (00000001 ())) (1)
               (00000111
                 ((00000011 (core2-eq (00000001 radio) (00000001 radio)) (00000001 t)) (1)
                  (00000111
                    ((00000011 (core2-truthy? 0) (00000001 t)) (1)
                     (00000001 (core2-profile-contract-ok)))
                    ((00000001 witness-fail) witness-fail
                     (00000001 (core2-profile-contract-violation zero-truthy)))))
                 ((00000001 witness-fail) witness-fail
                  (00000001 (core2-profile-contract-violation eq)))))
              ((00000001 witness-fail) witness-fail
               (00000001 (core2-profile-contract-violation atom-pair)))))
           ((00000001 witness-fail) witness-fail
            (00000001 (core2-profile-contract-violation atom-symbol)))))
        ((00000001 c2-contract-fail) c2-contract-fail
         (00100111 (00000001 core2-profile-contract-violation) failure))))))

(c2-verdict)