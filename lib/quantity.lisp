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
;
; Migrated: COND else (010 ()) → exact D1:1 (010 (001 ())).
; Migrated PredicateBit carriers: bare (101 1 0) → exact D1:0 form
; (101 (001 (0)) (001 (1))). D1:1 is projected directly as #d1:1. Width is identity.
; Two-field COND only. Every bit of the domain address is valued.
; Reuses science-proper-list?, quantity?, scientific-constant? surface.
;

(0011 *dimension-schema* (001 dimension/1))
(0011 *unit-schema* (001 unit/1))
(0011 *quantity-schema* (001 quantity/1))
(0011 *science-source-schema* (001 science-source/1))
(0011 *scientific-constant-schema* (001 scientific-constant/1))

(0011 science-proper-list?
  (0010 (x)
    (110
      ((010 x)
       (101 x (001 ())))
      (#d1:1
       (science-proper-list? (011 x))))))

(0011 science-list-length-equals?
  (0010 (items remaining)
    (110
      ((010 items) (101 remaining 0))
      ((101 remaining 0) (101 (001 (0)) (001 (1))))
      (#d1:1
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
      ((010 x) (001 ()))
      ((101 (science-proper-list? x) (001 ())) (001 ()))
      ((101 (science-list-length-equals? x 3) (101 (001 (0)) (001 (1)))) (001 ()))
      ((101 (100 x) *dimension-schema*)
       (110
         ((101 (110101100 (1001 x)) (001 ())) (001 ()))
         ((010 (001 ())) #d1:1)))
      ((010 (001 ())) (001 ())))))

(0011 dimension-base
  (0010 (dimension) (1001 dimension)))

(0011 dimension-exponent
  (0010 (dimension) (10011 dimension)))

(0011 make-unit
  (0010 (dimensions)
    (1110 *unit-schema* dimensions)))

(0011 unit?
  (0010 (x)
    (110
      ((010 x) (001 ()))
      ((101 (science-proper-list? x) (001 ())) (001 ()))
      ((101 (100 x) *unit-schema*)
       (science-proper-list? (011 x)))
      ((010 (001 ())) (001 ())))))

(0011 unit-dimensions
  (0010 (unit) (011 unit)))

(0011 make-quantity
  (0010 (value unit)
    (1110 *quantity-schema* value unit)))

(0011 quantity?
  (0010 (x)
    (110
      ((010 x) (001 ()))
      ((101 (science-proper-list? x) (001 ())) (001 ()))
      ((101 (science-list-length-equals? x 3) (101 (001 (0)) (001 (1)))) (001 ()))
      ((101 (100 x) *quantity-schema*)
       (unit? (10011 x)))
      ((010 (001 ())) (001 ())))))

(0011 quantity-value
  (0010 (quantity) (1001 quantity)))

(0011 quantity-unit
  (0010 (quantity) (10011 quantity)))

(0011 make-science-source
  (0010 (authority edition)
    (1110 *science-source-schema* authority edition)))

(0011 science-source?
  (0010 (x)
    (110
      ((010 x) (001 ()))
      ((101 (science-proper-list? x) (001 ())) (001 ()))
      ((101 (science-list-length-equals? x 3) (101 (001 (0)) (001 (1)))) (001 ()))
      ((101 (100 x) *science-source-schema*) #d1:1)
      ((010 (001 ())) (001 ())))))

(0011 science-source-authority
  (0010 (source) (1001 source)))

(0011 science-source-edition
  (0010 (source) (10011 source)))

(0011 scientific-constant-status-valid?
  (0010 (status)
    (110
      ((101 status (001 exact-by-definition)) #d1:1)
      ((101 status (001 measured)) #d1:1)
      ((010 (001 ())) (001 ())))))

(0011 scientific-constant-kind-valid?
  (0010 (kind)
    (110
      ((101 kind (001 physical-defining)) #d1:1)
      ((101 kind (001 physical-derived)) #d1:1)
      ((010 (001 ())) (001 ())))))

(0011 make-scientific-constant
  (0010 (name quantity status kind system source)
    (1110 *scientific-constant-schema* name quantity status kind system source)))

(0011 scientific-constant?
  (0010 (x)
    (110
      ((010 x) (001 ()))
      ((101 (science-proper-list? x) (001 ())) (001 ()))
      ((101 (science-list-length-equals? x 7) (101 (001 (0)) (001 (1)))) (001 ()))
      ((101 (100 x) *scientific-constant-schema*)
       (110
         ((101 (110101100 (1001 x)) (001 ())) (001 ()))
         ((101 (quantity? (10011 x)) (001 ())) (001 ()))
         ((101 (scientific-constant-status-valid? (100111 x)) (001 ())) (001 ()))
         ((101 (scientific-constant-kind-valid? (110110101 x)) (001 ())) (001 ()))
         ((101 (110101100 (science-sixth x)) (001 ())) (001 ()))
         ((101 (science-source? (science-seventh x)) (001 ())) (001 ()))
         ((010 (001 ())) #d1:1)))
      ((010 (001 ())) (001 ())))))

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

(0011 scientific-constant->clauses
  (0010 (constant)
    (110
      ((101 (scientific-constant? constant) (001 ())) (001 ()))
      ((010 (001 ()))
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
