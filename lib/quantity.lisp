; lib/quantity.lisp — scientific quantities and constants as finite Lisp data
;
; This is deliberately a library layer, not a new evaluator primitive.
; It distinguishes a bare numeric value from a quantity with a unit and from
; a scientific constant with epistemic metadata/provenance.
;
; Versioned shapes:
;
;   (dimension/1 BASE EXPONENT)
;   (unit/1 DIMENSION...)
;   (quantity/1 VALUE UNIT)
;   (science-source/1 AUTHORITY EDITION)
;   (scientific-constant/1 NAME QUANTITY STATUS KIND SYSTEM SOURCE)
;
; A dimension is a named Lisp term rather than an anonymous pair so the same
; finite data can pass through Advice Taker's existing knowledge grammar.

(def *dimension-schema* (quote dimension/1))
(def *unit-schema* (quote unit/1))
(def *quantity-schema* (quote quantity/1))
(def *science-source-schema* (quote science-source/1))
(def *scientific-constant-schema* (quote scientific-constant/1))

(def science-proper-list?
  (lambda (x)
    (cond
      ((atom? x)
       (cond
         ((eq? x (quote ())) t)
         (t (quote ()))))
      (t (science-proper-list? (cdr x))))))

(def science-sixth
  (lambda (values)
    (car (cdr (cdr (cdr (cdr (cdr values))))))))

(def science-seventh
  (lambda (values)
    (car (cdr (cdr (cdr (cdr (cdr (cdr values)))))))))

(def make-dimension
  (lambda (base exponent)
    (list *dimension-schema* base exponent)))

(def dimension?
  (lambda (x)
    (cond
      ((atom? x) (quote ()))
      ((eq? (science-proper-list? x) (quote ())) (quote ()))
      ((eq? (= (length x) 3) (quote ())) (quote ()))
      ((eq? (car x) *dimension-schema*)
       (cond
         ((eq? (symbol? (second x)) (quote ())) (quote ()))
         ((atom? (third x)) t)
         (t (quote ()))))
      (t (quote ())))))

(def dimension-base
  (lambda (dimension) (second dimension)))

(def dimension-exponent
  (lambda (dimension) (third dimension)))

(def science-dimensions-valid?
  (lambda (dimensions)
    (cond
      ((atom? dimensions)
       (cond
         ((eq? dimensions (quote ())) t)
         (t (quote ()))))
      ((dimension? (car dimensions))
       (science-dimensions-valid? (cdr dimensions)))
      (t (quote ())))))

(def make-unit
  (lambda (dimensions)
    (cons *unit-schema* dimensions)))

(def unit?
  (lambda (x)
    (cond
      ((atom? x) (quote ()))
      ((eq? (science-proper-list? x) (quote ())) (quote ()))
      ((eq? (car x) *unit-schema*)
       (science-dimensions-valid? (cdr x)))
      (t (quote ())))))

(def unit-dimensions
  (lambda (unit) (cdr unit)))

(def make-quantity
  (lambda (value unit)
    (list *quantity-schema* value unit)))

(def quantity?
  (lambda (x)
    (cond
      ((atom? x) (quote ()))
      ((eq? (science-proper-list? x) (quote ())) (quote ()))
      ((eq? (= (length x) 3) (quote ())) (quote ()))
      ((eq? (car x) *quantity-schema*)
       (unit? (third x)))
      (t (quote ())))))

(def quantity-value
  (lambda (quantity) (second quantity)))

(def quantity-unit
  (lambda (quantity) (third quantity)))

; Мінімальна точна алгебра одиниць. Вона не вводить нових примітивів:
; показники вимірностей додаються/віднімаються звичайною точною арифметикою
; my-lisp, а нульовий показник видаляє вимірність з результату.
(def science-add-dimension
  (lambda (dimension dimensions)
    (cond
      ((atom? dimensions)
       (cond
         ((= (dimension-exponent dimension) 0) 1 (quote ()))
         (t (list dimension))))
      ((eq? (dimension-base dimension)
           (dimension-base (car dimensions)))
       (let ((sum
               (+ (dimension-exponent dimension)
                  (dimension-exponent (car dimensions)))))
         (cond
           ((= sum 0) 1 (cdr dimensions))
           (t
            (cons
              (make-dimension (dimension-base dimension) sum)
              (cdr dimensions))))))
      (t
       (cons
         (car dimensions)
         (science-add-dimension dimension (cdr dimensions)))))))

(def science-merge-dimensions
  (lambda (from into)
    (cond
      ((atom? from) into)
      (t
       (science-merge-dimensions
         (cdr from)
         (science-add-dimension (car from) into))))))

