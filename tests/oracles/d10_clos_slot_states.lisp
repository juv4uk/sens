;;;; Д10: оракул історичного джерела CLOS; імена Common Lisp — лише еталон.
;;;; (role research-only)
;;;; (semantic-authority-change none)
;;;; Це не джерело СЕНС, не виконуваний .sens і не координати домену Д10.
(in-package :cl-user)

(defvar *d10-observations* 0)

(defun d10-observe (назва умова)
  (unless умова
    (error "D10 donor oracle failed: ~A" назва))
  (incf *d10-observations*)
  (format t "OBS~C~A~CPASS~%" #\Tab назва #\Tab))

(defun d10-signals-error-p (дія)
  (handler-case
      (progn (funcall дія) nil)
    (error () t)))

(defclass d10-oracle-parent () ())
(defclass d10-oracle-child (d10-oracle-parent)
  ((a)
   (b :initform nil)
   (c :initform 7)))

(let ((об'єкт (make-instance 'd10-oracle-child)))
  ;; Три різні стани: слота немає, слот не зв'язаний, слот має значення NIL.
  (d10-observe "SLOT_EXISTS_UNBOUND" (slot-exists-p об'єкт 'a))
  (d10-observe "SLOT_EXISTS_BOUND_NIL" (slot-exists-p об'єкт 'b))
  (d10-observe "SLOT_EXISTS_ABSENT_NO" (not (slot-exists-p об'єкт 'z)))
  (d10-observe "SLOT_BOUNDP_UNBOUND_NO" (not (slot-boundp об'єкт 'a)))
  (d10-observe "SLOT_BOUNDP_BOUND_NIL_YES" (slot-boundp об'єкт 'b))
  (d10-observe "SLOT_VALUE_BOUND_NIL_IS_NIL" (null (slot-value об'єкт 'b)))
  ;; Відсутній і незв'язаний слот не можна мовчки видавати за NIL.
  (d10-observe "SLOT_BOUNDP_MISSING_ERROR"
    (d10-signals-error-p (lambda () (slot-boundp об'єкт 'z))))
  (d10-observe "SLOT_VALUE_UNBOUND_ERROR"
    (d10-signals-error-p (lambda () (slot-value об'єкт 'a))))
  ;; Розв'язування слота не видаляє його та не змінює сусідні слоти.
  (d10-observe "SLOT_MAKUNBOUND_RETURNS_SAME"
    (eq об'єкт (slot-makunbound об'єкт 'b)))
  (d10-observe "SLOT_MAKUNBOUND_EXISTS_AFTER"
    (slot-exists-p об'єкт 'b))
  (d10-observe "SLOT_MAKUNBOUND_NOT_BOUND_AFTER"
    (not (slot-boundp об'єкт 'b)))
  (d10-observe "SLOT_MAKUNBOUND_UNTOUCHED"
    (and (slot-boundp об'єкт 'c)
         (= 7 (slot-value об'єкт 'c))))
  (d10-observe "SLOT_MAKUNBOUND_MISSING_ERROR"
    (d10-signals-error-p (lambda () (slot-makunbound об'єкт 'z))))
  (setf (slot-value об'єкт 'b) nil)
  (d10-observe "SLOT_MAKUNBOUND_REBIND_POSSIBLE"
    (and (slot-boundp об'єкт 'b) (null (slot-value об'єкт 'b))))
  ;; CLASS-OF повертає саме об'єкт безпосереднього класу, а не символ
  ;; назви класу й не довільний батьківський клас.
  (d10-observe "CLASS_OF_EXACT_CLASS_OBJECT"
    (eq (class-of об'єкт) (find-class 'd10-oracle-child)))
  (d10-observe "CLASS_OF_NOT_CLASS_SYMBOL"
    (not (eq (class-of об'єкт) 'd10-oracle-child)))
  (d10-observe "CLASS_OF_CHILD_NOT_PARENT"
    (not (eq (class-of об'єкт) (find-class 'd10-oracle-parent)))))

(format t "SUMMARY~CD10-CLOS-SLOT-ORACLE-V1~C~D~%"
        #\Tab #\Tab *d10-observations*)
