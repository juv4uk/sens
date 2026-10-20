;;;; Історичний оракул ANSI Common Lisp, CLHS, розділ 19 §19.4 (шляхи).
;;;; (role research-only)
;;;; (semantic-authority-change none)
;;;; Не є виконуваним кодом СЕНС, словами D2 чи транспортом T5.
;;;; Лише створені в пам'яті шляхи, без звернень до файлової системи.
;;;; Імена стандартних операцій та рядки-входи еталонних прикладів не змінено.
(defpackage :d10-clhs-pathname-witness (:use :cl))
(in-package :d10-clhs-pathname-witness)

(defvar *кількість-перевірок* 0)

(defun перевірити (назва умова)
  (unless умова
    (error "~A failed" назва))
  (incf *кількість-перевірок*))

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
        (перевірити "source classified as PATHNAME" (pathnamep частина))
        (перевірити "source name preserved" (equal (pathname-name частина) "tone"))
        (перевірити "merged is PATHNAME" (pathnamep об'єднаний))
        (перевірити "relative-directory append"
                   (equal (pathname-directory об'єднаний)
                          '(:absolute "science" "trial")))
        (перевірити "name takes precedence" (equal (pathname-name об'єднаний) "tone"))
        (перевірити "type defaults from base" (equal (pathname-type об'єднаний) "dat"))
        (перевірити "base pathname unchanged" (equal (pathname-name основа) "default"))
        (перевірити "nonwild ordinary pathname" (not (wild-pathname-p повний)))
        (перевірити "wild name recognized" (wild-pathname-p шаблон))
        (перевірити "wildcard in second argument matches actual"
                   (pathname-match-p повний шаблон))
        (перевірити "wildcard in first argument does not match concrete second"
                   (not (pathname-match-p шаблон повний)))
        (перевірити "merge agrees with full constructed components"
                   (equal (pathname-directory об'єднаний) (pathname-directory повний)))
        (перевірити "enough-namestring preserves relative reconstruction"
                   (equal (merge-pathnames (enough-namestring повний основа) основа)
                          (merge-pathnames повний основа)))
        (перевірити "explicit empty wildcard? not inferred"
                   (not (wild-pathname-p об'єднаний :name)))
        (перевірити "invalid pathname designator raises type-error"
                   (handler-case
                       (progn (pathname-match-p 42 шаблон) nil)
                     (type-error () t))))
      (format t "D10 CLHS PATHNAMES SBCL SOURCE WITNESS PASS ~D checks~%"
              *кількість-перевірок*)
      (finish-output))
  (error (помилка)
    (format *error-output* "D10 CLHS PATHNAMES SBCL FAIL after ~D: ~A~%"
            *кількість-перевірок* помилка)
    (sb-ext:exit :code 1)))
