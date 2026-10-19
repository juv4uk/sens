; #220/#287 — epistemic relation and round-trip verdicts belong to Lisp.
; Rust may execute this witness and observe its named status envelope, but it
; must not author the semantic expected shape for equal?/eq results.
;
; The rows preserve the laws previously hidden behind Rust `== "t"` checks:
; supporting-evidence returns the concrete matching record; canonical
; epistemic records and current core result values survive write/read; and a
; genuine external JSON Bool(false) remains distinct from its read-back ().

(визначити epistemic-authority-rows
  (функція ()
    (нехай-послідовно ((simple-claim-ref (як-є (claim-ref cml-build-available)))
           (simple-evidence
             (make-evidence
               simple-claim-ref
               (як-є live-test)
               (як-є supports)
               (як-є (digest "d"))))
           (structural-claim-ref
             (як-є
               (claim-ref
                 (claim
                   (statement (build cml succeeds))
                   (source (observation local-run))
                   (review proposed)))))
           (structural-evidence
             (make-evidence
               structural-claim-ref
               (як-є live-test)
               (як-є supports)
               (як-є (digest "d"))))
           (observation
             (make-observation
               (як-є (digest "sha256:abc"))
               (як-є (build cml succeeds))))
           (claim
             (make-claim
               (як-є (build cml succeeds))
               (як-є (observation local-run))
               (як-є proposed)))
           (evidence
             (make-evidence
               (як-є (claim-ref cml-build-available))
               (як-є live-test)
               (як-є supports)
               (як-є (test (fixture conformance.my) (case exact-rational-division)))))
           (intent
             (make-intent
               (як-є (build cml))
               (як-є (process:cargo tcp-client))
               (як-є (missing-capability))
               (як-є (build-artifact cml)))))
      (список
        (список
          (як-є supporting-evidence-simple)
          (однакові? (supporting-evidence simple-evidence simple-claim-ref) simple-evidence)
          (як-є (structural-relation same)))
        (список
          (як-є supporting-evidence-structural)
          (однакові? (supporting-evidence structural-evidence structural-claim-ref) structural-evidence)
          (як-є (structural-relation same)))
        (список
          (як-є observation-round-trip)
          (однакові? (read (write-to-string observation)) observation)
          (як-є (structural-relation same)))
        (список
          (як-є claim-round-trip)
          (однакові? (read (write-to-string claim)) claim)
          (як-є (structural-relation same)))
        (список
          (як-є evidence-round-trip)
          (однакові? (read (write-to-string evidence)) evidence)
          (як-є (structural-relation same)))
        (список
          (як-є intent-round-trip)
          (однакові? (read (write-to-string intent)) intent)
          (як-є (structural-relation same)))
        (список
          (як-є empty-list-round-trip)
          (однакові? (read (write-to-string (як-є ()))) (як-є ()))
          (як-є (structural-relation same)))
        (список
          (як-є eq-result-round-trip)
          (однакові? (read (write-to-string (eq 1 1))) (eq 1 1))
          (як-є (structural-relation same)))
        (список
          (як-є exact-less-false-round-trip)
          (однакові? (read (write-to-string (< 2 1))) (< 2 1))
          (як-є (structural-relation same)))
        (список
          (як-є exact-less-true-round-trip)
          (однакові? (read (write-to-string (< 1 2))) (< 1 2))
          (як-є (structural-relation same)))
        (список
          (як-є external-json-false-remains-distinct)
          (однакові?
            (read (write-to-string (json-parse "false")))
            (json-parse "false"))
          (як-є (structural-relation distinct)))))))

(визначити epistemic-authority-check
  (функція (rows)
    (за-умовою
      ((атом? rows) (structural-kind empty-list)
       (як-є (epistemic-authority-witness (status pass))))
      ((атом? rows) (structural-kind atom)
       (список
         (як-є epistemic-authority-witness)
         (список (як-є status) (як-є fail))
         (список (як-є case) (як-є malformed-row-tail))
         (список (як-є actual) rows)))
      ((атом? rows) (structural-kind pair)
       (нехай ((row (перше rows)))
         (за-умовою
           ((однакові? (друге row) (третє row)) (structural-relation same)
            (epistemic-authority-check (решта rows)))
           ((однакові? (друге row) (третє row)) (structural-relation distinct)
            (список
              (як-є epistemic-authority-witness)
              (список (як-є status) (як-є fail))
              (список (як-є case) (перше row))
              (список (як-є actual) (друге row))
              (список (як-є expected) (третє row))))))))))

(визначити epistemic-authority-witness
  (функція ()
    (epistemic-authority-check (epistemic-authority-rows))))
