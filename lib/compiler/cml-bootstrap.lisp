; Bounded Lisp-authored compiler frontend witness for juv4uk/cml#153.
; This file emits ordinary Lisp data only. It owns no machine encoding and
; does not duplicate the semantic registry/SID table.
;
; v0 scope:
;   (+ left right)
;     -> (cml-ir-bootstrap-v0
;          (prim + (literal left) (literal right)))
;
; Any other shape is an explicit compiler-front-end rejection record.

(def cml-bootstrap-rejection
  (lambda (reason)
    (list (quote compiler-frontend-rejection) reason)))

(def cml-bootstrap-lower-add
  (lambda (form)
    (cond
      ((atom form) (structural-kind pair)
       (cond
         ((eq (car form) (quote +)) (identity-relation same)
          (cond
            ((eq (length form) 3) (identity-relation same)
             (list
               (quote cml-ir-bootstrap-v0)
               (list
                 (quote prim)
                 (quote +)
                 (list (quote literal) (second form))
                 (list (quote literal) (third form)))))
            ((eq (length form) 3) (identity-relation distinct)
             (cml-bootstrap-rejection (quote arity)))))
         ((eq (car form) (quote +)) (identity-relation distinct)
          (cml-bootstrap-rejection (quote unsupported-form)))))
      ((atom form) (structural-kind atom)
       (cml-bootstrap-rejection (quote unsupported-form)))
      ((atom form) (structural-kind empty-list)
       (cml-bootstrap-rejection (quote unsupported-form))))))
