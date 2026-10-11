;;;; D10 historical LOOPS: constructive derivability CHALLENGE in ANSI Common Lisp.
;;;; This is NOT a Xerox LOOPS interpreter, nor an independent historical oracle.
;;;; Only CONS/EQ, lexical closures, a mutable captured cell, and FUNCALL are used.
;;;; Historical reference: Bobrow & Stefik (1983), The LOOPS Manual, 5.1–5.5.
(defpackage :loops-access-challenge (:use :cl))
(in-package :loops-access-challenge)

(defvar *checks* 0)
(defun check (label expected actual)
  (unless (equal expected actual)
    (error "~A: expected ~S, got ~S" label expected actual))
  (incf *checks*))

(defun make-cell (initial)
  (let ((contents initial))
    (lambda (operation &optional value)
      (ecase operation
        (:read contents)
        (:write (setf contents value))))))

(defun active-p (value)
  (and (consp value)
       (eq (car value) :active)
       (functionp (cdr value))))

(defun read-active (value)
  (if (active-p value)
      (funcall (cdr value) :read)
      value))

(defun write-active (node value)
  (unless (active-p node)
    (error "Not an active-value descriptor: ~S" node))
  (funcall (cdr node) :write value))

(defun raw-local (node)
  (funcall (cdr node) :raw-get))

(defun raw-write (node value)
  (funcall (cdr node) :raw-put value))

(defun make-active (initial &key getter setter)
  (let ((cell (make-cell initial)))
    (labels ((get-local ()
               (funcall cell :read))
             (put-only (value)
               (funcall cell :write value))
             (put-local (value)
               (let ((nested (get-local)))
                 (if (active-p nested)
                     (write-active nested value)
                     (put-only value))))
             (read-value ()
               (let ((value (read-active (get-local))))
                 (if getter (funcall getter value) value)))
             (write-value (value)
               (if setter
                   (funcall setter value #'put-local)
                   (put-only value))
               value))
      (cons :active
            (lambda (operation &optional value)
              (ecase operation
                (:read (read-value))
                (:write (write-value value))
                (:raw-get (get-local))
                (:raw-put (put-only value))))))))

(defun run-checks ()
  ;; This implementation uses a tagged CONS containing a closure and an
  ;; encapsulated ordinary lexical cell: no new evaluator special form.
  (let ((events '()))
    (let* ((inner
             (make-active 10
               :getter (lambda (x) (push :inner-get events) (+ x 2))
               :setter (lambda (x next)
                         (push :inner-put events)
                         (funcall next x))))
           (outer
             (make-active inner
               :getter (lambda (x) (push :outer-get events) (* x 3))
               :setter (lambda (x next)
                         (push :outer-put events)
                         (funcall next x)))))
      (check "nested read result" 36 (read-active outer))
      (check "nested GET inner-to-outer" '(:inner-get :outer-get)
             (reverse events))
      (setf events '())
      (check "write returns new value" 19 (write-active outer 19))
      (check "nested PUT outer-to-inner" '(:outer-put :inner-put)
             (reverse events))
      (check "inner updated through alias" 19 (raw-local inner))
      (setf events '())
      (check "raw GET returns immediate inner active object"
             t (eq (raw-local outer) inner))
      (check "raw access did not run handlers" nil events)
      (check "raw PUT immediate" 27 (raw-write outer 27))
      (check "raw PUT kept old aliased inner" 19 (raw-local inner))
      (check "raw PUT leaves plain value" 27 (raw-local outer))
      (check "raw PUT leaves log empty" nil events)))

  (let ((events '()))
    (let* ((inner
             (make-active 10
               :setter (lambda (x next)
                         (push :inner-put events)
                         (funcall next x))))
           (outer
             (make-active inner
               :setter (lambda (x next)
                         (declare (ignore x next))
                         (push :outer-put events)))))
      (write-active outer 99)
      (check "no delegation no inner PUT" '(:outer-put) (reverse events))
      (check "no delegation preserves nested storage" 10 (raw-local inner))))

  (let ((plain (make-active 4)))
    (check "empty getter is transparent" 4 (read-active plain))
    (check "empty setter is direct store" 7 (write-active plain 7))
    (check "updated local" 7 (raw-local plain)))

  (let ((plain (make-active 13))
        (function-as-value (lambda (x) (+ x 1))))
    (check "unrelated cell unchanged" 13 (read-active plain))
    (check "ordinary function value not mis-tagged as active"
           t (eq function-as-value (read-active function-as-value))))

  (format t "D10 LOOPS SBCL closure-derivability: PASS ~D checks~%" *checks*)
  (values))

(handler-case (run-checks)
  (error (condition)
    (format *error-output* "D10 LOOPS SBCL closure-derivability: FAIL ~A~%"
            condition)
    (sb-ext:exit :code 1)))
