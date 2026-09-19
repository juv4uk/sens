; Metacircular evaluator: my-eval interprets my-lisp source as Lisp data.
;
; Contract 6.0 ownership boundary:
; the finite Canon 0+7 surface-name set is resolved before the metacircular
; lexical environment and cannot be used by language binders. Callable Canon
; spellings resolve to first-class `(primitive identity)` values; quote/cond
; remain syntax-only. Ordinary non-Canon primitives such as +, -, *, <, =, >
; still live in the metacircular environment model and remain shadowable.
;
; The actual primitive operation is still supplied by the native substrate;
; this evaluator owns name resolution, Canon-first lookup, ordinary lexical
; shadowing, application shape, macro expansion, closure environments, chained
; comparison policy, shared top-level definition-frame visibility, self-recursive
; and dependency-aware finite mutually recursive top-level function binding,
; variadic/dotted lambda parameter binding, and named failure observations for
; unresolved names, non-callable values, lambda/macro arity mismatch, invalid
; lambda-list structure, and reserved Canon binding attempts.
;
; This remains an explicit self-hosting witness, not the always-loaded runtime.
; Full named-error parity is still a known gap and must not be claimed as
; complete self-hosting.

(def my-primitive
  (lambda (name)
    (list (quote primitive) name)))

(def my-error
  (lambda (kind detail)
    (list (quote error) kind detail)))

; Internal evaluator outcomes carry provenance that interpreted Lisp data cannot
; forge. The tag is a native closure identity, not a symbol or list shape that
; a program could reproduce with quote/cons. Public my-eval/my-apply unwrap the
; envelope, so the observable interface stays unchanged.
(def my-result-ok-token
  (lambda (value) value))

(def my-result-fail-token
  (lambda (value) value))

(def my-result-ok
  (lambda (value)
    (cons my-result-ok-token value)))

(def my-result-fail
  (lambda (error)
    (cons my-result-fail-token error)))

(def my-result-fail?
  (lambda (result)
    (cond
      ((atom result) (quote ()))
      (t (eq (car result) my-result-fail-token)))))

(def my-result-value
  (lambda (result)
    (cdr result)))

; Surface spellings are not owned here. The generated projection loaded before
; this evaluator maps every admitted runtime spelling to the numeric semantic ID
; from lib/surface/semantic-registry.lisp. This file owns only the mapping from
; those opaque IDs to evaluator mechanisms.
(def my-semantic-id?
  (lambda (name semantic-id)
    (equal? (my-semantic-id-for-surface name) semantic-id)))

(def my-canon-identity
  (lambda (name)
    (let ((semantic-id (my-semantic-id-for-surface name)))
      (cond
        ((equal? semantic-id "00000001") (quote quote))
        ((equal? semantic-id "00000010") (quote atom))
        ((equal? semantic-id "00000011") (quote eq))
        ((equal? semantic-id "00000100") (quote cons))
        ((equal? semantic-id "00000101") (quote car))
        ((equal? semantic-id "00000110") (quote cdr))
        ((equal? semantic-id "00000111") (quote cond))
        (t (quote ()))))))

(def my-lambda-name?
  (lambda (name)
    (my-semantic-id? name "00001000")))

(def my-define-name?
  (lambda (name)
    (my-semantic-id? name "00001001")))

(def my-defmacro-name?
  (lambda (name)
    (my-semantic-id? name "00001010")))

(def my-def-compat-name?
  (lambda (name)
    (my-semantic-id? name "00001011")))

(def my-definition-name?
  (lambda (name)
    (cond
      ((my-define-name? name) t)
      ((my-def-compat-name? name) t)
      (t (quote ())))))

(def my-canon-name?
  (lambda (name)
    (cond
      ((my-canon-identity name) t)
      (t (quote ())))))

(def my-canon-callable-identity?
  (lambda (identity)
    (cond
      ((eq identity (quote atom)) t)
      ((eq identity (quote eq)) t)
      ((eq identity (quote cons)) t)
      ((eq identity (quote car)) t)
      ((eq identity (quote cdr)) t)
      (t (quote ())))))

(def my-canon-quote-name?
  (lambda (name)
    (eq (my-canon-identity name) (quote quote))))

(def my-canon-cond-name?
  (lambda (name)
    (eq (my-canon-identity name) (quote cond))))

(def my-canon-binding-error
  (lambda (name)
    (my-error
      (quote invalid-form)
      (list (quote canonical-name-immutable) name))))

