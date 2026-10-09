; #220/#287 — epistemic relation and round-trip verdicts belong to Lisp.
; Rust may execute this witness and observe its named status envelope, but it
; must not author the semantic expected shape for equal?/eq results.
;
; The rows preserve the laws previously hidden behind Rust `== "t"` checks:
; supporting-evidence returns the concrete matching record; canonical
; epistemic records and current core result values survive write/read; and a
; genuine external JSON Bool(false) remains distinct from its read-back ().

(def epistemic-authority-rows
  (lambda ()
    (let* ((simple-claim-ref (quote (claim-ref cml-build-available)))
           (simple-evidence
             (make-evidence
               simple-claim-ref
               (quote live-test)
               (quote supports)
               (quote (digest "d"))))
           (structural-claim-ref
             (quote
               (claim-ref
                 (claim
                   (statement (build cml succeeds))
                   (source (observation local-run))
                   (review proposed)))))
           (structural-evidence
             (make-evidence
               structural-claim-ref
               (quote live-test)
               (quote supports)
               (quote (digest "d"))))
           (observation
             (make-observation
               (quote (digest "sha256:abc"))
               (quote (build cml succeeds))))
           (claim
             (make-claim
               (quote (build cml succeeds))
               (quote (observation local-run))
               (quote proposed)))
           (evidence
             (make-evidence
               (quote (claim-ref cml-build-available))
               (quote live-test)
               (quote supports)
               (quote (test (fixture conformance.my) (case exact-rational-division)))))
           (intent
             (make-intent
               (quote (build cml))
               (quote (process:cargo tcp-client))
               (quote (missing-capability))
               (quote (build-artifact cml)))))
      (list
        (list
          (quote supporting-evidence-simple)
          (equal? (supporting-evidence simple-evidence simple-claim-ref) simple-evidence)
          (quote (structural-relation same)))
        (list
          (quote supporting-evidence-structural)
          (equal? (supporting-evidence structural-evidence structural-claim-ref) structural-evidence)
          (quote (structural-relation same)))
        (list
          (quote observation-round-trip)
          (equal? (read (write-to-string observation)) observation)
          (quote (structural-relation same)))
        (list
          (quote claim-round-trip)
          (equal? (read (write-to-string claim)) claim)
          (quote (structural-relation same)))
        (list
          (quote evidence-round-trip)
          (equal? (read (write-to-string evidence)) evidence)
          (quote (structural-relation same)))
        (list
          (quote intent-round-trip)
          (equal? (read (write-to-string intent)) intent)
          (quote (structural-relation same)))
        (list
          (quote empty-list-round-trip)
          (equal? (read (write-to-string (quote ()))) (quote ()))
          (quote (structural-relation same)))
        (list
          (quote eq-result-round-trip)
          (equal? (read (write-to-string (eq 1 1))) (eq 1 1))
          (quote (structural-relation same)))
        (list
          (quote exact-less-false-round-trip)
          (equal? (read (write-to-string (< 2 1))) (< 2 1))
          (quote (structural-relation same)))
        (list
          (quote exact-less-true-round-trip)
          (equal? (read (write-to-string (< 1 2))) (< 1 2))
          (quote (structural-relation same)))
        (list
          (quote external-json-false-remains-distinct)
          (equal?
            (read (write-to-string (json-parse "false")))
            (json-parse "false"))
          (quote (structural-relation distinct)))))))

(def epistemic-authority-check
  (lambda (rows)
    (cond
      ((atom rows) (structural-kind empty-list)
       (quote (epistemic-authority-witness (status pass))))
      ((atom rows) (structural-kind atom)
       (list
         (quote epistemic-authority-witness)
         (list (quote status) (quote fail))
         (list (quote case) (quote malformed-row-tail))
         (list (quote actual) rows)))
      ((atom rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((equal? (second row) (third row)) (structural-relation same)
            (epistemic-authority-check (cdr rows)))
           ((equal? (second row) (third row)) (structural-relation distinct)
            (list
              (quote epistemic-authority-witness)
              (list (quote status) (quote fail))
              (list (quote case) (car row))
              (list (quote actual) (second row))
              (list (quote expected) (third row))))))))))

(def epistemic-authority-witness
  (lambda ()
    (epistemic-authority-check (epistemic-authority-rows))))
