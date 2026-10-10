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

(00001001 *dimension-schema* (00000001 dimension/1))
(00001001 *unit-schema* (00000001 unit/1))
(00001001 *quantity-schema* (00000001 quantity/1))
(00001001 *science-source-schema* (00000001 science-source/1))
(00001001 *scientific-constant-schema* (00000001 scientific-constant/1))

(00001001 science-proper-list?
  (00001000 (x)
    (00000111
      ; Pair cells recurse through CDR; never pass a compound value to EQ.
      ((0100 (00000010 x))
       (science-proper-list? (00000110 x)))
      ; EQ is atom-only. This branch runs only when X itself is an atom.
      ((00000010 x) 
       (00000011 x (00000001 ())))
      )))

(00001001 science-sixth
  (00001000 (values)
    (00000101 (00000110 (00000110 (00000110 (00000110 (00000110 values))))))))

(00001001 science-seventh
  (00001000 (values)
    (00000101 (00000110 (00000110 (00000110 (00000110 (00000110 (00000110 values)))))))))

(00001001 make-dimension
  (00001000 (base exponent)
    (00100111 *dimension-schema* base exponent)))

(00001001 dimension?
  (00001000 (x)
    (00000111
      
      ((00000010 x)  (00000001 ()))
      ((00000011 (science-proper-list? x) (00000001 ())) (00000001 ()))
      ((00000011 (00011100 (00101000 x) 3) (00000001 ())) (00000001 ()))
      ((00000011 (00000101 x) *dimension-schema*)
       (00000111
         ((00000011 (00100011 (00101111 x)) (00000001 ())) (00000001 ()))
         
         ((00000010 (00110000 x))  t)
         ))
      )))

(00001001 dimension-base
  (00001000 (dimension) (00101111 dimension)))

(00001001 dimension-exponent
  (00001000 (dimension) (00110000 dimension)))

(00001001 science-dimensions-valid?
  (00001000 (dimensions)
    (00000111
      
      ((00000010 dimensions)  (00000111
         ((00000011 dimensions (00000001 ())) t)
         ))
      ((dimension? (00000101 dimensions))
       (science-dimensions-valid? (00000110 dimensions)))
      )))

(00001001 make-unit
  (00001000 (dimensions)
    (00000100 *unit-schema* dimensions)))

(00001001 unit?
  (00001000 (x)
    (00000111
      
      ((00000010 x)  (00000001 ()))
      ((00000011 (science-proper-list? x) (00000001 ())) (00000001 ()))
      ((00000011 (00000101 x) *unit-schema*)
       (science-dimensions-valid? (00000110 x)))
      )))

(00001001 unit-dimensions
  (00001000 (unit) (00000110 unit)))

(00001001 make-quantity
  (00001000 (value unit)
    (00100111 *quantity-schema* value unit)))

(00001001 quantity?
  (00001000 (x)
    (00000111
      
      ((00000010 x)  (00000001 ()))
      ((00000011 (science-proper-list? x) (00000001 ())) (00000001 ()))
      ((00000011 (00011100 (00101000 x) 3) (00000001 ())) (00000001 ()))
      ((00000011 (00000101 x) *quantity-schema*)
       (unit? (00110000 x)))
      )))

(00001001 quantity-value
  (00001000 (quantity) (00101111 quantity)))

(00001001 quantity-unit
  (00001000 (quantity) (00110000 quantity)))

; Мінімальна точна алгебра одиниць. Вона не вводить нових примітивів:
; показники вимірностей додаються/віднімаються звичайною точною арифметикою
; my-lisp, а нульовий показник видаляє вимірність з результату.
(00001001 science-add-dimension
  (00001000 (dimension dimensions)
    (00000111
      
      ((00000010 dimensions)  (00000111
         ((00011100 (dimension-exponent dimension) 0)  (00000001 ()))
         (1 (00100111 dimension))))
      ((00000011 (dimension-base dimension)
           (dimension-base (00000101 dimensions)))
       (10011100 ((sum
               (00001100 (dimension-exponent dimension)
                  (dimension-exponent (00000101 dimensions)))))
         (00000111
           ((00011100 sum 0)  (00000110 dimensions))
           (1
            (00000100
              (make-dimension (dimension-base dimension) sum)
              (00000110 dimensions))))))
      (1
       (00000100
         (00000101 dimensions)
         (science-add-dimension dimension (00000110 dimensions)))))))

(00001001 science-merge-dimensions
  (00001000 (from into)
    (00000111
      
      ((00000010 from)  into)
      (1
       (science-merge-dimensions
         (00000110 from)
         (science-add-dimension (00000101 from) into))))))

(00001001 science-negate-dimensions
  (00001000 (dimensions)
    (00000111
      
      ((00000010 dimensions)  (00000001 ()))
      (1
       (00000100
         (make-dimension
           (dimension-base (00000101 dimensions))
           (00001101 0 (dimension-exponent (00000101 dimensions))))
         (science-negate-dimensions (00000110 dimensions)))))))

