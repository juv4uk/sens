; #801 — minimal LIFE-1 orchestration scheduler.
;
; Scheduler state is ordinary Lisp data. It controls activation timing only:
; it does not interpret Prolog, Datalog, CLIPS or Common Lisp semantics.
;
; Pending invocation shape:
;   (pending-invocation
;     (producer datalog)
;     (trigger (projection-ready prolog-substitutions-to-datalog-facts))
;     (provenance-ref observation-42)
;     (priority ordinary)
;     (semantic-id 00001100))
;
; Projection availability shape:
;   (projection-ready
;     prolog-substitutions-to-datalog-facts
;     observation-42)
;
; Quiescence is liveness/control data, never truth.

(00001001 life-scheduler-field
  (00001000 (entry field)
    (00000111
      ((00000010 entry)
       (00000001 ()))
      ((00000010 (00000001 ()))
       (10011100 ((rows (00000110 entry)))
         (00000111
           ((00000010 rows)
            (00000001 ()))
           ((00000010 (00000001 ()))
            (10011100 ((row (00000101 rows)))
              (00000111
                ((00000010 row)
                 (life-scheduler-field
                   (00000100 (00000101 entry) (00000110 rows))
                   field))
                ((00000010 (00000001 ()))
                 (00000111
                   ((00100010 field (00000101 row))
                    (00000101 (00000110 row)))
                   ((00000010 (00000001 ()))
                    (life-scheduler-field
                      (00000100 (00000101 entry) (00000110 rows))
                      field)))))))))))))
(00001001 life-scheduler-invocation-key
  (00001000 (invocation)
    (00100111
      (life-scheduler-field invocation (00000001 producer))
      (life-scheduler-field invocation (00000001 trigger))
      (life-scheduler-field invocation (00000001 provenance-ref))
      (life-scheduler-field invocation (00000001 semantic-id)))))

(00001001 life-scheduler-key-present?
  (00001000 (key keys)
    (00000111
      ((00000010 keys)
       (00000001 absent))
      ((00000010 (00000001 ()))
       (00000111
         ((00100010 key (00000101 keys))
          (00000001 present))
         ((00000010 (00000001 ()))
          (life-scheduler-key-present? key (00000110 keys))))))))
(00001001 life-scheduler-dedup-pending
  (00001000 (pending seen-keys)
    (00000111
      ((00000010 pending)
       (00000001 ()))
      ((00000010 (00000001 ()))
       (10011101 ((invocation (00000101 pending))
              (key (life-scheduler-invocation-key invocation)))
         (00000111
           ((00000011 (life-scheduler-key-present? key seen-keys) (00000001 present))
            (life-scheduler-dedup-pending (00000110 pending) seen-keys))
           ((00000011 (life-scheduler-key-present? key seen-keys) (00000001 absent))
            (00000100 invocation
                  (life-scheduler-dedup-pending
                    (00000110 pending)
                    (00000100 key seen-keys))))))))))
(00001001 life-scheduler-pending
  (00001000 (pending)
    (life-scheduler-dedup-pending pending (00000001 ()))))

(00001001 life-scheduler-projection-match?
  (00001000 (expected projections)
    (00000111
      ((00000010 projections)
       (00000001 absent))
      ((00000010 (00000001 ()))
       (10011100 ((projection (00000101 projections)))
         (00000111
           ((00100010 expected projection)
            (00000001 present))
           ((00000010 (00000001 ()))
            (life-scheduler-projection-match? expected (00000110 projections)))))))))
(00001001 life-scheduler-projection-ready?
  (00001000 (invocation projections)
    (10011101 ((trigger (life-scheduler-field invocation (00000001 trigger)))
           (provenance-ref-value (life-scheduler-field invocation (00000001 provenance-ref))))
      (00000111
        ((00000010 trigger)
         (00000001 absent))
        ((00000010 (00000001 ()))
         (10011100 ((tail (00000110 trigger)))
           (00000111
             ((00000010 tail)
              (00000001 absent))
             ((00000010 (00000001 ()))
              (life-scheduler-projection-match?
                (00100111
                  (00000001 projection-ready)
                  (00000101 tail)
                  provenance-ref-value)
                projections)))))))))
(00001001 life-scheduler-select-ready
  (00001000 (pending projections)
    (00000111
      ((00000010 pending)
       (00000001 (scheduler-selection none)))
      ((00000010 (00000001 ()))
       (10011100 ((invocation (00000101 pending)))
         (00000111
           ((00000011 (life-scheduler-projection-ready? invocation projections)
                (00000001 present))
            (00100111
              (00000001 scheduler-selection)
              (00000001 ready)
              invocation
              (00000110 pending)))
           ((00000011 (life-scheduler-projection-ready? invocation projections)
                (00000001 absent))
            (life-scheduler-select-ready (00000110 pending) projections))))))))
(00001001 life-scheduler-quiescence-state
  (00001000 (projections lifecycle-state)
    (00000111
      ((00000010 projections)
       (00000111
         ((00000011 projections (00000001 ()))
          (00000111
            ((00000011 lifecycle-state (00000001 no-transition-required))
             (00000001 (quiescence-state quiescent)))
            ((00000010 (00000001 ()))
             (00000001 (quiescence-state active)))))
         ((00000010 (00000001 ()))
          (00000001 (quiescence-state active)))))
      ((00000010 (00000001 ()))
       (00000001 (quiescence-state active))))))
(00001001 life-scheduler-quiescence
  (00001000 (pending projections lifecycle-state)
    (00000111
      ((00000010 pending)
       (00000111
         ((00000011 pending (00000001 ()))
          (life-scheduler-quiescence-state projections lifecycle-state))
         ((00000010 (00000001 ()))
          (00000001 (quiescence-state active)))))
      ((00000010 (00000001 ()))
       (00000001 (quiescence-state active))))))
(00001001 life-scheduler-state
  (00001000 (pending projections lifecycle-state)
    (00100111
      (00000001 scheduler-state)
      (00100111 (00000001 pending) (life-scheduler-pending pending))
      (00100111 (00000001 projections) projections)
      (00100111 (00000001 lifecycle) lifecycle-state)
      (life-scheduler-quiescence
        (life-scheduler-pending pending)
        projections
        lifecycle-state))))
