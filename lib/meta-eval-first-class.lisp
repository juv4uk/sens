; Experimental metacircular evaluator layer for contract 2.1 first-class builtins.
; This is deliberately additive: lib/meta-eval.lisp remains the current witness/oracle pair.
; The purpose here is to prove the next architectural step before merging it into my-eval:
; primitive names live in the metacircular environment as values, so ordinary lexical
; shadowing works for the evaluator written in Lisp too.
;
; Міграція: історичне ATOM(QUOTE EMPTY) як D1=YES → пряма точна проєкція #d1:1.
; Two-field COND. Reuses existing project primitives as first-class values.
; Width is identity; every bit of the domain address is valued.

(визначити my-fc-primitive
  (функція (назва)
    (список (як-є primitive) назва)))

(визначити my-fc-root-env
  (список
    (сполучити (як-є atom) (my-fc-primitive (як-є atom)))
    (сполучити (як-є eq)   (my-fc-primitive (як-є eq)))
    (сполучити (як-є car)  (my-fc-primitive (як-є car)))
    (сполучити (як-є cdr)  (my-fc-primitive (як-є cdr)))
    (сполучити (як-є cons) (my-fc-primitive (як-є cons)))
    (сполучити (як-є +)    (my-fc-primitive (як-є +)))
    (сполучити (як-є -)    (my-fc-primitive (як-є -)))
    (сполучити (як-є *)    (my-fc-primitive (як-є *)))
    (сполучити (як-є <)    (my-fc-primitive (як-є <)))
    (сполучити (як-є =)    (my-fc-primitive (як-є =)))
    (сполучити (як-є >)    (my-fc-primitive (як-є >)))))

(визначити my-fc-env-lookup
  (функція (назва оточення)
    (за-умовою
      ((атом? оточення) назва)
      ((тотожне? (перше (перше оточення)) назва) (решта (перше оточення)))
      (так (my-fc-env-lookup назва (решта оточення))))))

(визначити my-fc-primitive?
  (функція (значення)
    (за-умовою
      ((атом? значення) ні)
      (так (тотожне? (перше значення) (як-є primitive))))))

(визначити my-fc-closure?
  (функція (значення)
    (за-умовою
      ((атом? значення) ні)
      (так (тотожне? (перше значення) (як-є closure))))))

(визначити my-fc-bind-params
  (функція (параметри аргументи оточення)
    (за-умовою
      ((атом? параметри) оточення)
      (так
       (сполучити (сполучити (перше параметри) (перше аргументи))
            (my-fc-bind-params (решта параметри) (решта аргументи) оточення))))))

(визначити my-fc-eval-list
  (функція (вирази оточення)
    (за-умовою
      ((атом? вирази) (як-є ()))
      (так
       (сполучити (my-fc-eval (перше вирази) оточення)
            (my-fc-eval-list (решта вирази) оточення))))))

(визначити my-fc-eval-body
  (функція (тіло оточення)
    (за-умовою
      ((атом? (решта тіло)) (my-fc-eval (перше тіло) оточення))
      (так
       ((функція ()
          (my-fc-eval (перше тіло) оточення)
          (my-fc-eval-body (решта тіло) оточення)))))))

(визначити my-fc-eval-cond
  (функція (умови оточення)
    (за-умовою
      ((атом? умови) (як-є ()))
      ((my-fc-eval (перше (перше умови)) оточення)
       (my-fc-eval (друге (перше умови)) оточення))
      (так (my-fc-eval-cond (решта умови) оточення)))))

; Exact D1 chain: single remaining arg is true; pairwise op then recurse.
(визначити my-fc-compare-chain
  (функція (оператор аргументи)
    (за-умовою
      ((атом? (решта аргументи)) так)
      ((за-умовою
         ((тотожне? оператор (як-є <)) (менше? (перше аргументи) (друге аргументи)))
         ((тотожне? оператор (як-є =)) (однакові? (перше аргументи) (друге аргументи)))
         ((тотожне? оператор (як-є >)) (більше? (перше аргументи) (друге аргументи)))
         (так (як-є ())))
       (my-fc-compare-chain оператор (решта аргументи)))
      (так ні))))

(визначити my-fc-apply-primitive
  (функція (назва аргументи)
    (за-умовою
      ((тотожне? назва (як-є atom)) (атом? (перше аргументи)))
      ((тотожне? назва (як-є eq)) (тотожне? (перше аргументи) (друге аргументи)))
      ((тотожне? назва (як-є car)) (перше (перше аргументи)))
      ((тотожне? назва (як-є cdr)) (решта (перше аргументи)))
      ((тотожне? назва (як-є cons)) (сполучити (перше аргументи) (друге аргументи)))
      ((тотожне? назва (як-є +)) (додати (перше аргументи) (друге аргументи)))
      ((тотожне? назва (як-є -)) (відняти (перше аргументи) (друге аргументи)))
      ((тотожне? назва (як-є *)) (помножити (перше аргументи) (друге аргументи)))
      ((тотожне? назва (як-є <)) (my-fc-compare-chain (як-є <) аргументи))
      ((тотожне? назва (як-є =)) (my-fc-compare-chain (як-є =) аргументи))
      ((тотожне? назва (як-є >)) (my-fc-compare-chain (як-є >) аргументи))
      (так (список (як-є unknown-primitive) назва)))))

(визначити my-fc-apply
  (функція (виклична-функція аргументи)
    (за-умовою
      ((my-fc-primitive? виклична-функція)
       (my-fc-apply-primitive (друге виклична-функція) аргументи))
      ((my-fc-closure? виклична-функція)
       (my-fc-eval-body
         (третє виклична-функція)
         (my-fc-bind-params
           (друге виклична-функція)
           аргументи
           (перше (решта (решта (решта виклична-функція)))))))
      (так (список (як-є not-callable) виклична-функція)))))

(визначити my-fc-eval
  (функція (вираз оточення)
    (за-умовою
      ((атом? вираз) (my-fc-env-lookup вираз оточення))
      ((атом? (перше вираз))
       (за-умовою
         ; Syntax-only forms remain syntax. They are intentionally not values.
         ((тотожне? (перше вираз) (як-є quote)) (друге вираз))
         ((тотожне? (перше вираз) (як-є cond)) (my-fc-eval-cond (решта вираз) оточення))
         ((тотожне? (перше вираз) (як-є lambda))
          (список (як-є closure) (друге вираз) (решта (решта вираз)) оточення))
         ; Every ordinary head is resolved through the environment first.
         ; This is the contract-2.1 step: a local `+`, `car`, etc. can shadow
         ; the root primitive binding without the evaluator special-casing its name.
         (так
          (my-fc-apply
            (my-fc-eval (перше вираз) оточення)
            (my-fc-eval-list (решта вираз) оточення)))))
      (так
       (my-fc-apply
         (my-fc-eval (перше вираз) оточення)
         (my-fc-eval-list (решта вираз) оточення))))))

; Public experimental entry point. The root primitive environment is explicit
; Lisp data, so a future host/runtime only has to preserve the primitive mechanism
; identities; lexical resolution itself is owned here.
(визначити my-eval-first-class
  (функція (вираз)
    (my-fc-eval вираз my-fc-root-env)))
