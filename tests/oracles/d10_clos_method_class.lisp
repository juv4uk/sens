;;;; Історичний CLOS-оракул Д10: лише дослідницький еталон, не код СЕНС.
;;;; Спостереження спираються на ANSI Common Lisp і закони CLOS.
;;;; Викличні імена стандартної бібліотеки та контрольні мітки залишено без змін.
(in-package :cl-user)

(defvar *d10-method-class-observations* 0)

(defun d10-method-class-observe (назва умова)
  (unless умова
    (error "D10 CLOS method/class donor oracle failed: ~A" назва))
  (incf *d10-method-class-observations*)
  (format t "OBS~C~A~CPASS~%" #\Tab назва #\Tab))

(defun d10-method-class-signals-error-p (дія)
  (handler-case
      (progn (funcall дія) nil)
    (error () t)))

;;; Точне знаходження методу за сигнатурою не тотожне диспетчеризації виклику.
(defgeneric d10-method-class-dispatch (значення))
(defmethod d10-method-class-dispatch ((значення integer)) :integer)
(defmethod d10-method-class-dispatch ((значення number)) :number)
(defmethod d10-method-class-dispatch :before ((значення integer)) nil)
(defmethod d10-method-class-dispatch ((значення string)) :string)

;;; Класи та метод оновлення для CHANGE-CLASS визначено на верхньому рівні.
(defclass d10-method-class-before ()
  ((retained :initarg :retained)
   (common-unbound)
   (old-only :initform :old)))
(defclass d10-method-class-after ()
  ((retained)
   (common-unbound)
   (new-only :initform :new)))

(defvar *d10-change-class-target* nil)
(defvar *d10-change-class-hook-observation* nil)
(defmethod update-instance-for-different-class :before
    ((попередній d10-method-class-before)
     (поточний d10-method-class-after)
     &rest параметри-ініціалізації)
  (declare (ignore параметри-ініціалізації))
  (setf *d10-change-class-hook-observation*
        (list (slot-value попередній 'retained)
              (eq поточний *d10-change-class-target*))))

(let* ((узагальнена-функція #'d10-method-class-dispatch)
       (спеціалізатор-цілих (find-class 'integer))
       (спеціалізатор-чисел (find-class 'number))
       (метод-цілих (find-method узагальнена-функція nil (list спеціалізатор-цілих)))
       (метод-чисел (find-method узагальнена-функція nil (list спеціалізатор-чисел)))
       (попередній-метод (find-method узагальнена-функція '(:before) (list спеціалізатор-цілих))))
  (d10-method-class-observe "FIND_METHOD_INTEGER_EXACT"
    (eq метод-цілих (find-method узагальнена-функція nil (list спеціалізатор-цілих))))
  (d10-method-class-observe "FIND_METHOD_NUMBER_EXACT"
    (eq метод-чисел (find-method узагальнена-функція nil (list спеціалізатор-чисел))))
  (d10-method-class-observe "FIND_METHOD_BEFORE_QUALIFIER_EXACT"
    (eq попередній-метод (find-method узагальнена-функція '(:before) (list спеціалізатор-цілих))))
  (d10-method-class-observe "FIND_METHOD_QUALIFIER_DISTINCT"
    (not (eq метод-цілих попередній-метод)))
  (d10-method-class-observe "FIND_METHOD_MISSING_RETURNS_NIL"
    (null (find-method узагальнена-функція '(:after) (list спеціалізатор-цілих) nil)))
  (d10-method-class-observe "FIND_METHOD_MISSING_DEFAULT_ERRORS"
    (d10-method-class-signals-error-p
      (lambda () (find-method узагальнена-функція '(:after) (list спеціалізатор-цілих)))))
  (d10-method-class-observe "FIND_METHOD_SPECIALIZER_ARITY_ERRORS"
    (d10-method-class-signals-error-p
      (lambda () (find-method узагальнена-функція nil nil nil))))
  (d10-method-class-observe "FIND_METHOD_LOOKUP_NOT_DISPATCH_RESULT"
    (and (eq метод-чисел
             (find-method узагальнена-функція nil (list спеціалізатор-чисел)))
         (eq (funcall узагальнена-функція 42) :integer)
         (not (eq метод-чисел метод-цілих))))

  ;; Видалення методу зберігає узагальнену функцію, інші методи й кваліфікатори.
  (d10-method-class-observe "REMOVE_METHOD_RETURNS_SAME_GF"
    (eq узагальнена-функція (remove-method узагальнена-функція метод-цілих)))
  (d10-method-class-observe "REMOVE_METHOD_INTEGER_METHOD_ABSENT"
    (null (find-method узагальнена-функція nil (list спеціалізатор-цілих) nil)))
  (d10-method-class-observe "REMOVE_METHOD_ABSENT_NO_ERROR"
    (eq узагальнена-функція (remove-method узагальнена-функція метод-цілих)))
  (d10-method-class-observe "REMOVE_METHOD_ABSENT_RETURNS_SAME_GF"
    (eq узагальнена-функція (remove-method узагальнена-функція метод-цілих)))
  (d10-method-class-observe "REMOVE_METHOD_OTHER_METHOD_STILL_PRESENT"
    (eq метод-чисел (find-method узагальнена-функція nil (list спеціалізатор-чисел))))
  (d10-method-class-observe "REMOVE_METHOD_FALLBACK_DISPATCH"
    (eq (funcall узагальнена-функція 42) :number))
  (d10-method-class-observe "REMOVE_METHOD_BEFORE_STILL_PRESENT"
    (eq попередній-метод (find-method узагальнена-функція '(:before) (list спеціалізатор-цілих))))

  ;; CHANGE-CLASS зберігає тотожність об'єкта, значення спільного слота
  ;; та стан незв'язаного спільного слота.
  (let ((об'єкт (make-instance 'd10-method-class-before :retained 41)))
    (setf *d10-change-class-target* об'єкт
          *d10-change-class-hook-observation* nil)
    (d10-method-class-observe "CHANGE_CLASS_RETURNS_SAME_INSTANCE"
      (eq об'єкт (change-class об'єкт 'd10-method-class-after)))
    (d10-method-class-observe "CHANGE_CLASS_INSTANCE_CLASS_CHANGED"
      (eq (class-of об'єкт) (find-class 'd10-method-class-after)))
    (d10-method-class-observe "CHANGE_CLASS_RETAINS_COMMON_VALUE"
      (= (slot-value об'єкт 'retained) 41))
    (d10-method-class-observe "CHANGE_CLASS_PRESERVES_COMMON_UNBOUND"
      (not (slot-boundp об'єкт 'common-unbound)))
    (d10-method-class-observe "CHANGE_CLASS_INITIALIZES_NEW_SLOT"
      (and (slot-boundp об'єкт 'new-only)
           (eq (slot-value об'єкт 'new-only) :new)))
    (d10-method-class-observe "CHANGE_CLASS_UPDATE_HOOK_RUNS"
      (consp *d10-change-class-hook-observation*))
    (d10-method-class-observe "CHANGE_CLASS_HOOK_SEES_OLD_VALUE"
      (eql (first *d10-change-class-hook-observation*) 41))
    (d10-method-class-observe "CHANGE_CLASS_HOOK_SEES_CURRENT_INSTANCE"
      (second *d10-change-class-hook-observation*))))

(format t "SUMMARY~CD10-CLOS-METHOD-CLASS-ORACLE-V1~C~D~%"
        #\Tab #\Tab *d10-method-class-observations*)
