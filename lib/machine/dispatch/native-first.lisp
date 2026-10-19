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

(визначити нативний-повернути-до-обчислювача
  (функція (expression)
    (сполучити (як-є evaluator-fallback)
         (сполучити expression (як-є ())))))

(визначити нативний-скласти-план
  (функція (forms arena-bytes)
    (сполучити (як-є native-plan)
         (сполучити forms
              (сполучити arena-bytes (як-є ()))))))

(визначити нативний-план-перше-сполучити
  (функція (expression cons-expression)
    (за-умовою
      ((атом? (решта cons-expression))
       (нативний-повернути-до-обчислювача expression))
      (так
       (нативний-план-пари-ліва-частина
         expression
         (решта cons-expression))))))

(визначити нативний-план-пари-ліва-частина
  (функція (expression cons-arguments)
    (за-умовою
      ((атом? (решта cons-arguments))
       (нативний-повернути-до-обчислювача expression))
      (так
       (нативний-план-пари-права-частина
         expression
         cons-arguments
         (решта cons-arguments))))))

(визначити нативний-план-пари-права-частина
  (функція (expression cons-arguments rest-after-left)
    (за-умовою
      ((порожній? (решта rest-after-left))
       (за-умовою
         ((тотожне? (перше (x86-as-u64-imm (перше cons-arguments))) (як-є u64-imm))
          (за-умовою
            ((тотожне? (перше (x86-as-u64-imm (перше rest-after-left))) (як-є u64-imm))
             (нативний-скласти-план
               (x86-lower-cons-car-u64-forms
                 (x86-u64-imm-value (x86-as-u64-imm (перше cons-arguments)))
                 (x86-u64-imm-value (x86-as-u64-imm (перше rest-after-left))))
               x86-pair-cell-bytes))
            (так
             (нативний-повернути-до-обчислювача expression))))
         (так
          (нативний-повернути-до-обчислювача expression))))
      (так
       (нативний-повернути-до-обчислювача expression)))))

(визначити нативний-план-першого-аргументу
  (функція (expression argument)
    (за-умовою
      ((атом? argument)
       (нативний-повернути-до-обчислювача expression))
      (так
       (за-умовою
         ((хибне? (атом? (перше argument)))
          (нативний-повернути-до-обчислювача expression))
         (так
          (за-умовою
            ((тотожне? (перше argument) (як-є сполучити))
             (нативний-план-перше-сполучити expression argument))
            (так
             (нативний-повернути-до-обчислювача expression)))))))))

(визначити нативний-план-першого
  (функція (expression)
    (за-умовою
      ((атом? (решта expression))
       (нативний-повернути-до-обчислювача expression))
      (так
       (за-умовою
         ((атом? (решта (решта expression)))
          (нативний-план-першого-аргументу expression (перше (решта expression))))
         (так
          (нативний-повернути-до-обчислювача expression)))))))

(визначити native-first-plan
  (функція (expression)
    (за-умовою
      ((атом? expression)
       (нативний-повернути-до-обчислювача expression))
      (так
       (за-умовою
         ((хибне? (атом? (перше expression)))
          (нативний-повернути-до-обчислювача expression))
         (так
          (за-умовою
            ((тотожне? (перше expression) (як-є перше))
             (нативний-план-першого expression))
            (так
             (нативний-повернути-до-обчислювача expression)))))))))

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
(визначити нативна-форма-трибітного-ключа?
  (функція (форма-доменного-ключа біт-перший-очікуваний біт-другий-очікуваний біт-третій-очікуваний)
    (за-умовою
      ((атом? форма-доменного-ключа) ні)
      ((атом? (решта форма-доменного-ключа)) ні)
      ((порожній? (решта (решта форма-доменного-ключа)))
       (за-умовою
         ((тотожне? (перше форма-доменного-ключа) 3)
          (нативні-біти-трибітного-ключа?
            (перше (решта форма-доменного-ключа))
            біт-перший-очікуваний біт-другий-очікуваний біт-третій-очікуваний))
         (так ні)))
      (так ні))))

(визначити нативні-біти-трибітного-ключа?
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

(визначити нативний-домен-перше?
  (функція (shape-or-empty value)
    (нативна-форма-трибітного-ключа?
      (shape-or-empty value)
      так
      ні
      ні)))

(визначити нативний-домен-сполучити?
  (функція (shape-or-empty value)
    (нативна-форма-трибітного-ключа?
      (shape-or-empty value)
      так
      так
      так)))

(визначити нативний-план-доменного-сполучення
  (функція (shape-or-empty expression argument)
    (за-умовою
      ((атом? argument)
       (нативний-повернути-до-обчислювача expression))
      ((нативний-домен-сполучити? shape-or-empty (перше argument))
       (нативний-план-перше-сполучити expression argument))
      (так
       (нативний-повернути-до-обчислювача expression)))))

(визначити нативний-план-доменного-першого
  (функція (shape-or-empty expression)
    (за-умовою
      ((атом? (решта expression))
       (нативний-повернути-до-обчислювача expression))
      ((атом? (решта (решта expression)))
       (за-умовою
         ((тотожне? (решта (решта expression)) ())
          (нативний-план-доменного-сполучення
            shape-or-empty
            expression
            (перше (решта expression))))
         (так
          (нативний-повернути-до-обчислювача expression))))
      (так
       (нативний-повернути-до-обчислювача expression)))))

(визначити native-first-plan-domain
  (функція (shape-or-empty expression)
    (за-умовою
      ((атом? expression)
       (нативний-повернути-до-обчислювача expression))
      ((нативний-домен-перше? shape-or-empty (перше expression))
       (нативний-план-доменного-першого shape-or-empty expression))
      (так
       (нативний-повернути-до-обчислювача expression)))))