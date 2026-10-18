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
; scientific-constant->clauses: old D6:001000 LET replaced by exact D4:0010
; lexical lambda application, one binder, initializer evaluated once.
; Binary SENS checks: tests/semantic/quantity-d4-bind-{law,mutant}.bits.
; Migrated PredicateBit carriers: bare (101 1 0) → exact D1:0 form
; (101 (001 (0)) (001 (1))). D1:1 is projected directly as #d1:1. Width is identity.
; Two-field COND only. Every bit of the domain address is valued.
; Reuses science-proper-list?, quantity?, scientific-constant? surface.
;

(визначити *dimension-schema* (як-є dimension/1))
(визначити *unit-schema* (як-є unit/1))
(визначити *quantity-schema* (як-є quantity/1))
(визначити *science-source-schema* (як-є science-source/1))
(визначити *scientific-constant-schema* (як-є scientific-constant/1))

(визначити science-proper-list?
  (функція (x)
    (за-умовою
      ((атом? x)
       (тотожне? x (як-є ())))
      (так
       (science-proper-list? (решта x))))))

(визначити science-list-length-equals?
  (функція (items remaining)
    (за-умовою
      ((атом? items) (тотожне? remaining 0))
      ((тотожне? remaining 0) (тотожне? (як-є (0)) (як-є (1))))
      (так
       (science-list-length-equals? (решта items) (відняти remaining 1))))))

(визначити science-sixth
  (функція (values)
    (перше (решта (решта (решта (решта (решта values))))))))

(визначити science-seventh
  (функція (values)
    (перше (решта (решта (решта (решта (решта (решта values)))))))))

(визначити make-dimension
  (функція (base exponent)
    (список *dimension-schema* base exponent)))

(визначити dimension?
  (функція (x)
    (за-умовою
      ((атом? x) (як-є ()))
      ((тотожне? (science-proper-list? x) (як-є ())) (як-є ()))
      ((тотожне? (science-list-length-equals? x 3) (тотожне? (як-є (0)) (як-є (1)))) (як-є ()))
      ((тотожне? (перше x) *dimension-schema*)
       (за-умовою
         ((тотожне? (110101100 (друге x)) (як-є ())) (як-є ()))
         (так так)))
      (так (як-є ())))))

(визначити dimension-base
  (функція (dimension) (друге dimension)))

(визначити dimension-exponent
  (функція (dimension) (третє dimension)))

(визначити make-unit
  (функція (dimensions)
    (список *unit-schema* dimensions)))

(визначити unit?
  (функція (x)
    (за-умовою
      ((атом? x) (як-є ()))
      ((тотожне? (science-proper-list? x) (як-є ())) (як-є ()))
      ((тотожне? (перше x) *unit-schema*)
       (science-proper-list? (решта x)))
      (так (як-є ())))))

(визначити unit-dimensions
  (функція (unit) (решта unit)))

(визначити make-quantity
  (функція (value unit)
    (список *quantity-schema* value unit)))

(визначити quantity?
  (функція (x)
    (за-умовою
      ((атом? x) (як-є ()))
      ((тотожне? (science-proper-list? x) (як-є ())) (як-є ()))
      ((тотожне? (science-list-length-equals? x 3) (тотожне? (як-є (0)) (як-є (1)))) (як-є ()))
      ((тотожне? (перше x) *quantity-schema*)
       (unit? (третє x)))
      (так (як-є ())))))

(визначити quantity-value
  (функція (quantity) (друге quantity)))

(визначити quantity-unit
  (функція (quantity) (третє quantity)))

(визначити make-science-source
  (функція (authority edition)
    (список *science-source-schema* authority edition)))

(визначити science-source?
  (функція (x)
    (за-умовою
      ((атом? x) (як-є ()))
      ((тотожне? (science-proper-list? x) (як-є ())) (як-є ()))
      ((тотожне? (science-list-length-equals? x 3) (тотожне? (як-є (0)) (як-є (1)))) (як-є ()))
      ((тотожне? (перше x) *science-source-schema*) так)
      (так (як-є ())))))

(визначити science-source-authority
  (функція (source) (друге source)))

(визначити science-source-edition
  (функція (source) (третє source)))

(визначити scientific-constant-status-valid?
  (функція (status)
    (за-умовою
      ((тотожне? status (як-є exact-by-definition)) так)
      ((тотожне? status (як-є measured)) так)
      (так (як-є ())))))

(визначити scientific-constant-kind-valid?
  (функція (kind)
    (за-умовою
      ((тотожне? kind (як-є physical-defining)) так)
      ((тотожне? kind (як-є physical-derived)) так)
      (так (як-є ())))))

(визначити make-scientific-constant
  (функція (name quantity status kind system source)
    (список *scientific-constant-schema* name quantity status kind system source)))

(визначити scientific-constant?
  (функція (x)
    (за-умовою
      ((атом? x) (як-є ()))
      ((тотожне? (science-proper-list? x) (як-є ())) (як-є ()))
      ((тотожне? (science-list-length-equals? x 7) (тотожне? (як-є (0)) (як-є (1)))) (як-є ()))
      ((тотожне? (перше x) *scientific-constant-schema*)
       (за-умовою
         ((тотожне? (110101100 (друге x)) (як-є ())) (як-є ()))
         ((тотожне? (quantity? (третє x)) (як-є ())) (як-є ()))
         ((тотожне? (scientific-constant-status-valid? (четверте x)) (як-є ())) (як-є ()))
         ((тотожне? (scientific-constant-kind-valid? (110110101 x)) (як-є ())) (як-є ()))
         ((тотожне? (110101100 (science-sixth x)) (як-є ())) (як-є ()))
         ((тотожне? (science-source? (science-seventh x)) (як-є ())) (як-є ()))
         (так так)))
      (так (як-є ())))))

(визначити scientific-constant-name
  (функція (constant) (друге constant)))

(визначити scientific-constant-quantity
  (функція (constant) (третє constant)))

(визначити scientific-constant-value
  (функція (constant)
    (quantity-value (scientific-constant-quantity constant))))

(визначити scientific-constant-unit
  (функція (constant)
    (quantity-unit (scientific-constant-quantity constant))))

(визначити scientific-constant-status
  (функція (constant) (четверте constant)))

(визначити scientific-constant-kind
  (функція (constant) (110110101 constant)))

(визначити scientific-constant-system
  (функція (constant) (science-sixth constant)))

(визначити scientific-constant-source
  (функція (constant) (science-seventh constant)))

(визначити scientific-constant->clauses
  (функція (constant)
    (за-умовою
      ((тотожне? (scientific-constant? constant) (як-є ())) (як-є ()))
      (так
       ((функція (name)
          (список
           (список (список (як-є scientific-constant) name))
           (список
             (список (як-є constant-value)
                   name
                   (scientific-constant-value constant)))
           (список
             (список (як-є constant-unit)
                   name
                   (scientific-constant-unit constant)))
           (список
             (список (як-є constant-status)
                   name
                   (scientific-constant-status constant)))
           (список
             (список (як-є constant-kind)
                   name
                   (scientific-constant-kind constant)))
           (список
             (список (як-є constant-system)
                   name
                   (scientific-constant-system constant)))
           (список
             (список (як-є constant-source)
                   name
                   (scientific-constant-source constant))))
         )
         (scientific-constant-name constant))))))
