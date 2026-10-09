;;;; Independent historical AI mathematical donor oracle, NOT binary SENS code.
;;;; Reiter (1987) finite conflict -> subset-minimal hitting-set diagnoses.
;;;; This oracle enumerates whole integer-mask power set rather than using
;;;; the Python oracle's recursive uncovered-conflict branching algorithm.
(defpackage :d10-reiter-diagnoses (:use :cl))
(in-package :d10-reiter-diagnoses)

(defvar *checks* 0)
(defvar *family-count* 0)
(defun expect (label actual wanted)
  (unless (equal actual wanted)
    (error "~A: got ~S, expected ~S" label actual wanted))
  (incf *checks*))

(defun valid-input? (universe conflicts)
  (and (listp universe) (listp conflicts)
       (every #'symbolp universe)
       (= (length universe) (length (remove-duplicates universe)))
       (every (lambda (c)
                (and (listp c)
                     (every (lambda (v) (member v universe)) c)))
              conflicts)))

(defun hits-all? (selection conflicts)
  (every (lambda (conflict)
           (intersection selection conflict :test #'eq)) conflicts))

(defun ordered-subsets (items)
  (let ((result '()))
    (loop for mask from 0 below (ash 1 (length items))
          do (push (loop for v in items
                         for bit from 0
                         when (logbitp bit mask) collect v)
                   result))
    (nreverse result)))

(defun lex-indices-before (left right universe)
  (let ((l (mapcar (lambda (v) (position v universe)) left))
        (r (mapcar (lambda (v) (position v universe)) right)))
    (loop for x in l
          for y in r
          when (/= x y) do (return (< x y))
          finally (return (< (length l) (length r))))))

(defun source-diagnose (universe conflicts)
  (unless (valid-input? universe conflicts)
    (error "invalid conflict universe or conflict source labels"))
  (loop for conflict in conflicts for index from 0
        when (null conflict)
          do (return-from source-diagnose
               (list :no-diagnosis index)))
  (let* ((hits (remove-if-not
                (lambda (candidate) (hits-all? candidate conflicts))
                (ordered-subsets universe)))
         (minimal
           (remove-if
            (lambda (candidate)
              (some (lambda (other)
                      (and (< (length other) (length candidate))
                           (subsetp other candidate :test #'eq)))
                    hits))
            hits)))
    (setf minimal (sort minimal
                        (lambda (a b) (lex-indices-before a b universe))))
    (list :diagnoses
          (mapcar (lambda (diag)
                    (list diag
                          (loop for component in diag
                                collect
                                (list component
                                      (or (loop for edge in conflicts
                                                for k from 0
                                                when (equal
                                                      (intersection diag edge :test #'eq)
                                                      (list component))
                                                  return k)
                                          (error "minimal witness missing"))))))
                  minimal))))

(defun refuses? (thunk)
  (handler-case (progn (funcall thunk) nil) (error () t)))

(defun suite ()
  (expect "two incomparable minimal diagnoses"
          (source-diagnose '(a b c) '((a b) (b c)))
          '(:diagnoses (((a c) ((a 0) (c 1)))
                        ((b) ((b 0))))))
  (expect "empty conflict family -> one empty diagnosis"
          (source-diagnose '(a b) nil)
          '(:diagnoses ((nil nil))))
  (expect "empty universe with empty conflict collection"
          (source-diagnose nil nil)
          '(:diagnoses ((nil nil))))
  (expect "one empty conflict blocks all"
          (source-diagnose '(a b) '(nil))
          '(:no-diagnosis 0))
  (expect "earliest empty conflict index"
          (source-diagnose '(a) '((a) nil nil))
          '(:no-diagnosis 1))
  (expect "both independent components required"
          (source-diagnose '(a b) '((a) (b)))
          '(:diagnoses (((a b) ((a 0) (b 1))))))
  (expect "duplicate conflict does not multiply diagnoses"
          (source-diagnose '(a b) '((a b) (a b)))
          '(:diagnoses (((a) ((a 0))) ((b) ((b 0))))))
  (expect "one component conflicts with itself"
          (source-diagnose '(a b c) '((b) (a b c)))
          '(:diagnoses (((b) ((b 0))))))
  (expect "duplicate universe labels invalid"
          (refuses? (lambda () (source-diagnose '(a a) '((a)))))
          t)
  (expect "unknown conflict element invalid"
          (refuses? (lambda () (source-diagnose '(a b) '((c)))))
          t)
  (expect "non-list conflict invalid"
          (refuses? (lambda () (source-diagnose '(a) '(a))))
          t)
  (expect "component source positions lex order"
          (source-diagnose '(b a c) '((b a) (a c)))
          '(:diagnoses (((b c) ((b 0) (c 1)))
                        ((a) ((a 0))))))
  (expect "lex witness first original conflict index"
          (source-diagnose '(a) '((a) (a)))
          '(:diagnoses (((a) ((a 0))))))

  ;; Exhaustive 3-component families with 0/1/2 possible conflict edges,
  ;; including the empty conflict set. Verify minimality and completeness.
  (let ((edges (ordered-subsets '(a b c))))
    (dolist (family (cons nil
                          (append (mapcar #'list edges)
                                  (loop for first in edges
                                        append (loop for second in edges
                                                     collect (list first second))))))
      (let ((result (source-diagnose '(a b c) family)))
        (if (member nil family)
            (unless (eq (first result) :no-diagnosis)
              (error "empty conflict edge not rejected"))
            (progn
              (unless (eq (first result) :diagnoses)
                (error "no diagnostics despite satisfiable family"))
              (dolist (entry (second result))
                (let ((diag (first entry)))
                  (unless (hits-all? diag family)
                    (error "some conflict unhit"))
                  (dolist (component diag)
                    (when (hits-all? (remove component diag) family)
                      (error "diagnosis is not subset-minimal"))))))))
      (incf *family-count*)))
  (format t "D10 REITER real SBCL source oracle PASS ~D witnesses + ~D finite families~%"
          *checks* *family-count*)
  (finish-output))

(handler-case (suite)
  (error (condition)
    (format *error-output* "D10 REITER SBCL donor FAIL ~A~%" condition)
    (sb-ext:exit :code 1)))
