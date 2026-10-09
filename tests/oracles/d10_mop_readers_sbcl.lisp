;;;; External SBCL/MOP historical reader oracle, NOT executable SENS.
;;;; (role research-only)
;;;; (semantic-authority-change none)
;;;; Donor: AMOP Chapter 6 / SB-MOP; no D10 binary codes or ratification.
(in-package :cl-user)

(defvar *d10-mop-count* 0)
(defun d10-mop-observe (label satisfied)
  (unless satisfied
    (error "MOP donor contract failed: ~A" label))
  (incf *d10-mop-count*)
  (format t "OBS~C~A~CPASS~%" #\Tab label #\Tab))

(defclass d10-mop-parent () ((inherited :initform 5)))
(defclass d10-mop-child (d10-mop-parent) ((direct :initform 7)))
(defgeneric d10-mop-g (x))
(defmethod d10-mop-g ((x integer)) :integer)
(defmethod d10-mop-g ((x string)) :string)

(unless (find-package :sb-mop)
  (error "Required donor MOP package SB-MOP missing"))

(let* ((parent (find-class 'd10-mop-parent))
       (child (find-class 'd10-mop-child))
       (gf (symbol-function 'd10-mop-g)))
  (sb-mop:finalize-inheritance child)
  (let ((precedence (sb-mop:class-precedence-list child))
        (direct-names (mapcar #'sb-mop:slot-definition-name
                             (sb-mop:class-direct-slots child)))
        (all-names (mapcar #'sb-mop:slot-definition-name
                          (sb-mop:class-slots child))))
    (d10-mop-observe "PRECEDENCE_SELF_FIRST" (eq (first precedence) child))
    (d10-mop-observe "PRECEDENCE_ULTIMATE_T"
      (eq (car (last precedence)) (find-class 't)))
    (d10-mop-observe "PRECEDENCE_PARENT_PRESENT" (member parent precedence :test #'eq))
    (d10-mop-observe "PRECEDENCE_NO_DUPLICATES"
      (= (length precedence) (length (remove-duplicates precedence :test #'eq))))
    (d10-mop-observe "DIRECT_DECLARED_PRESENT" (member 'direct direct-names))
    (d10-mop-observe "DIRECT_EXCLUDES_INHERITED" (not (member 'inherited direct-names)))
    (d10-mop-observe "EFFECTIVE_INCLUDES_INHERITED" (member 'inherited all-names))
    (d10-mop-observe "EFFECTIVE_INCLUDES_DIRECT" (member 'direct all-names)))
  (let* ((methods (sb-mop:generic-function-methods gf))
         (integer-method (find-method gf nil (list (find-class 'integer))))
         (string-method (find-method gf nil (list (find-class 'string)))))
    (d10-mop-observe "METHODS_INITIAL_EXACT_TWO" (= 2 (length methods)))
    (d10-mop-observe "METHODS_EXACT_INTEGER_MEMBER" (member integer-method methods :test #'eq))
    (d10-mop-observe "METHODS_EXACT_STRING_MEMBER" (member string-method methods :test #'eq))
    (d10-mop-observe "ARGUMENT_ORDER_SINGLE_X"
      (equal (sb-mop:generic-function-argument-precedence-order gf) '(x)))
    (remove-method gf integer-method)
    (let ((remaining (sb-mop:generic-function-methods gf)))
      (d10-mop-observe "REMOVAL_DROPS_ONLY_INTEGER"
        (and (= (length remaining) 1)
             (not (member integer-method remaining :test #'eq))))
      (d10-mop-observe "REMOVAL_PRESERVES_STRING"
        (member string-method remaining :test #'eq))))
  (d10-mop-observe "CHILD_CLASS_REMAINS_UNCHANGED"
    (eq (find-class 'd10-mop-child) child)))

(format t "MOP-SUMMARY~C~A~C~D~%" #\Tab "SB-MOP-READER-OBS" #\Tab *d10-mop-count*)
(format t "MOP-DONOR~C~A~C~A~%" #\Tab "SBCL" #\Tab (lisp-implementation-version))
