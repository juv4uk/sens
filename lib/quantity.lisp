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

(0011 *dimension-schema* (001 dimension/1))
(0011 *unit-schema* (001 unit/1))
(0011 *quantity-schema* (001 quantity/1))
(0011 *science-source-schema* (001 science-source/1))
(0011 *scientific-constant-schema* (001 scientific-constant/1))

(0011 science-proper-list?
  (0010 (x)
    (110
      ; Атом: порожній хвіст завершує правильний список; інший атом — ні.
      ((010 x)
       (101 x (001 ())))
      ; Пара: точний D1-предикат забезпечує рекурсію без невідомого імені.
      ((010 (001 ()))
       (science-proper-list? (011 x))))))

; Exact Lisp-owned length predicate. The caller separately rejects dotted tails.
; D1 ATOM ends an empty tail; the remaining counter must reach zero there.
(0011 science-list-length-equals?
  (0010 (items remaining)
    (110
      ((010 items) (101 remaining 0))
      ((101 remaining 0) (101 1 0))
      ((010 (001 ()))
       (science-list-length-equals? (011 items) (01011 remaining 1))))))

(0011 science-sixth
  (0010 (values)
    (100 (011 (011 (011 (011 (011 values))))))))

(0011 science-seventh
  (0010 (values)
    (100 (011 (011 (011 (011 (011 (011 values)))))))))

(0011 make-dimension
  (0010 (base exponent)
    (1110 *dimension-schema* base exponent)))

(0011 dimension?
  (0010 (x)
    (110
      
      ((010 x)  (001 ()))
      ((101 (science-proper-list? x) (001 ())) (001 ()))
      ((101 (science-list-length-equals? x 3) (101 1 0)) (001 ()))
      ((101 (100 x) *dimension-schema*)
       (110
         ((101 (110101100 (1001 x)) (001 ())) (001 ()))
         
         ((010 (10011 x))  (010 (001 ())))
         ))
      )))

(0011 dimension-base
  (0010 (dimension) (1001 dimension)))

(0011 dimension-exponent
  (0010 (dimension) (10011 dimension)))

(0011 science-dimensions-valid?
  (0010 (dimensions)
    (110
      
      ((010 dimensions)  (110
         ((101 dimensions (001 ())) (010 (001 ())))
         ))
      ((dimension? (100 dimensions))
       (science-dimensions-valid? (011 dimensions)))
      )))

(0011 make-unit
  (0010 (dimensions)
    (111 *unit-schema* dimensions)))

(0011 unit?
  (0010 (x)
    (110
      
      ((010 x)  (001 ()))
      ((101 (science-proper-list? x) (001 ())) (001 ()))
      ((101 (100 x) *unit-schema*)
       (science-dimensions-valid? (011 x)))
      )))

(0011 unit-dimensions
  (0010 (unit) (011 unit)))

(0011 make-quantity
  (0010 (value unit)
    (1110 *quantity-schema* value unit)))

(0011 quantity?
  (0010 (x)
    (110
      
      ((010 x)  (001 ()))
      ((101 (science-proper-list? x) (001 ())) (001 ()))
      ((101 (science-list-length-equals? x 3) (101 1 0)) (001 ()))
      ((101 (100 x) *quantity-schema*)
       (unit? (10011 x)))
      )))

(0011 quantity-value
  (0010 (quantity) (1001 quantity)))

(0011 quantity-unit
  (0010 (quantity) (10011 quantity)))

; Мінімальна точна алгебра одиниць. Вона не вводить нових примітивів:
; показники вимірностей додаються/віднімаються звичайною точною арифметикою
; my-lisp, а нульовий показник видаляє вимірність з результату.
(0011 science-add-dimension
  (0010 (dimension dimensions)
    (110
      
      ((010 dimensions)  (110
         ((11110111 (dimension-exponent dimension) 0)  (001 ()))
         ((010 ()) (1110 dimension))))
      ((101 (dimension-base dimension)
           (dimension-base (100 dimensions)))
       (001000 ((sum
               (01010 (dimension-exponent dimension)
                  (dimension-exponent (100 dimensions)))))
         (110
           ((11110111 sum 0)  (011 dimensions))
           ((010 ())
            (111
              (make-dimension (dimension-base dimension) sum)
              (011 dimensions))))))
      ((010 ())
       (111
         (100 dimensions)
         (science-add-dimension dimension (011 dimensions)))))))

(0011 science-merge-dimensions
  (0010 (from into)
    (110
      
      ((010 from)  into)
      ((010 ())
       (science-merge-dimensions
         (011 from)
         (science-add-dimension (100 from) into))))))

(0011 science-negate-dimensions
  (0010 (dimensions)
    (110
      
      ((010 dimensions)  (001 ()))
      ((010 ())
       (111
         (make-dimension
           (dimension-base (100 dimensions))
           (01011 0 (dimension-exponent (100 dimensions))))
         (science-negate-dimensions (011 dimensions)))))))

