; #790 executable bounded witness.
; The scheduler coordinates references only. It never interprets producer payloads.

(def blackboard-key-seen?
  (lambda (key keys)
    (cond
      ((atom keys) (structural-kind empty-list) (quote no))
      ((atom keys) (structural-kind pair)
       (cond
         ((equal? key (car keys)) (structural-relation same) (quote yes))
         ((equal? key (car keys)) (structural-relation distinct)
          (blackboard-key-seen? key (cdr keys))))))))

(def blackboard-enqueue
  (lambda (activation seen queue)
    (let ((key (second activation)))
      (cond
        ((eq (blackboard-key-seen? key seen) (quote yes))
         (identity-relation same)
         (list seen queue))
        ((eq (blackboard-key-seen? key seen) (quote no))
         (identity-relation same)
         (list
           (cons key seen)
           (append queue (list activation))))))))

(def blackboard-run-790
  (lambda ()
    (let* (
      (a1
        (quote
          (activation
            (prolog p17 datalog)
            (observation-ref prolog p17)
            (consumer datalog)
            (provenance user-query q1))))
      (a1-repeat
        (quote
          (activation
            (prolog p17 datalog)
            (observation-ref prolog p17)
            (consumer datalog)
            (provenance user-query q1))))
      (a2
        (quote
          (activation
            (clips c9 lisp-observer)
            (observation-ref clips c9)
            (consumer lisp-observer)
            (provenance rule-fire r4))))
      (s1 (blackboard-enqueue a1 (quote ()) (quote ())))
      (s2 (blackboard-enqueue a1-repeat (car s1) (second s1)))
      (s3 (blackboard-enqueue a2 (car s2) (second s2)))
      (queue (second s3)))
      (cond
        ((equal? queue (list a1 a2))
         (structural-relation same)
         (quote
           (blackboard-790-witness
             (status pass)
             (coordination references-only)
             (duplicate-activation suppressed))))
        (t (car (quote ())))))))

(blackboard-run-790)
