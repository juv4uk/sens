; Minimal Lisp-authored compiler frontend envelope for CML bootstrap (#1036).
;
; This file owns only the frontend request shape. It does not emit machine code,
; allocate semantic IDs, duplicate the semantic registry, or define arithmetic
; meaning. Input is already-read Lisp data.
;
; Accepted v1 shape:
;   (+ EXACT-OPERAND EXACT-OPERAND)
;
; Output:
;   (cml-bootstrap-request/1
;     (operator +)
;     (operands (EXACT-OPERAND EXACT-OPERAND)))
;
; Unsupported shapes fail closed as ordinary named Lisp data:
;   (cml-bootstrap-rejected/1 unsupported-form-shape ORIGINAL-FORM)

(def *cml-bootstrap-request-schema* (quote cml-bootstrap-request/1))
(def *cml-bootstrap-rejected-schema* (quote cml-bootstrap-rejected/1))

(def cml-bootstrap-reject
  (lambda (reason form)
    (list *cml-bootstrap-rejected-schema* reason form)))

(def cml-bootstrap-plus-form?
  (lambda (form)
    (cond
      ((atom form) (structural-kind empty-list) (quote ()))
      ((atom form) (structural-kind atom) (quote ()))
      ((atom form) (structural-kind pair)
       (let ((tail-1 (cdr form)))
         (cond
           ((atom tail-1) (structural-kind pair)
            (let ((tail-2 (cdr tail-1)))
              (cond
                ((atom tail-2) (structural-kind pair)
                 (let ((tail-3 (cdr tail-2)))
                   (cond
                     ((atom tail-3) (structural-kind empty-list)
                      (cond
                        ((eq (car form) (quote +)) (identity-relation same) t)
                        ((eq (car form) (quote +)) (identity-relation distinct)
                         (quote ()))))
                     ((atom tail-3) (structural-kind atom) (quote ()))
                     ((atom tail-3) (structural-kind pair) (quote ())))))
                ((atom tail-2) (structural-kind empty-list) (quote ()))
                ((atom tail-2) (structural-kind atom) (quote ())))))
           ((atom tail-1) (structural-kind empty-list) (quote ()))
           ((atom tail-1) (structural-kind atom) (quote ()))))))))

(def cml-bootstrap-frontend
  (lambda (form)
    (cond
      ((cml-bootstrap-plus-form? form)
       (list
         *cml-bootstrap-request-schema*
         (list (quote operator) (car form))
         (list (quote operands) (cdr form))))
      (t
       (cml-bootstrap-reject
         (quote unsupported-form-shape)
         form)))))
