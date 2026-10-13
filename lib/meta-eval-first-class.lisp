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
  (0010 (name)
    (1110 (001 primitive) name)))

(0011 my-fc-root-env
  (1110
    (111 (001 atom) (my-fc-primitive (001 atom)))
    (111 (001 eq)   (my-fc-primitive (001 eq)))
    (111 (001 car)  (my-fc-primitive (001 car)))
    (111 (001 cdr)  (my-fc-primitive (001 cdr)))
    (111 (001 cons) (my-fc-primitive (001 cons)))
    (111 (001 +)    (my-fc-primitive (001 +)))
    (111 (001 -)    (my-fc-primitive (001 -)))
    (111 (001 *)    (my-fc-primitive (001 *)))
    (111 (001 <)    (my-fc-primitive (001 <)))
    (111 (001 =)    (my-fc-primitive (001 =)))
    (111 (001 >)    (my-fc-primitive (001 >)))))

(0011 my-fc-env-lookup
  (0010 (name env)
    (110
      ((010 env) name)
      ((101 (100 (100 env)) name) (011 (100 env)))
      (#d1:1 (my-fc-env-lookup name (011 env))))))

(0011 my-fc-primitive?
  (0010 (value)
    (110
      ((010 value) (001 ()))
      (#d1:1 (101 (100 value) (001 primitive))))))

(0011 my-fc-closure?
  (0010 (value)
    (110
      ((010 value) (001 ()))
      (#d1:1 (101 (100 value) (001 closure))))))

(0011 my-fc-bind-params
  (0010 (params args env)
    (110
      ((010 params) env)
      (#d1:1
       (111 (111 (100 params) (100 args))
            (my-fc-bind-params (011 params) (011 args) env))))))

(0011 my-fc-eval-list
  (0010 (exprs env)
    (110
      ((010 exprs) (001 ()))
      (#d1:1
       (111 (my-fc-eval (100 exprs) env)
            (my-fc-eval-list (011 exprs) env))))))

(0011 my-fc-eval-body
  (0010 (body env)
    (110
      ((010 (011 body)) (my-fc-eval (100 body) env))
      (#d1:1
       ((0010 ()
          (my-fc-eval (100 body) env)
          (my-fc-eval-body (011 body) env)))))))

(0011 my-fc-eval-cond
  (0010 (clauses env)
    (110
      ((010 clauses) (001 ()))
      ((my-fc-eval (100 (100 clauses)) env)
       (my-fc-eval (1001 (100 clauses)) env))
      (#d1:1 (my-fc-eval-cond (011 clauses) env)))))

; Exact D1 chain: single remaining arg is true; pairwise op then recurse.
(0011 my-fc-compare-chain
  (0010 (op args)
    (110
      ((010 (011 args)) #d1:1)
      ((110
         ((101 op (001 <)) (11010 (100 args) (1001 args)))
         ((101 op (001 =)) (11110111 (100 args) (1001 args)))
         ((101 op (001 >)) (11011 (100 args) (1001 args)))
         (#d1:1 (001 ())))
       (my-fc-compare-chain op (011 args)))
      (#d1:1 (001 ())))))

(0011 my-fc-apply-primitive
  (0010 (name args)
    (110
      ((101 name (001 atom)) (010 (100 args)))
      ((101 name (001 eq)) (101 (100 args) (1001 args)))
      ((101 name (001 car)) (100 (100 args)))
      ((101 name (001 cdr)) (011 (100 args)))
      ((101 name (001 cons)) (111 (100 args) (1001 args)))
      ((101 name (001 +)) (01010 (100 args) (1001 args)))
      ((101 name (001 -)) (01011 (100 args) (1001 args)))
      ((101 name (001 *)) (10110 (100 args) (1001 args)))
      ((101 name (001 <)) (my-fc-compare-chain (001 <) args))
      ((101 name (001 =)) (my-fc-compare-chain (001 =) args))
      ((101 name (001 >)) (my-fc-compare-chain (001 >) args))
      (#d1:1 (1110 (001 unknown-primitive) name)))))

(0011 my-fc-apply
  (0010 (fn args)
    (110
      ((my-fc-primitive? fn)
       (my-fc-apply-primitive (1001 fn) args))
      ((my-fc-closure? fn)
       (my-fc-eval-body
         (10011 fn)
         (my-fc-bind-params
           (1001 fn)
           args
           (100 (011 (011 (011 fn)))))))
      (#d1:1 (1110 (001 not-callable) fn)))))

(0011 my-fc-eval
  (0010 (expr env)
    (110
      ((010 expr) (my-fc-env-lookup expr env))
      ((010 (100 expr))
       (110
         ; Syntax-only forms remain syntax. They are intentionally not values.
         ((101 (100 expr) (001 quote)) (1001 expr))
         ((101 (100 expr) (001 cond)) (my-fc-eval-cond (011 expr) env))
         ((101 (100 expr) (001 lambda))
          (1110 (001 closure) (1001 expr) (011 (011 expr)) env))
         ; Every ordinary head is resolved through the environment first.
         ; This is the contract-2.1 step: a local `+`, `car`, etc. can shadow
         ; the root primitive binding without the evaluator special-casing its name.
         (#d1:1
          (my-fc-apply
            (my-fc-eval (100 expr) env)
            (my-fc-eval-list (011 expr) env)))))
      (#d1:1
       (my-fc-apply
         (my-fc-eval (100 expr) env)
         (my-fc-eval-list (011 expr) env))))))

; Public experimental entry point. The root primitive environment is explicit
; Lisp data, so a future host/runtime only has to preserve the primitive mechanism
; identities; lexical resolution itself is owned here.
(0011 my-eval-first-class
  (0010 (expr)
    (my-fc-eval expr my-fc-root-env)))
