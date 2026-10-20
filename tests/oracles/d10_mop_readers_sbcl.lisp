;;;; Зовнішній історичний SBCL/MOP-оракул читання, не код СЕНС.
;;;; (role research-only)
;;;; (semantic-authority-change none)
;;;; Джерело: AMOP, розділ 6 / SB-MOP; без кодів D10 чи ратифікації.
;;;; Власні функція спостереження й лічильник тепер мають українські імена.
;;;; Класи, слоти, тестові мітки та форми стандартного Common Lisp не змінено.
(in-package :cl-user)

(defvar *д10-моп-лічильник* 0)
(defun д10-моп-спостерігати (назва виконано)
  (unless виконано
    (error "Порушено контракт дослідного оракула MOP: ~A" назва))
  (incf *д10-моп-лічильник*)
  (format t "OBS~C~A~CPASS~%" #\Tab назва #\Tab))

(defclass д10-моп-батьківський-клас () ((inherited :initform 5)))
(defclass д10-моп-дочірній-клас (д10-моп-батьківський-клас) ((direct :initform 7)))
(defgeneric д10-моп-узагальнена-функція (x))
(defmethod д10-моп-узагальнена-функція ((x integer)) :integer)
(defmethod д10-моп-узагальнена-функція ((x string)) :string)

(unless (find-package :sb-mop)
  (error "Відсутній необхідний дослідний пакет SB-MOP"))

(let* ((батьківський (find-class 'д10-моп-батьківський-клас))
       (дочірній (find-class 'д10-моп-дочірній-клас))
       (узагальнена-функція (symbol-function 'д10-моп-узагальнена-функція)))
  (sb-mop:finalize-inheritance дочірній)
  (let ((порядок (sb-mop:class-precedence-list дочірній))
        (власні-назви (mapcar #'sb-mop:slot-definition-name
                             (sb-mop:class-direct-slots дочірній)))
        (усі-назви (mapcar #'sb-mop:slot-definition-name
                          (sb-mop:class-slots дочірній))))
    (д10-моп-спостерігати "PRECEDENCE_SELF_FIRST" (eq (first порядок) дочірній))
    (д10-моп-спостерігати "PRECEDENCE_ULTIMATE_T"
      (eq (car (last порядок)) (find-class 't)))
    (д10-моп-спостерігати "PRECEDENCE_PARENT_PRESENT" (member батьківський порядок :test #'eq))
    (д10-моп-спостерігати "PRECEDENCE_NO_DUPLICATES"
      (= (length порядок) (length (remove-duplicates порядок :test #'eq))))
    (д10-моп-спостерігати "DIRECT_DECLARED_PRESENT" (member 'direct власні-назви))
    (д10-моп-спостерігати "DIRECT_EXCLUDES_INHERITED" (not (member 'inherited власні-назви)))
    (д10-моп-спостерігати "EFFECTIVE_INCLUDES_INHERITED" (member 'inherited усі-назви))
    (д10-моп-спостерігати "EFFECTIVE_INCLUDES_DIRECT" (member 'direct усі-назви)))
  (let* ((методи (sb-mop:generic-function-methods узагальнена-функція))
         (метод-цілих (find-method узагальнена-функція nil (list (find-class 'integer))))
         (метод-рядків (find-method узагальнена-функція nil (list (find-class 'string)))))
    (д10-моп-спостерігати "METHODS_INITIAL_EXACT_TWO" (= 2 (length методи)))
    (д10-моп-спостерігати "METHODS_EXACT_INTEGER_MEMBER" (member метод-цілих методи :test #'eq))
    (д10-моп-спостерігати "METHODS_EXACT_STRING_MEMBER" (member метод-рядків методи :test #'eq))
    (д10-моп-спостерігати "ARGUMENT_ORDER_SINGLE_X"
      (equal (sb-mop:generic-function-argument-precedence-order узагальнена-функція) '(x)))
    (remove-method узагальнена-функція метод-цілих)
    (let ((залишок (sb-mop:generic-function-methods узагальнена-функція)))
      (д10-моп-спостерігати "REMOVAL_DROPS_ONLY_INTEGER"
        (and (= (length залишок) 1)
             (not (member метод-цілих залишок :test #'eq))))
      (д10-моп-спостерігати "REMOVAL_PRESERVES_STRING"
        (member метод-рядків залишок :test #'eq))))
  (д10-моп-спостерігати "CHILD_CLASS_REMAINS_UNCHANGED"
    (eq (find-class 'д10-моп-дочірній-клас) дочірній)))

(format t "MOP-SUMMARY~C~A~C~D~%" #\Tab "SB-MOP-READER-OBS" #\Tab *д10-моп-лічильник*)
(format t "MOP-DONOR~C~A~C~A~%" #\Tab "SBCL" #\Tab (lisp-implementation-version))
