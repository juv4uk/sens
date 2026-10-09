;;;; Historical CLOS donor oracle only; never SENS code or .sens source.
;;;; The observations are pinned to ANSI Common Lisp / CLOS semantics.
(in-package :cl-user)

(defvar *d10-method-class-observations* 0)

(defun d10-method-class-observe (id truth)
  (unless truth
    (error "D10 CLOS method/class donor oracle failed: ~A" id))
  (incf *d10-method-class-observations*)
  (format t "OBS~C~A~CPASS~%" #\Tab id #\Tab))

(defun d10-method-class-signals-error-p (thunk)
  (handler-case
      (progn (funcall thunk) nil)
    (error () t)))

;;; Exact signature lookup is different from runtime applicability.
(defgeneric d10-method-class-dispatch (x))
(defmethod d10-method-class-dispatch ((x integer)) :integer)
(defmethod d10-method-class-dispatch ((x number)) :number)
(defmethod d10-method-class-dispatch :before ((x integer)) nil)
(defmethod d10-method-class-dispatch ((x string)) :string)

;;; CHANGE-CLASS classes and hook must be global definitions.
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
    ((previous d10-method-class-before)
     (current d10-method-class-after)
     &rest initargs)
  (declare (ignore initargs))
  (setf *d10-change-class-hook-observation*
        (list (slot-value previous 'retained)
              (eq current *d10-change-class-target*))))

(let* ((gf #'d10-method-class-dispatch)
       (integer-specializer (find-class 'integer))
       (number-specializer (find-class 'number))
       (integer-method (find-method gf nil (list integer-specializer)))
       (number-method (find-method gf nil (list number-specializer)))
       (before-method (find-method gf '(:before) (list integer-specializer))))
  (d10-method-class-observe "FIND_METHOD_INTEGER_EXACT"
    (eq integer-method (find-method gf nil (list integer-specializer))))
  (d10-method-class-observe "FIND_METHOD_NUMBER_EXACT"
    (eq number-method (find-method gf nil (list number-specializer))))
  (d10-method-class-observe "FIND_METHOD_BEFORE_QUALIFIER_EXACT"
    (eq before-method (find-method gf '(:before) (list integer-specializer))))
  (d10-method-class-observe "FIND_METHOD_QUALIFIER_DISTINCT"
    (not (eq integer-method before-method)))
  (d10-method-class-observe "FIND_METHOD_MISSING_RETURNS_NIL"
    (null (find-method gf '(:after) (list integer-specializer) nil)))
  (d10-method-class-observe "FIND_METHOD_MISSING_DEFAULT_ERRORS"
    (d10-method-class-signals-error-p
      (lambda () (find-method gf '(:after) (list integer-specializer)))))
  (d10-method-class-observe "FIND_METHOD_SPECIALIZER_ARITY_ERRORS"
    (d10-method-class-signals-error-p
      (lambda () (find-method gf nil nil nil))))
  (d10-method-class-observe "FIND_METHOD_LOOKUP_NOT_DISPATCH_RESULT"
    (and (eq number-method
             (find-method gf nil (list number-specializer)))
         (eq (funcall gf 42) :integer)
         (not (eq number-method integer-method))))

  ;; Removing one method leaves the generic function, siblings and qualifiers.
  (d10-method-class-observe "REMOVE_METHOD_RETURNS_SAME_GF"
    (eq gf (remove-method gf integer-method)))
  (d10-method-class-observe "REMOVE_METHOD_INTEGER_METHOD_ABSENT"
    (null (find-method gf nil (list integer-specializer) nil)))
  (d10-method-class-observe "REMOVE_METHOD_ABSENT_NO_ERROR"
    (eq gf (remove-method gf integer-method)))
  (d10-method-class-observe "REMOVE_METHOD_ABSENT_RETURNS_SAME_GF"
    (eq gf (remove-method gf integer-method)))
  (d10-method-class-observe "REMOVE_METHOD_OTHER_METHOD_STILL_PRESENT"
    (eq number-method (find-method gf nil (list number-specializer))))
  (d10-method-class-observe "REMOVE_METHOD_FALLBACK_DISPATCH"
    (eq (funcall gf 42) :number))
  (d10-method-class-observe "REMOVE_METHOD_BEFORE_STILL_PRESENT"
    (eq before-method (find-method gf '(:before) (list integer-specializer))))

  ;; CHANGE-CLASS preserves identity, common slot value and unbound state.
  (let ((object (make-instance 'd10-method-class-before :retained 41)))
    (setf *d10-change-class-target* object
          *d10-change-class-hook-observation* nil)
    (d10-method-class-observe "CHANGE_CLASS_RETURNS_SAME_INSTANCE"
      (eq object (change-class object 'd10-method-class-after)))
    (d10-method-class-observe "CHANGE_CLASS_INSTANCE_CLASS_CHANGED"
      (eq (class-of object) (find-class 'd10-method-class-after)))
    (d10-method-class-observe "CHANGE_CLASS_RETAINS_COMMON_VALUE"
      (= (slot-value object 'retained) 41))
    (d10-method-class-observe "CHANGE_CLASS_PRESERVES_COMMON_UNBOUND"
      (not (slot-boundp object 'common-unbound)))
    (d10-method-class-observe "CHANGE_CLASS_INITIALIZES_NEW_SLOT"
      (and (slot-boundp object 'new-only)
           (eq (slot-value object 'new-only) :new)))
    (d10-method-class-observe "CHANGE_CLASS_UPDATE_HOOK_RUNS"
      (consp *d10-change-class-hook-observation*))
    (d10-method-class-observe "CHANGE_CLASS_HOOK_SEES_OLD_VALUE"
      (eql (first *d10-change-class-hook-observation*) 41))
    (d10-method-class-observe "CHANGE_CLASS_HOOK_SEES_CURRENT_INSTANCE"
      (eq (second *d10-change-class-hook-observation*) object))))

(format t "SUMMARY~CD10-CLOS-METHOD-CLASS-ORACLE-V1~C~D~%"
        #\Tab #\Tab *d10-method-class-observations*)
