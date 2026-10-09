;;;; Historical donor oracle: ANSI Common Lisp CLHS Ch19 §19.4 Pathnames.
;;;; (role research-only)
;;;; (semantic-authority-change none)
;;;; Never treated as executable SENS code, D2 words or T5.
;;;; Pure constructed pathname objects, no filesystem calls.
(defpackage :d10-clhs-pathname-witness (:use :cl))
(in-package :d10-clhs-pathname-witness)

(defvar *checks* 0)
(defun check (label condition)
  (unless condition (error "~A failed" label))
  (incf *checks*))

(handler-case
    (progn
      (let* ((base (make-pathname :directory '(:absolute "science")
                                  :name "default" :type "dat"))
             (part (make-pathname :directory '(:relative "trial")
                                  :name "tone" :type nil))
             (merged (merge-pathnames part base))
             (full (make-pathname :directory '(:absolute "science" "trial")
                                  :name "tone" :type "dat"))
             (wild (make-pathname :directory '(:absolute "science" "trial")
                                  :name :wild :type "dat")))
        (check "source classified as PATHNAME" (pathnamep part))
        (check "source name preserved" (equal (pathname-name part) "tone"))
        (check "merged is PATHNAME" (pathnamep merged))
        (check "relative-directory append"
               (equal (pathname-directory merged)
                      '(:absolute "science" "trial")))
        (check "name takes precedence" (equal (pathname-name merged) "tone"))
        (check "type defaults from base" (equal (pathname-type merged) "dat"))
        (check "base pathname unchanged" (equal (pathname-name base) "default"))
        (check "nonwild ordinary pathname" (not (wild-pathname-p full)))
        (check "wild name recognized" (wild-pathname-p wild))
        (check "wildcard in second argument matches actual" (pathname-match-p full wild))
        (check "wildcard in first argument does not match concrete second"
               (not (pathname-match-p wild full)))
        (check "merge agrees with full constructed components"
               (equal (pathname-directory merged) (pathname-directory full)))
        (check "enough-namestring preserves relative reconstruction"
               (equal (merge-pathnames (enough-namestring full base) base)
                      (merge-pathnames full base)))
        (check "explicit empty wildcard? not inferred"
               (not (wild-pathname-p merged :name)))
        (check "invalid pathname designator raises type-error"
               (handler-case (progn (pathname-match-p 42 wild) nil)
                 (type-error () t))))
      (format t "D10 CLHS PATHNAMES SBCL SOURCE WITNESS PASS ~D checks~%" *checks*)
      (finish-output))
  (error (e)
    (format *error-output* "D10 CLHS PATHNAMES SBCL FAIL after ~D: ~A~%"
            *checks* e)
    (sb-ext:exit :code 1)))
