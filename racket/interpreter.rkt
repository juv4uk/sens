#lang racket
;;;
;;; interpreter.rkt — повноцінний інтерпретатор my-lisp поверх Racket.
;;;
;;; Це не мапінг my-lisp на Racket-семантику, а власний evaluator,
;;; який працює зі значеннями my-lisp і може завантажувати справжню
;;; bootstrap-бібліотеку lib/core4.lisp (та інші *.lisp файли).
;;;

(require "reader-lib.rkt")
(require racket/runtime-path)

(define-runtime-path repo-core "../lib/core4.lisp")
(define-runtime-path boot-core "boot/core.lisp")

;; -----------------------------------------------------------------
;; Значення my-lisp
;; -----------------------------------------------------------------

;; Historical `t` may still exist as ordinary compatibility data while old
;; library source is being removed. It is NOT predicate truth and control must
;; never coerce it to truth.
(struct my-true () #:transparent
  #:methods gen:custom-write
  [(define (write-proc v port mode)
     (write-string "t" port))])

;; Exact contextual SENS predicate result. This is a Racket mechanism carrier,
;; not a Number and not a free-standing source literal.
(struct my-predicate-bit (bit) #:transparent
  #:methods gen:custom-write
  [(define (write-proc v port mode)
     (write-string (if (my-predicate-bit-bit v) "1" "0") port))])

