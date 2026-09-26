; #1275 — executable self-consistency witness for the Core4 EQ result law.
;
; The witness does not choose runtime representation.  It proves only that the
; Lisp-owned law for the existing SID 00000011 points same/distinct observations
; at the strongest yes/no directions already admitted by #1255.

(def eqr-law-form
  (car (read-all (read-file "contracts/core4-eq-result-law.lisp"))))
(def eqr-law-schema (car eqr-law-form))
(def eqr-law-sections (cdr eqr-law-form))

(def eqr-field-from
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
               (eqr-field-from name (cdr fields)))))
           ((quote eqr-next) eqr-next
            (eqr-field-from name (cdr fields)))))))))

(def eqr-field
  (lambda (section name)
    (eqr-field-from name section)))

(def eqr-check
  (lambda (label actual expected)
    (cond
      ((equal? actual expected) (1) (quote ()))
      ((quote eqr-fail) eqr-fail
       (list (quote core4-eq-result-law-mismatch)
             label expected actual)))))

(def eqr-first-failure
  (lambda (checks)
    (cond
      ((atom? checks) () (quote ()))
      ((atom? (car checks)) ()
       (eqr-first-failure (cdr checks)))
      ((quote eqr-failure) eqr-failure (car checks)))))

(def eqr-meta (car eqr-law-sections))
(def eqr-same (second eqr-law-sections))
(def eqr-distinct (third eqr-law-sections))
(def eqr-outside (fourth eqr-law-sections))
(def eqr-integration (fifth eqr-law-sections))

(def eqr-scale-form
  (car (read-all (read-file "contracts/core4-predicate-answer-scale.lisp"))))
(def eqr-scale-sections (cdr eqr-scale-form))
(def eqr-no-section (second eqr-scale-sections))
(def eqr-yes-section (fourth eqr-scale-sections))
(def eqr-no-levels (eqr-field eqr-no-section (quote levels)))
(def eqr-yes-levels (eqr-field eqr-yes-section (quote levels)))
(def eqr-strong-no (car eqr-no-levels))
(def eqr-strong-yes (car eqr-yes-levels))

(def eqr-verdict
  (lambda ()
    (let ((failure
            (eqr-first-failure
              (list
                (eqr-check (quote schema)
                           eqr-law-schema
                           (quote core4-eq-result-law/1))
                (eqr-check (quote profile)
                           (eqr-field eqr-meta (quote profile))
                           (quote core4))
                (eqr-check (quote sid)
                           (eqr-field eqr-meta (quote sid))
                           (quote 00000011))
                (eqr-check (quote raw-observation-domain)
                           (eqr-field eqr-meta (quote raw-observation-domain))
                           (quote identity-relation))
                (eqr-check (quote new-sid)
                           (eqr-field eqr-meta (quote new-sid))
                           (quote forbidden))
                (eqr-check (quote eq-alias)
                           (eqr-field eqr-meta (quote surface-alias-eq?))
                           (quote forbidden))
                (eqr-check (quote host-law-table)
                           (eqr-field eqr-meta (quote host-profile-law-table))
                           (quote forbidden))
                (eqr-check (quote runtime-carrier)
                           (eqr-field eqr-meta (quote runtime-carrier))
                           (quote unresolved-1257))
                (eqr-check (quote same-observation)
                           (eqr-field eqr-same (quote observation))
                           (quote (1)))
                (eqr-check (quote same-direction)
                           (eqr-field eqr-same (quote direction))
                           (quote yes))
                (eqr-check (quote same-open-steps)
                           (eqr-field eqr-same (quote open-steps))
                           0)
                (eqr-check (quote same-contradiction)
                           (eqr-field eqr-same (quote contradiction))
                           0)
                (eqr-check (quote distinct-observation)
                           (eqr-field eqr-distinct (quote observation))
                           (quote (0)))
                (eqr-check (quote distinct-direction)
                           (eqr-field eqr-distinct (quote direction))
                           (quote no))
                (eqr-check (quote distinct-open-steps)
                           (eqr-field eqr-distinct (quote open-steps))
                           0)
                (eqr-check (quote distinct-contradiction)
                           (eqr-field eqr-distinct (quote contradiction))
                           0)
                (eqr-check (quote strongest-yes-spelling)
                           (car eqr-strong-yes)
                           "1")
                (eqr-check (quote strongest-no-spelling)
                           (car eqr-strong-no)
                           "0")
                (eqr-check (quote outside-domain)
                           (eqr-field eqr-outside (quote outside-domain))
                           (quote type-error))
                (eqr-check (quote outside-is-no)
                           (eqr-field eqr-outside (quote outside-domain-is-no))
                           (quote forbidden))
                (eqr-check (quote integration)
                           (eqr-field eqr-integration (quote integration))
                           (quote pending-selected-core))))))
      (cond
        ((atom? failure) ()
         (quote (core4-eq-result-law-ok)))
        ((quote eqr-failure-result) eqr-failure-result failure)))))

(eqr-verdict)
