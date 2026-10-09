;;;; D10 source-donor oracle; Common Lisp names are historical reference only.
;;;; (role research-only)
;;;; (semantic-authority-change none)
;;;; Never SENS source, never executable .sens; no D10 bit coordinates.
(in-package :cl-user)

(defvar *d10-observations* 0)

(defun d10-observe (id truth)
  (unless truth
    (error "D10 donor oracle failed: ~A" id))
  (incf *d10-observations*)
  (format t "OBS~C~A~CPASS~%" #\Tab id #\Tab))

(defun d10-signals-error-p (thunk)
  (handler-case
      (progn (funcall thunk) nil)
    (error () t)))

(defclass d10-oracle-parent () ())
(defclass d10-oracle-child (d10-oracle-parent)
  ((a)
   (b :initform nil)
   (c :initform 7)))

(let ((object (make-instance 'd10-oracle-child)))
  ;; Three distinct states: absent, present-unbound, present-bound-to-NIL.
  (d10-observe "SLOT_EXISTS_UNBOUND" (slot-exists-p object 'a))
  (d10-observe "SLOT_EXISTS_BOUND_NIL" (slot-exists-p object 'b))
  (d10-observe "SLOT_EXISTS_ABSENT_NO" (not (slot-exists-p object 'z)))
  (d10-observe "SLOT_BOUNDP_UNBOUND_NO" (not (slot-boundp object 'a)))
  (d10-observe "SLOT_BOUNDP_BOUND_NIL_YES" (slot-boundp object 'b))
  (d10-observe "SLOT_VALUE_BOUND_NIL_IS_NIL" (null (slot-value object 'b)))
  ;; Missing-slot and unbound-slot are NOT silent NIL answers.
  (d10-observe "SLOT_BOUNDP_MISSING_ERROR"
    (d10-signals-error-p (lambda () (slot-boundp object 'z))))
  (d10-observe "SLOT_VALUE_UNBOUND_ERROR"
    (d10-signals-error-p (lambda () (slot-value object 'a))))
  ;; Unbinding changes boundness but does not remove a slot or affect peers.
  (d10-observe "SLOT_MAKUNBOUND_RETURNS_SAME"
    (eq object (slot-makunbound object 'b)))
  (d10-observe "SLOT_MAKUNBOUND_EXISTS_AFTER"
    (slot-exists-p object 'b))
  (d10-observe "SLOT_MAKUNBOUND_NOT_BOUND_AFTER"
    (not (slot-boundp object 'b)))
  (d10-observe "SLOT_MAKUNBOUND_UNTOUCHED"
    (and (slot-boundp object 'c)
         (= 7 (slot-value object 'c))))
  (d10-observe "SLOT_MAKUNBOUND_MISSING_ERROR"
    (d10-signals-error-p (lambda () (slot-makunbound object 'z))))
  (setf (slot-value object 'b) nil)
  (d10-observe "SLOT_MAKUNBOUND_REBIND_POSSIBLE"
    (and (slot-boundp object 'b) (null (slot-value object 'b))))
  ;; CLASS-OF returns the direct class metaobject, not a class-name symbol
  ;; and not an arbitrary superclass.
  (d10-observe "CLASS_OF_EXACT_CLASS_OBJECT"
    (eq (class-of object) (find-class 'd10-oracle-child)))
  (d10-observe "CLASS_OF_NOT_CLASS_SYMBOL"
    (not (eq (class-of object) 'd10-oracle-child)))
  (d10-observe "CLASS_OF_CHILD_NOT_PARENT"
    (not (eq (class-of object) (find-class 'd10-oracle-parent)))))

(format t "SUMMARY~CD10-CLOS-SLOT-ORACLE-V1~C~D~%"
        #\Tab #\Tab *d10-observations*)
