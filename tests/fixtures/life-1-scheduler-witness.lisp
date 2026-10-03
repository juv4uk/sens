; #801 — Lisp-owned scheduler witness.
;
; The witness models the first LIFE-1 activation path only as ordinary data:
; a Prolog projection becoming ready activates a Datalog pending invocation.
; No kernel is called here; invocation routing remains a later mechanism step.

(00001001 life-1-scheduler-witness
  (00001000 ()
    (10011101 ((first
             (00000001
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-42)
                 (priority ordinary)
                 (semantic-id 00001100))))
           (first-duplicate
             (00000001
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-42)
                 (priority ordinary)
                 (semantic-id 00001100))))
           (second-ref
             (00000001
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-99)
                 (priority ordinary)
                 (semantic-id 00001100))))
           (pending
             (life-scheduler-pending
               (00100111 first first-duplicate second-ref)))
           (projections
             (00000001
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
               (00000001
                 ((projection-ready
                    prolog-substitutions-to-datalog-facts
                    observation-99)))))
           (wrong-bridge
             (life-scheduler-projection-ready?
               first
               (00000001
                 ((projection-ready
                    different-bridge-contract
                    observation-42))))))
      (00000111
        ((00000010 selection)
         (00100111
           (00000001 life-1-scheduler-witness)
           (00100111 (00000001 status) (00000001 fail))
           (00100111 (00000001 detail) (00000001 missing-selection))))
        ((00000010 (00000001 ()))
         (10011101 ((ready (00000101 (00000110 selection)))
                (remaining (00000101 (00000110 (00000110 (00000110 selection)))))
                (ready-ok (00000011 ready (00000001 ready)))
                (dedup-ok (00100010 remaining (00100111 second-ref)))
                (quiescence-ok
                  (00100010
                    (life-scheduler-quiescence
                      (00000001 ())
                      (00000001 ())
                      (00000001 no-transition-required))
                    (00000001 (quiescence-state quiescent))))
                (adversarial-ok
                  (00100010
                    (00100111 wrong-provenance wrong-bridge)
                    (00000001 (absent absent)))))
           (00000111
             (adversarial-ok
              (00000111
                (ready-ok
                 (00000111
                   (dedup-ok
                    (00000111
                      (quiescence-ok
                       (00100111
                         (00000001 life-1-scheduler-witness)
                         (00100111 (00000001 status) (00000001 pass))
                         (00100111 (00000001 detail)
                               (00000001 deduplicated-activation-and-quiescence))))
                      ((00000010 (00000001 ()))
                       (00100111
                         (00000001 life-1-scheduler-witness)
                         (00100111 (00000001 status) (00000001 fail))
                         (00100111 (00000001 detail)
                               (00000001 scheduler-invariant-mismatch))))))
                   ((00000010 (00000001 ()))
                    (00100111
                      (00000001 life-1-scheduler-witness)
                      (00100111 (00000001 status) (00000001 fail))
                      (00100111 (00000001 detail)
                            (00000001 scheduler-invariant-mismatch))))))
                ((00000010 (00000001 ()))
                 (00100111
                   (00000001 life-1-scheduler-witness)
                   (00100111 (00000001 status) (00000001 fail))
                   (00100111 (00000001 detail)
                         (00000001 scheduler-invariant-mismatch))))))
             ((00000010 (00000001 ()))
              (00100111
                (00000001 life-1-scheduler-witness)
                (00100111 (00000001 status) (00000001 fail))
                (00100111 (00000001 detail)
                      (00000001 adversarial-readiness-mismatch)))))))))))

(life-1-scheduler-witness)
