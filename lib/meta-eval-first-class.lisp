; Experimental metacircular evaluator layer for contract 2.1 first-class builtins.
; This is deliberately additive: lib/meta-eval.lisp remains the current witness/oracle pair.
; The purpose here is to prove the next architectural step before merging it into my-eval:
; primitive names live in the metacircular environment as values, so ordinary lexical
; shadowing works for the evaluator written in Lisp too.

(00001001 my-fc-primitive
  (00001000 (name)
    (00100111 (00000001 primitive) name)))

(00001001 my-fc-root-env
  (00100111
    (00000100 (00000001 atom) (my-fc-primitive (00000001 atom)))
    (00000100 (00000001 eq)   (my-fc-primitive (00000001 eq)))
    (00000100 (00000001 car)  (my-fc-primitive (00000001 car)))
    (00000100 (00000001 cdr)  (my-fc-primitive (00000001 cdr)))
    (00000100 (00000001 cons) (my-fc-primitive (00000001 cons)))
    (00000100 (00000001 +)    (my-fc-primitive (00000001 +)))
    (00000100 (00000001 -)    (my-fc-primitive (00000001 -)))
    (00000100 (00000001 *)    (my-fc-primitive (00000001 *)))
    (00000100 (00000001 <)    (my-fc-primitive (00000001 <)))
    (00000100 (00000001 =)    (my-fc-primitive (00000001 =)))
    (00000100 (00000001 >)    (my-fc-primitive (00000001 >)))))

(00001001 my-fc-env-lookup
  (00001000 (name env)
    (00000111
      
      ((00000010 env)  name)
      ((00000011 (00000101 (00000101 env)) name) (00000110 (00000101 env)))
      (1 (my-fc-env-lookup name (00000110 env))))))

(00001001 my-fc-primitive?
  (00001000 (value)
    (00000111
      
      ((00000010 value)  (00000001 ()))
      (1 (00000011 (00000101 value) (00000001 primitive))))))

(00001001 my-fc-closure?
  (00001000 (value)
    (00000111
      
      ((00000010 value)  (00000001 ()))
      (1 (00000011 (00000101 value) (00000001 closure))))))

(00001001 my-fc-bind-params
  (00001000 (params args env)
    (00000111
      
      ((00000010 params)  env)
      (1 (00000100 (00000100 (00000101 params) (00000101 args))
               (my-fc-bind-params (00000110 params) (00000110 args) env))))))

(00001001 my-fc-eval-list
  (00001000 (exprs env)
    (00000111
      
      ((00000010 exprs)  (00000001 ()))
      (1 (00000100 (my-fc-eval (00000101 exprs) env)
               (my-fc-eval-list (00000110 exprs) env))))))

(00001001 my-fc-eval-body
  (00001000 (body env)
    (00000111
      
      ((00000010 (00000110 body))  (my-fc-eval (00000101 body) env))
      (1 ((00001000 ()
            (my-fc-eval (00000101 body) env)
            (my-fc-eval-body (00000110 body) env)))))))

(00001001 my-fc-eval-cond
  (00001000 (clauses env)
    (00000111
      
      ((00000010 clauses)  (00000001 ()))
      ((my-fc-eval (00000101 (00000101 clauses)) env)
       (my-fc-eval (00101111 (00000101 clauses)) env))
      (1 (my-fc-eval-cond (00000110 clauses) env)))))

(00001001 my-fc-compare-chain
  (00001000 (op args)
    (00000111
      
      ((00000010 (00000110 args))  t)
      ((00000111
         ((00000011 op (00000001 <)) (00011010 (00000101 args) (00101111 args)))
         ((00000011 op (00000001 =)) (00011100 (00000101 args) (00101111 args)))
         ((00000011 op (00000001 >)) (00011011 (00000101 args) (00101111 args)))
         (1 (00000001 ())))
       (my-fc-compare-chain op (00000110 args)))
      (1 (00000001 ())))))

(00001001 my-fc-apply-primitive
  (00001000 (name args)
    (00000111
      ((00000011 name (00000001 atom)) (00000010 (00000101 args)))
      ((00000011 name (00000001 eq)) (00000011 (00000101 args) (00101111 args)))
      ((00000011 name (00000001 car)) (00000101 (00000101 args)))
      ((00000011 name (00000001 cdr)) (00000110 (00000101 args)))
      ((00000011 name (00000001 cons)) (00000100 (00000101 args) (00101111 args)))
      ((00000011 name (00000001 +)) (00001100 (00000101 args) (00101111 args)))
      ((00000011 name (00000001 -)) (00001101 (00000101 args) (00101111 args)))
      ((00000011 name (00000001 *)) (00001110 (00000101 args) (00101111 args)))
      ((00000011 name (00000001 <)) (my-fc-compare-chain (00000001 <) args))
      ((00000011 name (00000001 =)) (my-fc-compare-chain (00000001 =) args))
      ((00000011 name (00000001 >)) (my-fc-compare-chain (00000001 >) args))
      (1 (00100111 (00000001 unknown-primitive) name)))))

(00001001 my-fc-apply
  (00001000 (fn args)
    (00000111
      ((my-fc-primitive? fn)
       (my-fc-apply-primitive (00101111 fn) args))
      ((my-fc-closure? fn)
       (my-fc-eval-body
         (00110000 fn)
         (my-fc-bind-params
           (00101111 fn)
           args
           (00000101 (00000110 (00000110 (00000110 fn)))))))
      (1 (00100111 (00000001 not-callable) fn)))))

(00001001 my-fc-eval
  (00001000 (expr env)
    (00000111
      
      ((00000010 expr)  (my-fc-env-lookup expr env))
      
      ((00000010 (00000101 expr))  (00000111
         ; Syntax-only forms remain syntax. They are intentionally not values.
         ((00000011 (00000101 expr) (00000001 quote)) (00101111 expr))
         ((00000011 (00000101 expr) (00000001 cond)) (my-fc-eval-cond (00000110 expr) env))
         ((00000011 (00000101 expr) (00000001 lambda))
          (00100111 (00000001 closure) (00101111 expr) (00000110 (00000110 expr)) env))
         ; Every ordinary head is resolved through the environment first.
         ; This is the contract-2.1 step: a local `+`, `car`, etc. can shadow
         ; the root primitive binding without the evaluator special-casing its name.
         (1 (my-fc-apply
              (my-fc-eval (00000101 expr) env)
              (my-fc-eval-list (00000110 expr) env)))))
      (1 (my-fc-apply
           (my-fc-eval (00000101 expr) env)
           (my-fc-eval-list (00000110 expr) env))))))

; Public experimental entry point.  The root primitive environment is explicit
; Lisp data, so a future host/runtime only has to preserve the primitive mechanism
; identities; lexical resolution itself is owned here.
(00001001 my-eval-first-class
  (00001000 (expr)
    (my-fc-eval expr my-fc-root-env)))
