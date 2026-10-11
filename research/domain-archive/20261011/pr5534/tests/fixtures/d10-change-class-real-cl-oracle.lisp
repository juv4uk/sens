;;;; Independent ANSI Common Lisp reference witness, not the SENS runtime.
(defclass d10-change-class-a ()
  ((shared :initarg :shared :accessor d10-change-class-shared)))

(defclass d10-change-class-b ()
  ((shared :initarg :shared :accessor d10-change-class-shared)
   (new-slot :initarg :new-slot :initform :new-default
             :accessor d10-change-class-new-slot)))

(let* ((object (make-instance 'd10-change-class-a :shared 7))
       (identity-before object))
  (change-class object 'd10-change-class-b)
  (assert (eq object identity-before))
  (assert (eq (class-of object) (find-class 'd10-change-class-b)))
  (assert (= (d10-change-class-shared object) 7))
  (assert (eq (d10-change-class-new-slot object) :new-default)))

(let* ((object (make-instance 'd10-change-class-a))
       (identity-before object))
  (assert (not (slot-boundp object 'shared)))
  (change-class object 'd10-change-class-b)
  (assert (eq object identity-before))
  (assert (not (slot-boundp object 'shared))))

(format t "D10-CHANGE-CLASS-REAL-CLOS-ORACLE PASS~%")
