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
      ((atom entry) (structural-kind empty-list) (quote ()))
      ((atom entry) (structural-kind pair)
       (let ((rows (cdr entry)))
         (cond
           ((atom rows) (structural-kind empty-list) (quote ()))
           ((atom rows) (structural-kind pair)
            (let ((row (car rows)))
              (cond
                ((atom row) (structural-kind empty-list)
                 (life-scheduler-field
                   (cons (car entry) (cdr rows))
                   field))
                ((atom row) (structural-kind atom)
                 (life-scheduler-field
                   (cons (car entry) (cdr rows))
                   field))
                ((atom row) (structural-kind pair)
                 (cond
                   ((equal? field (car row)) (structural-relation same)
                    (car (cdr row)))
                   ((equal? field (car row)) (structural-relation distinct)
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
      ((atom keys) (structural-kind empty-list) (quote absent))
      ((atom keys) (structural-kind pair)
       (cond
         ((equal? key (car keys)) (structural-relation same) (quote present))
         ((equal? key (car keys)) (structural-relation distinct)
          (life-scheduler-key-present? key (cdr keys))))))))

(def life-scheduler-dedup-pending
  (lambda (pending seen-keys)
    (cond
      ((atom pending) (structural-kind empty-list) (quote ()))
      ((atom pending) (structural-kind pair)
       (let* ((invocation (car pending))
              (key (life-scheduler-invocation-key invocation)))
         (cond
           ((life-scheduler-key-present? key seen-keys) (identity-relation same)
            (life-scheduler-dedup-pending (cdr pending) seen-keys))
           ((life-scheduler-key-present? key seen-keys) (identity-relation distinct)
            (cons invocation
                  (life-scheduler-dedup-pending
                    (cdr pending)
                    (cons key seen-keys))))))))))

(def life-scheduler-pending
  (lambda (pending)
    (life-scheduler-dedup-pending pending (quote ()))))

(def life-scheduler-projection-ready?
  (lambda (invocation projections)
    (let* ((trigger (life-scheduler-field invocation (quote trigger)))
           (provenance (life-scheduler-field invocation (quote provenance-ref)))
           (expected
             (list
               (quote projection-ready)
               (car (cdr trigger))
               provenance)))
      (cond
        ((atom projections) (structural-kind empty-list) (quote absent))
        ((atom projections) (structural-kind pair)
         (let ((projection (car projections)))
           (cond
             ((equal? expected projection)
              (quote (structural-relation same))
              (quote present))
             ((equal? expected projection)
              (quote (structural-relation distinct))
              (life-scheduler-projection-ready? invocation (cdr projections))))))))))

(def life-scheduler-select-ready
  (lambda (pending projections)
    (cond
      ((atom pending) (structural-kind empty-list)
       (quote (scheduler-selection none)))
      ((atom pending) (structural-kind pair)
       (let ((invocation (car pending)))
         (cond
           ((eq (life-scheduler-projection-ready? invocation projections)
                (quote present))
            (quote (identity-relation same))
            (list
              (quote scheduler-selection)
              (quote ready)
              invocation
              (cdr pending)))
           ((eq (life-scheduler-projection-ready? invocation projections)
                (quote absent))
            (quote (identity-relation distinct))
            (life-scheduler-select-ready (cdr pending) projections))))))))

(def life-scheduler-quiescence-state
  (lambda (projections lifecycle-state)
    (cond
      ((atom projections) (structural-kind empty-list)
       (cond
         ((eq lifecycle-state (quote no-transition-required))
          (quote (identity-relation same))
          (quote (quiescence-state quiescent)))
         ((eq lifecycle-state (quote no-transition-required))
          (quote (identity-relation distinct))
          (quote (quiescence-state active)))))
      ((atom projections) (structural-kind pair)
       (quote (quiescence-state active))))))

(def life-scheduler-quiescence
  (lambda (pending projections lifecycle-state)
    (cond
      ((atom pending) (structural-kind empty-list)
       (life-scheduler-quiescence-state projections lifecycle-state))
      ((atom pending) (structural-kind pair)
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