; Root primitive meanings are represented as values. Canon is handled first;
; ordinary non-Canon primitives continue through this default environment layer.
(def my-default-binding
  (lambda (name)
    (let ((identity (my-canon-identity name)))
      (cond
        ((my-canon-callable-identity? identity) (my-primitive identity))
        ((my-canon-name? name) (my-canon-binding-error name))
        ((eq name (quote +))    (my-primitive (quote +)))
        ((eq name (quote -))    (my-primitive (quote -)))
        ((eq name (quote *))    (my-primitive (quote *)))
        ((eq name (quote <))    (my-primitive (quote <)))
        ((eq name (quote =))    (my-primitive (quote =)))
        ((eq name (quote >))    (my-primitive (quote >)))
        ((eq name (quote write-to-string))
         (my-primitive (quote write-to-string)))
        ((eq name (quote string->symbol))
         (my-primitive (quote string->symbol)))
        (t name)))))

; ADR-009 shared definition frame.
;
; The metacircular environment remains finite Lisp data. A binding whose key is
; the non-symbol internal sentinel 0 stores the mutable-in-the-language-model
; top-level frame as an ordinary alist:
;
;   ((0 . ((latest . value) ...)) . lexical-outer-env)
;
; User binders are symbols, so the sentinel cannot collide with a legal source
; binding. Local lexical bindings are consed before this marker. At closure call
; time only the marker payload is refreshed from the caller; local captured
; bindings before it are preserved. This models shared frame identity without
; dynamic scope and without a cyclic host object.
(def my-shared-frame-binding?
  (lambda (binding)
    (cond
      ((atom binding) (quote ()))
      (t (eq (car binding) 0)))))

(def my-frame-bound?
  (lambda (name frame)
    (cond
      ((atom frame) (quote ()))
      ((eq (car (car frame)) name) t)
      (t (my-frame-bound? name (cdr frame))))))

(def my-frame-lookup
  (lambda (name frame)
    (cond
      ((eq (car (car frame)) name) (cdr (car frame)))
      (t (my-frame-lookup name (cdr frame))))))

(def my-env-has-shared-frame?
  (lambda (env)
    (cond
      ((atom env) (quote ()))
      ((my-shared-frame-binding? (car env)) t)
      (t (my-env-has-shared-frame? (cdr env))))))

(def my-shared-frame-value
  (lambda (env)
    (cond
      ((atom env) (quote ()))
      ((my-shared-frame-binding? (car env)) (cdr (car env)))
      (t (my-shared-frame-value (cdr env))))))

(def my-ensure-shared-frame
  (lambda (env)
    (cond
      ((my-env-has-shared-frame? env) env)
      (t (cons (cons 0 (quote ())) env)))))

(def my-replace-shared-frame
  (lambda (env frame)
    (cond
      ((atom env) env)
      ((my-shared-frame-binding? (car env))
       (cons (cons 0 frame) (cdr env)))
      (t
       (cons (car env)
             (my-replace-shared-frame (cdr env) frame))))))

(def my-refresh-shared-frame
  (lambda (captured-env caller-env)
    (cond
      ((my-env-has-shared-frame? captured-env)
       (cond
         ((my-env-has-shared-frame? caller-env)
          (my-replace-shared-frame
            captured-env
            (my-shared-frame-value caller-env)))
         (t captured-env)))
      (t captured-env))))

; Definitions update the shared marker when one is active. Outside
; my-eval-program this falls back to the historical plain-alist extension, so
; direct my-eval-top-form use remains compatible.
(def my-env-define
  (lambda (name value env)
    (cond
      ((atom env) (cons (cons name value) env))
      ((my-shared-frame-binding? (car env))
       (cons
         (cons 0
               (cons (cons name value)
                     (cdr (car env))))
         (cdr env)))
      (t
       (cons (car env)
             (my-env-define name value (cdr env)))))))

; Contract 6.0: Canon outranks the lexical alist even if a hostile/pre-existing
; environment contains the same text. Non-Canon names retain ordinary lookup.
(def env-lookup
  (lambda (name env)
    (let ((identity (my-canon-identity name)))
      (cond
        ((my-canon-callable-identity? identity) (my-primitive identity))
        ((my-canon-name? name) (my-canon-binding-error name))
        ((atom env) (my-default-binding name))
        ((my-shared-frame-binding? (car env))
         (cond
           ((my-frame-bound? name (cdr (car env)))
            (my-frame-lookup name (cdr (car env))))
           (t (env-lookup name (cdr env)))))
        ((eq (car (car env)) name) (cdr (car env)))
        (t (env-lookup name (cdr env)))))))

