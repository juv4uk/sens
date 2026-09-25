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

(def my-group-closure?
  (lambda (value)
    (cond
      ((atom? value) (quote ()))
      (t (eq? (car value) (quote recursive-group-closure))))))

(def my-sixth
  (lambda (values)
    (car (cdr (cdr (cdr (cdr (cdr values))))))))

(def my-lambda-def-form?
  (lambda (form)
    (cond
      ((atom? form) (quote ()))
      ((eq? (car form) (quote def))
       (my-lambda-form? (third form)))
      (t (quote ())))))

(def my-take-lambda-def-group
  (lambda (forms)
    (cond
      ((atom? forms) (quote ()))
      ((my-lambda-def-form? (car forms))
       (cons (car forms)
             (my-take-lambda-def-group (cdr forms))))
      (t (quote ())))))

(def my-drop-lambda-def-group
  (lambda (forms)
    (cond
      ((atom? forms) (quote ()))
      ((my-lambda-def-form? (car forms))
       (my-drop-lambda-def-group (cdr forms)))
      (t forms))))

(def my-group-closure-from-def
  (lambda (form group captured-env)
    (let ((lambda-form (third form)))
      (list (quote recursive-group-closure)
            (second form)
            (second lambda-form)
            (cdr (cdr lambda-form))
            group
            captured-env))))

; Build onto the captured environment so later definitions in the same group
; appear earlier in the alist, matching same-frame overwrite order.
(def my-build-group-env-onto
  (lambda (forms group captured-env out)
    (cond
      ((atom? forms) out)
      (t
       (let ((form (car forms)))
         (my-build-group-env-onto
           (cdr forms)
           group
           captured-env
           (cons
             (cons (second form)
                   (my-group-closure-from-def form group captured-env))
             out)))))))

(def my-build-group-env
  (lambda (group captured-env)
    (my-build-group-env-onto group group captured-env captured-env)))

(def my-apply-group-closure
  (lambda (fn args)
    (let ((group-env
            (my-build-group-env (my-fifth fn) (my-sixth fn))))
      (my-eval-body
        (my-fourth fn)
        (bind-params
          (third fn)
          args
          group-env)))))

; Apply wrapper used only by this experiment. Ordinary values delegate to the
; already-proven main my-apply path.
(def my-group-apply
  (lambda (fn args)
    (cond
      ((my-group-closure? fn) (my-apply-group-closure fn args))
      (t (my-apply fn args)))))

; Evaluator wrapper mirrors my-eval, changing only the apply hook so nested
; calls between members of a recursive group can invoke group closures.
(def my-group-eval-list
  (lambda (exprs env)
    (cond
      ((atom? exprs) (quote ()))
      (t (cons (my-group-eval (car exprs) env)
               (my-group-eval-list (cdr exprs) env))))))

(def my-group-eval-body
  (lambda (body env)
    (cond
      ((atom? (cdr body)) (my-group-eval (car body) env))
      (t ((lambda ()
            (my-group-eval (car body) env)
            (my-group-eval-body (cdr body) env)))))))

(def my-group-eval-cond
  (lambda (clauses env)
    (cond
      ((atom? clauses) (quote ()))
      ((my-group-eval (car (car clauses)) env)
       (my-group-eval (second (car clauses)) env))
      (t (my-group-eval-cond (cdr clauses) env)))))

(def my-group-apply-owned
  (lambda (fn args)
    (cond
      ((my-group-closure? fn)
       (let ((group-env
               (my-build-group-env (my-fifth fn) (my-sixth fn))))
         (my-group-eval-body
           (my-fourth fn)
           (bind-params (third fn) args group-env))))
      (t (my-apply fn args)))))

(def my-group-eval
  (lambda (expr env)
    (cond
      ((atom? expr) (env-lookup expr env))
      ((atom? (car expr))
       (cond
         ((eq? (car expr) (quote quote)) (second expr))
         ((eq? (car expr) (quote cond))
          (my-group-eval-cond (cdr expr) env))
         ((eq? (car expr) (quote lambda))
          (list (quote closure) (second expr) (cdr (cdr expr)) env))
         (t
          (let ((fn (my-group-eval (car expr) env)))
            (cond
              ((my-macro? fn)
               (my-group-eval (my-apply fn (cdr expr)) env))
              (t
               (my-group-apply-owned
                 fn
                 (my-group-eval-list (cdr expr) env))))))))
      (t
       (my-group-apply-owned
         (my-group-eval (car expr) env)
         (my-group-eval-list (cdr expr) env))))))

(def my-group-eval-top-form
  (lambda (form env)
    (cond
      ((atom? form) (cons env (my-group-eval form env)))
      ((eq? (car form) (quote def))
       (let ((value (my-group-eval (third form) env)))
         (cons (cons (cons (second form) value) env) value)))
      ((eq? (car form) (quote defmacro))
       (my-eval-top-form form env))
      (t (cons env (my-group-eval form env))))))

(def my-eval-program-with-groups
  (lambda (forms env)
    (cond
      ((my-lambda-def-form? (car forms))
       (let ((group (my-take-lambda-def-group forms)))
         (let ((rest (my-drop-lambda-def-group forms)))
           (let ((group-env (my-build-group-env group env)))
             (cond
               ((atom? rest)
                (cons group-env (cdr (car group-env))))
               (t (my-eval-program-with-groups rest group-env)))))))
      (t
       (let ((result (my-group-eval-top-form (car forms) env)))
         (cond
           ((atom? (cdr forms)) result)
           (t (my-eval-program-with-groups
                (cdr forms)
                (car result)))))))))
