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
         ((хибне? (атом? (перше argument)))
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
         ((хибне? (атом? (перше expression)))
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

; Доменною шириною та формою керує SENS. Пошкоджені списки
; відхиляються до D3 CAR/CDR/EQ: жодного часткового збігу бітів.
(визначити native-first-domain-key3-shape?
  (функція (форма-доменного-ключа біт-перший-очікуваний біт-другий-очікуваний біт-третій-очікуваний)
    (за-умовою
      ((атом? форма-доменного-ключа) ні)
      ((атом? (решта форма-доменного-ключа)) ні)
      ((порожній? (решта (решта форма-доменного-ключа)))
       (за-умовою
         ((тотожне? (перше форма-доменного-ключа) 3)
          (native-first-domain-key3-bits?
            (перше (решта форма-доменного-ключа))
            біт-перший-очікуваний біт-другий-очікуваний біт-третій-очікуваний))
         (так ні)))
      (так ні))))

(визначити native-first-domain-key3-bits?
  (функція (біти-ключа-д3 біт-перший-очікуваний біт-другий-очікуваний біт-третій-очікуваний)
    (за-умовою
      ((атом? біти-ключа-д3) ні)
      ((атом? (решта біти-ключа-д3)) ні)
      ((атом? (решта (решта біти-ключа-д3))) ні)
      ((порожній? (решта (решта (решта біти-ключа-д3))))
       (за-умовою
         ((тотожне? (перше біти-ключа-д3) біт-перший-очікуваний)
          (за-умовою
            ((тотожне? (перше (решта біти-ключа-д3)) біт-другий-очікуваний)
             (тотожне? (перше (решта (решта біти-ключа-д3))) біт-третій-очікуваний))
            (так ні)))
         (так ні)))
      (так ні))))

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