;;;; Д10: оракул історичної поведінки слотів CLOS у Common Lisp.
;;;; (role research-only)
;;;; (semantic-authority-change none)
;;;; Це не виконуваний код СЕНС і не визначення координат домену Д10.
;;;; Власні назви класів, слотів, змінних та повідомлень українські.
;;;; Стандартні оператори Common Lisp і машинні мітки спостережень незмінні.
(in-package :cl-user)

(defvar *д10-спостережень* 0)

(defun д10-спостерігати (назва умова)
  (unless умова
    (error "Д10: порушено умову оракула: ~A" назва))
  (incf *д10-спостережень*)
  (format t "OBS~C~A~CPASS~%" #\Tab назва #\Tab))

(defun д10-сигналізує-помилку? (дія)
  (handler-case
      (progn (funcall дія) nil)
    (error () t)))

(defclass д10-оракул-батько () ())
(defclass д10-оракул-нащадок (д10-оракул-батько)
  ((незв'язаний)
   (порожнє-значення :initform nil)
   (заповнений :initform 7)))

(let ((об'єкт (make-instance 'д10-оракул-нащадок)))
  ;; Три різні стани: слота немає, слот не зв'язаний, слот містить NIL.
  (д10-спостерігати "SLOT_EXISTS_UNBOUND"
    (slot-exists-p об'єкт 'незв'язаний))
  (д10-спостерігати "SLOT_EXISTS_BOUND_NIL"
    (slot-exists-p об'єкт 'порожнє-значення))
  (д10-спостерігати "SLOT_EXISTS_ABSENT_NO"
    (not (slot-exists-p об'єкт 'відсутній)))
  (д10-спостерігати "SLOT_BOUNDP_UNBOUND_NO"
    (not (slot-boundp об'єкт 'незв'язаний)))
  (д10-спостерігати "SLOT_BOUNDP_BOUND_NIL_YES"
    (slot-boundp об'єкт 'порожнє-значення))
  (д10-спостерігати "SLOT_VALUE_BOUND_NIL_IS_NIL"
    (null (slot-value об'єкт 'порожнє-значення)))
  ;; Відсутній і незв'язаний слот не можна мовчки видавати за NIL.
  (д10-спостерігати "SLOT_BOUNDP_MISSING_ERROR"
    (д10-сигналізує-помилку?
      (lambda () (slot-boundp об'єкт 'відсутній))))
  (д10-спостерігати "SLOT_VALUE_UNBOUND_ERROR"
    (д10-сигналізує-помилку?
      (lambda () (slot-value об'єкт 'незв'язаний))))
  ;; Розв'язування слота не видаляє його та не змінює сусідні слоти.
  (д10-спостерігати "SLOT_MAKUNBOUND_RETURNS_SAME"
    (eq об'єкт (slot-makunbound об'єкт 'порожнє-значення)))
  (д10-спостерігати "SLOT_MAKUNBOUND_EXISTS_AFTER"
    (slot-exists-p об'єкт 'порожнє-значення))
  (д10-спостерігати "SLOT_MAKUNBOUND_NOT_BOUND_AFTER"
    (not (slot-boundp об'єкт 'порожнє-значення)))
  (д10-спостерігати "SLOT_MAKUNBOUND_UNTOUCHED"
    (and (slot-boundp об'єкт 'заповнений)
         (= 7 (slot-value об'єкт 'заповнений))))
  (д10-спостерігати "SLOT_MAKUNBOUND_MISSING_ERROR"
    (д10-сигналізує-помилку?
      (lambda () (slot-makunbound об'єкт 'відсутній))))
  (setf (slot-value об'єкт 'порожнє-значення) nil)
  (д10-спостерігати "SLOT_MAKUNBOUND_REBIND_POSSIBLE"
    (and (slot-boundp об'єкт 'порожнє-значення)
         (null (slot-value об'єкт 'порожнє-значення))))
  ;; CLASS-OF повертає саме об'єкт безпосереднього класу, а не символ
  ;; назви класу й не довільний батьківський клас.
  (д10-спостерігати "CLASS_OF_EXACT_CLASS_OBJECT"
    (eq (class-of об'єкт) (find-class 'д10-оракул-нащадок)))
  (д10-спостерігати "CLASS_OF_NOT_CLASS_SYMBOL"
    (not (eq (class-of об'єкт) 'д10-оракул-нащадок)))
  (д10-спостерігати "CLASS_OF_CHILD_NOT_PARENT"
    (not (eq (class-of об'єкт) (find-class 'д10-оракул-батько)))))

(format t "SUMMARY~CD10-CLOS-SLOT-ORACLE-V1~C~D~%"
        #\Tab #\Tab *д10-спостережень*)
