;;;; Історичний оракул ANSI Common Lisp: CLHS, розділ 19 §19.4 (шляхи).
;;;; (role research-only)
;;;; (semantic-authority-change none)
;;;; Не є виконуваним кодом СЕНС, словами D2 чи транспортом T5.
;;;; Досліджуються лише шляхи в пам'яті, без звернення до файлової системи.
;;;; Стандартні оператори Common Lisp, шляхи та вхідні рядки не змінено.
;;;; Авторські назви, пояснення і повідомлення перевірок — українською.
;;;; Машинні підсумкові маркери PASS/FAIL збережено для зовнішніх читачів.

(defpackage :d10-clhs-pathname-witness (:use :cl))
(in-package :d10-clhs-pathname-witness)

(defvar *кількість-перевірок* 0)

(defun перевірити (назва умова)
  (unless умова
    (error "Перевірку не пройдено: ~A" назва))
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
        (перевірити "Джерело є об'єктом PATHNAME" (pathnamep частина))
        (перевірити "Ім'я джерела збережено" (equal (pathname-name частина) "tone"))
        (перевірити "Об'єднаний шлях є PATHNAME" (pathnamep об'єднаний))
        (перевірити "Відносний каталог додано"
                   (equal (pathname-directory об'єднаний)
                          '(:absolute "science" "trial")))
        (перевірити "Ім'я частини має перевагу"
                   (equal (pathname-name об'єднаний) "tone"))
        (перевірити "Тип успадковано з основи"
                   (equal (pathname-type об'єднаний) "dat"))
        (перевірити "Основний шлях не змінено"
                   (equal (pathname-name основа) "default"))
        (перевірити "Звичайний шлях не має шаблонів"
                   (not (wild-pathname-p повний)))
        (перевірити "Шаблонне ім'я розпізнано"
                   (wild-pathname-p шаблон))
        (перевірити "Шаблон другого аргументу збігається з повним шляхом"
                   (pathname-match-p повний шаблон))
        (перевірити "Шаблон першого аргументу не збігається з конкретним другим"
                   (not (pathname-match-p шаблон повний)))
        (перевірити "Об'єднання збігається з компонентами явно створеного шляху"
                   (equal (pathname-directory об'єднаний)
                          (pathname-directory повний)))
        (перевірити "Скорочене ім'я дозволяє відновити відносний шлях"
                   (equal (merge-pathnames (enough-namestring повний основа) основа)
                          (merge-pathnames повний основа)))
        (перевірити "Шаблонне ім'я не виникає з порожнього місця"
                   (not (wild-pathname-p об'єднаний :name)))
        (перевірити "Недопустимий позначник шляху спричиняє помилку типу"
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
