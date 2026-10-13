; Experimental extension for mutually recursive top-level lambda definitions.
; Load after the current Core4 profile (`lib/core4.lisp`) and lib/meta-eval.lisp.
;
; Міграція: 10 однозв'язувальних D6:001000 LET усунено через чинну D4:0010 LAMBDA.
; Семантика: те саме одноразове обчислення аргументу, те саме локальне зв'язування.
; Two-field D3 COND and exact D1 fallback (010 (001 ())) preserved.
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

(0011 my-group-closure?
  (0010 (value)
    (110
      ((010 value) (001 ()))
      ((010 (001 ())) (101 (100 value) (001 recursive-group-closure))))))

(0011 my-sixth
  (0010 (values)
    (100 (011 (011 (011 (011 (011 values))))))))

(0011 my-lambda-def-form?
  (0010 (form)
    (110
      ((010 form) (001 ()))
      ((101 (100 form) (001 def))
       (my-lambda-form? (10011 form)))
      ((010 (001 ())) (001 ())))))

(0011 my-take-lambda-def-group
  (0010 (forms)
    (110
      ((010 forms) (001 ()))
      ((my-lambda-def-form? (100 forms))
       (111 (100 forms)
            (my-take-lambda-def-group (011 forms))))
      ((010 (001 ())) (001 ())))))

(0011 my-drop-lambda-def-group
  (0010 (forms)
    (110
      ((010 forms) (001 ()))
      ((my-lambda-def-form? (100 forms))
       (my-drop-lambda-def-group (011 forms)))
      ((010 (001 ())) forms))))

(0011 my-group-closure-from-def
  (0010 (form group captured-env)
    ((0010 (lambda-form) (1110 (001 recursive-group-closure)
            (1001 form)
            (1001 lambda-form)
            (011 (011 lambda-form))
            group
            captured-env)) (10011 form))))

; Build onto the captured environment so later definitions in the same group
; appear earlier in the alist, matching same-frame overwrite order.
(0011 my-build-group-env-onto
  (0010 (forms group captured-env out)
    (110
      ((010 forms) out)
      ((010 (001 ()))
       ((0010 (form) (my-build-group-env-onto
           (011 forms)
           group
           captured-env
           (111
             (111 (1001 form)
                   (my-group-closure-from-def form group captured-env))
             out))) (100 forms))))))

(0011 my-build-group-env
  (0010 (group captured-env)
    (my-build-group-env-onto group group captured-env captured-env)))

(0011 my-apply-group-closure
  (0010 (fn args)
    ((0010 (group-env) (my-eval-body
        (my-fourth fn)
        (bind-params
          (10011 fn)
          args
          group-env))) (my-build-group-env (my-fifth fn) (my-sixth fn)))))

; Apply wrapper: group closures go through group path; others reuse my-apply.
(0011 my-group-apply
  (0010 (fn args)
    (110
      ((my-group-closure? fn) (my-apply-group-closure fn args))
      ((010 (001 ())) (my-apply fn args)))))

(0011 my-group-eval-list
  (0010 (exprs env)
    (110
      ((010 exprs) (001 ()))
      ((010 (001 ()))
       (111 (my-group-eval (100 exprs) env)
            (my-group-eval-list (011 exprs) env))))))

(0011 my-group-eval-body
  (0010 (body env)
    (110
      ((010 (011 body)) (my-group-eval (100 body) env))
      ((010 (001 ()))
       ((0010 ()
          (my-group-eval (100 body) env)
          (my-group-eval-body (011 body) env)))))))

(0011 my-group-eval-cond
  (0010 (clauses env)
    (110
      ((010 clauses) (001 ()))
      ((my-group-eval (100 (100 clauses)) env)
       (my-group-eval (1001 (100 clauses)) env))
      ((010 (001 ())) (my-group-eval-cond (011 clauses) env)))))

(0011 my-group-apply-owned
  (0010 (fn args)
    (110
      ((my-group-closure? fn)
       ((0010 (group-env) (my-group-eval-body
           (my-fourth fn)
           (bind-params (10011 fn) args group-env))) (my-build-group-env (my-fifth fn) (my-sixth fn))))
      ((010 (001 ())) (my-apply fn args)))))

(0011 my-group-eval
  (0010 (expr env)
    (110
      ((010 expr) (env-lookup expr env))
      ((010 (100 expr))
       (110
         ((101 (100 expr) (001 quote)) (1001 expr))
         ((101 (100 expr) (001 cond))
          (my-group-eval-cond (011 expr) env))
         ((101 (100 expr) (001 lambda))
          (1110 (001 closure) (1001 expr) (011 (011 expr)) env))
         ((010 (001 ()))
          ((0010 (fn) (110
              ((my-macro? fn)
               (my-group-eval (my-apply fn (011 expr)) env))
              ((010 (001 ()))
               (my-group-apply-owned
                 fn
                 (my-group-eval-list (011 expr) env))))) (my-group-eval (100 expr) env)))))
      ((010 (001 ()))
       (my-group-apply-owned
         (my-group-eval (100 expr) env)
         (my-group-eval-list (011 expr) env))))))

(0011 my-group-eval-top-form
  (0010 (form env)
    (110
      ((010 form) (111 env (my-group-eval form env)))
      ((101 (100 form) (001 def))
       ((0010 (value) (111 (111 (111 (1001 form) value) env) value)) (my-group-eval (10011 form) env)))
      ((101 (100 form) (001 defmacro))
       (my-eval-top-form form env))
      ((010 (001 ())) (111 env (my-group-eval form env))))))

(0011 my-eval-program-with-groups
  (0010 (forms env)
    (110
      ((my-lambda-def-form? (100 forms))
       ((0010 (group) ((0010 (rest) ((0010 (group-env) (110
               ((010 rest) (111 group-env (011 (100 group-env))))
               ((010 (001 ())) (my-eval-program-with-groups rest group-env)))) (my-build-group-env group env))) (my-drop-lambda-def-group forms))) (my-take-lambda-def-group forms)))
      ((010 (001 ()))
       ((0010 (result) (110
           ((010 (011 forms)) result)
           ((010 (001 ()))
            (my-eval-program-with-groups
              (011 forms)
              (100 result))))) (my-group-eval-top-form (100 forms) env))))))
