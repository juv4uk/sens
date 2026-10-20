;;;; Історичний оракул ANSI Common Lisp, CLHS, розділ 19 §19.4 (шляхи).
;;;; (role research-only)
;;;; (semantic-authority-change none)
;;;; Не є виконуваним кодом СЕНС, словами D2 чи транспортом T5.
;;;; Лише створені в пам'яті шляхи, без звернень до файлової системи.
(defpackage :d10-clhs-pathname-witness (:use :cl))
(in-package :d10-clhs-pathname-witness)

(defvar *checks* 0)
(defun check (назва умова)
  (unless умова (error "~A failed" назва))
  (incf *checks*))

(handler-case
    (progn
      (let* ((основа (make-pathname :directory '(:absolute "science")
                                  :name "default" :type "dat"))
             (частина (make-pathname :directory '(:relative "trial")
                                  :name "tone" :type nil))
             (об'єднаний (merge-pathnames частина основа))
             (повний (make-pathname :directory '(:absolute "science" "trial")
                                  :name "tone" :type "dat"))
             (шаблон (make-pathname :directory '(:absolute "science" "trial")
                                  :name :wild :type "dat")))
        (check "source classified as PATHNAME" (pathnamep частина))
        (check "source name preserved" (equal (pathname-name частина) "tone"))
        (check "merged is PATHNAME" (pathnamep об'єднаний))
        (check "relative-directory append"
               (equal (pathname-directory об'єднаний)
                      '(:absolute "science" "trial")))
        (check "name takes precedence" (equal (pathname-name об'єднаний) "tone"))
        (check "type defaults from base" (equal (pathname-type об'єднаний) "dat"))
        (check "base pathname unchanged" (equal (pathname-name основа) "default"))
        (check "nonwild ordinary pathname" (not (wild-pathname-p повний)))
        (check "wild name recognized" (wild-pathname-p шаблон))
        (check "wildcard in second argument matches actual" (pathname-match-p повний шаблон))
        (check "wildcard in first argument does not match concrete second"
               (not (pathname-match-p шаблон повний)))
        (check "merge agrees with full constructed components"
               (equal (pathname-directory об'єднаний) (pathname-directory повний)))
        (check "enough-namestring preserves relative reconstruction"
               (equal (merge-pathnames (enough-namestring повний основа) основа)
                      (merge-pathnames повний основа)))
        (check "explicit empty wildcard? not inferred"
               (not (wild-pathname-p об'єднаний :name)))
        (check "invalid pathname designator raises type-error"
               (handler-case (progn (pathname-match-p 42 шаблон) nil)
                 (type-error () t))))
      (format t "D10 CLHS PATHNAMES SBCL SOURCE WITNESS PASS ~D checks~%" *checks*)
      (finish-output))
  (error (помилка)
    (format *error-output* "D10 CLHS PATHNAMES SBCL FAIL after ~D: ~A~%"
            *checks* помилка)
    (sb-ext:exit :code 1)))
