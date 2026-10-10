; Experimental extension for mutually recursive top-level lambda definitions.
; Load after the current Core4 profile (`lib/core4.lisp`) and lib/meta-eval.lisp.
;
; This deliberately proves the representation before changing the main
; evaluator. Consecutive top-level `(def name (lambda ...))` forms are treated
; as one finite recursive group. No cyclic Rust Environment is required.
;
; A group closure stores the raw finite group as Lisp data:
;
;   (recursive-group-closure name params body group captured-env)
;
; At call time the group environment is reconstructed from that data. This
; gives every member the same lexical group while preserving ordinary lexical
; parameter shadowing. The experiment intentionally covers only contiguous
; top-level lambda-definition groups; later non-group top-level bindings are
; not claimed visible through an earlier captured environment.

(00001001 my-group-closure?
  (00001000 (value)
    (00000111
      
      ((00000010 value)  (00000001 ()))
      (1 (00000011 (00000101 value) (00000001 recursive-group-closure))))))

(00001001 my-sixth
  (00001000 (values)
    (00000101 (00000110 (00000110 (00000110 (00000110 (00000110 values))))))))

(00001001 my-lambda-def-form?
  (00001000 (form)
    (00000111
      
      ((00000010 form)  (00000001 ()))
      ((00000011 (00000101 form) (00000001 def))
       (my-lambda-form? (00110000 form)))
      (1 (00000001 ())))))

(00001001 my-take-lambda-def-group
  (00001000 (forms)
    (00000111
      
      ((00000010 forms)  (00000001 ()))
      ((my-lambda-def-form? (00000101 forms))
       (00000100 (00000101 forms)
             (my-take-lambda-def-group (00000110 forms))))
      (1 (00000001 ())))))

(00001001 my-drop-lambda-def-group
  (00001000 (forms)
    (00000111
      
      ((00000010 forms)  (00000001 ()))
      ((my-lambda-def-form? (00000101 forms))
       (my-drop-lambda-def-group (00000110 forms)))
      (1 forms))))

(00001001 my-group-closure-from-def
  (00001000 (form group captured-env)
    (10011100 ((lambda-form (00110000 form)))
      (00100111 (00000001 recursive-group-closure)
            (00101111 form)
            (00101111 lambda-form)
            (00000110 (00000110 lambda-form))
            group
            captured-env))))

; Build onto the captured environment so later definitions in the same group
; appear earlier in the alist, matching same-frame overwrite order.
(00001001 my-build-group-env-onto
  (00001000 (forms group captured-env out)
    (00000111
      
      ((00000010 forms)  out)
      (1
       (10011100 ((form (00000101 forms)))
         (my-build-group-env-onto
           (00000110 forms)
           group
           captured-env
           (00000100
             (00000100 (00101111 form)
                   (my-group-closure-from-def form group captured-env))
             out)))))))

(00001001 my-build-group-env
  (00001000 (group captured-env)
    (my-build-group-env-onto group group captured-env captured-env)))

(00001001 my-apply-group-closure
  (00001000 (fn args)
    (10011100 ((group-env
            (my-build-group-env (my-fifth fn) (my-sixth fn))))
      (my-eval-body
        (my-fourth fn)
        (bind-params
          (00110000 fn)
          args
          group-env)))))

; Apply wrapper used only by this experiment. Ordinary values delegate to the
; already-proven main my-apply path.
(00001001 my-group-apply
  (00001000 (fn args)
    (00000111
      ((my-group-closure? fn) (my-apply-group-closure fn args))
      (1 (my-apply fn args)))))

; Evaluator wrapper mirrors my-eval, changing only the apply hook so nested
; calls between members of a recursive group can invoke group closures.
(00001001 my-group-eval-list
  (00001000 (exprs env)
    (00000111
      
      ((00000010 exprs)  (00000001 ()))
      (1 (00000100 (my-group-eval (00000101 exprs) env)
               (my-group-eval-list (00000110 exprs) env))))))

(00001001 my-group-eval-body
  (00001000 (body env)
    (00000111
      
      ((00000010 (00000110 body))  (my-group-eval (00000101 body) env))
      (1 ((00001000 ()
            (my-group-eval (00000101 body) env)
            (my-group-eval-body (00000110 body) env)))))))

(00001001 my-group-eval-cond
  (00001000 (clauses env)
    (00000111
      
      ((00000010 clauses)  (00000001 ()))
      ((my-group-eval (00000101 (00000101 clauses)) env)
       (my-group-eval (00101111 (00000101 clauses)) env))
      (1 (my-group-eval-cond (00000110 clauses) env)))))

(00001001 my-group-apply-owned
  (00001000 (fn args)
    (00000111
      ((my-group-closure? fn)
       (10011100 ((group-env
               (my-build-group-env (my-fifth fn) (my-sixth fn))))
         (my-group-eval-body
           (my-fourth fn)
           (bind-params (00110000 fn) args group-env))))
      (1 (my-apply fn args)))))

(00001001 my-group-eval
  (00001000 (expr env)
    (00000111
      
      ((00000010 expr)  (env-lookup expr env))
      
      ((00000010 (00000101 expr))  (00000111
         ((00000011 (00000101 expr) (00000001 quote)) (00101111 expr))
         ((00000011 (00000101 expr) (00000001 cond))
          (my-group-eval-cond (00000110 expr) env))
         ((00000011 (00000101 expr) (00000001 lambda))
          (00100111 (00000001 closure) (00101111 expr) (00000110 (00000110 expr)) env))
         (1
          (10011100 ((fn (my-group-eval (00000101 expr) env)))
            (00000111
              ((my-macro? fn)
               (my-group-eval (my-apply fn (00000110 expr)) env))
              (1
               (my-group-apply-owned
                 fn
                 (my-group-eval-list (00000110 expr) env))))))))
      (1
       (my-group-apply-owned
         (my-group-eval (00000101 expr) env)
         (my-group-eval-list (00000110 expr) env))))))

(00001001 my-group-eval-top-form
  (00001000 (form env)
    (00000111
      
      ((00000010 form)  (00000100 env (my-group-eval form env)))
      ((00000011 (00000101 form) (00000001 def))
       (10011100 ((value (my-group-eval (00110000 form) env)))
         (00000100 (00000100 (00000100 (00101111 form) value) env) value)))
      ((00000011 (00000101 form) (00000001 defmacro))
       (my-eval-top-form form env))
      (1 (00000100 env (my-group-eval form env))))))

(00001001 my-eval-program-with-groups
  (00001000 (forms env)
    (00000111
      ((my-lambda-def-form? (00000101 forms))
       (10011100 ((group (my-take-lambda-def-group forms)))
         (10011100 ((rest (my-drop-lambda-def-group forms)))
           (10011100 ((group-env (my-build-group-env group env)))
             (00000111
               
               ((00000010 rest)  (00000100 group-env (00000110 (00000101 group-env))))
               (1 (my-eval-program-with-groups rest group-env)))))))
      (1
       (10011100 ((result (my-group-eval-top-form (00000101 forms) env)))
         (00000111
           
           ((00000010 (00000110 forms))  result)
           (1 (my-eval-program-with-groups
                (00000110 forms)
                (00000101 result)))))))))
