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

(визначити науковий-список-правильний?
  (функція (значення)
    (за-умовою
      ((атом? значення)
       (тотожне? значення (як-є ())))
      (так
       (науковий-список-правильний? (решта значення))))))

(визначити науковий-список-довжина-дорівнює?
  (функція (елементи залишок)
    (за-умовою
      ((атом? елементи) (тотожне? залишок 0))
      ((тотожне? залишок 0) ні)
      (так
       (науковий-список-довжина-дорівнює? (решта елементи) (відняти залишок 1))))))

(визначити науковий-шостий
  (функція (поля)
    (перше (решта (решта (решта (решта (решта поля))))))))

(визначити науковий-сьомий
  (функція (поля)
    (перше (решта (решта (решта (решта (решта (решта поля)))))))))

(визначити створити-розмірність
  (функція (base exponent)
    (список *dimension-schema* base exponent)))

(визначити розмірність?
  (функція (x)
    (за-умовою
      ((атом? x) (як-є ()))
      ((тотожне? (науковий-список-правильний? x) (як-є ())) (як-є ()))
      ((тотожне? (науковий-список-довжина-дорівнює? x 3) ні) (як-є ()))
      ((тотожне? (перше x) *dimension-schema*)
       (за-умовою
         ((тотожне? (символ? (друге x)) (як-є ())) (як-є ()))
         (так так)))
      (так (як-є ())))))

(визначити розмірність-основа
  (функція (dimension) (друге dimension)))

(визначити розмірність-показник
  (функція (dimension) (третє dimension)))

(визначити створити-одиниця
  (функція (dimensions)
    (список *unit-schema* dimensions)))

(визначити одиниця-виміру?
  (функція (x)
    (за-умовою
      ((атом? x) (як-є ()))
      ((тотожне? (науковий-список-правильний? x) (як-є ())) (як-є ()))
      ((тотожне? (перше x) *unit-schema*)
       (науковий-список-правильний? (решта x)))
      (так (як-є ())))))

(визначити одиниця-розмірності
  (функція (unit) (решта unit)))

(визначити створити-величина
  (функція (value unit)
    (список *quantity-schema* value unit)))

(визначити величина?
  (функція (x)
    (за-умовою
      ((атом? x) (як-є ()))
      ((тотожне? (науковий-список-правильний? x) (як-є ())) (як-є ()))
      ((тотожне? (науковий-список-довжина-дорівнює? x 3) ні) (як-є ()))
      ((тотожне? (перше x) *quantity-schema*)
       (одиниця-виміру? (третє x)))
      (так (як-є ())))))

(визначити величина-значення
  (функція (quantity) (друге quantity)))

(визначити величина-одиниця
  (функція (quantity) (третє quantity)))

(визначити створити-наука-джерело
  (функція (authority edition)
    (список *science-source-schema* authority edition)))

(визначити наука-джерело?
  (функція (x)
    (за-умовою
      ((атом? x) (як-є ()))
      ((тотожне? (науковий-список-правильний? x) (як-є ())) (як-є ()))
      ((тотожне? (науковий-список-довжина-дорівнює? x 3) ні) (як-є ()))
      ((тотожне? (перше x) *science-source-schema*) так)
      (так (як-є ())))))

(визначити science-source-authority
  (функція (source) (друге source)))

(визначити science-source-edition
  (функція (source) (третє source)))

(визначити науковий-константа-стан-чинний?
  (функція (status)
    (за-умовою
      ((тотожне? status (як-є exact-by-definition)) так)
      ((тотожне? status (як-є measured)) так)
      (так (як-є ())))))

(визначити науковий-константа-вид-чинний?
  (функція (kind)
    (за-умовою
      ((тотожне? kind (як-є physical-defining)) так)
      ((тотожне? kind (як-є physical-derived)) так)
      (так (як-є ())))))

(визначити створити-науковий-константа
  (функція (name quantity status kind system source)
    (список *scientific-constant-schema* name quantity status kind system source)))

