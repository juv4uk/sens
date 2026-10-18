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
(визначити my-group-closure?
  (функція (value)
    (за-умовою
      ((атом? value) ні)
      (так (тотожне? (перше value) (як-є recursive-group-closure))))))

(визначити my-sixth
  (функція (values)
    (перше (решта (решта (решта (решта (решта values))))))))

(визначити my-lambda-def-form?
  (функція (form)
    (за-умовою
      ((атом? form) ні)
      ((тотожне? (перше form) (як-є def))
       (перевірити-форму-лямбда? (третє form)))
      (так ні))))

(визначити my-take-lambda-def-group
  (функція (forms)
    (за-умовою
      ((атом? forms) (як-є ()))
      ((визначення-лямбди-на-верхньому-рівні? (перше forms))
       (сполучити (перше forms)
            (my-take-lambda-def-group (решта forms))))
      (так (як-є ())))))

(визначити my-drop-lambda-def-group
  (функція (forms)
    (за-умовою
      ((атом? forms) (як-є ()))
      ((визначення-лямбди-на-верхньому-рівні? (перше forms))
       (my-drop-lambda-def-group (решта forms)))
      (так forms))))

(визначити my-group-closure-from-def
  (функція (form group captured-env)
    ((функція (lambda-form) (список (як-є recursive-group-closure)
            (друге form)
            (друге lambda-form)
            (решта (решта lambda-form))
            group
            captured-env)) (третє form))))

; Build onto the captured environment so later definitions in the same group
; appear earlier in the alist, matching same-frame overwrite order.
(визначити my-build-group-env-onto
  (функція (forms group captured-env out)
    (за-умовою
      ((атом? forms) out)
      (так
       ((функція (form) (my-build-group-env-onto
           (решта forms)
           group
           captured-env
           (сполучити
             (сполучити (друге form)
                   (my-group-closure-from-def form group captured-env))
             out))) (перше forms))))))

(визначити my-build-group-env
  (функція (group captured-env)
    (my-build-group-env-onto group group captured-env captured-env)))

(визначити my-apply-group-closure
  (функція (fn args)
    ((функція (group-env) (my-eval-body
        (my-fourth fn)
        (bind-params
          (третє fn)
          args
          group-env))) (побудувати-лексичні-зв'язки-рекурсивної-групи (my-fifth fn) (my-sixth fn)))))

; Apply wrapper: group closures go through group path; others reuse my-apply.
(визначити my-group-apply
  (функція (fn args)
    (за-умовою
      ((це-замикання-рекурсивної-групи? fn) (my-apply-group-closure fn args))
      (так (my-apply fn args)))))

(визначити my-group-eval-list
  (функція (exprs env)
    (за-умовою
      ((атом? exprs) (як-є ()))
      (так
       (сполучити (my-group-eval (перше exprs) env)
            (my-group-eval-list (решта exprs) env))))))

(визначити my-group-eval-body
  (функція (body env)
    (за-умовою
      ((атом? (решта body)) (my-group-eval (перше body) env))
      (так
       ((функція ()
          (my-group-eval (перше body) env)
          (my-group-eval-body (решта body) env)))))))

(визначити my-group-eval-cond
  (функція (clauses env)
    (за-умовою
      ((атом? clauses) (як-є ()))
      ((my-group-eval (перше (перше clauses)) env)
       (my-group-eval (друге (перше clauses)) env))
      (так (my-group-eval-cond (решта clauses) env)))))

(визначити my-group-apply-owned
  (функція (fn args)
    (за-умовою
      ((це-замикання-рекурсивної-групи? fn)
       ((функція (group-env) (my-group-eval-body
           (my-fourth fn)
           (bind-params (третє fn) args group-env))) (побудувати-лексичні-зв'язки-рекурсивної-групи (my-fifth fn) (my-sixth fn))))
      (так (my-apply fn args)))))

(визначити my-group-eval
  (функція (expr env)
    (за-умовою
      ((атом? expr) (знайти-значення-імені-в-лексичному-середовищі expr env))
      ((атом? (перше expr))
       (за-умовою
         ((тотожне? (перше expr) (як-є quote)) (друге expr))
         ((тотожне? (перше expr) (як-є cond))
          (my-group-eval-cond (решта expr) env))
         ((тотожне? (перше expr) (як-є lambda))
          (список (як-є closure) (друге expr) (решта (решта expr)) env))
         (так
          ((функція (fn) (за-умовою
              ((my-macro? fn)
               (my-group-eval (my-apply fn (решта expr)) env))
              (так
               (my-group-apply-owned
                 fn
                 (my-group-eval-list (решта expr) env))))) (my-group-eval (перше expr) env)))))
      (так
       (my-group-apply-owned
         (my-group-eval (перше expr) env)
         (my-group-eval-list (решта expr) env))))))

(визначити my-group-eval-top-form
  (функція (form env)
    (за-умовою
      ((атом? form) (сполучити env (my-group-eval form env)))
      ((тотожне? (перше form) (як-є def))
       ((функція (value) (сполучити (сполучити (сполучити (друге form) value) env) value)) (my-group-eval (третє form) env)))
      ((тотожне? (перше form) (як-є defmacro))
       (обчислити-форму-та-оновити-оточення form env))
      (так (сполучити env (my-group-eval form env))))))

(визначити my-eval-program-with-groups
  (функція (forms env)
    (за-умовою
      ((визначення-лямбди-на-верхньому-рівні? (перше forms))
       ((функція (group) ((функція (rest) ((функція (group-env) (за-умовою
               ((атом? rest) (сполучити group-env (решта (перше group-env))))
               (так (my-eval-program-with-groups rest group-env)))) (побудувати-лексичні-зв'язки-рекурсивної-групи group env))) (my-drop-lambda-def-group forms))) (my-take-lambda-def-group forms)))
      (так
       ((функція (result) (за-умовою
           ((атом? (решта forms)) result)
           (так
            (my-eval-program-with-groups
              (решта forms)
              (перше result))))) (my-group-eval-top-form (перше forms) env))))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити побудувати-лексичні-зв'язки-рекурсивної-групи my-build-group-env)
(визначити це-замикання-рекурсивної-групи? my-group-closure?)
(визначити визначення-лямбди-на-верхньому-рівні? my-lambda-def-form?)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити знайти-значення-імені-в-лексичному-середовищі env-lookup)
(визначити обчислити-форму-та-оновити-оточення my-eval-top-form)
(визначити перевірити-форму-лямбда? my-lambda-form?)