(define predicate-yes (my-predicate-bit #t))
(define predicate-no  (my-predicate-bit #f))

;; Замикання: (lambda params body...) або макро-трансформер.
(struct my-closure (params variadic? body env) #:transparent)

;; Макрос — це замикання, яке викликається на невиражених аргументах.
(struct my-macro (closure) #:transparent)

;; Примітив — Racket-процедура, обгортка для вбудованих функцій.
(struct my-primitive (name proc) #:transparent)

(define t (my-true))
(define nil '())

;; -----------------------------------------------------------------
;; Середовище (chain of frames)
;; -----------------------------------------------------------------

(struct env (frame parent) #:transparent)

(define (make-env [parent #f])
  (env (make-hash) parent))

(define (env-lookup e name)
  (cond
    [(not e) (error 'my-lisp "unbound identifier: ~a" name)]
    [(hash-ref (env-frame e) name (lambda () #f)) => values]
    [else (env-lookup (env-parent e) name)]))

(define (env-bound? e name)
  (cond
    [(not e) #f]
    [(hash-has-key? (env-frame e) name) #t]
    [else (env-bound? (env-parent e) name)]))

(define (env-define! e name val)
  (hash-set! (env-frame e) name val))

(define (env-set! e name val)
  (cond
    [(hash-has-key? (env-frame e) name)
     (hash-set! (env-frame e) name val)]
    [(env-parent e) (env-set! (env-parent e) name val)]
    [else (error 'my-lisp "unbound identifier: ~a" name)]))

;; -----------------------------------------------------------------
;; PredicateBit / atom / eq
;; -----------------------------------------------------------------

(define (predicate-value holds?)
  (if holds? predicate-yes predicate-no))

(define (predicate-select? value who)
  (cond
    [(my-predicate-bit? value) (my-predicate-bit-bit value)]
    [else
     (error who
            "expected exact one-bit SENS predicate result, got: ~a"
            (my-format-string value))]))

(define (atom-val x)
  (predicate-value (not (pair? x))))

(define (eq-val a b)
  (when (or (pair? a) (pair? b))
    (error 'eq "eq expects two atoms"))
  (cond
    [(and (number? a) (number? b))
     (predicate-value (and (= a b) (eq? (exact? a) (exact? b))))]
    ;; Closures/macros/primitives are `#:transparent` (so `print`/error
    ;; messages show their contents), which makes plain Racket `equal?`
    ;; compare them structurally — two separately-created closures with
    ;; identical params/body/env would then wrongly count as `eq`. The
    ;; Rust reference compares functions by identity, not structure
    ;; (`(eq (lambda (x) x) (lambda (x) x))` => `()`), same as `car`/
    ;; `cdr`/`cons` never make two distinct allocations `eq` either.
    [(or (my-closure? a) (my-closure? b) (my-macro? a) (my-macro? b) (my-primitive? a) (my-primitive? b))
     (predicate-value (eq? a b))]
    [else (predicate-value (equal? a b))]))

(define (my-pred proc)
  (lambda args (predicate-value (apply proc args))))

;; Canonical my-lisp printed form of a value — no Racket quote-sugar
;; (`'radio`/`'(1 2)`), matching the Rust reference's writer. Racket's
;; own `print` defaults to `print-as-expression #t`, which prefixes a
;; leading quote on symbols/pairs on the assumption you're printing
;; something meant to be pasted back as a literal expression; my-lisp's
;; writer never does that, so both the `print`/`princ` primitives and
;; the REPL's own value-echo (see main.rkt's `current-print`) go through
;; this instead of calling Racket's `print` directly.
(define (my-format-string v)
  (define out (open-output-string))
  (parameterize ([print-as-expression #f])
    (write v out))
  (get-output-string out))

;; -----------------------------------------------------------------
;; Читання файлів
;; -----------------------------------------------------------------

(define (read-file path)
  (define in (open-input-file path))
  (begin0
    (let loop ()
      (define v (my-read in))
      (if (eof-object? v) '() (cons v (loop))))
    (close-input-port in)))

(define (find-core-path)
  (cond
    [(file-exists? repo-core) repo-core]
    [(file-exists? boot-core) boot-core]
    [else #f]))

;; -----------------------------------------------------------------
;; Примітиви
;; -----------------------------------------------------------------

(define (register-primitives! e)
  ;; Арифметика
  (env-define! e '+ (my-primitive '+ (lambda args (apply + args))))
  (env-define! e '- (my-primitive '- (lambda args (apply - args))))
  (env-define! e '* (my-primitive '* (lambda args (apply * args))))
  (env-define! e '/ (my-primitive '/ (lambda args (apply / args))))
  ;; Порівняння
  (env-define! e '< (my-primitive '< (my-pred <)))
  (env-define! e '> (my-primitive '> (my-pred >)))
  (env-define! e '= (my-primitive '= (my-pred =)))
  ;; Списки / Маккарті
  (env-define! e 'atom (my-primitive 'atom atom-val))
  (env-define! e 'eq   (my-primitive 'eq   eq-val))
  (env-define! e 'car  (my-primitive 'car  (lambda (p) (if (pair? p) (car p) (error 'car "expected pair")))))
  (env-define! e 'cdr  (my-primitive 'cdr  (lambda (p) (if (pair? p) (cdr p) (error 'cdr "expected pair")))))
  (env-define! e 'cons (my-primitive 'cons cons))
  ;; Рядки / символи
  (env-define! e 'string-first  (my-primitive 'string-first  (lambda (s) (substring s 0 1))))
  (env-define! e 'string-rest   (my-primitive 'string-rest   (lambda (s) (substring s 1))))
  (env-define! e 'string-append (my-primitive 'string-append (lambda args (apply string-append args))))
  (env-define! e 'symbol->string (my-primitive 'symbol->string symbol->string))
  (env-define! e 'string->symbol (my-primitive 'string->symbol string->symbol))
  (env-define! e 'write-to-string
    (my-primitive 'write-to-string my-format-string))
  ;; Предикати
  (env-define! e 'number? (my-primitive 'number? (my-pred number?)))
  (env-define! e 'string? (my-primitive 'string? (my-pred string?)))
  ;; Введення-виведення
  (env-define! e 'display   (my-primitive 'display   (lambda (x) (display x) x)))
  (env-define! e 'displayln (my-primitive 'displayln (lambda (x) (displayln x) x)))
  ;; The Rust reference records each `print` call as one line and always
  ;; terminates it with a newline when flushed (see io.rs's
  ;; evaluate_print + the CLI's `println!("{}", out)` per output line) —
  ;; `displayln`, not `display`, matches that.
  (env-define! e 'print     (my-primitive 'print     (lambda (x) (displayln (my-format-string x)) x)))
  (env-define! e 'princ     (my-primitive 'princ     (lambda (x) (displayln x) x)))
  (env-define! e 'read
    (my-primitive 'read
                  (case-lambda
                    [() (my-read (current-input-port))]
                    [(s) (if (string? s)
                             (my-read (open-input-string s))
                             (my-read s))])))
  (env-define! e 'read-all
    (my-primitive 'read-all
                  (lambda (s)
                    (define in (open-input-string s))
                    (let loop ()
                      (define v (my-read in))
                      (if (eof-object? v) '() (cons v (loop)))))))
  ;; Значення істини
  (env-define! e 't t)
  (env-define! e 'nil nil))

;; -----------------------------------------------------------------
;; Замикання / макроси
;; -----------------------------------------------------------------

(define (bind-args! params args new-env)
  (cond
    ;; Дotted tail (a b . rest): решта аргументів йде у rest.
    [(symbol? params)
     (env-define! new-env params args)]
    [(null? params)
     (unless (null? args) (error 'my-lisp "too many arguments"))]
    [(null? args) (error 'my-lisp "too few arguments")]
    [else
     (env-define! new-env (car params) (car args))
     (bind-args! (cdr params) (cdr args) new-env)]))

(define (make-closure params body env)
  (if (symbol? params)
      (my-closure params #t body env)
      (my-closure params #f body env)))

(define (apply-closure clo args env eval-loop)
  (define new-env (make-env (my-closure-env clo)))
  (if (my-closure-variadic? clo)
      (env-define! new-env (my-closure-params clo) args)
      (bind-args! (my-closure-params clo) args new-env))
  (eval-sequence (my-closure-body clo) new-env eval-loop))

(define (define-macro! env args)
  (match args
    [(list (cons name params) body ...)
     (define clo (make-closure params body env))
     (env-define! env name (my-macro clo))
     nil]
     [(list name params body ...)
      (define-macro! env (cons (cons name params) body))]
    [_ (error 'my-lisp "bad defmacro syntax")]))

;; -----------------------------------------------------------------
;; Послідовності
;; -----------------------------------------------------------------

(define (eval-sequence exprs env eval-loop)
  (cond
    [(null? exprs) nil]
    [(null? (cdr exprs)) (eval-loop (car exprs) env)]
    [else
     (eval-loop (car exprs) env)
     (eval-sequence (cdr exprs) env eval-loop)]))

(define (eval-cond clauses env eval-loop)
  (if (null? clauses)
      nil
      (let ([clause (car clauses)])
        (unless (and (list? clause) (= (length clause) 2))
          (error 'cond "expected exactly (test expression)"))
        (if (predicate-select? (eval-loop (car clause) env) 'cond)
            (eval-loop (cadr clause) env)
            (eval-cond (cdr clauses) env eval-loop)))))

(define (apply-proc proc args env eval-loop)
  (cond
    [(my-closure? proc) (apply-closure proc args env eval-loop)]
    [(my-primitive? proc) (apply (my-primitive-proc proc) args)]
    [(procedure? proc) (apply proc args)]
    [else (error 'my-lisp "not a function: ~a" proc)]))

;; -----------------------------------------------------------------
;; Головний evaluator
;; -----------------------------------------------------------------

(define (my-eval expr env)
  (let eval-loop ([expr expr] [env env])
    (cond
      [(or (number? expr) (string? expr) (my-true? expr)
           (my-predicate-bit? expr) (null? expr)) expr]
      [(symbol? expr) (env-lookup env expr)]
      [(not (pair? expr)) expr]
      [else
       (define op (car expr))
       (define args (cdr expr))
       (case op
         [(quote)
          (if (null? args) nil (car args))]
         [(atom)
          (atom-val (eval-loop (car args) env))]
         [(eq)
          (eq-val (eval-loop (car args) env)
                  (eval-loop (cadr args) env))]
         [(car)
          (define v (eval-loop (car args) env))
          (if (pair? v) (car v) (error 'car "expected pair"))]
         [(cdr)
          (define v (eval-loop (car args) env))
          (if (pair? v) (cdr v) (error 'cdr "expected pair"))]
         [(cons)
          (cons (eval-loop (car args) env)
                (eval-loop (cadr args) env))]
         [(cond)
          (eval-cond args env eval-loop)]
         [(if)
          (if (predicate-select? (eval-loop (car args) env) 'if)
              (eval-loop (cadr args) env)
              (if (null? (cddr args))
                  nil
                  (eval-loop (caddr args) env)))]
         [(lambda)
          (make-closure (car args) (cdr args) env)]
         [(def)
          (env-define! env (car args) (eval-loop (cadr args) env))
          nil]
         [(defmacro)
          (define-macro! env args)
          nil]
         [(begin)
          (eval-sequence args env eval-loop)]
         [(load)
          (define path (eval-loop (car args) env))
          (unless (string? path) (error 'load "expected string path"))
          (eval-sequence (read-file path) env eval-loop)]
         [(set!)
          (env-set! env (car args) (eval-loop (cadr args) env))
          nil]
         [(eval)
          ;; A special form, not a primitive: `(eval x)` evaluates `x`
          ;; to get a datum, then evaluates *that datum* again — the
          ;; second evaluation needs the caller's env, which a plain
          ;; my-primitive (args already evaluated, no env access) can't
          ;; see. Matches Rust's evaluate_eval (special_forms/io.rs):
          ;; closures/macros evaluate to themselves, not through
          ;; another round of evaluation.
          (define datum (eval-loop (car args) env))
          (if (or (my-closure? datum) (my-macro? datum))
              datum
              (eval-loop datum env))]
         [else
          (define proc (eval-loop op env))
          (cond
            [(my-macro? proc)
             (define expanded (apply-closure (my-macro-closure proc) args env eval-loop))
             (eval-loop expanded env)]
            [else
             (define evaled-args (map (lambda (a) (eval-loop a env)) args))
             (apply-proc proc evaled-args env eval-loop)])])])))

;; -----------------------------------------------------------------
;; Початкове середовище з lib/core4.lisp
;; -----------------------------------------------------------------

(define (make-initial-env)
  (define e (make-env))
  (register-primitives! e)
  (define core-path (find-core-path))
  (unless core-path
    (error 'my-lisp "cannot find core4.lisp; expected ../lib/core4.lisp or boot/core.lisp"))
  (define forms (read-file core-path))
  (eval-sequence forms e my-eval)
  e)

;; -----------------------------------------------------------------
;; Запуск модуля / REPL
;; -----------------------------------------------------------------

(define (run-module forms)
  (define env (make-initial-env))
  (eval-sequence forms env my-eval))

(provide
 ;; evaluator / sequences
 my-eval eval-sequence
 ;; environments
 make-env env-lookup env-bound? env-define! env-set!
 ;; values
 t nil my-true? my-predicate-bit? my-closure? my-macro? my-primitive?
 ;; module / file loading
 make-initial-env run-module read-file
 ;; needed by main.rkt for REPL echo
 atom-val eq-val my-format-string)