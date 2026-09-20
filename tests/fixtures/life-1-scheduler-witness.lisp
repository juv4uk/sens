; #801 — Lisp-owned scheduler witness.
;
; The witness models the first LIFE-1 activation path only as ordinary data:
; a Prolog projection becoming ready activates a Datalog pending invocation.
; No kernel is called here; invocation routing remains a later mechanism step.

(load "lib/core.lisp")
(load "lib/life-1-scheduler.lisp")

(def life-1-scheduler-witness
  (lambda ()
    (let* ((first
             (quote
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-42)
                 (priority ordinary)
                 (semantic-id "00001100"))))
           (first-duplicate
             (quote
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-42)
                 (priority ordinary)
                 (semantic-id "00001100"))))
           (second
             (quote
               (pending-invocation
                 (producer datalog)
                 (trigger (projection-ready prolog-substitutions-to-datalog-facts))
                 (provenance-ref observation-99)
                 (priority ordinary)
                 (semantic-id "00001100"))))
           (pending
             (life-scheduler-pending
               (list first first-duplicate second)))
           (projections
             (quote
               ((projection-ready
                  prolog-substitutions-to-datalog-facts
                  observation-42)
                (projection-ready
                  prolog-substitutions-to-datalog-facts
                  observation-99))))
           (selection
             (life-scheduler-select-ready pending projections)))
      (cond
        ((atom selection) (structural-kind empty-list)
         (list (quote life-1-scheduler-witness)
               (list (quote status) (quote fail))
               (list (quote detail) (quote missing-selection))))
        ((atom selection) (structural-kind pair)
         (cond
           ((eq (car (cdr selection)) (quote ready))
            (identity-relation same)
            (let ((remaining (cdr (cdr (cdr selection)))))
              (cond
                ((equal? remaining (list second))
                 (structural-relation same)
                 (cond
                   ((equal?
                      (life-scheduler-quiescence
                        (quote ())
                        (quote ())
                        (quote no-transition-required))
                      (quote (quiescence-state quiescent)))
                    (structural-relation same)
                    (list
                      (quote life-1-scheduler-witness)
                      (list (quote status) (quote pass))
                      (list (quote detail)
                            (quote deduplicated-activation-and-quiescence))))
                   ((equal?
                      (life-scheduler-quiescence
                        (quote ())
                        (quote ())
                        (quote no-transition-required))
                      (quote (quiescence-state quiescent)))
                    (structural-relation distinct)
                    (list
                      (quote life-1-scheduler-witness)
                      (list (quote status) (quote fail))
                      (list (quote detail) (quote quiescence-mismatch)))))
                ((equal? remaining (list second))
                 (structural-relation distinct)
                 (list
                   (quote life-1-scheduler-witness)
                   (list (quote status) (quote fail))
                   (list (quote detail) (quote deduplication-mismatch))))))
           ((eq (car (cdr selection)) (quote ready))
            (identity-relation distinct)
            (list
              (quote life-1-scheduler-witness)
              (list (quote status) (quote fail))
              (list (quote detail) (quote readiness-mismatch))))))))

(life-1-scheduler-witness)
