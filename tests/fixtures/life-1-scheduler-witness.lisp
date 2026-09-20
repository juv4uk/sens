; #801 — Lisp-owned scheduler witness.
;
; The witness models the first LIFE-1 activation path only as ordinary data:
; a Prolog projection becoming ready activates a Datalog pending invocation.
; No kernel is called here; invocation routing remains a later mechanism step.

(def life-1-scheduler-witness
  (lambda ()
    (let* ((first
             (quote
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-42)
                 (priority ordinary)
                 (semantic-id "00001100"))))
           (first-duplicate
             (quote
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-42)
                 (priority ordinary)
                 (semantic-id "00001100"))))
           (second
             (quote
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-99)
                 (priority ordinary)
                 (semantic-id "00001100"))))
           (pending
             (life-scheduler-pending
               (list first first-duplicate second)))
           (projections
             (quote
               ((projection-ready
                  prolog-substitutions-to-datalog-facts
                  observation-42)
                (projection-ready
                  prolog-substitutions-to-datalog-facts
                  observation-99))))
           (selection
             (life-scheduler-select-ready pending projections))
           (wrong-provenance
             (life-scheduler-projection-ready?
               first
               (quote
                 ((projection-ready
                    prolog-substitutions-to-datalog-facts
                    observation-99)))))
           (wrong-bridge
             (life-scheduler-projection-ready?
               first
               (quote
                 ((projection-ready
                    different-bridge-contract
                    observation-42))))))
      (cond
        ((atom selection) (structural-kind empty-list)
         (list
           (quote life-1-scheduler-witness)
           (list (quote status) (quote fail))
           (list (quote detail) (quote missing-selection))))
        ((atom selection) (structural-kind pair)
         (let* ((ready (car (cdr selection)))
                (remaining (car (cdr (cdr (cdr selection)))))
                (dedup-ok (equal? remaining (list second)))
                (quiescence-ok
                  (equal?
                    (life-scheduler-quiescence
                      (quote ())
                      (quote ())
                      (quote no-transition-required))
                    (quote (quiescence-state quiescent))))
                (adversarial-ok
                  (equal?
                    (list wrong-provenance wrong-bridge)
                    (quote (absent absent)))))
           (cond
             ((equal?
                (list ready dedup-ok quiescence-ok adversarial-ok)
                (quote
                  (ready
                    (structural-relation same)
                    (structural-relation same)
                    (structural-relation same))))
              (structural-relation same)
              (list
                (quote life-1-scheduler-witness)
                (list (quote status) (quote pass))
                (list (quote detail)
                      (quote deduplicated-activation-and-quiescence))))
             ((equal? (list wrong-provenance wrong-bridge)
                      (quote (absent absent)))
              (structural-relation same)
              (list
                (quote life-1-scheduler-witness)
                (list (quote status) (quote fail))
                (list (quote detail) (quote scheduler-invariant-mismatch))))
             ((equal? (list wrong-provenance wrong-bridge)
                      (quote (absent absent)))
              (structural-relation distinct)
              (list
                (quote life-1-scheduler-witness)
                (list (quote status) (quote fail))
                (list (quote detail) (quote adversarial-readiness-mismatch)))))))))))

(life-1-scheduler-witness)
