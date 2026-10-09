;;;; D10 independent source oracle: finite cyclic bit word minima.
;;;; (role research-only)
;;;; (semantic-authority-change none)
;;;; Source: SageMath FiniteWord.minimal_conjugate and Booth (1980).
;;;; This is ordinary Common Lisp donor evidence, NOT SENS executable source.

(defpackage :d10-cyclic-bit-oracle (:use :cl))
(in-package :d10-cyclic-bit-oracle)

(defvar *checks* 0)
(defvar *orbit-cases* 0)
(defun assert-equal (caption actual expected)
  (unless (equal actual expected)
    (error "~A: expected ~S, received ~S" caption expected actual))
  (incf *checks*))

(defun bit-vector-source-p (xs)
  (and (listp xs) xs
       (every (lambda (x) (and (integerp x) (member x '(0 1) :test #'eql)))
              xs)))

(defun left-conjugate (bits shift)
  (let ((i (mod shift (length bits))))
    (append (subseq bits i) (subseq bits 0 i))))

(defun lexbit-before? (xs ys)
  (loop for x in xs for y in ys
        when (/= x y) do (return (< x y))
        finally (return nil)))

(defun source-cyclic-canon (bits)
  (unless (bit-vector-source-p bits)
    (error "Nonempty source word with only exact bits required"))
  (let ((best nil) (best-shift nil))
    (loop for k from 0 below (length bits)
          for rotated = (left-conjugate bits k)
          do (when (or (null best) (lexbit-before? rotated best))
               (setf best rotated best-shift k)))
    (list best best-shift)))

(defun bits-of-integer (x width)
  (loop for i downfrom (1- width) to 0
        collect (ldb (byte 1 i) x)))

(defun reject? (source)
  (handler-case
      (progn (source-cyclic-canon source) nil)
    (error () t)))

(defun suite ()
  (dolist (row '(((1 1 0 0)       ((0 0 1 1) 2))
                 ((1 0 0 1)       ((0 0 1 1) 1))
                 ((1 0 1 0)       ((0 1 0 1) 1))
                 ((0 1 0 0 1 0)   ((0 0 1 0 0 1) 2))
                 ((1 1 1 1)       ((1 1 1 1) 0))
                 ((0 1 0 1 0)     ((0 0 1 0 1) 4))
                 ((0 1 1 0)       ((0 0 1 1) 3))
                 ((0)             ((0) 0))
                 ((1)             ((1) 0))))
    (assert-equal "source witness"
                  (source-cyclic-canon (first row))
                  (second row)))
  (assert-equal "tie in all-ones" (source-cyclic-canon '(1 1 1 1 1 1))
                '((1 1 1 1 1 1) 0))
  (assert-equal "full-length is preserved"
                (length (first (source-cyclic-canon '(0 1 0 1 0))))
                5)
  (assert-equal "empty rejected" (reject? nil) t)
  (assert-equal "invalid out-of-alphabet bit rejected" (reject? '(1 2 0)) t)
  (assert-equal "text char is not an exact bit" (reject? '(1 #\0)) t)
  (assert-equal "float is not exact bit" (reject? '(0.0 1)) t)
  ;; The independent donor enumerates the ORBIT itself, rather than
  ;; implementing Booth+KMP (the Python source-under-test).
  (loop for n from 1 to 9 do
    (loop for value from 0 below (ash 1 n) do
      (let* ((word (bits-of-integer value n))
             (answer (source-cyclic-canon word))
             (canonical (first answer))
             (k (second answer)))
        (unless (equal canonical (left-conjugate word k))
          (error "source witness rotation is invalid"))
        (loop for j from 0 below n
              for alt = (left-conjugate word j)
              do (when (lexbit-before? alt canonical)
                   (error "nonminimal circular shift in source oracle"))
              when (equal alt canonical)
                do (when (< j k)
                     (error "earliest tied original source shift violated")))
        (incf *orbit-cases*))))
  (format t "D10 CYCLIC WORD real SBCL donor PASS ~D named controls + ~D exhaustive words~%"
          *checks* *orbit-cases*)
  (finish-output))

(handler-case (suite)
  (error (condition)
    (format *error-output* "D10 CYCLIC WORD real SBCL donor FAIL ~A~%"
            condition)
    (sb-ext:exit :code 1)))