(def env-bound?
  (lambda (name env)
    (cond
      ((my-canon-name? name) t)
      ((atom env) (quote ()))
      ((my-shared-frame-binding? (car env))
       (cond
         ((my-frame-bound? name (cdr (car env))) t)
         (t (env-bound? name (cdr env)))))
      ((eq (car (car env)) name) t)
      (t (env-bound? name (cdr env))))))

(def my-primitive?
  (lambda (value)
    (cond
      ((atom value) (quote ()))
      (t (eq (car value) (quote primitive))))))

; UnknownSymbol belongs to name resolution, not application. A symbol produced
; as a value (for example by quote) is not an unresolved lookup and therefore
; must later fail as not-callable/Type if placed in operator position.
;
; `symbol?` itself is language-owned in core.lisp, derived without a Rust builtin,
; so this distinction adds no primitive to the closed Canon.
(def my-unresolved-name?
  (lambda (name env)
    (cond
      ((symbol? name)
       (cond
         ((eq name t) (quote ()))
         ((my-canon-name? name) (quote ()))
         ((env-bound? name env) (quote ()))
         ((my-primitive? (my-default-binding name)) (quote ()))
         (t t)))
      (t (quote ())))))

(def my-macro?
  (lambda (value)
    (cond
      ((atom value) (quote ()))
      (t (eq (car value) (quote macro))))))

(def my-closure?
  (lambda (value)
    (cond
      ((atom value) (quote ()))
      (t (eq (car value) (quote closure))))))

; A recursive closure is finite Lisp data. It does not require a cyclic host
; Environment. At call time my-apply reconstructs the one self-binding that
; the function needs. Contract 6 guarantees that this name is never Canon.
;
; Shape:
;   (recursive-closure name params body captured-env)
(def my-recursive-closure?
  (lambda (value)
    (cond
      ((atom value) (quote ()))
      (t (eq (car value) (quote recursive-closure))))))

; A mutually-recursive group is also finite Lisp data. Every member stores the
; same raw group and captured outer environment; my-apply reconstructs the
; group's bindings at call time rather than relying on a cyclic host object.
;
; Shape:
;   (recursive-group-closure name params body group captured-env)
(def my-group-closure?
  (lambda (value)
    (cond
      ((atom value) (quote ()))
      (t (eq (car value) (quote recursive-group-closure))))))

(def my-lambda-form?
  (lambda (form)
    (cond
      ((atom form) (quote ()))
      ((atom (car form)) (my-lambda-name? (car form)))
      (t (quote ())))))

(def my-lambda-def-form?
  (lambda (form)
    (cond
      ((atom form) (quote ()))
      ((my-definition-name? (car form))
       (cond
         ((my-canon-name? (second form)) (quote ()))
         (t (my-lambda-form? (third form)))))
      (t (quote ())))))

(def my-fourth
  (lambda (values)
    (car (cdr (cdr (cdr values))))))

(def my-fifth
  (lambda (values)
    (car (cdr (cdr (cdr (cdr values)))))))

(def my-sixth
  (lambda (values)
    (car (cdr (cdr (cdr (cdr (cdr values))))))))

(def my-compare-two
  (lambda (operator left right)
    (cond
      ((eq operator (quote <)) (< left right))
      ((eq operator (quote =)) (= left right))
      ((eq operator (quote >)) (> left right))
      (t (quote ())))))

; Chained comparison semantics are Lisp-owned: values arrive already
; evaluated, adjacent pairs are compared left-to-right, and evaluation stops
; at the first false pair.
(def my-compare-chain
  (lambda (operator values)
    (cond
      ((atom (cdr values)) t)
      ((my-compare-two operator (car values) (second values))
       (my-compare-chain operator (cdr values)))
      (t (quote ())))))

; Primitive *identity* is a Lisp value. This function is the narrow bridge
; from that identity to the admitted native operation mechanism.
(def my-apply-primitive
  (lambda (name args)
    (cond
      ((eq name (quote atom)) (atom (car args)))
      ((eq name (quote eq))   (eq (car args) (second args)))
      ((eq name (quote car))  (car (car args)))
      ((eq name (quote cdr))  (cdr (car args)))
      ((eq name (quote cons)) (cons (car args) (second args)))
      ((eq name (quote +))    (+ (car args) (second args)))
      ((eq name (quote -))    (- (car args) (second args)))
      ((eq name (quote *))    (* (car args) (second args)))
      ((eq name (quote <))    (my-compare-chain (quote <) args))
      ((eq name (quote =))    (my-compare-chain (quote =) args))
      ((eq name (quote >))    (my-compare-chain (quote >) args))
      ((eq name (quote write-to-string))
       (write-to-string (car args)))
      ((eq name (quote string->symbol))
       (string->symbol (car args)))
      (t (list (quote unknown-primitive) name)))))

