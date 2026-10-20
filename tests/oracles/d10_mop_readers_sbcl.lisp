;;;; Зовнішній історичний SBCL/MOP-оракул читання, не код СЕНС.
;;;; (role research-only)
;;;; (semantic-authority-change none)
;;;; Джерело: AMOP, розділ 6 / SB-MOP; без кодів D10 чи ратифікації.
(in-package :cl-user)

(defvar *d10-mop-count* 0)
(defun d10-mop-observe (назва виконано)
  (unless виконано
    (error "MOP donor contract failed: ~A" назва))
  (incf *d10-mop-count*)
  (format t "OBS~C~A~CPASS~%" #\Tab назва #\Tab))

(defclass d10-mop-parent () ((inherited :initform 5)))
(defclass d10-mop-child (d10-mop-parent) ((direct :initform 7)))
(defgeneric d10-mop-g (x))
(defmethod d10-mop-g ((x integer)) :integer)
(defmethod d10-mop-g ((x string)) :string)

(unless (find-package :sb-mop)
  (error "Required donor MOP package SB-MOP missing"))

(let* ((батьківський (find-class 'd10-mop-parent))
       (дочірній (find-class 'd10-mop-child))
       (узагальнена-функція (symbol-function 'd10-mop-g)))
  (sb-mop:finalize-inheritance дочірній)
  (let ((порядок (sb-mop:class-precedence-list дочірній))
        (власні-назви (mapcar #'sb-mop:slot-definition-name
                             (sb-mop:class-direct-slots дочірній)))
        (усі-назви (mapcar #'sb-mop:slot-definition-name
                          (sb-mop:class-slots дочірній))))
    (d10-mop-observe "PRECEDENCE_SELF_FIRST" (eq (first порядок) дочірній))
    (d10-mop-observe "PRECEDENCE_ULTIMATE_T"
      (eq (car (last порядок)) (find-class 't)))
    (d10-mop-observe "PRECEDENCE_PARENT_PRESENT" (member батьківський порядок :test #'eq))
    (d10-mop-observe "PRECEDENCE_NO_DUPLICATES"
      (= (length порядок) (length (remove-duplicates порядок :test #'eq))))
    (d10-mop-observe "DIRECT_DECLARED_PRESENT" (member 'direct власні-назви))
    (d10-mop-observe "DIRECT_EXCLUDES_INHERITED" (not (member 'inherited власні-назви)))
    (d10-mop-observe "EFFECTIVE_INCLUDES_INHERITED" (member 'inherited усі-назви))
    (d10-mop-observe "EFFECTIVE_INCLUDES_DIRECT" (member 'direct усі-назви)))
  (let* ((методи (sb-mop:generic-function-methods узагальнена-функція))
         (метод-цілих (find-method узагальнена-функція nil (list (find-class 'integer))))
         (метод-рядків (find-method узагальнена-функція nil (list (find-class 'string)))))
    (d10-mop-observe "METHODS_INITIAL_EXACT_TWO" (= 2 (length методи)))
    (d10-mop-observe "METHODS_EXACT_INTEGER_MEMBER" (member метод-цілих методи :test #'eq))
    (d10-mop-observe "METHODS_EXACT_STRING_MEMBER" (member метод-рядків методи :test #'eq))
    (d10-mop-observe "ARGUMENT_ORDER_SINGLE_X"
      (equal (sb-mop:generic-function-argument-precedence-order узагальнена-функція) '(x)))
    (remove-method узагальнена-функція метод-цілих)
    (let ((залишок (sb-mop:generic-function-methods узагальнена-функція)))
      (d10-mop-observe "REMOVAL_DROPS_ONLY_INTEGER"
        (and (= (length залишок) 1)
             (not (member метод-цілих залишок :test #'eq))))
      (d10-mop-observe "REMOVAL_PRESERVES_STRING"
        (member метод-рядків залишок :test #'eq))))
  (d10-mop-observe "CHILD_CLASS_REMAINS_UNCHANGED"
    (eq (find-class 'd10-mop-child) дочірній)))

(format t "MOP-SUMMARY~C~A~C~D~%" #\Tab "SB-MOP-READER-OBS" #\Tab *d10-mop-count*)
(format t "MOP-DONOR~C~A~C~A~%" #\Tab "SBCL" #\Tab (lisp-implementation-version))
