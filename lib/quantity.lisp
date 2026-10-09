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
    (за-умовою
      ((порожнє? x) так)
      ((атом? x) ні)
      ((science-proper-list? (решта x)) так)
      ((хибне? (science-proper-list? (решта x))) ні))))

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
    (за-умовою
      ((хибне? (science-proper-list? x)) ні)
      ((хибне? (однакові? (довжина x) 3)) ні)
      ((хибне? (тотожне? (перше x) *dimension-schema*)) ні)
      ((хибне? (символ? (dimension-base x))) ні)
      ((хибне? (атом? (dimension-exponent x))) ні)
      ((так) так))))

(00001001 dimension-base
  (00001000 (dimension) (00101111 dimension)))

(00001001 dimension-exponent
  (00001000 (dimension) (00110000 dimension)))

(00001001 science-dimensions-valid?
  (00001000 (dimensions)
    (за-умовою
      ((порожнє? dimensions) так)
      ((атом? dimensions) ні)
      ((dimension? (перше dimensions))
       (science-dimensions-valid? (решта dimensions)))
      ((хибне? (dimension? (перше dimensions))) ні))))

(00001001 make-unit
  (00001000 (dimensions)
    (00000100 *unit-schema* dimensions)))

(00001001 unit?
  (00001000 (x)
    (за-умовою
      ((хибне? (science-proper-list? x)) ні)
      ((хибне? (однакові? (довжина x) 2)) ні)
      ((хибне? (тотожне? (перше x) *unit-schema*)) ні)
      ((хибне? (science-dimensions-valid? (перше (решта x)))) ні)
      ((так) так))))

(00001001 unit-dimensions
  (00001000 (unit) (00000110 unit)))

(00001001 make-quantity
  (00001000 (value unit)
    (00100111 *quantity-schema* value unit)))

(00001001 quantity?
  (00001000 (x)
    (за-умовою
      ((хибне? (science-proper-list? x)) ні)
      ((хибне? (однакові? (довжина x) 3)) ні)
      ((хибне? (тотожне? (перше x) *quantity-schema*)) ні)
      ((хибне? (unit? (перше (решта (решта x))))) ні)
      ((так) так))))

(00001001 quantity-value
  (00001000 (quantity) (00101111 quantity)))

(00001001 quantity-unit
  (00001000 (quantity) (00110000 quantity)))

; Мінімальна точна алгебра одиниць. Вона не вводить нових примітивів:
; показники вимірностей додаються/віднімаються звичайною точною арифметикою
; my-lisp, а нульовий показник видаляє вимірність з результату.
(00001001 science-add-dimension
  (00001000 (dimension dimensions)
    (за-умовою
      ((атом? dimensions)
       (за-умовою
         ((нуль? (dimension-exponent dimension)) (як-є ()))
         ((хибне? (нуль? (dimension-exponent dimension)))
          (сполучити dimension (як-є ())))))
      ((тотожне? (dimension-base dimension)
                 (dimension-base (перше dimensions)))
       (за-умовою
         ((нуль? (додати (dimension-exponent dimension)
                         (dimension-exponent (перше dimensions))))
          (решта dimensions))
         ((хибне? (нуль? (додати (dimension-exponent dimension)
                                 (dimension-exponent (перше dimensions)))))
          (сполучити
            (make-dimension
              (dimension-base dimension)
              (додати (dimension-exponent dimension)
                      (dimension-exponent (перше dimensions))))
            (решта dimensions)))))
      ((хибне? (тотожне? (dimension-base dimension)
                         (dimension-base (перше dimensions))))
       (сполучити
         (перше dimensions)
         (science-add-dimension dimension (решта dimensions)))))))

(00001001 science-merge-dimensions
  (00001000 (from into)
    (за-умовою
      ((атом? from) into)
      ((хибне? (атом? from))
       (science-merge-dimensions
         (решта from)
         (science-add-dimension (перше from) into))))))

(00001001 science-negate-dimensions
  (00001000 (dimensions)
    (за-умовою
      ((атом? dimensions) (як-є ()))
      ((хибне? (атом? dimensions))
       (сполучити
         (make-dimension
           (dimension-base (перше dimensions))
           (відняти 0 (dimension-exponent (перше dimensions))))
         (science-negate-dimensions (решта dimensions)))))))

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
    (за-умовою
      ((хибне? (science-proper-list? x)) ні)
      ((хибне? (однакові? (довжина x) 3)) ні)
      ((хибне? (тотожне? (перше x) *science-source-schema*)) ні)
      ((хибне? (символ? (перше (решта x)))) ні)
      ((хибне? (атом? (перше (решта (решта x))))) ні)
      ((так) так))))

(00001001 scientific-constant-status-valid?
  (00001000 (status)
    (за-умовою
      ((тотожне? status (як-є exact-by-definition)) так)
      ((тотожне? status (як-є exact-derived)) так)
      ((тотожне? status (як-є measured)) так)
      ((так) ні))))

(00001001 scientific-constant-kind-valid?
  (00001000 (kind)
    (за-умовою
      ((тотожне? kind (як-є physical-defining)) так)
      ((тотожне? kind (як-є physical-derived)) так)
      ((тотожне? kind (як-є physical-measured)) так)
      ((тотожне? kind (як-є mathematical)) так)
      ((так) ні))))

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
    (за-умовою
      ((хибне? (science-proper-list? x)) ні)
      ((хибне? (однакові? (довжина x) 7)) ні)
      ((хибне? (тотожне? (перше x) *scientific-constant-schema*)) ні)
      ((хибне? (символ? (перше (решта x))) ) ні)
      ((хибне? (quantity? (перше (решта (решта x))))) ні)
      ((хибне? (scientific-constant-status-valid?
                 (перше (решта (решта (решта x)))))) ні)
      ((хибне? (scientific-constant-kind-valid?
                 (перше (решта (решта (решта (решта x))))))) ні)
      ((хибне? (символ? (science-sixth x))) ні)
      ((хибне? (science-source? (science-seventh x))) ні)
      ((так) так))))

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
    (за-умовою
      ((хибне? (scientific-constant? constant)) (як-є ()))
      ((так)
       (let ((name (scientific-constant-name constant)))
         (00100111
           (00100111 (00100111 (00000001 scientific-constant) name))
           (00100111
             (00100111 (00000001 constant-value)
                   name
                   (scientific-constant-value constant))
             (00100111 (00000001 constant-unit)
                   name
                   (scientific-constant-unit constant))
             (00100111 (00000001 constant-status)
                   name
                   (scientific-constant-status constant))
             (00100111 (00000001 constant-kind)
                   name
                   (scientific-constant-kind constant))
             (00100111 (00000001 constant-system)
                   name
                   (scientific-constant-system constant))
             (00100111 (00000001 constant-source)
                   name
                   (scientific-constant-source constant)))))))))