(0011 unit-product
  (0010 (left right)
    (make-unit
      (science-merge-dimensions
        (unit-dimensions right)
        (unit-dimensions left)))))

(0011 unit-quotient
  (0010 (left right)
    (make-unit
      (science-merge-dimensions
        (science-negate-dimensions (unit-dimensions right))
        (unit-dimensions left)))))

(0011 quantity-product
  (0010 (left right)
    (make-quantity
      (10110 (quantity-value left) (quantity-value right))
      (unit-product (quantity-unit left) (quantity-unit right)))))

(0011 quantity-quotient
  (0010 (left right)
    (make-quantity
      (11110110 (quantity-value left) (quantity-value right))
      (unit-quotient (quantity-unit left) (quantity-unit right)))))

(0011 make-science-source
  (0010 (authority edition)
    (1110 *science-source-schema* authority edition)))

(0011 science-source?
  (0010 (x)
    (110
      
      ((010 x)  (001 ()))
      ((101 (science-proper-list? x) (001 ())) (001 ()))
      ((101 (science-list-length-equals? x 3) (101 1 0)) (001 ()))
      ((101 (100 x) *science-source-schema*)
       (110
         ((101 (110101100 (1001 x)) (001 ())) (001 ()))
         
         ((010 (10011 x))  (010 (001 ())))
         ))
      )))

(0011 scientific-constant-status-valid?
  (0010 (status)
    (110
      ((101 status (001 exact-by-definition)) (010 (001 ())))
      ((101 status (001 exact-derived)) (010 (001 ())))
      ((101 status (001 measured)) (010 (001 ())))
      )))

(0011 scientific-constant-kind-valid?
  (0010 (kind)
    (110
      ((101 kind (001 physical-defining)) (010 (001 ())))
      ((101 kind (001 physical-derived)) (010 (001 ())))
      ((101 kind (001 physical-measured)) (010 (001 ())))
      ((101 kind (001 mathematical)) (010 (001 ())))
      )))

(0011 make-scientific-constant
  (0010 (name quantity status kind system source)
    (1110
      *scientific-constant-schema*
      name
      quantity
      status
      kind
      system
      source)))

(0011 scientific-constant?
  (0010 (x)
    (110

      ((010 x) (001 ()))
      ((101 (science-proper-list? x) (001 ())) (001 ()))
      ; Короткі записи відхиляються до CAR/CDR-зчитування полів.
      ((101 (science-list-length-equals? x 7) (101 1 0)) (001 ()))
      ((101 (100 x) *scientific-constant-schema*)
       (110
         ((101 (110101100 (1001 x)) (001 ())) (001 ()))
         ((101 (quantity? (10011 x)) (001 ())) (001 ()))
         ((101 (scientific-constant-status-valid? (100111 x)) (001 ())) (001 ()))
         ((101 (scientific-constant-kind-valid? (110110101 x)) (001 ())) (001 ()))
         ((101 (110101100 (science-sixth x)) (001 ())) (001 ()))
         ((101 (science-source? (science-seventh x)) (001 ())) (001 ()))
         ((010 ()) (010 (001 ())))))
      )))

(0011 scientific-constant-name
  (0010 (constant) (1001 constant)))

(0011 scientific-constant-quantity
  (0010 (constant) (10011 constant)))

(0011 scientific-constant-value
  (0010 (constant)
    (quantity-value (scientific-constant-quantity constant))))

(0011 scientific-constant-unit
  (0010 (constant)
    (quantity-unit (scientific-constant-quantity constant))))

(0011 scientific-constant-status
  (0010 (constant) (100111 constant)))

(0011 scientific-constant-kind
  (0010 (constant) (110110101 constant)))

(0011 scientific-constant-system
  (0010 (constant) (science-sixth constant)))

(0011 scientific-constant-source
  (0010 (constant) (science-seventh constant)))

; Pure projection into the existing knowledge clause format. It does not write
; *knowledge-journal*: callers must still pass the returned batch through the
; explicit advise-all admission boundary. A malformed constant projects to ().
(0011 scientific-constant->clauses
  (0010 (constant)
    (110
      ((101 (scientific-constant? constant) (001 ())) (001 ()))
      ((010 ())
       (001000 ((name (scientific-constant-name constant)))
         (1110
           (1110 (1110 (001 scientific-constant) name))
           (1110
             (1110 (001 constant-value)
                   name
                   (scientific-constant-value constant)))
           (1110
             (1110 (001 constant-unit)
                   name
                   (scientific-constant-unit constant)))
           (1110
             (1110 (001 constant-status)
                   name
                   (scientific-constant-status constant)))
           (1110
             (1110 (001 constant-kind)
                   name
                   (scientific-constant-kind constant)))
           (1110
             (1110 (001 constant-system)
                   name
                   (scientific-constant-system constant)))
           (1110
             (1110 (001 constant-source)
                   name
                   (scientific-constant-source constant)))))))))