;;;; Independent SBCL witness for ANSI CLHS §9.2 COMPUTE-RESTARTS.
;;;; Research-only: validates visible list shape/order; no SENS semantic admission.
;;;; (role research-only)
;;;; (semantic-authority-change none)
(defun assert-equal (expected actual label)
  (unless (equal expected actual)
    (error "~A: expected ~S, got ~S" label expected actual)))
(defun restart-names (restarts)
  (mapcar #'restart-name restarts))
(let ((observed nil))
  (restart-bind
      ((duplicate (lambda () :first)
         :report-function (lambda (s) (write-string "first duplicate" s)))
       (duplicate (lambda () :second)
         :report-function (lambda (s) (write-string "second duplicate" s)))
       (nil (lambda () :anonymous)
         :report-function (lambda (s) (write-string "anonymous" s))))
    (let* ((all (compute-restarts))
           (names (restart-names all)))
      ;; The three explicitly bound restarts are all discoverable; an
      ;; anonymous restart has name NIL and duplicate names are not collapsed.
      (assert-equal 3 (length all) "restart cardinality")
      (assert-equal 2 (count 'duplicate names) "duplicate names retained")
      (assert-equal 1 (count nil names) "anonymous restart retained")
      ;; ANSI requires most recently established restart nearest the head.
      (assert-equal '(nil duplicate duplicate) names "dynamic establishment order")
      (setf observed names)))
  (format t "CLHS-COMPUTE-RESTARTS-SBCL: PASS ~S~%" observed))
