;;; Source-backed executable witness for Common Lisp ADJUST-ARRAY laws.
;;; Runs on SBCL; it is not an oracle for the historical MacLisp implementation.
(defun witness (name condition)
  (unless condition (error "D10 ADJUST-ARRAY witness failed: ~A" name))
  (format t "PASS ~A~%" name))

;; Adjustable arrays preserve object identity under adjustment.
(let* ((a (make-array 2 :adjustable t :initial-contents '(alpha beta)))
       (result (adjust-array a 4 :initial-element :new)))
  (witness "adjustable-array-identity" (eq result a))
  (witness "in-bounds-elements-preserved"
           (and (eq (aref result 0) 'alpha)
                (eq (aref result 1) 'beta)))
  (witness "new-tail-initialized"
           (and (eq (aref result 2) :new) (eq (aref result 3) :new))))

;; If an implementation returns a distinct array, the original must stay unchanged.
(let* ((a (make-array 3 :initial-contents '(alpha beta gamma)))
       (before (copy-seq a))
       (result (adjust-array a 2)))
  (witness "adjust-result-dimensions" (= (array-total-size result) 2))
  (witness "distinct-result-preserves-original"
           (or (eq result a) (equalp a before))))

;; INITIAL-CONTENTS is a replacement, not preservation of old contents.
(let* ((a (make-array 2 :adjustable t :initial-contents '(old-a old-b)))
       (result (adjust-array a 2 :initial-contents '(new-a new-b))))
  (witness "initial-contents-replaces-old-data"
           (and (eq (aref result 0) 'new-a) (eq (aref result 1) 'new-b))))

;; FILL-POINTER T tracks the adjusted vector's new size.
(let* ((v (make-array 2 :adjustable t :fill-pointer 1
                      :initial-contents '(alpha beta)))
       (result (adjust-array v 4 :fill-pointer t :initial-element :extra)))
  (witness "fill-pointer-t-tracks-size"
           (and (eq result v) (= (fill-pointer result) 4))))

;; Displaced arrays share backing storage and report the immediate base + offset.
(let* ((base (make-array 6 :initial-contents '(0 1 2 3 4 5)))
       (src (make-array 2 :adjustable t :initial-contents '(8 9)))
       (result (adjust-array src 3 :displaced-to base
                             :displaced-index-offset 2)))
  (multiple-value-bind (backing offset) (array-displacement result)
    (witness "displacement-base-and-offset"
             (and (eq backing base) (= offset 2))))
  (setf (aref result 0) 77)
  (witness "displacement-alias-visible" (= (aref base 2) 77)))

;; Displacement-chain semantics retain the intermediate object after adjustment.
(let* ((c (make-array 8 :initial-contents '(0 1 2 3 4 5 6 7)))
       (b (make-array 5 :adjustable t :displaced-to c
                      :displaced-index-offset 1))
       (a (make-array 3 :displaced-to b :displaced-index-offset 1)))
  (adjust-array b 4 :initial-element 99)
  (multiple-value-bind (backing offset) (array-displacement a)
    (witness "chain-keeps-immediate-middle"
             (and (eq backing b) (= offset 1))))
  (setf (aref a 0) 88)
  (witness "chain-mutates-adjusted-middle" (= (aref b 1) 88)))

(format t "D10-ADJUST-ARRAY-SBCL-ORACLE: PASS~%")