(визначити науковий-константа?
  (функція (x)
    (за-умовою
      ((атом? x) (як-є ()))
      ((тотожне? (науковий-список-правильний? x) (як-є ())) (як-є ()))
      ((тотожне? (науковий-список-довжина-дорівнює? x 7) ні) (як-є ()))
      ((тотожне? (перше x) *scientific-constant-schema*)
       (за-умовою
         ((тотожне? (символ? (друге x)) (як-є ())) (як-є ()))
         ((тотожне? (величина? (третє x)) (як-є ())) (як-є ()))
         ((тотожне? (науковий-константа-стан-чинний? (четверте x)) (як-є ())) (як-є ()))
         ((тотожне? (науковий-константа-вид-чинний? (п'ятий x)) (як-є ())) (як-є ()))
         ((тотожне? (символ? (науковий-шостий x)) (як-є ())) (як-є ()))
         ((тотожне? (наука-джерело? (науковий-сьомий x)) (як-є ())) (як-є ()))
         (так так)))
      (так (як-є ())))))

(визначити науковий-константа-ім'я
  (функція (constant) (друге constant)))

(визначити науковий-константа-величина
  (функція (constant) (третє constant)))

(визначити науковий-константа-значення
  (функція (constant)
    (величина-значення (науковий-константа-величина constant))))

(визначити науковий-константа-одиниця
  (функція (constant)
    (величина-одиниця (науковий-константа-величина constant))))

(визначити науковий-константа-стан
  (функція (constant) (четверте constant)))

(визначити науковий-константа-вид
  (функція (constant) (п'ятий constant)))

(визначити науковий-константа-система
  (функція (constant) (науковий-шостий constant)))

(визначити науковий-константа-джерело
  (функція (constant) (науковий-сьомий constant)))

(визначити науковий-константа-клаузи
  (функція (constant)
    (за-умовою
      ((тотожне? (науковий-константа? constant) (як-є ())) (як-є ()))
      (так
       ((функція (name)
          (список
           (список (список (як-є scientific-constant) name))
           (список
             (список (як-є constant-value)
                   name
                   (науковий-константа-значення constant)))
           (список
             (список (як-є constant-unit)
                   name
                   (науковий-константа-одиниця constant)))
           (список
             (список (як-є constant-status)
                   name
                   (науковий-константа-стан constant)))
           (список
             (список (як-є constant-kind)
                   name
                   (науковий-константа-вид constant)))
           (список
             (список (як-є constant-system)
                   name
                   (науковий-константа-система constant)))
           (список
             (список (як-є constant-source)
                   name
                   (науковий-константа-джерело constant))))
         )
         (науковий-константа-ім'я constant))))))

; Повні українські назви — первинні визначення за точними проєкціями D9.
; Англійські назви — лише сумісні псевдоніми тих самих Lisp-замикань.
; Ключі залишаються в lib/domains/d9.lisp; цей файл не вводить бінарних call-heads.
(визначити make-dimension створити-розмірність)
(визначити dimension? розмірність?)
(визначити dimension-base розмірність-основа)
(визначити dimension-exponent розмірність-показник)
(визначити make-unit створити-одиниця)
(визначити unit? одиниця-виміру?)
(визначити unit-dimensions одиниця-розмірності)
(визначити make-quantity створити-величина)
(визначити quantity? величина?)
(визначити quantity-value величина-значення)
(визначити quantity-unit величина-одиниця)
(визначити make-science-source створити-наука-джерело)
(визначити science-source? наука-джерело?)
(визначити scientific-constant-status-valid? науковий-константа-стан-чинний?)
(визначити scientific-constant-kind-valid? науковий-константа-вид-чинний?)
(визначити make-scientific-constant створити-науковий-константа)
(визначити scientific-constant? науковий-константа?)
(визначити scientific-constant-name науковий-константа-ім'я)
(визначити scientific-constant-quantity науковий-константа-величина)
(визначити scientific-constant-value науковий-константа-значення)
(визначити scientific-constant-unit науковий-константа-одиниця)
(визначити scientific-constant-status науковий-константа-стан)
(визначити scientific-constant-kind науковий-константа-вид)
(визначити scientific-constant-system науковий-константа-система)
(визначити scientific-constant-source науковий-константа-джерело)
(визначити scientific-constant->clauses науковий-константа-клаузи)

; Українські локальні імена є тими самими Lisp-замиканнями.
; Старі імена лишаються сумісними проєкціями для зовнішніх споживачів.
; Це не нові D9/D10 identity, не новий механізм і не D24+ математика.
(визначити science-proper-list? науковий-список-правильний?)
(визначити science-list-length-equals? науковий-список-довжина-дорівнює?)
(визначити science-sixth науковий-шостий)
(визначити science-seventh науковий-сьомий)