(00001001 unit-product
  (00001000 (left right)
    (make-unit
      (science-merge-dimensions
        (unit-dimensions right)
        (unit-dimensions left)))))

(00001001 unit-quotient
  (00001000 (left right)
    (make-unit
      (science-merge-dimensions
        (science-negate-dimensions (unit-dimensions right))
        (unit-dimensions left)))))

(00001001 quantity-product
  (00001000 (left right)
    (make-quantity
      (00001110 (quantity-value left) (quantity-value right))
      (unit-product (quantity-unit left) (quantity-unit right)))))

(00001001 quantity-quotient
  (00001000 (left right)
    (make-quantity
      (00001111 (quantity-value left) (quantity-value right))
      (unit-quotient (quantity-unit left) (quantity-unit right)))))

(00001001 make-science-source
  (00001000 (authority edition)
    (00100111 *science-source-schema* authority edition)))

(00001001 science-source?
  (00001000 (x)
    (00000111
      
      ((00000010 x)  (00000001 ()))
      ((00000011 (science-proper-list? x) (00000001 ())) (00000001 ()))
      ((00000011 (00011100 (00101000 x) 3) (00000001 ())) (00000001 ()))
      ((00000011 (00000101 x) *science-source-schema*)
       (00000111
         ((00000011 (00100011 (00101111 x)) (00000001 ())) (00000001 ()))
         
         ((00000010 (00110000 x))  t)
         ))
      )))

(00001001 scientific-constant-status-valid?
  (00001000 (status)
    (00000111
      ((00000011 status (00000001 exact-by-definition)) t)
      ((00000011 status (00000001 exact-derived)) t)
      ((00000011 status (00000001 measured)) t)
      )))

(00001001 scientific-constant-kind-valid?
  (00001000 (kind)
    (00000111
      ((00000011 kind (00000001 physical-defining)) t)
      ((00000011 kind (00000001 physical-derived)) t)
      ((00000011 kind (00000001 physical-measured)) t)
      ((00000011 kind (00000001 mathematical)) t)
      )))

(00001001 make-scientific-constant
  (00001000 (name quantity status kind system source)
    (00100111
      *scientific-constant-schema*
      name
      quantity
      status
      kind
      system
      source)))

(00001001 scientific-constant?
  (00001000 (x)
    (00000111
      
      (1 (00000001 ()))
      ((00000011 (science-proper-list? x) (00000001 ())) (00000001 ()))
      
      ((00000011 (00000101 x) *scientific-constant-schema*)
       (00000111
         ((00000011 (00100011 (00101111 x)) (00000001 ())) (00000001 ()))
         ((00000011 (quantity? (00110000 x)) (00000001 ())) (00000001 ()))
         ((00000011 (scientific-constant-status-valid? (00110001 x)) (00000001 ())) (00000001 ()))
         ((00000011 (scientific-constant-kind-valid? (00110010 x)) (00000001 ())) (00000001 ()))
         ((00000011 (00100011 (science-sixth x)) (00000001 ())) (00000001 ()))
         ((00000011 (science-source? (science-seventh x)) (00000001 ())) (00000001 ()))
         (1 t)))
      )))

(00001001 scientific-constant-name
  (00001000 (constant) (00101111 constant)))

(00001001 scientific-constant-quantity
  (00001000 (constant) (00110000 constant)))

(00001001 scientific-constant-value
  (00001000 (constant)
    (quantity-value (scientific-constant-quantity constant))))

(00001001 scientific-constant-unit
  (00001000 (constant)
    (quantity-unit (scientific-constant-quantity constant))))

(00001001 scientific-constant-status
  (00001000 (constant) (00110001 constant)))

(00001001 scientific-constant-kind
  (00001000 (constant) (00110010 constant)))

(00001001 scientific-constant-system
  (00001000 (constant) (science-sixth constant)))

(00001001 scientific-constant-source
  (00001000 (constant) (science-seventh constant)))

; Pure projection into the existing knowledge clause format. It does not write
; *knowledge-journal*: callers must still pass the returned batch through the
; explicit advise-all admission boundary. A malformed constant projects to ().
(00001001 scientific-constant->clauses
  (00001000 (constant)
    (00000111
      ((00000011 (scientific-constant? constant) (00000001 ())) (00000001 ()))
      (1
       (10011100 ((name (scientific-constant-name constant)))
         (00100111
           (00100111 (00100111 (00000001 scientific-constant) name))
           (00100111
             (00100111 (00000001 constant-value)
                   name
                   (scientific-constant-value constant)))
           (00100111
             (00100111 (00000001 constant-unit)
                   name
                   (scientific-constant-unit constant)))
           (00100111
             (00100111 (00000001 constant-status)
                   name
                   (scientific-constant-status constant)))
           (00100111
             (00100111 (00000001 constant-kind)
                   name
                   (scientific-constant-kind constant)))
           (00100111
             (00100111 (00000001 constant-system)
                   name
                   (scientific-constant-system constant)))
           (00100111
             (00100111 (00000001 constant-source)
                   name
                   (scientific-constant-source constant)))))))))