(def science-negate-dimensions
  (lambda (dimensions)
    (cond
      ((atom? dimensions) (quote ()))
      (t
       (cons
         (make-dimension
           (dimension-base (car dimensions))
           (- 0 (dimension-exponent (car dimensions))))
         (science-negate-dimensions (cdr dimensions)))))))

(def unit-product
  (lambda (left right)
    (make-unit
      (science-merge-dimensions
        (unit-dimensions right)
        (unit-dimensions left)))))

(def unit-quotient
  (lambda (left right)
    (make-unit
      (science-merge-dimensions
        (science-negate-dimensions (unit-dimensions right))
        (unit-dimensions left)))))

(def quantity-product
  (lambda (left right)
    (make-quantity
      (* (quantity-value left) (quantity-value right))
      (unit-product (quantity-unit left) (quantity-unit right)))))

(def quantity-quotient
  (lambda (left right)
    (make-quantity
      (/ (quantity-value left) (quantity-value right))
      (unit-quotient (quantity-unit left) (quantity-unit right)))))

(def make-science-source
  (lambda (authority edition)
    (list *science-source-schema* authority edition)))

(def science-source?
  (lambda (x)
    (cond
      ((atom? x) (quote ()))
      ((eq? (science-proper-list? x) (quote ())) (quote ()))
      ((eq? (= (length x) 3) (quote ())) (quote ()))
      ((eq? (car x) *science-source-schema*)
       (cond
         ((eq? (symbol? (second x)) (quote ())) (quote ()))
         ((atom? (third x)) t)
         (t (quote ()))))
      (t (quote ())))))

(def scientific-constant-status-valid?
  (lambda (status)
    (cond
      ((eq? status (quote exact-by-definition)) t)
      ((eq? status (quote exact-derived)) t)
      ((eq? status (quote measured)) t)
      (t (quote ())))))

(def scientific-constant-kind-valid?
  (lambda (kind)
    (cond
      ((eq? kind (quote physical-defining)) t)
      ((eq? kind (quote physical-derived)) t)
      ((eq? kind (quote physical-measured)) t)
      ((eq? kind (quote mathematical)) t)
      (t (quote ())))))

(def make-scientific-constant
  (lambda (name quantity status kind system source)
    (list
      *scientific-constant-schema*
      name
      quantity
      status
      kind
      system
      source)))

(def scientific-constant?
  (lambda (x)
    (cond
      ((atom? x) (quote ()))
      ((eq? (science-proper-list? x) (quote ())) (quote ()))
      ((= (length x) 7) 0 (quote ()))
      ((eq? (car x) *scientific-constant-schema*)
       (cond
         ((eq? (symbol? (second x)) (quote ())) (quote ()))
         ((eq? (quantity? (third x)) (quote ())) (quote ()))
         ((eq? (scientific-constant-status-valid? (fourth x)) (quote ())) (quote ()))
         ((eq? (scientific-constant-kind-valid? (fifth x)) (quote ())) (quote ()))
         ((eq? (symbol? (science-sixth x)) (quote ())) (quote ()))
         ((eq? (science-source? (science-seventh x)) (quote ())) (quote ()))
         (t t)))
      (t (quote ())))))

(def scientific-constant-name
  (lambda (constant) (second constant)))

(def scientific-constant-quantity
  (lambda (constant) (third constant)))

(def scientific-constant-value
  (lambda (constant)
    (quantity-value (scientific-constant-quantity constant))))

(def scientific-constant-unit
  (lambda (constant)
    (quantity-unit (scientific-constant-quantity constant))))

(def scientific-constant-status
  (lambda (constant) (fourth constant)))

(def scientific-constant-kind
  (lambda (constant) (fifth constant)))

(def scientific-constant-system
  (lambda (constant) (science-sixth constant)))

(def scientific-constant-source
  (lambda (constant) (science-seventh constant)))

; Pure projection into the existing knowledge clause format. It does not write
; *knowledge-journal*: callers must still pass the returned batch through the
; explicit advise-all admission boundary. A malformed constant projects to ().
(def scientific-constant->clauses
  (lambda (constant)
    (cond
      ((eq? (scientific-constant? constant) (quote ())) (quote ()))
      (t
       (let ((name (scientific-constant-name constant)))
         (list
           (list (list (quote scientific-constant) name))
           (list
             (list (quote constant-value)
                   name
                   (scientific-constant-value constant)))
           (list
             (list (quote constant-unit)
                   name
                   (scientific-constant-unit constant)))
           (list
             (list (quote constant-status)
                   name
                   (scientific-constant-status constant)))
           (list
             (list (quote constant-kind)
                   name
                   (scientific-constant-kind constant)))
           (list
             (list (quote constant-system)
                   name
                   (scientific-constant-system constant)))
           (list
             (list (quote constant-source)
                   name
                   (scientific-constant-source constant)))))))))