; Lambda-list arity is derivable from Lisp list structure itself:
;   (x y)        -> exact 2
;   (x y . rest) -> at least 2
;   args         -> at least 0
; No host metadata is required.
(def my-fixed-param-count
  (lambda (params)
    (cond
      ((atom params) 0)
      (t (+ 1 (my-fixed-param-count (cdr params)))))))

(def my-rest-param?
  (lambda (params)
    (cond
      ((atom params)
       (cond
         ((eq params (quote ())) (quote ()))
         (t t)))
      (t (my-rest-param? (cdr params))))))

(def my-arity-ok?
  (lambda (params args)
    (let ((fixed (my-fixed-param-count params))
          (received (length args)))
      (cond
        ((my-rest-param? params)
         (cond
           ((< received fixed) (quote ()))
           (t t)))
        (t (= received fixed))))))

(def my-arity-detail
  (lambda (params args)
    (let ((fixed (my-fixed-param-count params))
          (received (length args)))
      (list
        (quote expected)
        (cond
          ((my-rest-param? params) (list (quote at-least) fixed))
          (t (list (quote exact) fixed)))
        (quote received)
        received))))

(def my-arity-error
  (lambda (params args)
    (my-error (quote arity) (my-arity-detail params args))))

; Lambda-list validation is syntax semantics, not application semantics.
; Contract 6 adds reserved-Canon rejection to the existing structural checks.
(def my-symbol-member?
  (lambda (name names)
    (cond
      ((atom names) (quote ()))
      ((eq name (car names)) t)
      (t (my-symbol-member? name (cdr names))))))

(def my-lambda-list-error-pairs
  (lambda (params seen)
    (cond
      ((atom params)
       (cond
         ((eq params (quote ())) (quote ()))
         ((symbol? params)
          (cond
            ((my-canon-name? params)
             (list (quote canonical-parameter) params))
            ((my-symbol-member? params seen)
             (list (quote duplicate-parameter) params))
            (t (quote ()))))
         (t (list (quote invalid-rest) params))))
      ((symbol? (car params))
       (cond
         ((my-canon-name? (car params))
          (list (quote canonical-parameter) (car params)))
         ((my-symbol-member? (car params) seen)
          (list (quote duplicate-parameter) (car params)))
         (t
          (my-lambda-list-error-pairs
            (cdr params)
            (cons (car params) seen)))))
      (t (list (quote non-symbol-parameter) (car params))))))

(def my-lambda-list-error
  (lambda (params)
    (cond
      ((atom params)
       (cond
         ((eq params (quote ())) (quote ()))
         ((symbol? params)
          (cond
            ((my-canon-name? params)
             (list (quote canonical-parameter) params))
            (t (quote ()))))
         (t (list (quote invalid-parameters) params))))
      (t (my-lambda-list-error-pairs params (quote ()))))))

(def my-lambda-invalid-form
  (lambda (problem)
    (my-error
      (quote invalid-form)
      (cons (quote lambda-parameters) problem))))

(def my-make-closure
  (lambda (params body env)
    (let ((problem (my-lambda-list-error params)))
      (cond
        ((atom problem) (list (quote closure) params body env))
        (t (my-lambda-invalid-form problem))))))

; Return the first malformed lambda-list in a top-level recursive group.
; Canon-named definitions never enter a recursive group; my-lambda-def-form?
; routes them to the ordinary top-form rejection path first.
(def my-lambda-def-group-error
  (lambda (forms)
    (cond
      ((atom forms) (quote ()))
      (t
       (let ((problem
               (my-lambda-list-error (second (third (car forms))))))
         (cond
           ((atom problem) (my-lambda-def-group-error (cdr forms)))
           (t problem)))))))

; Parameter binding owns only the successful path. Arity and Canon-name
; validity are checked before this function is entered.
(def bind-params
  (lambda (params args env)
    (cond
      ((atom params)
       (cond
         ((eq params (quote ())) env)
         (t (cons (cons params args) env))))
      (t (cons (cons (car params) (car args))
               (bind-params (cdr params) (cdr args) env))))))

