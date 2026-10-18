; Experimental metacircular evaluator layer for contract 2.1 first-class builtins.
; This is deliberately additive: lib/meta-eval.lisp remains the current witness/oracle pair.
; The purpose here is to prove the next architectural step before merging it into my-eval:
; primitive names live in the metacircular environment as values, so ordinary lexical
; shadowing works for the evaluator written in Lisp too.
;
; Міграція: історичне ATOM(QUOTE EMPTY) як D1=YES → пряма точна проєкція #d1:1.
; Two-field COND. Reuses existing project primitives as first-class values.
; Width is identity; every bit of the domain address is valued.

(0011 my-fc-primitive
  (функція (name)
    (список (як-є primitive) name)))

(0011 my-fc-root-env
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

(0011 my-fc-env-lookup
  (функція (name ctx)
    (за-умовою
      ((атом? ctx) name)
      ((тотожне? (перше (перше ctx)) name) (решта (перше ctx)))
      (#d1:1 (my-fc-env-lookup name (011 ctx))))))

(0011 my-fc-primitive?
  (функція (value)
    (за-умовою
      ((010 value) #d1:0)
      (#d1:1 (101 (100 value) (001 primitive))))))

(0011 my-fc-closure?
  (функція (value)
    (за-умовою
      ((010 value) #d1:0)
      (#d1:1 (101 (100 value) (001 closure))))))

(0011 my-fc-bind-params
  (функція (params args ctx)
    (за-умовою
      ((атом? params) ctx)
      (#d1:1
       (сполучити (сполучити (перше params) (перше args))
            (my-fc-bind-params (решта params) (решта args) ctx))))))

(0011 my-fc-eval-list
  (функція (exprs ctx)
    (за-умовою
      ((атом? exprs) (як-є ()))
      (#d1:1
       (сполучити (my-fc-eval (перше exprs) ctx)
            (my-fc-eval-list (решта exprs) ctx))))))

(0011 my-fc-eval-body
  (функція (body ctx)
    (за-умовою
      ((атом? (решта body)) (my-fc-eval (перше body) ctx))
      (#d1:1
       ((функція ()
          (my-fc-eval (перше body) ctx)
          (my-fc-eval-body (решта body) ctx)))))))

(0011 my-fc-eval-cond
  (функція (clauses ctx)
    (за-умовою
      ((атом? clauses) (як-є ()))
      ((my-fc-eval (перше (перше clauses)) ctx)
       (my-fc-eval (друге (перше clauses)) ctx))
      (#d1:1 (my-fc-eval-cond (011 clauses) ctx)))))

; Exact D1 chain: single remaining arg is true; pairwise op then recurse.
(0011 my-fc-compare-chain
  (функція (op args)
    (за-умовою
      ((010 (011 args)) #d1:1)
      ((за-умовою
         ((101 op (001 <)) (11010 (100 args) (1001 args)))
         ((101 op (001 =)) (11110111 (100 args) (1001 args)))
         ((101 op (001 >)) (11011 (100 args) (1001 args)))
         (#d1:1 (001 ())))
       (my-fc-compare-chain op (решта args)))
      (#d1:1 #d1:0))))

(0011 my-fc-apply-primitive
  (функція (name args)
    (за-умовою
      ((тотожне? name (як-є atom)) (атом? (перше args)))
      ((тотожне? name (як-є eq)) (тотожне? (перше args) (друге args)))
      ((тотожне? name (як-є car)) (перше (перше args)))
      ((тотожне? name (як-є cdr)) (решта (перше args)))
      ((тотожне? name (як-є cons)) (сполучити (перше args) (друге args)))
      ((101 name (001 +)) (01010 (100 args) (1001 args)))
      ((101 name (001 -)) (01011 (100 args) (1001 args)))
      ((101 name (001 *)) (10110 (100 args) (1001 args)))
      ((тотожне? name (як-є <)) (my-fc-compare-chain (як-є <) args))
      ((тотожне? name (як-є =)) (my-fc-compare-chain (як-є =) args))
      ((тотожне? name (як-є >)) (my-fc-compare-chain (як-є >) args))
      (#d1:1 (1110 (001 unknown-primitive) name)))))

(0011 my-fc-apply
  (функція (fn args)
    (за-умовою
      ((my-fc-primitive? fn)
       (my-fc-apply-primitive (друге fn) args))
      ((my-fc-closure? fn)
       (my-fc-eval-body
         (10011 fn)
         (my-fc-bind-params
           (друге fn)
           args
           (перше (решта (решта (решта fn)))))))
      (#d1:1 (1110 (001 not-callable) fn)))))

(0011 my-fc-eval
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
         (#d1:1
          (my-fc-apply
            (my-fc-eval (перше expr) ctx)
            (my-fc-eval-list (решта expr) ctx)))))
      (#d1:1
       (my-fc-apply
         (my-fc-eval (перше expr) ctx)
         (my-fc-eval-list (решта expr) ctx))))))

; Public experimental entry point. The root primitive environment is explicit
; Lisp data, so a future host/runtime only has to preserve the primitive mechanism
; identities; lexical resolution itself is owned here.
(0011 my-eval-first-class
  (функція (expr)
    (my-fc-eval expr my-fc-root-env)))
