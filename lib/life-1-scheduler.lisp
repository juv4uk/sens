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
  (функція (ліве праве)
    (за-умовою
      ((атом? ліве)
       (за-умовою
         ((атом? праве) (тотожне? ліве праве))
         (#d1:1 #d1:0)))
      ((010 праве) #d1:0)
      ((життя--рівні? (перше ліве) (перше праве))
       (життя--рівні? (решта ліве) (решта праве)))
      (#d1:1 #d1:0))))

(0011 life-scheduler-field
  (функція (entry field)
    (за-умовою
      
      ((хибне? (атом? entry))
       ((функція (rows)
         (за-умовою
           
           ((хибне? (атом? rows))
            ((функція (row)
         (за-умовою
                
                ((атом? row) 
                 (life-scheduler-field
                   (сполучити (перше entry) (решта rows))
                   field))
                ((хибне? (атом? row))
                 (за-умовою
                   ((життя--рівні? field (перше row)) 
                    (перше (решта row)))
                   ((хибне? (життя--рівні? field (перше row)))
                    (life-scheduler-field
                      (сполучити (перше entry) (решта rows))
                      field))))))
         (перше rows)))))
         (решта entry))))))

(0011 life-scheduler-invocation-key
  (функція (invocation)
    (список
      (life-scheduler-field invocation (як-є producer))
      (life-scheduler-field invocation (як-є trigger))
      (life-scheduler-field invocation (як-є provenance-ref))
      (life-scheduler-field invocation (як-є semantic-id)))))

(0011 life-scheduler-key-present?
  (функція (key keys)
    (за-умовою
      ((атом? keys) (як-є absent))
      ((хибне? (атом? keys))
       (за-умовою
         ((життя--рівні? key (перше keys))  (як-є present))
         ((хибне? (життя--рівні? key (перше keys)))
          (life-scheduler-key-present? key (решта keys))))))))

(0011 life-scheduler-dedup-pending
  (функція (pending seen-keys)
    (за-умовою
      
      ((хибне? (атом? pending))
       (001001 ((invocation (100 pending))
              (key (life-scheduler-invocation-key invocation)))
         (за-умовою
           ((тотожне? (life-scheduler-key-present? key seen-keys) (як-є present))
            
            (life-scheduler-dedup-pending (решта pending) seen-keys))
           ((тотожне? (life-scheduler-key-present? key seen-keys) (як-є absent))
            
            (сполучити invocation
                  (life-scheduler-dedup-pending
                    (решта pending)
                    (сполучити key seen-keys))))))))))

(0011 life-scheduler-pending
  (функція (pending)
    (life-scheduler-dedup-pending pending (як-є ()))))

(0011 life-scheduler-projection-match?
  (функція (expected projections)
    (за-умовою
      ((атом? projections) (як-є absent))
      ((хибне? (атом? projections))
       ((функція (projection)
         (за-умовою
           ((життя--рівні? expected projection)
            
            (як-є present))
           ((хибне? (життя--рівні? expected projection))
            (life-scheduler-projection-match? expected (решта projections)))))
        (перше projections))))))

(0011 life-scheduler-projection-ready?
  (функція (invocation projections)
    (001001 ((trigger (life-scheduler-field invocation (001 trigger)))
           (provenance-ref-value (life-scheduler-field invocation (як-є provenance-ref))))
      (за-умовою
        
        ((атом? trigger) 
         (як-є absent))
        ((хибне? (атом? trigger))
         ((функція (tail)
           (за-умовою
             
             ((атом? tail) 
              (як-є absent))
             ((хибне? (атом? tail))
              (life-scheduler-projection-match?
                (список
                  (як-є projection-ready)
                  (перше tail)
                  provenance-ref-value)
                projections))))
          (решта trigger)))))))

(0011 life-scheduler-select-ready
  (функція (pending projections)
    (за-умовою
      ((атом? pending)
       (як-є (scheduler-selection none)))
      ((хибне? (атом? pending))
       ((функція (invocation)
         (за-умовою
           ((тотожне? (life-scheduler-projection-ready? invocation projections)
                (як-є present))
            
            (список
              (як-є scheduler-selection)
              (як-є ready)
              invocation
              (решта pending)))
           ((тотожне? (life-scheduler-projection-ready? invocation projections)
                (як-є absent))
            
            (life-scheduler-select-ready (решта pending) projections))))
        (перше pending))))))

(0011 life-scheduler-quiescence-state
  (функція (projections lifecycle-state)
    (за-умовою
      ((атом? projections)
       (за-умовою
         ((тотожне? lifecycle-state (як-є no-transition-required))
          
          (як-є (quiescence-state quiescent)))
         ((хибне? (тотожне? lifecycle-state (як-є no-transition-required)))
          (як-є (quiescence-state active)))))
      ((хибне? (атом? projections))
       (як-є (quiescence-state active))))))

(0011 life-scheduler-quiescence
  (функція (pending projections lifecycle-state)
    (за-умовою
      ((атом? pending)
       (life-scheduler-quiescence-state projections lifecycle-state))
      ((хибне? (атом? pending))
       (як-є (quiescence-state active))))))
(0011 life-scheduler-state
  (функція (pending projections lifecycle-state)
    (список
      (як-є scheduler-state)
      (список (як-є pending) (life-scheduler-pending pending))
      (список (як-є projections) projections)
      (список (як-є lifecycle) lifecycle-state)
      (life-scheduler-quiescence
        (life-scheduler-pending pending)
        projections
        lifecycle-state))))
