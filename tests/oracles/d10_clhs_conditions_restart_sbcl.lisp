;;;; (role research-only)
;;;; (semantic-authority-change none)
;;;; Live SBCL witness of ANSI CLHS §9.2 COMPUTE-RESTARTS.
;;;; This is donor-language observation, NOT native binary SENS execution.
(in-package #:cl-user)

(defun d10-clhs-check (ok label)
  (unless ok (error "CLHS-CONDITIONS-ORACLE FAIL ~A" label)))

(let ((outer nil) (inner nil) (anonymous nil))
  (restart-bind ((d10-same (lambda () :outer)))
    (setf outer (find-restart 'd10-same))
    (restart-bind ((d10-same (lambda () :inner))
                   (nil (lambda () :anonymous)))
      (let* ((all (compute-restarts))
             (named (remove-if-not
                     (lambda (r) (eq (restart-name r) 'd10-same))
                     all))
             (anon (remove-if-not
                    (lambda (r) (null (restart-name r)))
                    all)))
        (setf inner (find-restart 'd10-same)
              anonymous (find-if (lambda (r) (null (restart-name r))) all))
        (d10-clhs-check (= (length named) 2) "both same-name restarts retained")
        (d10-clhs-check (eq (first named) inner) "innermost duplicate first")
        (d10-clhs-check (eq (second named) outer) "outer duplicate follows")
        (d10-clhs-check (eq (first named) (find-restart 'd10-same)) "find-restart sees one nearest")
        (d10-clhs-check (not (null anon)) "anonymous restarts retained")
        (d10-clhs-check (member anonymous all :test #'eq) "anonymous restart identity")
        (d10-clhs-check
         (equal (mapcar #'restart-name (subseq named 0 2))
                '(d10-same d10-same))
         "shadowing must not deduplicate names")))))

(let ((condition-a (make-condition 'simple-condition
                                   :format-control "A"
                                   :format-arguments nil))
      (condition-b (make-condition 'simple-condition
                                   :format-control "B"
                                   :format-arguments nil)))
  (restart-bind ((d10-filtered (lambda () :filtered))
                 (d10-free (lambda () :free)))
    (let ((filtered (find-restart 'd10-filtered))
          (free (find-restart 'd10-free)))
      (with-condition-restarts condition-a (list filtered)
        (let ((for-a (compute-restarts condition-a))
              (for-b (compute-restarts condition-b))
              (for-any (compute-restarts)))
          (d10-clhs-check (member filtered for-a :test #'eq)
                          "associated restart appears for condition A")
          (d10-clhs-check (not (member filtered for-b :test #'eq))
                          "associated restart not visible for B")
          (d10-clhs-check (member filtered for-any :test #'eq)
                          "no-condition query includes all")
          (d10-clhs-check (member free for-a :test #'eq)
                          "unassociated restart remains for A")
          (d10-clhs-check (member free for-b :test #'eq)
                          "unassociated restart remains for B")
          (d10-clhs-check
           (= (length (remove-if-not
                       (lambda (r) (eq (restart-name r) 'd10-filtered))
                       for-any))
              1)
           "filtered restart not duplicated"))))))

(format t "D10-CLHS-CONDITIONS-SBCL: PASS nested, same-name, anonymous, condition-filtered restarts~%")
