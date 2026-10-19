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
(визначити це-замикання-рекурсивної-групи?
  (функція (значення)
    (за-умовою
      ((атом? значення) ні)
      (так (тотожне? (перше значення) (як-є recursive-group-closure))))))

(визначити my-sixth
  (функція (значення)
    (перше (решта (решта (решта (решта (решта значення))))))))

(визначити визначення-лямбди-на-верхньому-рівні?
  (функція (форма)
    (за-умовою
      ((атом? форма) ні)
      ((тотожне? (перше форма) (як-є def))
       (перевірити-форму-лямбда? (третє форма)))
      (так ні))))

(визначити my-take-lambda-def-group
  (функція (форми)
    (за-умовою
      ((атом? форми) (як-є ()))
      ((визначення-лямбди-на-верхньому-рівні? (перше форми))
       (сполучити (перше форми)
            (my-take-lambda-def-group (решта форми))))
      (так (як-є ())))))

(визначити my-drop-lambda-def-group
  (функція (форми)
    (за-умовою
      ((атом? форми) (як-є ()))
      ((визначення-лямбди-на-верхньому-рівні? (перше форми))
       (my-drop-lambda-def-group (решта форми)))
      (так форми))))

(визначити створити-замикання-взаєморекурсивної-групи
  (функція (форма група захоплене-оточення)
    ((функція (lambda-form) (список (як-є recursive-group-closure)
            (друге форма)
            (друге lambda-form)
            (решта (решта lambda-form))
            група
            захоплене-оточення)) (третє форма))))

; Build onto the captured environment so later definitions in the same group
; appear earlier in the alist, matching same-frame overwrite order.
(визначити my-build-group-env-onto
  (функція (форми група захоплене-оточення накопичувач)
    (за-умовою
      ((атом? форми) накопичувач)
      (так
       ((функція (form) (my-build-group-env-onto
           (решта форми)
           група
           захоплене-оточення
           (сполучити
             (сполучити (друге form)
                   (створити-замикання-взаєморекурсивної-групи form група захоплене-оточення))
             накопичувач))) (перше форми))))))

(визначити побудувати-лексичні-зв'язки-рекурсивної-групи
  (функція (група захоплене-оточення)
    (my-build-group-env-onto група група захоплене-оточення захоплене-оточення)))

(визначити my-apply-group-closure
  (функція (викликана-функція аргументи)
    ((функція (group-env) (my-eval-body
        (my-fourth викликана-функція)
        (зв'язати-аргументи-з-лямбда-параметрами
          (третє викликана-функція)
          аргументи
          group-env))) (побудувати-лексичні-зв'язки-рекурсивної-групи (my-fifth викликана-функція) (my-sixth викликана-функція)))))

; Apply wrapper: group closures go through group path; others reuse my-apply.
(визначити my-group-apply
  (функція (викликана-функція аргументи)
    (за-умовою
      ((це-замикання-рекурсивної-групи? викликана-функція) (my-apply-group-closure викликана-функція аргументи))
      (так (my-apply викликана-функція аргументи)))))

(визначити my-group-eval-list
  (функція (вирази оточення)
    (за-умовою
      ((атом? вирази) (як-є ()))
      (так
       (сполучити (my-group-eval (перше вирази) оточення)
            (my-group-eval-list (решта вирази) оточення))))))

(визначити my-group-eval-body
  (функція (тіло-функції оточення)
    (за-умовою
      ((атом? (решта тіло-функції)) (my-group-eval (перше тіло-функції) оточення))
      (так
       ((функція ()
          (my-group-eval (перше тіло-функції) оточення)
          (my-group-eval-body (решта тіло-функції) оточення)))))))

(визначити my-group-eval-cond
  (функція (гілки-умов оточення)
    (за-умовою
      ((атом? гілки-умов) (як-є ()))
      ((my-group-eval (перше (перше гілки-умов)) оточення)
       (my-group-eval (друге (перше гілки-умов)) оточення))
      (так (my-group-eval-cond (решта гілки-умов) оточення)))))

(визначити my-group-apply-owned
  (функція (викликана-функція аргументи)
    (за-умовою
      ((це-замикання-рекурсивної-групи? викликана-функція)
       ((функція (group-env) (my-group-eval-body
           (my-fourth викликана-функція)
           (зв'язати-аргументи-з-лямбда-параметрами (третє викликана-функція) аргументи group-env))) (побудувати-лексичні-зв'язки-рекурсивної-групи (my-fifth викликана-функція) (my-sixth викликана-функція))))
      (так (my-apply викликана-функція аргументи)))))

(визначити my-group-eval
  (функція (вираз оточення)
    (за-умовою
      ((атом? вираз) (знайти-значення-імені-в-лексичному-середовищі вираз оточення))
      ((атом? (перше вираз))
       (за-умовою
         ((тотожне? (перше вираз) (як-є quote)) (друге вираз))
         ((тотожне? (перше вираз) (як-є cond))
          (my-group-eval-cond (решта вираз) оточення))
         ((тотожне? (перше вираз) (як-є lambda))
          (список (як-є closure) (друге вираз) (решта (решта вираз)) оточення))
         (так
          ((функція (fn) (за-умовою
              ((my-macro? fn)
               (my-group-eval (my-apply fn (решта вираз)) оточення))
              (так
               (my-group-apply-owned
                 fn
                 (my-group-eval-list (решта вираз) оточення))))) (my-group-eval (перше вираз) оточення)))))
      (так
       (my-group-apply-owned
         (my-group-eval (перше вираз) оточення)
         (my-group-eval-list (решта вираз) оточення))))))

(визначити my-group-eval-top-form
  (функція (форма оточення)
    (за-умовою
      ((атом? форма) (сполучити оточення (my-group-eval форма оточення)))
      ((тотожне? (перше форма) (як-є def))
       ((функція (value) (сполучити (сполучити (сполучити (друге форма) value) оточення) value)) (my-group-eval (третє форма) оточення)))
      ((тотожне? (перше форма) (як-є defmacro))
       (обчислити-форму-та-оновити-оточення форма оточення))
      (так (сполучити оточення (my-group-eval форма оточення))))))

(визначити my-eval-program-with-groups
  (функція (форми оточення)
    (за-умовою
      ((визначення-лямбди-на-верхньому-рівні? (перше форми))
       ((функція (group) ((функція (rest) ((функція (group-env) (за-умовою
               ((атом? rest) (сполучити group-env (решта (перше group-env))))
               (так (my-eval-program-with-groups rest group-env)))) (побудувати-лексичні-зв'язки-рекурсивної-групи group оточення))) (my-drop-lambda-def-group форми))) (my-take-lambda-def-group форми)))
      (так
       ((функція (result) (за-умовою
           ((атом? (решта форми)) result)
           (так
            (my-eval-program-with-groups
              (решта форми)
              (перше result))))) (my-group-eval-top-form (перше форми) оточення))))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити my-build-group-env побудувати-лексичні-зв'язки-рекурсивної-групи)
(визначити my-group-closure? це-замикання-рекурсивної-групи?)
(визначити my-lambda-def-form? визначення-лямбди-на-верхньому-рівні?)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити знайти-значення-імені-в-лексичному-середовищі env-lookup)
(визначити обчислити-форму-та-оновити-оточення my-eval-top-form)
(визначити перевірити-форму-лямбда? my-lambda-form?)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас.
(визначити зв'язати-аргументи-з-лямбда-параметрами bind-params)
(визначити my-group-closure-from-def створити-замикання-взаєморекурсивної-групи)
