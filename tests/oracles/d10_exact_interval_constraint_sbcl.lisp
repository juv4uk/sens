;;;; D10 source-research math oracle, not executable SENS source.
;;;; (role research-only)
;;;; (semantic-authority-change none)
;;;; Ordinary Common Lisp rational arithmetic and pairwise evidence witnesses.
;;;; Independent of Python source implementation and physical T5.
(defpackage :d10-interval-source-research (:use :cl))
(in-package :d10-interval-source-research)

(defvar *checks* 0)
(defun check (name actual expected)
  (unless (equal actual expected)
    (error "~A: got ~S expected ~S" name actual expected))
  (incf *checks*))

(defun exact-interval-constraint (records)
  (unless (and (listp records) records)
    (error "nonempty list of labelled closed rational intervals required"))
  (let ((seen '()))
    (dolist (r records)
      (destructuring-bind (id lo hi) r
        (unless (and (symbolp id)
                     (not (member id seen :test #'eq))
                     (rationalp lo) (rationalp hi)
                     (<= lo hi))
          (error "invalid input interval or duplicate label: ~S" r))
        (push id seen))))
  (let* ((initial (first records))
         (lo (second initial))
         (hi (third initial))
         (losrc (first initial))
         (hisrc (first initial)))
    (dolist (r (rest records))
      (when (> (second r) lo)
        (setf lo (second r) losrc (first r)))
      (when (< (third r) hi)
        (setf hi (third r) hisrc (first r))))
    (when (<= lo hi)
      (return-from exact-interval-constraint
        (list :sat lo hi losrc hisrc)))
    ;; Finite exact inconsistency: find earliest pair in original order.
    (loop for i from 0 below (length records) do
      (loop for j from (1+ i) below (length records)
            for a = (nth i records)
            for b = (nth j records) do
        (cond
          ((< (third a) (second b))
           (return-from exact-interval-constraint
             (list :unsat i j (first b) (first a) (second b) (third a))))
          ((< (third b) (second a))
           (return-from exact-interval-constraint
             (list :unsat i j (first a) (first b) (second a) (third b)))))))
    (error "impossible: maxima contradicted but no pair conflicts")))

(defun rejects? (input)
  (handler-case
      (progn (exact-interval-constraint input) nil)
    (error () t)))

(defun suite ()
  (check "overlap with source bounds"
         (exact-interval-constraint '((a 0 4) (b 2 6)))
         '(:sat 2 4 b a))
  (check "singleton touch is SAT"
         (exact-interval-constraint '((a 0 2) (b 2 4)))
         '(:sat 2 2 b a))
  (check "actual incompatible pair"
         (exact-interval-constraint '((a 0 1) (b 2 3)))
         '(:unsat 0 1 b a 2 1))
  (check "reversed conflicting bounds"
         (exact-interval-constraint '((a 2 3) (b 0 1)))
         '(:unsat 0 1 a b 2 1))
  (check "source bound ties select first"
         (exact-interval-constraint '((a 1 3) (b 1 3)))
         '(:sat 1 3 a a))
  (check "first input pair, not latest extreme"
         (exact-interval-constraint
          '((a 0 4) (b 5 9) (c -100 100) (d 20 30)))
         '(:unsat 0 1 b a 5 4))
  (check "exact third rational"
         (exact-interval-constraint '((a 1/3 5/3) (b 2/3 7/3)))
         '(:sat 2/3 5/3 b a))
  (check "one interval identity"
         (exact-interval-constraint '((a -3/5 7/11)))
         '(:sat -3/5 7/11 a a))
  (check "first index early with disjoint pair i0,j2"
         (exact-interval-constraint
          '((a 0 1) (b -1/2 1/2) (c 2 3)))
         '(:unsat 0 2 c a 2 1))
  (check "gap never becomes convex hull"
         (first (exact-interval-constraint '((a 0 1) (b 3 4))))
         :unsat)
  (check "empty list errors" (rejects? nil) t)
  (check "invalid reversed bound errors" (rejects? '((a 5 4))) t)
  (check "duplicate source errors" (rejects? '((a 1 2) (a 2 3))) t)
  (check "inexact floating-point errors" (rejects? '((a 0.5 2))) t)
  (format t "D10 exact interval independent SBCL oracle: PASS ~D checks~%" *checks*)
  (finish-output))

(handler-case (suite)
  (error (e)
    (format *error-output* "D10 exact interval independent SBCL oracle: FAIL ~A~%" e)
    (sb-ext:exit :code 1)))
