; #801 — Lisp-owned scheduler witness.
;
; The witness models the first LIFE-1 activation path only as ordinary data:
; a Prolog projection becoming ready activates a Datalog pending invocation.
; No kernel is called here; invocation routing remains a later mechanism step.

(0011 life-1-scheduler-witness
  (0010 ()
    (001001 ((first
             (001
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-42)
                 (priority ordinary)
                 (semantic-id 00001100))))
           (first-duplicate
             (001
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-42)
                 (priority ordinary)
                 (semantic-id 00001100))))
           (second-ref
             (001
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-99)
                 (priority ordinary)
                 (semantic-id 00001100))))
           (pending
             (life-scheduler-pending
               (1110 first first-duplicate second-ref)))
           (projections
             (001
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
               (001
                 ((projection-ready
                    prolog-substitutions-to-datalog-facts
                    observation-99)))))
           (wrong-bridge
             (life-scheduler-projection-ready?
               first
               (001
                 ((projection-ready
                    different-bridge-contract
                    observation-42))))))
      (110
        ((010 selection) ()
         (1110
           (001 life-1-scheduler-witness)
           (1110 (001 status) (001 fail))
           (1110 (001 detail) (001 missing-selection))))
        ((010 selection) (0)
         (001001 ((ready (100 (011 selection)))
                (remaining (100 (011 (011 (011 selection)))))
                (dedup-ok (11110111 remaining (1110 second-ref)))
                (quiescence-ok
                  (11110111
                    (life-scheduler-quiescence
                      (001 ())
                      (001 ())
                      (001 no-transition-required))
                    (001 (quiescence-state quiescent))))
                (adversarial-ok
                  (11110111
                    (1110 wrong-provenance wrong-bridge)
                    (001 (absent absent)))))
           (110
             ((11110111
                (1110 ready dedup-ok quiescence-ok adversarial-ok)
                (001
                  (ready
                    (1)
                    (1)
                    (1))))
              (1)
              (1110
                (001 life-1-scheduler-witness)
                (1110 (001 status) (001 pass))
                (1110 (001 detail)
                      (001 deduplicated-activation-and-quiescence))))
             ((11110111 (1110 wrong-provenance wrong-bridge)
                      (001 (absent absent)))
              (1)
              (1110
                (001 life-1-scheduler-witness)
                (1110 (001 status) (001 fail))
                (1110 (001 detail) (001 scheduler-invariant-mismatch))))
             ((11110111 (1110 wrong-provenance wrong-bridge)
                      (001 (absent absent)))
              (0)
              (1110
                (001 life-1-scheduler-witness)
                (1110 (001 status) (001 fail))
                (1110 (001 detail) (001 adversarial-readiness-mismatch)))))))))))

(life-1-scheduler-witness)
