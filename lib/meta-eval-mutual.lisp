; Experimental extension for mutually recursive top-level lambda definitions.
; Load after the current Core4 profile (`lib/core4.lisp`) and lib/meta-eval.lisp.
;
; Міграція: 10 однозв'язувальних D6:001000 LET усунено через чинну D4:0010 LAMBDA.
; Семантика: те саме одноразове обчислення аргументу, те саме локальне зв'язування.
; Двопольний D3 COND; резервна умова — прямий однобітний D1:YES.
; Reuses existing meta-eval surface: my-apply, my-eval-body, bind-params,
; env-lookup, my-macro?, my-lambda-form?, my-fifth, my-fourth.
; Width is identity; every bit of the domain address is valued.
;
; Consecutive top-level `(def name (lambda ...))` forms are treated as one
; finite recursive group. No cyclic Rust Environment is required.
;
; A group closure stores the raw finite group as Lisp data:
;   (recursive-group-closure name params body group captured-env)
;
; At call time the group environment is reconstructed from that data.

; D3:110 condition requires an exact D1 control bit, not quoted D3 empty.
; These two predicates return D1:0 on negative branches so callers can
; compose them inside D3 COND without historical truthiness.
(0011 my-group-closure?
  (функція (value)
    (за-умовою
      ((010 value) #d1:0)
      (#d1:1 (101 (100 value) (001 recursive-group-closure))))))

(0011 my-sixth
  (функція (values)
    (перше (решта (решта (решта (решта (решта values))))))))

(0011 my-lambda-def-form?
  (функція (form)
    (за-умовою
      ((010 form) #d1:0)
      ((тотожне? (перше form) (як-є def))
       (my-lambda-form? (10011 form)))
      (#d1:1 #d1:0))))

(0011 my-take-lambda-def-group
  (функція (forms)
    (за-умовою
      ((атом? forms) (як-є ()))
      ((my-lambda-def-form? (перше forms))
       (сполучити (перше forms)
            (my-take-lambda-def-group (решта forms))))
      (#d1:1 (001 ())))))

(0011 my-drop-lambda-def-group
  (функція (forms)
    (за-умовою
      ((атом? forms) (як-є ()))
      ((my-lambda-def-form? (перше forms))
       (my-drop-lambda-def-group (решта forms)))
      (#d1:1 forms))))

(0011 my-group-closure-from-def
  (функція (form group captured-env)
    ((функція (lambda-form) (список (як-є recursive-group-closure)
            (друге form)
            (друге lambda-form)
            (решта (решта lambda-form))
            group
            captured-env)) (10011 form))))

; Build onto the captured environment so later definitions in the same group
; appear earlier in the alist, matching same-frame overwrite order.
(0011 my-build-group-env-onto
  (функція (forms group captured-env out)
    (за-умовою
      ((атом? forms) out)
      (#d1:1
       ((функція (form) (my-build-group-env-onto
           (решта forms)
           group
           captured-env
           (сполучити
             (сполучити (друге form)
                   (my-group-closure-from-def form group captured-env))
             out))) (перше forms))))))

(0011 my-build-group-env
  (функція (group captured-env)
    (my-build-group-env-onto group group captured-env captured-env)))

(0011 my-apply-group-closure
  (функція (fn args)
    ((функція (group-env) (my-eval-body
        (my-fourth fn)
        (bind-params
          (10011 fn)
          args
          group-env))) (my-build-group-env (my-fifth fn) (my-sixth fn)))))

; Apply wrapper: group closures go through group path; others reuse my-apply.
(0011 my-group-apply
  (функція (fn args)
    (за-умовою
      ((my-group-closure? fn) (my-apply-group-closure fn args))
      (#d1:1 (my-apply fn args)))))

(0011 my-group-eval-list
  (функція (exprs env)
    (за-умовою
      ((атом? exprs) (як-є ()))
      (#d1:1
       (сполучити (my-group-eval (перше exprs) env)
            (my-group-eval-list (решта exprs) env))))))

(0011 my-group-eval-body
  (функція (body env)
    (за-умовою
      ((атом? (решта body)) (my-group-eval (перше body) env))
      (#d1:1
       ((функція ()
          (my-group-eval (перше body) env)
          (my-group-eval-body (решта body) env)))))))

(0011 my-group-eval-cond
  (функція (clauses env)
    (за-умовою
      ((атом? clauses) (як-є ()))
      ((my-group-eval (перше (перше clauses)) env)
       (my-group-eval (друге (перше clauses)) env))
      (#d1:1 (my-group-eval-cond (011 clauses) env)))))

(0011 my-group-apply-owned
  (функція (fn args)
    (за-умовою
      ((my-group-closure? fn)
       ((функція (group-env) (my-group-eval-body
           (my-fourth fn)
           (bind-params (10011 fn) args group-env))) (my-build-group-env (my-fifth fn) (my-sixth fn))))
      (#d1:1 (my-apply fn args)))))

(0011 my-group-eval
  (функція (expr env)
    (за-умовою
      ((атом? expr) (env-lookup expr env))
      ((атом? (перше expr))
       (за-умовою
         ((тотожне? (перше expr) (як-є quote)) (друге expr))
         ((тотожне? (перше expr) (як-є cond))
          (my-group-eval-cond (решта expr) env))
         ((тотожне? (перше expr) (як-є lambda))
          (список (як-є closure) (друге expr) (решта (решта expr)) env))
         (#d1:1
          ((функція (fn) (за-умовою
              ((my-macro? fn)
               (my-group-eval (my-apply fn (решта expr)) env))
              (#d1:1
               (my-group-apply-owned
                 fn
                 (my-group-eval-list (решта expr) env))))) (my-group-eval (перше expr) env)))))
      (#d1:1
       (my-group-apply-owned
         (my-group-eval (перше expr) env)
         (my-group-eval-list (решта expr) env))))))

(0011 my-group-eval-top-form
  (функція (form env)
    (за-умовою
      ((атом? form) (сполучити env (my-group-eval form env)))
      ((тотожне? (перше form) (як-є def))
       ((0010 (value) (111 (111 (111 (1001 form) value) env) value)) (my-group-eval (10011 form) env)))
      ((тотожне? (перше form) (як-є defmacro))
       (my-eval-top-form form env))
      (#d1:1 (111 env (my-group-eval form env))))))

(0011 my-eval-program-with-groups
  (функція (forms env)
    (за-умовою
      ((my-lambda-def-form? (перше forms))
       ((функція (group) ((функція (rest) ((функція (group-env) (за-умовою
               ((атом? rest) (сполучити group-env (решта (перше group-env))))
               (#d1:1 (my-eval-program-with-groups rest group-env)))) (my-build-group-env group env))) (my-drop-lambda-def-group forms))) (my-take-lambda-def-group forms)))
      (#d1:1
       ((функція (result) (за-умовою
           ((атом? (решта forms)) result)
           (#d1:1
            (my-eval-program-with-groups
              (решта forms)
              (перше result))))) (my-group-eval-top-form (перше forms) env))))))
