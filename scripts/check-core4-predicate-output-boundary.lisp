; #1260 — executable guard for the final Core4 predicate-answer boundary.
;
; The language-owned policy decides only the output boundary.  It does not
; outlaw rich observations inside mechanisms and it does not make performance,
; native fast paths, FPGA layout, or SID width into semantic authority.

(def pob-policy-form
  (car (read-all (read-file "contracts/core4-predicate-output-boundary.lisp"))))
(def pob-policy-sections (cdr pob-policy-form))
(def pob-policy-raw (second pob-policy-sections))
(def pob-policy-final (third pob-policy-sections))
(def pob-policy-endpoint (fifth pob-policy-sections))

(def pob-boundary-form
  (car (read-all (read-file "contracts/core4-predicate-answer-boundary.lisp"))))
(def pob-boundary-sections (cdr pob-boundary-form))
(def pob-boundary-lower (second pob-boundary-sections))
(def pob-boundary-upper (third pob-boundary-sections))

(def pob-field-from
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
               (pob-field-from name (cdr fields)))))
           ((quote pob-next) pob-next
            (pob-field-from name (cdr fields)))))))))

(def pob-field
  (lambda (section name)
    (pob-field-from name section)))

(def pob-symbol-in
  (lambda (needle values)
    (cond
      ((atom values) (structural-kind empty-list) (quote no))
      ((atom values) (structural-kind pair)
       (cond
         ((eq needle (car values)) (identity-relation same) (quote yes))
         ((eq needle (car values)) (identity-relation distinct)
          (pob-symbol-in needle (cdr values))))))))

(def pob-load-row
  (lambda (path)
    (second (car (read-all (read-file path))))))

(def pob-check-case
  (lambda (row)
    (let ((role (pob-field row (quote role)))
          (raw-domain (pob-field row (quote raw-domain)))
          (projection-law (pob-field row (quote projection-law)))
          (final-domain (pob-field row (quote final-domain)))
          (rich-domains
            (pob-field pob-policy-raw (quote raw-observation-domains)))
          (required-final
            (pob-field pob-policy-final
                       (quote predicate-question-final-domain))))
      (cond
        ((eq role (quote predicate-question)) (identity-relation same)
         (cond
           ((eq final-domain required-final) (identity-relation distinct)
            (quote (violation rich-observation-as-final)))
           ((eq final-domain required-final) (identity-relation same)
            (cond
              ((pob-symbol-in raw-domain rich-domains) yes
               (cond
                 ((equal? projection-law (quote none))
                  (structural-relation same)
                  (quote (violation missing-lisp-projection)))
                 ((quote projection-present) projection-present
                  (quote pass))))
              ((quote raw-domain-not-rich) raw-domain-not-rich
               (quote pass))))))
        ((quote non-predicate-row) non-predicate-row
         (quote pass))))))

(def pob-allowed
  (pob-check-case
    (pob-load-row "tests/fixtures/core4-predicate-output-allowed.lisp")))

(def pob-forbidden
  (pob-check-case
    (pob-load-row "tests/fixtures/core4-predicate-output-forbidden.lisp")))

(def pob-policy-endpoint-flow
  (pob-field pob-policy-endpoint (quote endpoint-flow)))

(def pob-boundary-endpoint-flow
  (list
    (list
      (pob-field pob-boundary-lower (quote direction))
      (pob-field pob-boundary-lower (quote sid-anchor))
      (pob-field pob-boundary-lower (quote projection)))
    (list
      (pob-field pob-boundary-upper (quote direction))
      (pob-field pob-boundary-upper (quote sid-anchor))
      (pob-field pob-boundary-upper (quote projection)))))

(cond
  ((eq pob-allowed (quote pass)) (identity-relation same)
   (cond
     ((equal? pob-forbidden
              (quote (violation rich-observation-as-final)))
      (structural-relation same)
      (cond
        ((equal? pob-policy-endpoint-flow pob-boundary-endpoint-flow)
         (structural-relation same)
         (quote (core4-predicate-output-boundary-ok)))
        ((quote endpoint-flow-mismatch) endpoint-flow-mismatch
         (list (quote core4-predicate-output-endpoint-flow-mismatch)
               pob-boundary-endpoint-flow
               pob-policy-endpoint-flow))))
     ((quote negative-fixture-failed) negative-fixture-failed
      (list (quote core4-predicate-output-negative-fixture-mismatch)
            pob-forbidden))))
  ((quote positive-fixture-failed) positive-fixture-failed
   (list (quote core4-predicate-output-positive-fixture-mismatch)
         pob-allowed)))
