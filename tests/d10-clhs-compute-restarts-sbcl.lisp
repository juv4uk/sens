;;;; Independent executable witness for ANSI CLHS §9.2 COMPUTE-RESTARTS.
;;;; Run with: sbcl --noinform --script tests/d10-clhs-compute-restarts-sbcl.lisp
;;;; No SENS runtime, D2 control mutation, restart invocation, or T5 artifact.

(defun d10-check (truth label)
  (unless truth (error "CLHS COMPUTE-RESTARTS witness failed: ~A" label)))
(defun d10-check-equal (expected actual label)
  (unless (equal expected actual)
    (error "CLHS COMPUTE-RESTARTS witness failed: ~A; expected ~S, got ~S"
           label expected actual)))
(defun d10-new-restarts (all baseline)
  (remove-if (lambda (restart) (member restart baseline :test #'eq)) all))
(defun d10-count-name (name restarts)
  (count name restarts :key #'restart-name :test #'eq))

(define-condition d10-test-condition (condition) ())

;; Witness A: nested dynamic scopes are returned innermost-first.
(let ((baseline (compute-restarts))
      (invoked nil))
  (restart-bind ((d10-outer (lambda () (setf invoked t) :outer)))
    (restart-bind ((d10-inner (lambda () (setf invoked t) :inner)))
      (let* ((all (compute-restarts))
             (added (d10-new-restarts all baseline)))
        (d10-check-equal 2 (length added) "two nested restarts are visible")
        (d10-check-equal '(d10-inner d10-outer)
                         (mapcar #'restart-name added)
                         "innermost restart precedes outer restart")
        (d10-check (not invoked) "enumeration must not invoke a restart")))))

;; Witness B: nested shadowed names still denote distinct restart objects.
;; ANSI orders the nested contour before the outer one, but does not impose a
;; relative order among multiple restart definitions in the same RESTART-BIND.
(let ((baseline (compute-restarts))
      (invoked nil)
      (outer nil))
  (restart-bind ((d10-duplicate (lambda () (setf invoked t) :outer)))
    (setf outer (find-restart 'd10-duplicate))
    (restart-bind ((d10-duplicate (lambda () (setf invoked t) :inner))
                   (nil (lambda () (setf invoked t) :anonymous)))
      (let* ((all (compute-restarts))
             (added (d10-new-restarts all baseline))
             (duplicates (remove-if-not
                          (lambda (restart) (eq (restart-name restart) 'd10-duplicate))
                          added))
             (nearest (find-restart 'd10-duplicate)))
        (d10-check-equal 3 (length added) "all three new restart objects are visible")
        (d10-check-equal 2 (length duplicates) "duplicate names do not collapse")
        (d10-check (not (eq (first duplicates) (second duplicates)))
                   "same-name entries have distinct restart identities")
        (d10-check (eq (first duplicates) nearest)
                   "FIND-RESTART returns the nearest same-name restart")
        (d10-check (eq (second duplicates) outer)
                   "COMPUTE-RESTARTS retains the outer shadowed restart")
        (d10-check-equal 1 (d10-count-name nil added) "anonymous restart is retained")
        (d10-check (not invoked) "listing must not invoke a restart")))))

;; Witness C: condition association filters only restarts bound to another condition;
;; unassociated restarts remain visible to both condition queries.
(let ((condition-a (make-condition 'd10-test-condition))
      (condition-b (make-condition 'd10-test-condition))
      (invoked nil))
  (restart-bind ((d10-associated-a (lambda () (setf invoked t) :a))
                 (d10-unassociated (lambda () (setf invoked t) :global)))
    (let ((r-a (find-restart 'd10-associated-a))
          (r-global (find-restart 'd10-unassociated)))
      (d10-check r-a "associated restart exists")
      (d10-check r-global "unassociated restart exists")
      (with-condition-restarts condition-a (list r-a)
        (let ((for-a (compute-restarts condition-a))
              (for-b (compute-restarts condition-b)))
          (d10-check (member r-a for-a :test #'eq)
                     "a restart is visible for its associated condition")
          (d10-check (not (member r-a for-b :test #'eq))
                     "a restart associated only with another condition is excluded")
          (d10-check (member r-global for-a :test #'eq)
                     "unassociated restart remains visible for condition A")
          (d10-check (member r-global for-b :test #'eq)
                     "unassociated restart remains visible for condition B"))))
    (d10-check (not invoked) "condition-filtered enumeration must not invoke a restart")))

(format t "D10-CLHS-COMPUTE-RESTARTS: PASS (order, duplicate names, anonymous restart, condition filter, observation-only)~%")