(def my-eval-list-result
  (lambda (exprs env)
    (cond
      ((atom exprs) (my-result-ok (quote ())))
      (t
       (let ((head-result (my-eval-result (car exprs) env)))
         (cond
           ((my-result-fail? head-result) head-result)
           (t
            (let ((tail-result (my-eval-list-result (cdr exprs) env)))
              (cond
                ((my-result-fail? tail-result) tail-result)
                (t
                 (my-result-ok
                   (cons
                     (my-result-value head-result)
                     (my-result-value tail-result)))))))))))))

(def my-eval-list
  (lambda (exprs env)
    (my-result-value (my-eval-list-result exprs env))))

(def my-eval-body-result
  (lambda (body env)
    (cond
      ((atom (cdr body)) (my-eval-result (car body) env))
      (t
       (let ((first-result (my-eval-result (car body) env)))
         (cond
           ((my-result-fail? first-result) first-result)
           (t (my-eval-body-result (cdr body) env))))))))

(def my-eval-body
  (lambda (body env)
    (my-result-value (my-eval-body-result body env))))

(def my-eval-cond-result
  (lambda (clauses env)
    (cond
      ((atom clauses) (my-result-ok (quote ())))
      (t
       (let ((clause (car clauses)))
         (cond
           ; #217 canonical path: evaluate only the query. The expected result
           ; is already Lisp data in the interpreted program and must never be
           ; executed as code. Match it structurally, then evaluate the branch.
           ((eq (length clause) 3) (identity-relation same)
            (let ((test-result (my-eval-result (car clause) env)))
              (cond
                ((my-result-fail? test-result) test-result)
                ((equal? (my-result-value test-result) (second clause))
                 (structural-relation same)
                 (my-eval-result (third clause) env))
                ((equal? (my-result-value test-result) (second clause))
                 (structural-relation distinct)
                 (my-eval-cond-result (cdr clauses) env)))))
           ; Historical two-part clauses remain migration-only, mirroring the
           ; native evaluator until their callers are moved to explicit result
           ; matching. This path intentionally retains old truthiness.
           ((eq (length clause) 2) (identity-relation same)
            (let ((test-result (my-eval-result (car clause) env)))
              (cond
                ((my-result-fail? test-result) test-result)
                ((my-result-value test-result)
                 (my-eval-result (second clause) env))
                (t (my-eval-cond-result (cdr clauses) env)))))
           (t
            (my-result-fail
              (my-error
                (quote invalid-form)
                (list (quote cond-clause) clause))))))))))

(def my-eval-cond
  (lambda (clauses env)
    (my-result-value (my-eval-cond-result clauses env))))

(def my-take-lambda-def-group
  (lambda (forms)
    (cond
      ((atom forms) (quote ()))
      ((my-lambda-def-form? (car forms))
       (cons (car forms)
             (my-take-lambda-def-group (cdr forms))))
      (t (quote ())))))

