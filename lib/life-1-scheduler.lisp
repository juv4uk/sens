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
;     (semantic-id 01010))
;
; Projection availability shape:
;   (projection-ready
;     prolog-substitutions-to-datalog-facts
;     observation-42)
;
; Quiescence is liveness/control data, never truth.

(0011 life-scheduler-field
  (0010 (entry field)
    (011
      ((010 entry) () (001 ()))
      ((010 entry) (0)
       (001000 ((rows (110 entry)))
         (011
           ((010 rows) () (001 ()))
           ((010 rows) (0)
            (001000 ((row (101 rows)))
              (011
                ((010 row) ()
                 (life-scheduler-field
                   (100 (101 entry) (110 rows))
                   field))
                ((010 row) (1)
                 (life-scheduler-field
                   (100 (101 entry) (110 rows))
                   field))
                ((010 row) (0)
                 (011
                   ((equal? field (101 row)) (1)
                    (101 (110 row)))
                   ((equal? field (101 row)) (0)
                    (life-scheduler-field
                      (100 (101 entry) (110 rows))
                      field)))))))))))))

(0011 life-scheduler-invocation-key
  (0010 (invocation)
    (1000
      (life-scheduler-field invocation (001 producer))
      (life-scheduler-field invocation (001 trigger))
      (life-scheduler-field invocation (001 provenance-ref))
      (life-scheduler-field invocation (001 semantic-id)))))

(0011 life-scheduler-key-present?
  (0010 (key keys)
    (011
      ((010 keys) () (001 absent))
      ((010 keys) (0)
       (011
         ((equal? key (101 keys)) (1) (001 present))
         ((equal? key (101 keys)) (0)
          (life-scheduler-key-present? key (110 keys))))))))

(0011 life-scheduler-dedup-pending
  (0010 (pending seen-keys)
    (011
      ((010 pending) () (001 ()))
      ((010 pending) (0)
       (001001 ((invocation (101 pending))
              (key (life-scheduler-invocation-key invocation)))
         (011
           ((111 (life-scheduler-key-present? key seen-keys) (001 present))
            (1)
            (life-scheduler-dedup-pending (110 pending) seen-keys))
           ((111 (life-scheduler-key-present? key seen-keys) (001 absent))
            (1)
            (100 invocation
                  (life-scheduler-dedup-pending
                    (110 pending)
                    (100 key seen-keys))))))))))

(0011 life-scheduler-pending
  (0010 (pending)
    (life-scheduler-dedup-pending pending (001 ()))))

(0011 life-scheduler-projection-match?
  (0010 (expected projections)
    (011
      ((010 projections) () (001 absent))
      ((010 projections) (0)
       (001000 ((projection (101 projections)))
         (011
           ((equal? expected projection)
            (1)
            (001 present))
           ((equal? expected projection)
            (0)
            (life-scheduler-projection-match? expected (110 projections)))))))))

(0011 life-scheduler-projection-ready?
  (0010 (invocation projections)
    (001001 ((trigger (life-scheduler-field invocation (001 trigger)))
           (provenance-ref-value (life-scheduler-field invocation (001 provenance-ref))))
      (011
        ((010 trigger) ()
         (001 absent))
        ((010 trigger) (1)
         (001 absent))
        ((010 trigger) (0)
         (001000 ((tail (110 trigger)))
           (011
             ((010 tail) ()
              (001 absent))
             ((010 tail) (1)
              (001 absent))
             ((010 tail) (0)
              (life-scheduler-projection-match?
                (1000
                  (001 projection-ready)
                  (101 tail)
                  provenance-ref-value)
                projections)))))))))

(0011 life-scheduler-select-ready
  (0010 (pending projections)
    (011
      ((010 pending) ()
       (001 (scheduler-selection none)))
      ((010 pending) (0)
       (001000 ((invocation (101 pending)))
         (011
           ((111 (life-scheduler-projection-ready? invocation projections)
                (001 present))
            (1)
            (1000
              (001 scheduler-selection)
              (001 ready)
              invocation
              (110 pending)))
           ((111 (life-scheduler-projection-ready? invocation projections)
                (001 absent))
            (1)
            (life-scheduler-select-ready (110 pending) projections))))))))

(0011 life-scheduler-quiescence-state
  (0010 (projections lifecycle-state)
    (011
      ((010 projections) ()
       (011
         ((111 lifecycle-state (001 no-transition-required))
          (1)
          (001 (quiescence-state quiescent)))
         ((111 lifecycle-state (001 no-transition-required))
          (0)
          (001 (quiescence-state active)))))
      ((010 projections) (0)
       (001 (quiescence-state active))))))

(0011 life-scheduler-quiescence
  (0010 (pending projections lifecycle-state)
    (011
      ((010 pending) ()
       (life-scheduler-quiescence-state projections lifecycle-state))
      ((010 pending) (0)
       (001 (quiescence-state active))))))
(0011 life-scheduler-state
  (0010 (pending projections lifecycle-state)
    (1000
      (001 scheduler-state)
      (1000 (001 pending) (life-scheduler-pending pending))
      (1000 (001 projections) projections)
      (1000 (001 lifecycle) lifecycle-state)
      (life-scheduler-quiescence
        (life-scheduler-pending pending)
        projections
        lifecycle-state))))
