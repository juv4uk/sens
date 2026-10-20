; #790 executable bounded witness.
; The scheduler coordinates references only. It never interprets producer payloads.

(визначити blackboard-key-seen?
  (функція (key keys)
    (за-умовою
      ((атом? keys) (structural-kind empty-list) (як-є no))
      ((атом? keys) (structural-kind pair)
       (за-умовою
         ((однакові? key (перше keys)) (structural-relation same) (як-є yes))
         ((однакові? key (перше keys)) (structural-relation distinct)
          (blackboard-key-seen? key (решта keys))))))))

(визначити blackboard-enqueue
  (функція (activation seen queue)
    (нехай ((key (друге activation)))
      (за-умовою
        ((тотожне? (blackboard-key-seen? key seen) (як-є yes))
         (identity-relation same)
         (список seen queue))
        ((тотожне? (blackboard-key-seen? key seen) (як-є no))
         (identity-relation same)
         (список
           (сполучити key seen)
           (приєднати queue (список activation))))))))

(визначити blackboard-run-790
  (функція ()
    (нехай-послідовно (
      (a1
        (як-є
          (activation
            (prolog p17 datalog)
            (observation-ref prolog p17)
            (consumer datalog)
            (provenance user-query q1))))
      (a1-repeat
        (як-є
          (activation
            (prolog p17 datalog)
            (observation-ref prolog p17)
            (consumer datalog)
            (provenance user-query q1))))
      (a2
        (як-є
          (activation
            (clips c9 lisp-observer)
            (observation-ref clips c9)
            (consumer lisp-observer)
            (provenance rule-fire r4))))
      (s1 (blackboard-enqueue a1 (як-є ()) (як-є ())))
      (s2 (blackboard-enqueue a1-repeat (перше s1) (друге s1)))
      (s3 (blackboard-enqueue a2 (перше s2) (друге s2)))
      (queue (друге s3)))
      (за-умовою
        ((однакові? queue (список a1 a2))
         (structural-relation same)
         (як-є
           (blackboard-790-witness
             (status pass)
             (coordination references-only)
             (duplicate-activation suppressed))))
        (так (перше (як-є ())))))))

(blackboard-run-790)
