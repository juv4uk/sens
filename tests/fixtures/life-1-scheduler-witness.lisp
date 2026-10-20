; #801 — Lisp-owned scheduler witness.
; Ukrainian projection only.

(визначити life-1-scheduler-witness
  (функція ()
    (нехай ((first
             (як-є
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-42)
                 (priority ordinary)
                 (semantic-id 12))))
           (first-duplicate
             (як-є
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-42)
                 (priority ordinary)
                 (semantic-id 12))))
           (second-ref
             (як-є
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-99)
                 (priority ordinary)
                 (semantic-id 12))))
           (pending
             (life-scheduler-pending
               (список first first-duplicate second-ref)))
           (projections
             (як-є
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
               (як-є
                 ((projection-ready
                    prolog-substitutions-to-datalog-facts
                    observation-99)))))
           (wrong-bridge
             (life-scheduler-projection-ready?
               first
               (як-є
                 ((projection-ready
                    different-bridge-contract
                    observation-42))))))
      (за-умовою
        ((атом? selection)
         (список
           (як-є life-1-scheduler-witness)
           (список (як-є status) (як-є fail))
           (список (як-є detail) (як-є missing-selection))))
        (так
         (нехай ((ready (перше (решта selection)))
                (remaining (перше (решта (решта (решта selection)))))
                (dedup-ok (однакові? remaining (список second-ref)))
                (quiescence-ok
                  (однакові?
                    (life-scheduler-quiescence
                      (як-є ())
                      (як-є ())
                      (як-є no-transition-required))
                    (як-є (quiescence-state quiescent))))
                (adversarial-ok
                  (однакові?
                    (список wrong-provenance wrong-bridge)
                    (як-є (absent absent)))))
           (за-умовою
             ((однакові?
                (список ready dedup-ok quiescence-ok adversarial-ok)
                (як-є (ready (1) (1) (1))))
              (список
                (як-є life-1-scheduler-witness)
                (список (як-є status) (як-є pass))
                (список (як-є detail)
                      (як-є deduplicated-activation-and-quiescence))))
             (так
              (список
                (як-є life-1-scheduler-witness)
                (список (як-є status) (як-є fail))
                (список (як-є detail) (як-є scheduler-invariant-mismatch)))))))))))

(life-1-scheduler-witness)
