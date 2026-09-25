; Experimental metacircular evaluator layer for contract 2.1 first-class builtins.
; This is deliberately additive: lib/meta-eval.lisp remains the current witness/oracle pair.
; The purpose here is to prove the next architectural step before merging it into my-eval:
; primitive names live in the metacircular environment as values, so ordinary lexical
; shadowing works for the evaluator written in Lisp too.

(def my-fc-primitive
  (lambda (name)
    (list (quote primitive) name)))

(def my-fc-root-env
  (list
    (cons (quote atom) (my-fc-primitive (quote atom)))
    (cons (quote eq)   (my-fc-primitive (quote eq)))
    (cons (quote car)  (my-fc-primitive (quote car)))
    (cons (quote cdr)  (my-fc-primitive (quote cdr)))
    (cons (quote cons) (my-fc-primitive (quote cons)))
    (cons (quote +)    (my-fc-primitive (quote +)))
    (cons (quote -)    (my-fc-primitive (quote -)))
    (cons (quote *)    (my-fc-primitive (quote *)))
    (cons (quote <)    (my-fc-primitive (quote <)))
    (cons (quote =)    (my-fc-primitive (quote =)))
    (cons (quote >)    (my-fc-primitive (quote >)))))

(def my-fc-env-lookup
  (lambda (name env)
    (cond
      ((atom? env) name)
      ((eq? (car (car env)) name) (cdr (car env)))
      (t (my-fc-env-lookup name (cdr env))))))

(def my-fc-primitive?
  (lambda (value)
    (cond
      ((atom? value) (quote ()))
      (t (eq? (car value) (quote primitive))))))

(def my-fc-closure?
  (lambda (value)
    (cond
      ((atom? value) (quote ()))
      (t (eq? (car value) (quote closure))))))

(def my-fc-bind-params
  (lambda (params args env)
    (cond
      ((atom? params) env)
      (t (cons (cons (car params) (car args))
               (my-fc-bind-params (cdr params) (cdr args) env))))))

(def my-fc-eval-list
  (lambda (exprs env)
    (cond
      ((atom? exprs) (quote ()))
      (t (cons (my-fc-eval (car exprs) env)
               (my-fc-eval-list (cdr exprs) env))))))

(def my-fc-eval-body
  (lambda (body env)
    (cond
      ((atom? (cdr body)) (my-fc-eval (car body) env))
      (t ((lambda ()
            (my-fc-eval (car body) env)
            (my-fc-eval-body (cdr body) env)))))))

(def my-fc-eval-cond
  (lambda (clauses env)
    (cond
      ((atom? clauses) (quote ()))
      ((my-fc-eval (car (car clauses)) env)
       (my-fc-eval (second (car clauses)) env))
      (t (my-fc-eval-cond (cdr clauses) env)))))

(def my-fc-compare-chain
  (lambda (op args)
    (cond
      ((atom? (cdr args)) t)
      ((cond
         ((eq? op (quote <)) (< (car args) (second args)))
         ((eq? op (quote =)) (= (car args) (second args)))
         ((eq? op (quote >)) (> (car args) (second args)))
         (t (quote ())))
       (my-fc-compare-chain op (cdr args)))
      (t (quote ())))))

(def my-fc-apply-primitive
  (lambda (name args)
    (cond
      ((eq? name (quote atom)) (atom? (car args)))
      ((eq? name (quote eq)) (eq? (car args) (second args)))
      ((eq? name (quote car)) (car (car args)))
      ((eq? name (quote cdr)) (cdr (car args)))
      ((eq? name (quote cons)) (cons (car args) (second args)))
      ((eq? name (quote +)) (+ (car args) (second args)))
      ((eq? name (quote -)) (- (car args) (second args)))
      ((eq? name (quote *)) (* (car args) (second args)))
      ((eq? name (quote <)) (my-fc-compare-chain (quote <) args))
      ((eq? name (quote =)) (my-fc-compare-chain (quote =) args))
      ((eq? name (quote >)) (my-fc-compare-chain (quote >) args))
      (t (list (quote unknown-primitive) name)))))

(def my-fc-apply
  (lambda (fn args)
    (cond
      ((my-fc-primitive? fn)
       (my-fc-apply-primitive (second fn) args))
      ((my-fc-closure? fn)
       (my-fc-eval-body
         (third fn)
         (my-fc-bind-params
           (second fn)
           args
           (car (cdr (cdr (cdr fn)))))))
      (t (list (quote not-callable) fn)))))

(def my-fc-eval
  (lambda (expr env)
    (cond
      ((atom? expr) (my-fc-env-lookup expr env))
      ((atom? (car expr))
       (cond
         ; Syntax-only forms remain syntax. They are intentionally not values.
         ((eq? (car expr) (quote quote)) (second expr))
         ((eq? (car expr) (quote cond)) (my-fc-eval-cond (cdr expr) env))
         ((eq? (car expr) (quote lambda))
          (list (quote closure) (second expr) (cdr (cdr expr)) env))
         ; Every ordinary head is resolved through the environment first.
         ; This is the contract-2.1 step: a local `+`, `car`, etc. can shadow
         ; the root primitive binding without the evaluator special-casing its name.
         (t (my-fc-apply
              (my-fc-eval (car expr) env)
              (my-fc-eval-list (cdr expr) env)))))
      (t (my-fc-apply
           (my-fc-eval (car expr) env)
           (my-fc-eval-list (cdr expr) env))))))

; Public experimental entry point.  The root primitive environment is explicit
; Lisp data, so a future host/runtime only has to preserve the primitive mechanism
; identities; lexical resolution itself is owned here.
(def my-eval-first-class
  (lambda (expr)
    (my-fc-eval expr my-fc-root-env)))
