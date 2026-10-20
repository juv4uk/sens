;;;; Історичний CLOS-оракул Д10: лише дослідницький еталон, не код СЕНС.
;;;; Спостереження спираються на ANSI Common Lisp і закони CLOS.
;;;; Власні назви слотів українські; імена стандартних операторів і контрольні мітки незмінні.
(in-package :cl-user)

(defvar *д10-клос-кількість-спостережень* 0)

(defun д10-клос-спостерігати (назва умова)
  (unless умова
    (error "D10 CLOS method/class donor oracle failed: ~A" назва))
  (incf *д10-клос-кількість-спостережень*)
  (format t "OBS~C~A~CPASS~%" #\Tab назва #\Tab))

(defun д10-клос-сигналізує-помилку? (дія)
  (handler-case
      (progn (funcall дія) nil)
    (error () t)))

;;; Точне знаходження методу за сигнатурою не тотожне диспетчеризації виклику.
(defgeneric д10-клос-диспетчеризувати (значення))
(defmethod д10-клос-диспетчеризувати ((значення integer)) :integer)
(defmethod д10-клос-диспетчеризувати ((значення number)) :number)
(defmethod д10-клос-диспетчеризувати :before ((значення integer)) nil)
(defmethod д10-клос-диспетчеризувати ((значення string)) :string)

;;; Класи та метод оновлення для CHANGE-CLASS визначено на верхньому рівні.
(defclass д10-клос-попередній-клас ()
  ((збережений :initarg :збережений)
   (спільний-без-значення)
   (лише-попередній :initform :old)))
(defclass д10-клос-наступний-клас ()
  ((збережений)
   (спільний-без-значення)
   (лише-наступний :initform :new)))

(defvar *д10-ціль-перетворення-класу* nil)
(defvar *д10-спостереження-перетворення-класу* nil)
(defmethod update-instance-for-different-class :before
    ((попередній д10-клос-попередній-клас)
     (поточний д10-клос-наступний-клас)
     &rest параметри-ініціалізації)
  (declare (ignore параметри-ініціалізації))
  (setf *д10-спостереження-перетворення-класу*
        (list (slot-value попередній 'збережений)
              (eq поточний *д10-ціль-перетворення-класу*))))

(let* ((узагальнена-функція #'д10-клос-диспетчеризувати)
       (спеціалізатор-цілих (find-class 'integer))
       (спеціалізатор-чисел (find-class 'number))
       (метод-цілих (find-method узагальнена-функція nil (list спеціалізатор-цілих)))
       (метод-чисел (find-method узагальнена-функція nil (list спеціалізатор-чисел)))
       (попередній-метод (find-method узагальнена-функція '(:before) (list спеціалізатор-цілих))))
  (д10-клос-спостерігати "FIND_METHOD_INTEGER_EXACT"
    (eq метод-цілих (find-method узагальнена-функція nil (list спеціалізатор-цілих))))
  (д10-клос-спостерігати "FIND_METHOD_NUMBER_EXACT"
    (eq метод-чисел (find-method узагальнена-функція nil (list спеціалізатор-чисел))))
  (д10-клос-спостерігати "FIND_METHOD_BEFORE_QUALIFIER_EXACT"
    (eq попередній-метод (find-method узагальнена-функція '(:before) (list спеціалізатор-цілих))))
  (д10-клос-спостерігати "FIND_METHOD_QUALIFIER_DISTINCT"
    (not (eq метод-цілих попередній-метод)))
  (д10-клос-спостерігати "FIND_METHOD_MISSING_RETURNS_NIL"
    (null (find-method узагальнена-функція '(:after) (list спеціалізатор-цілих) nil)))
  (д10-клос-спостерігати "FIND_METHOD_MISSING_DEFAULT_ERRORS"
    (д10-клос-сигналізує-помилку?
      (lambda () (find-method узагальнена-функція '(:after) (list спеціалізатор-цілих)))))
  (д10-клос-спостерігати "FIND_METHOD_SPECIALIZER_ARITY_ERRORS"
    (д10-клос-сигналізує-помилку?
      (lambda () (find-method узагальнена-функція nil nil nil))))
  (д10-клос-спостерігати "FIND_METHOD_LOOKUP_NOT_DISPATCH_RESULT"
    (and (eq метод-чисел
             (find-method узагальнена-функція nil (list спеціалізатор-чисел)))
         (eq (funcall узагальнена-функція 42) :integer)
         (not (eq метод-чисел метод-цілих))))

  ;; Видалення методу зберігає узагальнену функцію, інші методи й кваліфікатори.
  (д10-клос-спостерігати "REMOVE_METHOD_RETURNS_SAME_GF"
    (eq узагальнена-функція (remove-method узагальнена-функція метод-цілих)))
  (д10-клос-спостерігати "REMOVE_METHOD_INTEGER_METHOD_ABSENT"
    (null (find-method узагальнена-функція nil (list спеціалізатор-цілих) nil)))
  (д10-клос-спостерігати "REMOVE_METHOD_ABSENT_NO_ERROR"
    (eq узагальнена-функція (remove-method узагальнена-функція метод-цілих)))
  (д10-клос-спостерігати "REMOVE_METHOD_ABSENT_RETURNS_SAME_GF"
    (eq узагальнена-функція (remove-method узагальнена-функція метод-цілих)))
  (д10-клос-спостерігати "REMOVE_METHOD_OTHER_METHOD_STILL_PRESENT"
    (eq метод-чисел (find-method узагальнена-функція nil (list спеціалізатор-чисел))))
  (д10-клос-спостерігати "REMOVE_METHOD_FALLBACK_DISPATCH"
    (eq (funcall узагальнена-функція 42) :number))
  (д10-клос-спостерігати "REMOVE_METHOD_BEFORE_STILL_PRESENT"
    (eq попередній-метод (find-method узагальнена-функція '(:before) (list спеціалізатор-цілих))))

  ;; CHANGE-CLASS зберігає тотожність об'єкта, значення спільного слота
  ;; та стан незв'язаного спільного слота.
  (let ((об'єкт (make-instance 'д10-клос-попередній-клас :збережений 41)))
    (setf *д10-ціль-перетворення-класу* об'єкт
          *д10-спостереження-перетворення-класу* nil)
    (д10-клос-спостерігати "CHANGE_CLASS_RETURNS_SAME_INSTANCE"
      (eq об'єкт (change-class об'єкт 'д10-клос-наступний-клас)))
    (д10-клос-спостерігати "CHANGE_CLASS_INSTANCE_CLASS_CHANGED"
      (eq (class-of об'єкт) (find-class 'д10-клос-наступний-клас)))
    (д10-клос-спостерігати "CHANGE_CLASS_RETAINS_COMMON_VALUE"
      (= (slot-value об'єкт 'збережений) 41))
    (д10-клос-спостерігати "CHANGE_CLASS_PRESERVES_COMMON_UNBOUND"
      (not (slot-boundp об'єкт 'спільний-без-значення)))
    (д10-клос-спостерігати "CHANGE_CLASS_INITIALIZES_NEW_SLOT"
      (and (slot-boundp об'єкт 'лише-наступний)
           (eq (slot-value об'єкт 'лише-наступний) :new)))
    (д10-клос-спостерігати "CHANGE_CLASS_UPDATE_HOOK_RUNS"
      (consp *д10-спостереження-перетворення-класу*))
    (д10-клос-спостерігати "CHANGE_CLASS_HOOK_SEES_OLD_VALUE"
      (eql (first *д10-спостереження-перетворення-класу*) 41))
    (д10-клос-спостерігати "CHANGE_CLASS_HOOK_SEES_CURRENT_INSTANCE"
      (second *д10-спостереження-перетворення-класу*))))

(format t "SUMMARY~CD10-CLOS-METHOD-CLASS-ORACLE-V1~C~D~%"
        #\Tab #\Tab *д10-клос-кількість-спостережень*)
