;;;; Independent actual SBCL research oracle; no executable SENS runtime claims.
;;;; Formal donor: Isabelle AFP Stern_Brocot_Tree.mk_path, path uniqueness.
;;;; The source model uses L=0 and R=1 as data bits, not D2 structural words.
(defpackage :d10-sb-runs (:use :cl))
(in-package :d10-sb-runs)
(defvar *checks* 0)
(defvar *small-ratios* 0)

(defun check (name actual expected)
  (unless (equal actual expected)
    (error "~A: expected ~S, got ~S" name expected actual))
  (incf *checks*))

(defun source-path (p q)
  "Literal subtraction equation from formal mk_path, no quotients."
  (unless (and (integerp p) (integerp q) (> p 0) (> q 0))
    (error "positive integers only"))
  (let ((a p) (b q) (answer nil))
    (loop until (= a b)
          do (if (< a b)
                 (progn (push 0 answer) (decf b a))
                 (progn (push 1 answer) (decf a b))))
    (nreverse answer)))

(defun collect-runs (bits)
  (let ((groups nil))
    (dolist (bit bits)
      (if (and groups (eql bit (caar groups)))
          (incf (cadar groups))
          (push (list bit 1) groups)))
    (nreverse groups)))

(defun validate-runs (runs)
  (unless (listp runs) (error "path runs must be proper list"))
  (let ((prior nil))
    (dolist (run runs)
      (unless (and (listp run) (= (length run) 2)
                   (integerp (first run)) (member (first run) '(0 1) :test #'eql)
                   (integerp (second run)) (> (second run) 0)
                   (not (eql prior (first run))))
        (error "invalid or noncanonical run: ~S" run))
      (setf prior (first run))))
  runs)

(defun decode-exact-batched (runs)
  "Independent arithmetic on the two bounding rationals, not Python algorithm."
  (validate-runs runs)
  (let ((left-num 0) (left-den 1) (right-num 1) (right-den 0))
    (dolist (run runs)
      (destructuring-bind (direction count) run
        (cond
          ((eql direction 0)
           (incf right-num (* count left-num))
           (incf right-den (* count left-den)))
          ((eql direction 1)
           (incf left-num (* count right-num))
           (incf left-den (* count right-den))))))
    (/ (+ left-num right-num) (+ left-den right-den))))

(defun reject? (function)
  (handler-case (progn (funcall function) nil)
    (error () t)))

(defun suite ()
  (dolist (item '((1 1 nil)
                  (1 2 ((0 1)))
                  (2 1 ((1 1)))
                  (2 3 ((0 1) (1 1)))
                  (3 2 ((1 1) (0 1)))
                  (5 2 ((1 2) (0 1)))
                  (13 9 ((1 1) (0 2) (1 3)))))
    (destructuring-bind (p q want) item
      (check "source literal Euclid path"
             (collect-runs (source-path p q)) want)
      (check "source exact mediant inversion"
             (decode-exact-batched want) (/ p q))))
  ;; Deliberately use the direct formal subtractive path for small ratios.
  (loop for p from 1 to 24 do
    (loop for q from 1 to 24 do
      (let* ((runs (collect-runs (source-path p q)))
             (x (decode-exact-batched runs)))
        (unless (= x (/ p q))
          (error "inconsistent exact positive ratio ~D/~D" p q))
        (incf *small-ratios*))))
  (check "left billion run compressed"
         (decode-exact-batched '((0 1000000000))) 1/1000000001)
  (check "right billion run compressed"
         (decode-exact-batched '((1 1000000000))) 1000000001)
  (check "noncanonical adjacent same bit"
         (reject? (lambda () (decode-exact-batched '((0 1) (0 2))))) t)
  (check "nonpositive run rejected"
         (reject? (lambda () (decode-exact-batched '((1 0))))) t)
  (check "inexact run rejected"
         (reject? (lambda () (decode-exact-batched '((0 1.0))))) t)
  (check "invalid bit rejected"
         (reject? (lambda () (decode-exact-batched '((2 1))))) t)
  (check "nonpositive numerator source rejected"
         (reject? (lambda () (source-path 0 1))) t)
  (check "negative denominator source rejected"
         (reject? (lambda () (source-path 1 -2))) t)
  (format t "D10 STERN-BROCOT real SBCL source PASS ~D named checks + ~D positive ratios~%"
          *checks* *small-ratios*)
  (finish-output))

(handler-case (suite)
  (error (err)
    (format *error-output* "D10 STERN-BROCOT real SBCL donor FAIL ~A~%" err)
    (sb-ext:exit :code 1)))
