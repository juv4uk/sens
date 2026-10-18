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
  (функція (name)
    (список (як-є primitive) name)))

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
  (функція (name ctx)
    (за-умовою
      ((атом? ctx) name)
      ((тотожне? (перше (перше ctx)) name) (решта (перше ctx)))
      (так (my-fc-env-lookup name (решта ctx))))))

(визначити my-fc-primitive?
  (функція (value)
    (за-умовою
      ((атом? value) ні)
      (так (тотожне? (перше value) (як-є primitive))))))

(визначити my-fc-closure?
  (функція (value)
    (за-умовою
      ((атом? value) ні)
      (так (тотожне? (перше value) (як-є closure))))))

(визначити my-fc-bind-params
  (функція (params args ctx)
    (за-умовою
      ((атом? params) ctx)
      (так
       (сполучити (сполучити (перше params) (перше args))
            (my-fc-bind-params (решта params) (решта args) ctx))))))

(визначити my-fc-eval-list
  (функція (exprs ctx)
    (за-умовою
      ((атом? exprs) (як-є ()))
      (так
       (сполучити (my-fc-eval (перше exprs) ctx)
            (my-fc-eval-list (решта exprs) ctx))))))

(визначити my-fc-eval-body
  (функція (body ctx)
    (за-умовою
      ((атом? (решта body)) (my-fc-eval (перше body) ctx))
      (так
       ((функція ()
          (my-fc-eval (перше body) ctx)
          (my-fc-eval-body (решта body) ctx)))))))

(визначити my-fc-eval-cond
  (функція (clauses ctx)
    (за-умовою
      ((атом? clauses) (як-є ()))
      ((my-fc-eval (перше (перше clauses)) ctx)
       (my-fc-eval (друге (перше clauses)) ctx))
      (так (my-fc-eval-cond (решта clauses) ctx)))))

; Exact D1 chain: single remaining arg is true; pairwise op then recurse.
(визначити my-fc-compare-chain
  (функція (op args)
    (за-умовою
      ((атом? (решта args)) так)
      ((за-умовою
         ((тотожне? op (як-є <)) (менше? (перше args) (друге args)))
         ((тотожне? op (як-є =)) (однакові? (перше args) (друге args)))
         ((тотожне? op (як-є >)) (більше? (перше args) (друге args)))
         (так (як-є ())))
       (my-fc-compare-chain op (решта args)))
      (так ні))))

(визначити my-fc-apply-primitive
  (функція (name args)
    (за-умовою
      ((тотожне? name (як-є atom)) (атом? (перше args)))
      ((тотожне? name (як-є eq)) (тотожне? (перше args) (друге args)))
      ((тотожне? name (як-є car)) (перше (перше args)))
      ((тотожне? name (як-є cdr)) (решта (перше args)))
      ((тотожне? name (як-є cons)) (сполучити (перше args) (друге args)))
      ((тотожне? name (як-є +)) (додати (перше args) (друге args)))
      ((тотожне? name (як-є -)) (відняти (перше args) (друге args)))
      ((тотожне? name (як-є *)) (помножити (перше args) (друге args)))
      ((тотожне? name (як-є <)) (my-fc-compare-chain (як-є <) args))
      ((тотожне? name (як-є =)) (my-fc-compare-chain (як-є =) args))
      ((тотожне? name (як-є >)) (my-fc-compare-chain (як-є >) args))
      (так (список (як-є unknown-primitive) name)))))

(визначити my-fc-apply
  (функція (fn args)
    (за-умовою
      ((my-fc-primitive? fn)
       (my-fc-apply-primitive (друге fn) args))
      ((my-fc-closure? fn)
       (my-fc-eval-body
         (третє fn)
         (my-fc-bind-params
           (друге fn)
           args
           (перше (решта (решта (решта fn)))))))
      (так (список (як-є not-callable) fn)))))

(визначити my-fc-eval
  (функція (expr ctx)
    (за-умовою
      ((атом? expr) (my-fc-env-lookup expr ctx))
      ((атом? (перше expr))
       (за-умовою
         ; Syntax-only forms remain syntax. They are intentionally not values.
         ((тотожне? (перше expr) (як-є quote)) (друге expr))
         ((тотожне? (перше expr) (як-є cond)) (my-fc-eval-cond (решта expr) ctx))
         ((тотожне? (перше expr) (як-є lambda))
          (список (як-є closure) (друге expr) (решта (решта expr)) ctx))
         ; Every ordinary head is resolved through the environment first.
         ; This is the contract-2.1 step: a local `+`, `car`, etc. can shadow
         ; the root primitive binding without the evaluator special-casing its name.
         (так
          (my-fc-apply
            (my-fc-eval (перше expr) ctx)
            (my-fc-eval-list (решта expr) ctx)))))
      (так
       (my-fc-apply
         (my-fc-eval (перше expr) ctx)
         (my-fc-eval-list (решта expr) ctx))))))

; Public experimental entry point. The root primitive environment is explicit
; Lisp data, so a future host/runtime only has to preserve the primitive mechanism
; identities; lexical resolution itself is owned here.
(визначити my-eval-first-class
  (функція (expr)
    (my-fc-eval expr my-fc-root-env)))
