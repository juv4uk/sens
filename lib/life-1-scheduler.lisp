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

; Точне структурне порівняння для ключів рою: жодного історичного W8
; і жодного ототожнення W8:11110111 з D8:11110111.
; D3 ATOM/ EQ/ CAR/ CDR/ COND; відповідь — виключно D1:1 або D1:0.
; Порівняння атомів перед викликом D3 EQ, пар — рекурсивно.
(0011 життя--рівні?
  (0010 (ліве праве)
    (110
      ((010 ліве)
       (110
         ((010 праве) (101 ліве праве))
         ((010 (001 ())) (001 ()))))
      ((010 праве) (001 ()))
      ((життя--рівні? (100 ліве) (100 праве))
       (життя--рівні? (011 ліве) (011 праве)))
      ((010 (001 ())) (001 ())))))

(0011 life-scheduler-field
  (0010 (entry field)
    (110
      
      ((0100 (010 entry))
       (001000 ((rows (011 entry)))
         (110
           
           ((0100 (010 rows))
            (001000 ((row (100 rows)))
              (110
                
                ((010 row) 
                 (life-scheduler-field
                   (111 (100 entry) (011 rows))
                   field))
                ((0100 (010 row))
                 (110
                   ((життя--рівні? field (100 row)) 
                    (100 (011 row)))
                   ((0100 (життя--рівні? field (100 row)))
                    (life-scheduler-field
                      (111 (100 entry) (011 rows))
                      field)))))))))))))

(0011 life-scheduler-invocation-key
  (0010 (invocation)
    (1110
      (life-scheduler-field invocation (001 producer))
      (life-scheduler-field invocation (001 trigger))
      (life-scheduler-field invocation (001 provenance-ref))
      (life-scheduler-field invocation (001 semantic-id)))))

(0011 life-scheduler-key-present?
  (0010 (key keys)
    (110
      ((0100 (010 keys)) (001 absent))
      ((0100 (010 keys))
       (110
         ((життя--рівні? key (100 keys))  (001 present))
         ((0100 (життя--рівні? key (100 keys)))
          (life-scheduler-key-present? key (011 keys))))))))

(0011 life-scheduler-dedup-pending
  (0010 (pending seen-keys)
    (110
      
      ((0100 (010 pending))
       (001001 ((invocation (100 pending))
              (key (life-scheduler-invocation-key invocation)))
         (110
           ((101 (life-scheduler-key-present? key seen-keys) (001 present))
            
            (life-scheduler-dedup-pending (011 pending) seen-keys))
           ((101 (life-scheduler-key-present? key seen-keys) (001 absent))
            
            (111 invocation
                  (life-scheduler-dedup-pending
                    (011 pending)
                    (111 key seen-keys))))))))))

(0011 life-scheduler-pending
  (0010 (pending)
    (life-scheduler-dedup-pending pending (001 ()))))

(0011 life-scheduler-projection-match?
  (0010 (expected projections)
    (110
      ((0100 (010 projections)) (001 absent))
      ((0100 (010 projections))
       (001000 ((projection (100 projections)))
         (110
           ((життя--рівні? expected projection)
            
            (001 present))
           ((0100 (життя--рівні? expected projection))
            (life-scheduler-projection-match? expected (011 projections)))))))))

(0011 life-scheduler-projection-ready?
  (0010 (invocation projections)
    (001001 ((trigger (life-scheduler-field invocation (001 trigger)))
           (provenance-ref-value (life-scheduler-field invocation (001 provenance-ref))))
      (110
        
        ((010 trigger) 
         (001 absent))
        ((0100 (010 trigger))
         (001000 ((tail (011 trigger)))
           (110
             
             ((010 tail) 
              (001 absent))
             ((0100 (010 tail))
              (life-scheduler-projection-match?
                (1110
                  (001 projection-ready)
                  (100 tail)
                  provenance-ref-value)
                projections)))))))))

(0011 life-scheduler-select-ready
  (0010 (pending projections)
    (110
      ((0100 (010 pending))
       (001 (scheduler-selection none)))
      ((0100 (010 pending))
       (001000 ((invocation (100 pending)))
         (110
           ((101 (life-scheduler-projection-ready? invocation projections)
                (001 present))
            
            (1110
              (001 scheduler-selection)
              (001 ready)
              invocation
              (011 pending)))
           ((101 (life-scheduler-projection-ready? invocation projections)
                (001 absent))
            
            (life-scheduler-select-ready (011 pending) projections))))))))

(0011 life-scheduler-quiescence-state
  (0010 (projections lifecycle-state)
    (110
      ((0100 (010 projections))
       (110
         ((101 lifecycle-state (001 no-transition-required))
          
          (001 (quiescence-state quiescent)))
         ((0100 (101 lifecycle-state (001 no-transition-required)))
          (001 (quiescence-state active)))))
      ((0100 (010 projections))
       (001 (quiescence-state active))))))

(0011 life-scheduler-quiescence
  (0010 (pending projections lifecycle-state)
    (110
      ((0100 (010 pending))
       (life-scheduler-quiescence-state projections lifecycle-state))
      ((0100 (010 pending))
       (001 (quiescence-state active))))))
(0011 life-scheduler-state
  (0010 (pending projections lifecycle-state)
    (1110
      (001 scheduler-state)
      (1110 (001 pending) (life-scheduler-pending pending))
      (1110 (001 projections) projections)
      (1110 (001 lifecycle) lifecycle-state)
      (life-scheduler-quiescence
        (life-scheduler-pending pending)
        projections
        lifecycle-state))))