(def my-drop-lambda-def-group
  (lambda (forms)
    (cond
      ((atom forms) (quote ()))
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

; Application-time reconstruction keeps SCC members as lexical bindings around
; the refreshed shared frame. This retains finite group recursion.
(def my-build-group-env-onto
  (lambda (forms group captured-env out)
    (cond
      ((atom forms) out)
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

; Program-time installation is different: SCC members are top-level definitions
; and therefore belong to the shared definition frame rather than to a lexical
; prefix that could become a stale snapshot for later closures.
(def my-install-group-env-onto
  (lambda (forms group captured-env out)
    (cond
      ((atom forms) out)
      (t
       (let ((form (car forms)))
         (my-install-group-env-onto
           (cdr forms)
           group
           captured-env
           (my-env-define
             (second form)
             (my-group-closure-from-def form group captured-env)
             out)))))))

(def my-install-group-env
  (lambda (group captured-env)
    (my-install-group-env-onto group group captured-env captured-env)))

; caller-env is optional only for compatibility with the old experimental
; meta-eval-mutual wrapper. Main my-eval always passes it. When present it is
; used solely to refresh the shared top-level marker in a captured environment.
; Internal application returns an outcome envelope. This keeps evaluator
; failures distinct from ordinary Lisp data whose printed shape happens to be
; `(error ...)`.
(def my-apply-result
  (lambda (fn args caller-env)
    (cond
      ((atom fn)
       (my-result-fail (my-error (quote not-callable) fn)))
      ((my-primitive? fn)
       (my-result-ok (my-apply-primitive (second fn) args)))
      ((my-closure? fn)
       (cond
         ((my-arity-ok? (second fn) args)
          (my-eval-body-result
            (third fn)
            (bind-params
              (second fn)
              args
              (my-refresh-shared-frame
                (my-fourth fn)
                caller-env))))
         (t
          (my-result-fail (my-arity-error (second fn) args)))))
      ((my-recursive-closure? fn)
       (cond
         ((my-arity-ok? (third fn) args)
          (let ((captured
                  (my-refresh-shared-frame
                    (my-fifth fn)
                    caller-env)))
            (let ((self-env
                    (cons (cons (second fn) fn)
                          captured)))
              (my-eval-body-result
                (my-fourth fn)
                (bind-params
                  (third fn)
                  args
                  self-env)))))
         (t
          (my-result-fail (my-arity-error (third fn) args)))))
      ((my-group-closure? fn)
       (cond
         ((my-arity-ok? (third fn) args)
          (let ((captured
                  (my-refresh-shared-frame
                    (my-sixth fn)
                    caller-env)))
            (let ((group-env
                    (my-build-group-env (my-fifth fn) captured)))
              (my-eval-body-result
                (my-fourth fn)
                (bind-params
                  (third fn)
                  args
                  group-env)))))
         (t
          (my-result-fail (my-arity-error (third fn) args)))))
      ((my-macro? fn)
       (cond
         ((my-arity-ok? (second fn) args)
          (my-eval-body-result
            (third fn)
            (bind-params
              (second fn)
              args
              (my-refresh-shared-frame
                (my-fourth fn)
                caller-env))))
         (t
          (my-result-fail (my-arity-error (second fn) args)))))
      (t
       (my-result-fail (my-error (quote not-callable) fn))))))

(def my-apply
  (lambda (fn args . caller-env-rest)
    (let ((caller-env
            (cond
              ((atom caller-env-rest) (quote ()))
              (t (car caller-env-rest)))))
      (my-result-value (my-apply-result fn args caller-env)))))

; Evaluate one ordinary application with explicit operator-first and
; left-to-right argument sequencing. Recursive evaluation stays inside the
; outcome channel until this application has produced a value or its first
; failure.
(def my-eval-application-result
  (lambda (expr env)
    (let ((fn-result (my-eval-result (car expr) env)))
      (cond
        ((my-result-fail? fn-result) fn-result)
        (t
         (let ((fn (my-result-value fn-result)))
           (cond
             ((my-macro? fn)
              (cond
                ((my-arity-ok? (second fn) (cdr expr))
                 (let ((expansion-result
                         (my-apply-result fn (cdr expr) env)))
                   (cond
                     ((my-result-fail? expansion-result) expansion-result)
                     (t
                      (my-eval-result
                        (my-result-value expansion-result)
                        env)))))
                (t
                 (my-result-fail
                   (my-arity-error (second fn) (cdr expr))))))
             (t
              (let ((args-result
                      (my-eval-list-result (cdr expr) env)))
                (cond
                  ((my-result-fail? args-result) args-result)
                  (t
                   (my-apply-result
                     fn
                     (my-result-value args-result)
                     env))))))))))))

(def my-eval-result
  (lambda (expr env)
    (cond
      ((atom expr)
       (cond
         ((my-unresolved-name? expr env)
          (my-result-fail
            (my-error (quote unbound-symbol) expr)))
         (t
          (my-result-ok (env-lookup expr env)))))
      ((atom (car expr))
       (cond
         ((my-canon-quote-name? (car expr))
          (my-result-ok (second expr)))
         ((my-canon-cond-name? (car expr))
          (my-eval-cond-result (cdr expr) env))
         ((my-lambda-name? (car expr))
          (let ((problem (my-lambda-list-error (second expr))))
            (cond
              ((atom problem)
               (my-result-ok
                 (my-make-closure
                   (second expr)
                   (cdr (cdr expr))
                   env)))
              (t
               (my-result-fail
                 (my-lambda-invalid-form problem))))))
         (t
          (my-eval-application-result expr env))))
      (t
       (my-eval-application-result expr env)))))

(def my-eval
  (lambda (expr env)
    (my-result-value (my-eval-result expr env))))

; Top-level sequencing. `def` and `defmacro` return `(new-env . value)` so
; the environment can be threaded explicitly to the next form. Under
; my-eval-program, my-env-define updates the ADR-009 shared definition frame;
; direct calls without a marker retain the historical plain-alist behavior.
;
; Contract 6 rejects Canon definition names before value construction.
(def my-eval-top-form
  (lambda (form env)
    (cond
      ((atom form) (cons env (my-eval form env)))
      ((my-definition-name? (car form))
       (cond
         ((my-canon-name? (second form))
          (cons env (my-canon-binding-error (second form))))
         (t
          (let ((value-form (third form)))
            (cond
              ((my-lambda-form? value-form)
               (let ((problem (my-lambda-list-error (second value-form))))
                 (cond
                   ((atom problem)
                    (let ((value
                            (list (quote recursive-closure)
                                  (second form)
                                  (second value-form)
                                  (cdr (cdr value-form))
                                  env)))
                      (cons
                        (my-env-define (second form) value env)
                        value)))
                   (t (cons env (my-lambda-invalid-form problem))))))
              (t
               (let ((value (my-eval value-form env)))
                 (cons
                   (my-env-define (second form) value env)
                   value))))))))
      ((my-defmacro-name? (car form))
       (cond
         ((my-canon-name? (second form))
          (cons env (my-canon-binding-error (second form))))
         (t
          (let ((macro-val
                  (list (quote macro)
                        (third form)
                        (cdr (cdr (cdr form)))
                        env)))
            (cons
              (my-env-define (second form) macro-val env)
              macro-val)))))
      (t (cons env (my-eval form env))))))

; Dependency analysis for top-level lambda definitions stays in Lisp data.
; A graph entry is `(name dependencies)`, where dependencies are only free
; references to names from the same contiguous lambda-definition block.
(def my-params-bind-name?
  (lambda (name params)
    (cond
      ((atom params)
       (cond
         ((eq params (quote ())) (quote ()))
         ((eq params name) t)
         (t (quote ()))))
      ((eq (car params) name) t)
      (t (my-params-bind-name? name (cdr params))))))

(def my-forms-reference-name?
  (lambda (forms name)
    (cond
      ((atom forms) (quote ()))
      ((my-form-references-name? (car forms) name) t)
      (t (my-forms-reference-name? (cdr forms) name)))))

(def my-form-references-name?
  (lambda (form name)
    (cond
      ((atom form)
       (cond
         ((symbol? form) (eq form name))
         (t (quote ()))))
      ((atom (car form))
       (cond
         ; Quoted data is not a lexical dependency.
         ((my-canon-quote-name? (car form)) (quote ()))
         ; A nested lambda can shadow a candidate top-level name.
         ((my-lambda-name? (car form))
          (cond
            ((my-params-bind-name? name (second form)) (quote ()))
            (t (my-forms-reference-name? (cdr (cdr form)) name))))
         (t (my-forms-reference-name? form name))))
      (t (my-forms-reference-name? form name)))))

(def my-lambda-def-references-name?
  (lambda (form name)
    (let ((lambda-form (third form)))
      (cond
        ((my-params-bind-name? name (second lambda-form)) (quote ()))
        (t (my-forms-reference-name? (cdr (cdr lambda-form)) name))))))

(def my-lambda-def-names
  (lambda (forms)
    (cond
      ((atom forms) (quote ()))
      (t (cons (second (car forms))
               (my-lambda-def-names (cdr forms)))))))

(def my-def-dependencies
  (lambda (form candidates)
    (cond
      ((atom candidates) (quote ()))
      ((my-lambda-def-references-name? form (car candidates))
       (cons (car candidates)
             (my-def-dependencies form (cdr candidates))))
      (t (my-def-dependencies form (cdr candidates))))))

(def my-build-dependency-graph-with-names
  (lambda (forms names)
    (cond
      ((atom forms) (quote ()))
      (t
       (cons
         (list
           (second (car forms))
           (my-def-dependencies (car forms) names))
         (my-build-dependency-graph-with-names (cdr forms) names))))))

(def my-build-dependency-graph
  (lambda (forms)
    (let ((names (my-lambda-def-names forms)))
      (my-build-dependency-graph-with-names forms names))))

(def my-graph-dependencies
  (lambda (name graph)
    (cond
      ((atom graph) (quote ()))
      ((eq name (car (car graph))) (second (car graph)))
      (t (my-graph-dependencies name (cdr graph))))))

(def my-graph-dependencies-reach?
  (lambda (dependencies target graph visited)
    (cond
      ((atom dependencies) (quote ()))
      ((eq (car dependencies) target) t)
      ((my-symbol-member? (car dependencies) visited)
       (my-graph-dependencies-reach?
         (cdr dependencies) target graph visited))
      ((my-graph-reaches?
         (car dependencies)
         target
         graph
         (cons (car dependencies) visited))
       t)
      (t
       (my-graph-dependencies-reach?
         (cdr dependencies) target graph visited)))))

(def my-graph-reaches?
  (lambda (from target graph visited)
    (my-graph-dependencies-reach?
      (my-graph-dependencies from graph)
      target
      graph
      (cons from visited))))

; The SCC containing `name` is the set of block names mutually reachable
; with it. `name` itself is always retained so an acyclic node is a singleton
; component; only components with 2+ members use recursive-group-closure.
(def my-scc-names
  (lambda (name candidates graph)
    (cond
      ((atom candidates) (quote ()))
      ((eq name (car candidates))
       (cons (car candidates)
             (my-scc-names name (cdr candidates) graph)))
      ((my-graph-reaches? name (car candidates) graph (quote ()))
       (cond
         ((my-graph-reaches? (car candidates) name graph (quote ()))
          (cons (car candidates)
                (my-scc-names name (cdr candidates) graph)))
         (t (my-scc-names name (cdr candidates) graph))))
      (t (my-scc-names name (cdr candidates) graph)))))

(def my-select-defs-by-names
  (lambda (forms names)
    (cond
      ((atom forms) (quote ()))
      ((my-symbol-member? (second (car forms)) names)
       (cons (car forms)
             (my-select-defs-by-names (cdr forms) names)))
      (t (my-select-defs-by-names (cdr forms) names)))))

(def my-remove-defs-by-names
  (lambda (forms names)
    (cond
      ((atom forms) (quote ()))
      ((my-symbol-member? (second (car forms)) names)
       (my-remove-defs-by-names (cdr forms) names))
      (t
       (cons (car forms)
             (my-remove-defs-by-names (cdr forms) names))))))

(def my-last-lambda-def-name
  (lambda (forms)
    (cond
      ((atom (cdr forms)) (second (car forms)))
      (t (my-last-lambda-def-name (cdr forms))))))

(def my-eval-lambda-components
  (lambda (forms graph env final-name)
    (cond
      ((atom forms)
       (cons env (env-lookup final-name env)))
      (t
       (let ((name (second (car forms))))
         (let ((component-names
                 (my-scc-names
                   name
                   (my-lambda-def-names forms)
                   graph)))
           (cond
             ; A singleton stays on the ordinary top-level path. That path
             ; already gives self-recursive definitions a finite
             ; recursive-closure without falsely inventing a group.
             ((atom (cdr component-names))
              (let ((result (my-eval-top-form (car forms) env)))
                (my-eval-lambda-components
                  (cdr forms)
                  graph
                  (car result)
                  final-name)))
             (t
              (let ((component
                      (my-select-defs-by-names forms component-names)))
                (let ((group-env (my-install-group-env component env)))
                  (my-eval-lambda-components
                    (my-remove-defs-by-names forms component-names)
                    graph
                    group-env
                    final-name)))))))))))

(def my-eval-lambda-block
  (lambda (forms env)
    (let ((graph (my-build-dependency-graph forms))
          (final-name (my-last-lambda-def-name forms)))
      (my-eval-lambda-components forms graph env final-name))))

; `my-eval-program` validates each contiguous top-level non-Canon
; lambda-definition block, builds its explicit dependency graph, and gives
; recursive-group-closure only to real multi-member strongly-connected
; components. Independent or one-way-dependent definitions stay on the
; ordinary singleton path. This prevents adjacency itself from inventing
; recursion while keeping finite Lisp data for genuine mutual recursion.
;
; For every non-empty program ADR-009 installs one finite shared-frame marker.
; Recursive calls reuse that same marker. An empty form list remains a valid
; no-op program and preserves the supplied environment exactly, so TASK-001's
; empty-program witness is unchanged.
(def my-eval-program
  (lambda (forms env)
    (cond
      ((atom forms) (cons env (quote ())))
      (t
       (let ((program-env (my-ensure-shared-frame env)))
         (cond
           ((my-lambda-def-form? (car forms))
            (let ((block (my-take-lambda-def-group forms)))
              (let ((problem (my-lambda-def-group-error block)))
                (cond
                  ((atom problem)
                   (let ((rest (my-drop-lambda-def-group forms)))
                     (let ((block-result
                             (my-eval-lambda-block block program-env)))
                       (cond
                         ((atom rest) block-result)
                         (t
                          (my-eval-program
                            rest
                            (car block-result)))))))
                  (t
                   (cons
                     program-env
                     (my-lambda-invalid-form problem)))))))
           (t
            (let ((result (my-eval-top-form (car forms) program-env)))
              (cond
                ((atom (cdr forms)) result)
                (t
                 (my-eval-program
                   (cdr forms)
                   (car result))))))))))))