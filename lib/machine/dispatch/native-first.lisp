; #505 — Lisp-owned native-first execution-plan classifier.
; baseline control-only edit for #4242 diagnosis.
;
; This file decides only whether an already-proven machine lowering applies to
; expression *data*. It does not define language meaning, encode bytes, or call
; the host. Unsupported expressions are ordinary evaluator-fallback outcomes.
;
; Required layers are loaded by the caller:
;   lib/machine/layout/pair-x86-64.lisp
;   lib/machine/operands/x86-64.lisp
;   lib/machine/lowering/semantic-x86-64.lisp

(визначити native-first-fallback
  (функція (expression)
    (сполучити (як-є evaluator-fallback)
         (сполучити expression (як-є ())))))

(визначити native-first-native-plan
  (функція (forms arena-bytes)
    (сполучити (як-є native-plan)
         (сполучити forms
              (сполучити arena-bytes (як-є ()))))))

(визначити native-first-plan-car-cons-u64
  (функція (expression cons-expression)
    (за-умовою
      ((атом? (решта cons-expression))
       (native-first-fallback expression))
      (так
       (native-first-plan-car-cons-u64-rest-left
         expression
         (решта cons-expression))))))

(визначити native-first-plan-car-cons-u64-rest-left
  (функція (expression cons-arguments)
    (за-умовою
      ((атом? (решта cons-arguments))
       (native-first-fallback expression))
      (так
       (native-first-plan-car-cons-u64-rest-right
         expression
         cons-arguments
         (решта cons-arguments))))))

(визначити native-first-plan-car-cons-u64-rest-right
  (функція (expression cons-arguments rest-after-left)
    (за-умовою
      ((порожній? (решта rest-after-left))
       (за-умовою
         ((тотожне? (перше (x86-as-u64-imm (перше cons-arguments))) (як-є u64-imm))
          (за-умовою
            ((тотожне? (перше (x86-as-u64-imm (перше rest-after-left))) (як-є u64-imm))
             (native-first-native-plan
               (x86-lower-cons-car-u64-forms
                 (x86-u64-imm-value (x86-as-u64-imm (перше cons-arguments)))
                 (x86-u64-imm-value (x86-as-u64-imm (перше rest-after-left))))
               x86-pair-cell-bytes))
            (так
             (native-first-fallback expression))))
         (так
          (native-first-fallback expression))))
      (так
       (native-first-fallback expression)))))

(визначити native-first-plan-car-argument
  (функція (expression argument)
    (за-умовою
      ((атом? argument)
       (native-first-fallback expression))
      (так
       (за-умовою
         ((атом? (перше argument))
          (native-first-fallback expression))
         (так
          (за-умовою
            ((тотожне? (перше argument) (як-є сполучити))
             (native-first-plan-car-cons-u64 expression argument))
            (так
             (native-first-fallback expression)))))))))

(визначити native-first-plan-car
  (функція (expression)
    (за-умовою
      ((атом? (решта expression))
       (native-first-fallback expression))
      (так
       (за-умовою
         ((атом? (решта (решта expression)))
          (native-first-plan-car-argument expression (перше (решта expression))))
         (так
          (native-first-fallback expression)))))))

(визначити native-first-plan
  (функція (expression)
    (за-умовою
      ((атом? expression)
       (native-first-fallback expression))
      (так
       (за-умовою
         ((атом? (перше expression))
          (native-first-fallback expression))
         (так
          (за-умовою
            ((тотожне? (перше expression) (як-є перше))
             (native-first-plan-car expression))
            (так
             (native-first-fallback expression)))))))))

; #4081 — exact-domain native-first classifier.
;
; Input is already-lowered source-shaped program-data:
;   (DomainIdentity arg...)
; The caller supplies a representation-only SHAPE-OR-EMPTY mechanism:
;   DomainIdentity -> (width (PredicateBit...))
;   any other value -> ()
;
; This block never matches CAR/CONS by spelling and never relies on a raw W3
; source token whose leading zero/width could be lost by the ordinary reader.

(визначити native-first-domain-true
  (функція (seed)
    (атом? seed)))

(визначити native-first-domain-false
  (функція (seed)
    (атом? (сполучити seed ()))))

(визначити native-first-domain-key3-shape?
  (функція (shape bit0 bit1 bit2)
    (за-умовою
      ((атом? shape)
       ні)
      ((тотожне? (перше shape) 3)
       (native-first-domain-key3-bits?
         (перше (решта shape))
         bit0 bit1 bit2))
      (так
       ні))))

(визначити native-first-domain-key3-bits?
  (функція (bits bit0 bit1 bit2)
    (за-умовою
      ((тотожне? (перше bits) bit0)
       (за-умовою
         ((тотожне? (перше (решта bits)) bit1)
          (тотожне?
            (перше (решта (решта bits)))
            bit2))
         (так
          ні)))
      (так
       ні))))

(визначити native-first-domain-d3-car?
  (функція (shape-or-empty value)
    (native-first-domain-key3-shape?
      (shape-or-empty value)
      так
      ні
      ні)))

(визначити native-first-domain-d3-cons?
  (функція (shape-or-empty value)
    (native-first-domain-key3-shape?
      (shape-or-empty value)
      так
      так
      так)))

(визначити native-first-plan-domain-cons-argument
  (функція (shape-or-empty expression argument)
    (за-умовою
      ((атом? argument)
       (native-first-fallback expression))
      ((native-first-domain-d3-cons? shape-or-empty (перше argument))
       (native-first-plan-car-cons-u64 expression argument))
      (так
       (native-first-fallback expression)))))

(визначити native-first-plan-domain-car
  (функція (shape-or-empty expression)
    (за-умовою
      ((атом? (решта expression))
       (native-first-fallback expression))
      ((атом? (решта (решта expression)))
       (за-умовою
         ((тотожне? (решта (решта expression)) ())
          (native-first-plan-domain-cons-argument
            shape-or-empty
            expression
            (перше (решта expression))))
         (так
          (native-first-fallback expression))))
      (так
       (native-first-fallback expression)))))

(визначити native-first-plan-domain
  (функція (shape-or-empty expression)
    (за-умовою
      ((атом? expression)
       (native-first-fallback expression))
      ((native-first-domain-d3-car? shape-or-empty (перше expression))
       (native-first-plan-domain-car shape-or-empty expression))
      (так
       (native-first-fallback expression)))))