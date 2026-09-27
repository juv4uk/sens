; #1275 — executable self-consistency witness for the Core4 EQ result law.
;
; The witness does not choose runtime representation.  It proves only that the
; Lisp-owned law for the existing SID 00000011 points same/distinct observations
; at the strongest yes/no directions already admitted by #1255.

(00001001 eqr-law-form
  (00000101 (01001011 (10100110 "contracts/core4-eq-result-law.lisp"))))
(00001001 eqr-law-schema (00000101 eqr-law-form))
(00001001 eqr-law-sections (00000110 eqr-law-form))

(00001001 eqr-field-from
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
               (eqr-field-from name (00000110 fields)))))
           ((00000001 eqr-next) eqr-next
            (eqr-field-from name (00000110 fields)))))))))

(00001001 eqr-field
  (00001000 (section name)
    (eqr-field-from name section)))

(00001001 eqr-check
  (00001000 (label actual expected)
    (00000111
      ((00100010 actual expected) (1) (00000001 ()))
      ((00000001 eqr-fail) eqr-fail
       (00100111 (00000001 core4-eq-result-law-mismatch)
             label expected actual)))))

(00001001 eqr-first-failure
  (00001000 (checks)
    (00000111
      ((00000010 checks) () (00000001 ()))
      ((00000010 (00000101 checks)) ()
       (eqr-first-failure (00000110 checks)))
      ((00000001 eqr-failure) eqr-failure (00000101 checks)))))

(00001001 eqr-meta (00000101 eqr-law-sections))
(00001001 eqr-same (00101111 eqr-law-sections))
(00001001 eqr-distinct (00110000 eqr-law-sections))
(00001001 eqr-outside (00110001 eqr-law-sections))
(00001001 eqr-integration (00110010 eqr-law-sections))

(00001001 eqr-scale-form
  (00000101 (01001011 (10100110 "contracts/core4-predicate-answer-scale.lisp"))))
(00001001 eqr-scale-sections (00000110 eqr-scale-form))
(00001001 eqr-no-section (00101111 eqr-scale-sections))
(00001001 eqr-yes-section (00110001 eqr-scale-sections))
(00001001 eqr-no-levels (eqr-field eqr-no-section (00000001 levels)))
(00001001 eqr-yes-levels (eqr-field eqr-yes-section (00000001 levels)))
(00001001 eqr-strong-no (00000101 eqr-no-levels))
(00001001 eqr-strong-yes (00000101 eqr-yes-levels))

(00001001 eqr-verdict
  (00001000 ()
    (10011100 ((failure
            (eqr-first-failure
              (00100111
                (eqr-check (00000001 schema)
                           eqr-law-schema
                           (00000001 core4-eq-result-law/1))
                (eqr-check (00000001 profile)
                           (eqr-field eqr-meta (00000001 profile))
                           (00000001 core4))
                (eqr-check (00000001 sid)
                           (eqr-field eqr-meta (00000001 sid))
                           (00000001 00000011))
                (eqr-check (00000001 raw-observation-domain)
                           (eqr-field eqr-meta (00000001 raw-observation-domain))
                           (00000001 identity-relation))
                (eqr-check (00000001 new-sid)
                           (eqr-field eqr-meta (00000001 new-sid))
                           (00000001 forbidden))
                (eqr-check (00000001 eq-alias)
                           (eqr-field eqr-meta (00000001 surface-alias-eq?))
                           (00000001 forbidden))
                (eqr-check (00000001 host-law-table)
                           (eqr-field eqr-meta (00000001 host-profile-law-table))
                           (00000001 forbidden))
                (eqr-check (00000001 runtime-carrier)
                           (eqr-field eqr-meta (00000001 runtime-carrier))
                           (00000001 unresolved-1257))
                (eqr-check (00000001 same-observation)
                           (eqr-field eqr-same (00000001 observation))
                           (00000001 (1)))
                (eqr-check (00000001 same-direction)
                           (eqr-field eqr-same (00000001 direction))
                           (00000001 yes))
                (eqr-check (00000001 same-open-steps)
                           (eqr-field eqr-same (00000001 open-steps))
                           0)
                (eqr-check (00000001 same-contradiction)
                           (eqr-field eqr-same (00000001 contradiction))
                           0)
                (eqr-check (00000001 distinct-observation)
                           (eqr-field eqr-distinct (00000001 observation))
                           (00000001 (0)))
                (eqr-check (00000001 distinct-direction)
                           (eqr-field eqr-distinct (00000001 direction))
                           (00000001 no))
                (eqr-check (00000001 distinct-open-steps)
                           (eqr-field eqr-distinct (00000001 open-steps))
                           0)
                (eqr-check (00000001 distinct-contradiction)
                           (eqr-field eqr-distinct (00000001 contradiction))
                           0)
                (eqr-check (00000001 strongest-yes-spelling)
                           (00000101 eqr-strong-yes)
                           "1")
                (eqr-check (00000001 strongest-no-spelling)
                           (00000101 eqr-strong-no)
                           "0")
                (eqr-check (00000001 outside-domain)
                           (eqr-field eqr-outside (00000001 outside-domain))
                           (00000001 type-error))
                (eqr-check (00000001 outside-is-no)
                           (eqr-field eqr-outside (00000001 outside-domain-is-no))
                           (00000001 forbidden))
                (eqr-check (00000001 integration)
                           (eqr-field eqr-integration (00000001 integration))
                           (00000001 pending-selected-core))))))
      (00000111
        ((00000010 failure) ()
         (00000001 (core4-eq-result-law-ok)))
        ((00000001 eqr-failure-result) eqr-failure-result failure)))))

(eqr-verdict)
