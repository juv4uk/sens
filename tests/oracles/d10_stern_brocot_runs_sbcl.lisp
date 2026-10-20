;;;; Незалежний дослідний оракул справжнього SBCL, а не виконання СЕНС.
;;;; Формальне джерело: Isabelle AFP Stern_Brocot_Tree.mk_path, єдиність шляху.
;;;; У моделі L=0 і R=1 — біти даних, а не структурні слова D2.
(defpackage :d10-sb-runs (:use :cl))
(in-package :d10-sb-runs)
(defvar *checks* 0)
(defvar *small-ratios* 0)

(defun перевірити (назва фактичне очікуване)
  (unless (equal фактичне очікуване)
    (error "~A: expected ~S, got ~S" назва очікуване фактичне))
  (incf *checks*))

(defun шлях-джерела (чисельник знаменник)
  "Literal subtraction equation from formal mk_path, no quotients."
  (unless (and (integerp чисельник) (integerp знаменник)
               (> чисельник 0) (> знаменник 0))
    (error "positive integers only"))
  (let ((ліве чисельник) (праве знаменник) (шлях nil))
    (loop until (= ліве праве)
          do (if (< ліве праве)
                 (progn (push 0 шлях) (decf праве ліве))
                 (progn (push 1 шлях) (decf ліве праве))))
    (nreverse шлях)))

(defun зібрати-серії (біти)
  (let ((серії nil))
    (dolist (біт біти)
      (if (and серії (eql біт (caar серії)))
          (incf (cadar серії))
          (push (list біт 1) серії)))
    (nreverse серії)))

(defun перевірити-серії (серії)
  (unless (listp серії) (error "path runs must be proper list"))
  (let ((попередній nil))
    (dolist (серія серії)
      (unless (and (listp серія) (= (length серія) 2)
                   (integerp (first серія))
                   (member (first серія) '(0 1) :test #'eql)
                   (integerp (second серія)) (> (second серія) 0)
                   (not (eql попередній (first серія))))
        (error "invalid or noncanonical run: ~S" серія))
      (setf попередній (first серія))))
  серії)

(defun декодувати-точно-серіями (серії)
  "Independent arithmetic on the two bounding rationals, not Python algorithm."
  (перевірити-серії серії)
  (let ((лівий-чисельник 0) (лівий-знаменник 1)
        (правий-чисельник 1) (правий-знаменник 0))
    (dolist (серія серії)
      (destructuring-bind (напрям кількість) серія
        (cond
          ((eql напрям 0)
           (incf правий-чисельник (* кількість лівий-чисельник))
           (incf правий-знаменник (* кількість лівий-знаменник)))
          ((eql напрям 1)
           (incf лівий-чисельник (* кількість правий-чисельник))
           (incf лівий-знаменник (* кількість правий-знаменник))))))
    (/ (+ лівий-чисельник правий-чисельник)
       (+ лівий-знаменник правий-знаменник))))

(defun відхилено? (дія)
  (handler-case (progn (funcall дія) nil)
    (error () t)))

(defun набір-перевірок ()
  (dolist (випадок '((1 1 nil)
                    (1 2 ((0 1)))
                    (2 1 ((1 1)))
                    (2 3 ((0 1) (1 1)))
                    (3 2 ((1 1) (0 1)))
                    (5 2 ((1 2) (0 1)))
                    (13 9 ((1 1) (0 2) (1 3)))))
    (destructuring-bind (чисельник знаменник очікуване) випадок
      (перевірити "source literal Euclid path"
                 (зібрати-серії (шлях-джерела чисельник знаменник)) очікуване)
      (перевірити "source exact mediant inversion"
                 (декодувати-точно-серіями очікуване)
                 (/ чисельник знаменник))))
  ;; Для малих відношень використовуємо саме формальне віднімання.
  (loop for чисельник from 1 to 24 do
    (loop for знаменник from 1 to 24 do
      (let* ((серії (зібрати-серії (шлях-джерела чисельник знаменник)))
             (результат (декодувати-точно-серіями серії)))
        (unless (= результат (/ чисельник знаменник))
          (error "inconsistent exact positive ratio ~D/~D" чисельник знаменник))
        (incf *small-ratios*))))
  (перевірити "left billion run compressed"
             (декодувати-точно-серіями '((0 1000000000))) 1/1000000001)
  (перевірити "right billion run compressed"
             (декодувати-точно-серіями '((1 1000000000))) 1000000001)
  (перевірити "noncanonical adjacent same bit"
             (відхилено? (lambda () (декодувати-точно-серіями '((0 1) (0 2))))) t)
  (перевірити "nonpositive run rejected"
             (відхилено? (lambda () (декодувати-точно-серіями '((1 0))))) t)
  (перевірити "inexact run rejected"
             (відхилено? (lambda () (декодувати-точно-серіями '((0 1.0))))) t)
  (перевірити "invalid bit rejected"
             (відхилено? (lambda () (декодувати-точно-серіями '((2 1))))) t)
  (перевірити "nonpositive numerator source rejected"
             (відхилено? (lambda () (шлях-джерела 0 1))) t)
  (перевірити "negative denominator source rejected"
             (відхилено? (lambda () (шлях-джерела 1 -2))) t)
  (format t "D10 STERN-BROCOT real SBCL source PASS ~D named checks + ~D positive ratios~%"
          *checks* *small-ratios*)
  (finish-output))

(handler-case (набір-перевірок)
  (error (помилка)
    (format *error-output* "D10 STERN-BROCOT real SBCL donor FAIL ~A~%" помилка)
    (sb-ext:exit :code 1)))
