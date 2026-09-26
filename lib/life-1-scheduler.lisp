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
;     (semantic-id "00001100"))
;
; Projection availability shape:
;   (projection-ready
;     prolog-substitutions-to-datalog-facts
;     observation-42)
;
; Quiescence is liveness/control data, never truth.

(def life-scheduler-field
  (lambda (entry field)
    (cond
      ((atom? entry) () (quote ()))
      ((atom? entry) (0)
       (let ((rows (cdr entry)))
         (cond
           ((atom? rows) () (quote ()))
           ((atom? rows) (0)
            (let ((row (car rows)))
              (cond
                ((atom? row) ()
                 (life-scheduler-field
                   (cons (car entry) (cdr rows))
                   field))
                ((atom? row) (1)
                 (life-scheduler-field
                   (cons (car entry) (cdr rows))
                   field))
                ((atom? row) (0)
                 (cond
                   ((equal? field (car row)) (1)
                    (car (cdr row)))
                   ((equal? field (car row)) (0)
                    (life-scheduler-field
                      (cons (car entry) (cdr rows))
                      field)))))))))))))

(def life-scheduler-invocation-key
  (lambda (invocation)
    (list
      (life-scheduler-field invocation (quote producer))
      (life-scheduler-field invocation (quote trigger))
      (life-scheduler-field invocation (quote provenance-ref))
      (life-scheduler-field invocation (quote semantic-id)))))

(def life-scheduler-key-present?
  (lambda (key keys)
    (cond
      ((atom? keys) () (quote absent))
      ((atom? keys) (0)
       (cond
         ((equal? key (car keys)) (1) (quote present))
         ((equal? key (car keys)) (0)
          (life-scheduler-key-present? key (cdr keys))))))))

(def life-scheduler-dedup-pending
  (lambda (pending seen-keys)
    (cond
      ((atom? pending) () (quote ()))
      ((atom? pending) (0)
       (let* ((invocation (car pending))
              (key (life-scheduler-invocation-key invocation)))
         (cond
           ((eq? (life-scheduler-key-present? key seen-keys) (quote present))
            (1)
            (life-scheduler-dedup-pending (cdr pending) seen-keys))
           ((eq? (life-scheduler-key-present? key seen-keys) (quote absent))
            (1)
            (cons invocation
                  (life-scheduler-dedup-pending
                    (cdr pending)
                    (cons key seen-keys))))))))))

(def life-scheduler-pending
  (lambda (pending)
    (life-scheduler-dedup-pending pending (quote ()))))

(def life-scheduler-projection-match?
  (lambda (expected projections)
    (cond
      ((atom? projections) () (quote absent))
      ((atom? projections) (0)
       (let ((projection (car projections)))
         (cond
           ((equal? expected projection)
            (1)
            (quote present))
           ((equal? expected projection)
            (0)
            (life-scheduler-projection-match? expected (cdr projections)))))))))

(def life-scheduler-projection-ready?
  (lambda (invocation projections)
    (let* ((trigger (life-scheduler-field invocation (quote trigger)))
           (provenance (life-scheduler-field invocation (quote provenance-ref))))
      (cond
        ((atom? trigger) ()
         (quote absent))
        ((atom? trigger) (1)
         (quote absent))
        ((atom? trigger) (0)
         (let ((tail (cdr trigger)))
           (cond
             ((atom? tail) ()
              (quote absent))
             ((atom? tail) (1)
              (quote absent))
             ((atom? tail) (0)
              (life-scheduler-projection-match?
                (list
                  (quote projection-ready)
                  (car tail)
                  provenance)
                projections)))))))))

(def life-scheduler-select-ready
  (lambda (pending projections)
    (cond
      ((atom? pending) ()
       (quote (scheduler-selection none)))
      ((atom? pending) (0)
       (let ((invocation (car pending)))
         (cond
           ((eq? (life-scheduler-projection-ready? invocation projections)
                (quote present))
            (1)
            (list
              (quote scheduler-selection)
              (quote ready)
              invocation
              (cdr pending)))
           ((eq? (life-scheduler-projection-ready? invocation projections)
                (quote absent))
            (1)
            (life-scheduler-select-ready (cdr pending) projections))))))))

(def life-scheduler-quiescence-state
  (lambda (projections lifecycle-state)
    (cond
      ((atom? projections) ()
       (cond
         ((eq? lifecycle-state (quote no-transition-required))
          (1)
          (quote (quiescence-state quiescent)))
         ((eq? lifecycle-state (quote no-transition-required))
          (0)
          (quote (quiescence-state active)))))
      ((atom? projections) (0)
       (quote (quiescence-state active))))))

(def life-scheduler-quiescence
  (lambda (pending projections lifecycle-state)
    (cond
      ((atom? pending) ()
       (life-scheduler-quiescence-state projections lifecycle-state))
      ((atom? pending) (0)
       (quote (quiescence-state active))))))
(def life-scheduler-state
  (lambda (pending projections lifecycle-state)
    (list
      (quote scheduler-state)
      (list (quote pending) (life-scheduler-pending pending))
      (list (quote projections) projections)
      (list (quote lifecycle) lifecycle-state)
      (life-scheduler-quiescence
        (life-scheduler-pending pending)
        projections
        lifecycle-state))))
