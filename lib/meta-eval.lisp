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

(0011 my-primitive
  (0010 (name)
    (1110 (001 primitive) name)))

(0011 my-error
  (0010 (kind detail)
    (1110 (001 error) kind detail)))

; Internal evaluator outcomes carry provenance that interpreted Lisp data cannot
; forge. The tag is a native closure identity, not a symbol or list shape that
; a program could reproduce with quote/cons. Public my-eval/my-apply unwrap the
; envelope, so the observable interface stays unchanged.
(0011 my-result-ok-token
  (0010 (value) value))

(0011 my-result-fail-token
  (0010 (value) value))

(0011 my-result-ok
  (0010 (value)
    (111 my-result-ok-token value)))

(0011 my-result-fail
  (0010 (error)
    (111 my-result-fail-token error)))

(0011 my-result-fail?
  (0010 (result)
    (110
      
      ((010 result)  (001 ()))
      ((010 ()) (101 (100 result) my-result-fail-token)))))

(0011 my-result-value
  (0010 (result)
    (011 result)))

; Surface spellings are not owned here. The generated projection loaded before
; this evaluator maps every admitted runtime spelling to the numeric semantic ID
; from lib/surface/semantic-registry.lisp. This file owns only the mapping from
; those opaque IDs to evaluator mechanisms.
(0011 my-semantic-id?
  (0010 (name semantic-id)
    (110
      ((11110111 name semantic-id) t)
      ((010 ()) (11110111 (my-semantic-id-for-surface name) semantic-id)))))

(0011 my-canon-identity
  (0010 (name)
    (001000 ((semantic-id (110
                         ((11110111 name 001) 001)
                         ((11110111 name 010) 010)
                         ((11110111 name 101) 101)
                         ((11110111 name 111) 111)
                         ((11110111 name 100) 100)
                         ((11110111 name 011) 011)
                         ((11110111 name 110) 110)
                         ((010 ()) (my-semantic-id-for-surface name)))))
      (110
        ((101 semantic-id 001) (001 quote))
        ((101 semantic-id 010) (001 atom))
        ((101 semantic-id 101) (001 eq))
        ((101 semantic-id 111) (001 cons))
        ((101 semantic-id 100) (001 car))
        ((101 semantic-id 011) (001 cdr))
        ((101 semantic-id 110) (001 cond))
        ))))

(0011 my-lambda-name?
  (0010 (name)
    (my-semantic-id? name 0010)))

(0011 my-define-name?
  (0010 (name)
    (my-semantic-id? name 0011)))

(0011 my-defmacro-name?
  (0010 (name)
    (my-semantic-id? name 00011)))

(0011 my-def-compat-name?
  (0010 (name)
    (my-semantic-id? name 0011)))

(0011 my-definition-name?
  (0010 (name)
    (110
      ((my-define-name? name) t)
      ((my-def-compat-name? name) t)
      )))

(0011 my-canon-name?
  (0010 (name)
    (110
      ((my-canon-identity name) t)
      )))

(0011 my-canon-callable-identity?
  (0010 (identity-ref)
    (110
      ((101 identity-ref (001 atom)) t)
      ((101 identity-ref (001 eq)) t)
      ((101 identity-ref (001 cons)) t)
      ((101 identity-ref (001 car)) t)
      ((101 identity-ref (001 cdr)) t)
      )))

(0011 my-canon-quote-name?
  (0010 (name)
    (101 (my-canon-identity name) (001 quote))))

(0011 my-canon-cond-name?
  (0010 (name)
    (101 (my-canon-identity name) (001 cond))))

(0011 my-canon-binding-error
  (0010 (name)
    (my-error
      (001 invalid-form)
      (1110 (001 canonical-name-immutable) name))))

; Root primitive meanings are represented as values. Canon is handled first.
; Ordinary non-Canon boundary spellings are resolved to exact SENS identities
; here; the primitive value carried by the evaluator never uses the human
; spelling as its identity.
(0011 my-default-binding
  (0010 (name)
    (001000 ((identity-ref (my-canon-identity name)))
      (110
        ((my-canon-callable-identity? identity-ref) (my-primitive identity-ref))
        ((my-canon-name? name) (my-canon-binding-error name))
        ((my-semantic-id? name 01010) (my-primitive 01010))
        ((my-semantic-id? name 01011) (my-primitive 01011))
        ((my-semantic-id? name 10110) (my-primitive 10110))
        ((my-semantic-id? name 11010) (my-primitive 11010))
        ((my-semantic-id? name 11110111) (my-primitive 11110111))
        ((my-semantic-id? name 11011) (my-primitive 11011))
        ((my-semantic-id? name 11110100)
         (my-primitive 11110100))
        ((my-semantic-id? name 11101101)
         (my-primitive 11101101))
        ((010 ()) name)))))

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
(0011 my-shared-frame-binding?
  (0010 (binding)
    (110
      
      ((010 binding)  (001 ()))
      ((010 ()) (101 (100 binding) 0)))))

(0011 my-frame-bound?
  (0010 (name frame)
    (110
      
      ((010 frame)  (001 ()))
      ((101 (100 (100 frame)) name) t)
      ((010 ()) (my-frame-bound? name (011 frame))))))

(0011 my-frame-lookup
  (0010 (name frame)
    (110
      ((101 (100 (100 frame)) name) (011 (100 frame)))
      ((010 ()) (my-frame-lookup name (011 frame))))))

(0011 my-env-has-shared-frame?
  (0010 (env-ref)
    (110
      
      ((010 env-ref)  (001 ()))
      ((my-shared-frame-binding? (100 env-ref)) t)
      ((010 ()) (my-env-has-shared-frame? (011 env-ref))))))

(0011 my-shared-frame-value
  (0010 (env-ref)
    (110
      
      ((010 env-ref)  (001 ()))
      ((my-shared-frame-binding? (100 env-ref)) (011 (100 env-ref)))
      ((010 ()) (my-shared-frame-value (011 env-ref))))))

(0011 my-ensure-shared-frame
  (0010 (env-ref)
    (110
      ((my-env-has-shared-frame? env-ref) env-ref)
      ((010 ()) (111 (111 0 (001 ())) env-ref)))))

(0011 my-replace-shared-frame
  (0010 (env-ref frame)
    (110
      
      ((010 env-ref)  env-ref)
      ((my-shared-frame-binding? (100 env-ref))
       (111 (111 0 frame) (011 env-ref)))
      ((010 ())
       (111 (100 env-ref)
             (my-replace-shared-frame (011 env-ref) frame))))))

(0011 my-refresh-shared-frame
  (0010 (captured-env caller-env)
    (110
      ((my-env-has-shared-frame? captured-env)
       (110
         ((my-env-has-shared-frame? caller-env)
          (my-replace-shared-frame
            captured-env
            (my-shared-frame-value caller-env)))
         ((010 ()) captured-env)))
      ((010 ()) captured-env))))

; Definitions update the shared marker when one is active. Outside
; my-eval-program this falls back to the historical plain-alist extension, so
; direct my-eval-top-form use remains compatible.
(0011 my-env-define
  (0010 (name value env-ref)
    (110
      ((0100 (010 env-ref)) (111 (111 name value) env-ref))
      ((010 env-ref)  (111 (111 name value) env-ref))
      ((my-shared-frame-binding? (100 env-ref))
       (111
         (111 0
               (111 (111 name value)
                     (011 (100 env-ref))))
         (011 env-ref)))
      ((010 ())
       (111 (100 env-ref)
             (my-env-define name value (011 env-ref)))))))

; Contract 6.0: Canon outranks the lexical alist even if a hostile/pre-existing
; environment contains the same text. Non-Canon names retain ordinary lookup.
(0011 env-lookup
  (0010 (name env-ref)
    (001000 ((identity-ref (my-canon-identity name)))
      (110
        ((my-canon-callable-identity? identity-ref) (my-primitive identity-ref))
        ((my-canon-name? name) (my-canon-binding-error name))
        ((0100 (010 env-ref)) (my-default-binding name))
        ((010 env-ref)  (my-default-binding name))
        ((my-shared-frame-binding? (100 env-ref))
         (110
           ((my-frame-bound? name (011 (100 env-ref)))
            (my-frame-lookup name (011 (100 env-ref))))
           ((010 ()) (env-lookup name (011 env-ref)))))
        ((101 (100 (100 env-ref)) name) (011 (100 env-ref)))
        ((010 ()) (env-lookup name (011 env-ref)))))))

(0011 env-bound?
  (0010 (name env-ref)
    (110
      ((my-canon-name? name) t)
      
      ((010 env-ref)  (001 ()))
      ((my-shared-frame-binding? (100 env-ref))
       (110
         ((my-frame-bound? name (011 (100 env-ref))) t)
         ((010 ()) (env-bound? name (011 env-ref)))))
      ((101 (100 (100 env-ref)) name) t)
      ((010 ()) (env-bound? name (011 env-ref))))))

(0011 my-primitive?
  (0010 (value)
    (110
      
      ((010 value)  (001 ()))
      ((010 ()) (101 (100 value) (001 primitive))))))

; UnknownSymbol belongs to name resolution, not application. A symbol produced
; as a value (for example by quote) is not an unresolved lookup and therefore
; must later fail as not-callable/Type if placed in operator position.
;
; `symbol?` itself is language-owned in core.lisp, derived without a Rust builtin,
; so this distinction adds no primitive to the closed Canon.
(0011 my-unresolved-name?
  (0010 (name env-ref)
    (110
      ((110101100 name)
       (110
         ((101 name t) (001 ()))
         ((my-canon-name? name) (001 ()))
         ((env-bound? name env-ref) (001 ()))
         ((my-primitive? (my-default-binding name)) (001 ()))
         ((010 ()) t)))
      )))

(0011 my-macro?
  (0010 (value)
    (110
      
      ((010 value)  (001 ()))
      ((010 ()) (101 (100 value) (001 macro))))))

(0011 my-closure?
  (0010 (value)
    (110
      
      ((010 value)  (001 ()))
      ((010 ()) (101 (100 value) (001 closure))))))

; A recursive closure is finite Lisp data. It does not require a cyclic host
; Environment. At call time my-apply reconstructs the one self-binding that
; the function needs. Contract 6 guarantees that this name is never Canon.
;
; Shape:
;   (recursive-closure name params body captured-env)
(0011 my-recursive-closure?
  (0010 (value)
    (110
      
      ((010 value)  (001 ()))
      ((010 ()) (101 (100 value) (001 recursive-closure))))))

; A mutually-recursive group is also finite Lisp data. Every member stores the
; same raw group and captured outer environment; my-apply reconstructs the
; group's bindings at call time rather than relying on a cyclic host object.
;
; Shape:
;   (recursive-group-closure name params body group captured-env)
(0011 my-group-closure?
  (0010 (value)
    (110
      
      ((010 value)  (001 ()))
      ((010 ()) (101 (100 value) (001 recursive-group-closure))))))

(0011 my-lambda-form?
  (0010 (form)
    (110
      
      ((010 form)  (001 ()))
      ((0100 (010 (100 form))) (my-lambda-name? (100 form)))
      ((010 (100 form))  (my-lambda-name? (100 form)))
      )))

(0011 my-lambda-def-form?
  (0010 (form)
    (110
      
      ((010 form)  (001 ()))
      ((my-definition-name? (100 form))
       (110
         ((my-canon-name? (1001 form)) (001 ()))
         ((010 ()) (my-lambda-form? (10011 form)))))
      )))

(0011 my-fourth
  (0010 (values)
    (100 (011 (011 (011 values))))))

(0011 my-fifth
  (0010 (values)
    (100 (011 (011 (011 (011 values)))))))

(0011 my-sixth
  (0010 (values)
    (100 (011 (011 (011 (011 (011 values))))))))

(0011 my-compare-two
  (0010 (operator left right)
    (110
      ((101 operator 11010) (11010 left right))
      ((101 operator 11110111) (11110111 left right))
      ((101 operator 11011) (11011 left right))
      )))

; Chained comparison semantics are Lisp-owned: values arrive already
; evaluated, adjacent pairs are compared left-to-right, and evaluation stops
; at the first false pair.
; NOTE: my-compare-two returns exact-Q 1/0, not t/(). Since 0 is truthy
; in my-lisp (only Nil and Bool(false) are falsy), we MUST use a 3-part
; clause matching the exact-Q YES result (1) — not a 2-part clause.
(0011 my-compare-chain
  (0010 (operator values)
    (110
      
      ((010 (011 values))  t)
      ((101 (my-compare-two operator (100 values) (1001 values)) 1)
       (my-compare-chain operator (011 values)))
      )))

; Primitive *identity* is a Lisp value. This function is the narrow bridge
; from that identity to the admitted native operation mechanism.
(0011 my-apply-primitive
  (0010 (name args)
    (110
      ((101 name (001 atom)) (010 (100 args)))
      ((101 name (001 eq))   (101 (100 args) (1001 args)))
      ((101 name (001 car))  (100 (100 args)))
      ((101 name (001 cdr))  (011 (100 args)))
      ((101 name (001 cons)) (111 (100 args) (1001 args)))
      ((101 name 01010) (01010 (100 args) (1001 args)))
      ((101 name 01011) (01011 (100 args) (1001 args)))
      ((101 name 10110) (10110 (100 args) (1001 args)))
      ((101 name 11010) (my-compare-chain 11010 args))
      ((101 name 11110111) (my-compare-chain 11110111 args))
      ((101 name 11011) (my-compare-chain 11011 args))
      ((101 name 11110100)
       (11110100 (100 args)))
      ((101 name 11101101)
       (11101101 (100 args)))
      ((010 ()) (1110 (001 unknown-primitive) name)))))

; Lambda-list arity is derivable from Lisp list structure itself:
;   (x y)        -> exact 2
;   (x y . rest) -> at least 2
;   args         -> at least 0
; No host metadata is required.
(0011 my-fixed-param-count
  (0010 (params)
    (110
      
      ((010 params)  0)
      ((010 ()) (01010 1 (my-fixed-param-count (011 params)))))))

(0011 my-rest-param?
  (0010 (params)
    (110
      ((0100 (010 params)) (110
         ((101 params (001 ())) (001 ()))
         ((010 ()) t)))
      ((010 params)  (110
         ((101 params (001 ())) (001 ()))
         ((010 ()) t)))
      ((010 ()) (my-rest-param? (011 params))))))

(0011 my-arity-ok?
  (0010 (params args)
    (001000 ((fixed (my-fixed-param-count params))
          (received (000000 args)))
      (110
        ((my-rest-param? params)
         (110
           ((11010 received fixed)  (001 ()))
           ((0100 (11010 received fixed)) t)))
        ((010 ())
         (110
           ((101 received fixed)  t)
           ))))))

(0011 my-arity-detail
  (0010 (params args)
    (001000 ((fixed (my-fixed-param-count params))
          (received (000000 args)))
      (1110
        (001 expected)
        (110
          ((my-rest-param? params) (1110 (001 at-least) fixed))
          ((010 ()) (1110 (001 exact) fixed)))
        (001 received)
        received))))

(0011 my-arity-error
  (0010 (params args)
    (my-error (001 arity) (my-arity-detail params args))))

; Lambda-list validation is syntax semantics, not application semantics.
; Contract 6 adds reserved-Canon rejection to the existing structural checks.
(0011 my-symbol-member?
  (0010 (name names)
    (110
      
      ((010 names)  (001 ()))
      ((101 name (100 names)) t)
      ((010 ()) (my-symbol-member? name (011 names))))))

(0011 my-lambda-list-error-pairs
  (0010 (params seen)
    (110
      ((0100 (010 params)) (110
         ((101 params (001 ())) (001 ()))
         ((110101100 params)
          (110
            ((my-canon-name? params)
             (1110 (001 canonical-parameter) params))
            ((my-symbol-member? params seen)
             (1110 (001 duplicate-parameter) params))
            ))
         ((010 ()) (1110 (001 invalid-rest) params))))
      ((010 params)  (110
         ((101 params (001 ())) (001 ()))
         ((110101100 params)
          (110
            ((my-canon-name? params)
             (1110 (001 canonical-parameter) params))
            ((my-symbol-member? params seen)
             (1110 (001 duplicate-parameter) params))
            ))
         ((010 ()) (1110 (001 invalid-rest) params))))
      ((110101100 (100 params))
       (110
         ((my-canon-name? (100 params))
          (1110 (001 canonical-parameter) (100 params)))
         ((my-symbol-member? (100 params) seen)
          (1110 (001 duplicate-parameter) (100 params)))
         ((010 ())
          (my-lambda-list-error-pairs
            (011 params)
            (111 (100 params) seen)))))
      ((010 ()) (1110 (001 non-symbol-parameter) (100 params))))))

(0011 my-lambda-list-error
  (0010 (params)
    (110
      ((0100 (010 params)) (110
         ((101 params (001 ())) (001 ()))
         ((110101100 params)
          (110
            ((my-canon-name? params)
             (1110 (001 canonical-parameter) params))
            ))
         ((010 ()) (1110 (001 invalid-parameters) params))))
      ((010 params)  (110
         ((101 params (001 ())) (001 ()))
         ((110101100 params)
          (110
            ((my-canon-name? params)
             (1110 (001 canonical-parameter) params))
            ))
         ((010 ()) (1110 (001 invalid-parameters) params))))
      ((010 ()) (my-lambda-list-error-pairs params (001 ()))))))

(0011 my-lambda-invalid-form
  (0010 (problem)
    (my-error
      (001 invalid-form)
      (111 (001 lambda-parameters) problem))))

(0011 my-make-closure
  (0010 (params body env-ref)
    (001000 ((problem (my-lambda-list-error params)))
      (110
        ((0100 (010 problem)) (1110 (001 closure) params body env-ref))
        ((010 problem)  (1110 (001 closure) params body env-ref))
        ((010 ()) (my-lambda-invalid-form problem))))))

; Return the first malformed lambda-list in a top-level recursive group.
; Canon-named definitions never enter a recursive group; my-lambda-def-form?
; routes them to the ordinary top-form rejection path first.
(0011 my-lambda-def-group-error
  (0010 (forms)
    (110
      
      ((010 forms)  (001 ()))
      ((010 ())
       (001000 ((problem
               (my-lambda-list-error (1001 (10011 (100 forms))))))
         (110
           ((0100 (010 problem)) (my-lambda-def-group-error (011 forms)))
           ((010 problem)  (my-lambda-def-group-error (011 forms)))
           ((010 ()) problem)))))))

; Parameter binding owns only the successful path. Arity and Canon-name
; validity are checked before this function is entered.
(0011 bind-params
  (0010 (params args env-ref)
    (110
      ((0100 (010 params)) (110
         ((101 params (001 ())) env-ref)
         ((010 ()) (111 (111 params args) env-ref))))
      ((010 params)  (110
         ((101 params (001 ())) env-ref)
         ((010 ()) (111 (111 params args) env-ref))))
      ((010 ()) (111 (111 (100 params) (100 args))
               (bind-params (011 params) (011 args) env-ref))))))

(0011 my-eval-list-result
  (0010 (exprs env-ref)
    (110
      ((0100 (010 exprs)) (my-result-ok (001 ())))
      ((010 exprs)  (my-result-ok (001 ())))
      ((010 ())
       (001000 ((head-result (my-eval-result (100 exprs) env-ref)))
         (110
           ((my-result-fail? head-result) head-result)
           ((010 ())
            (001000 ((tail-result (my-eval-list-result (011 exprs) env-ref)))
              (110
                ((my-result-fail? tail-result) tail-result)
                ((010 ())
                 (my-result-ok
                   (111
                     (my-result-value head-result)
                     (my-result-value tail-result)))))))))))))

(0011 my-eval-list
  (0010 (exprs env-ref)
    (my-result-value (my-eval-list-result exprs env-ref))))

(0011 my-eval-body-result
  (0010 (body env-ref)
    (110
      ((0100 (010 (011 body))) (my-eval-result (100 body) env-ref))
      ((010 (011 body))  (my-eval-result (100 body) env-ref))
      ((010 ())
       (001000 ((first-result (my-eval-result (100 body) env-ref)))
         (110
           ((my-result-fail? first-result) first-result)
           ((010 ()) (my-eval-body-result (011 body) env-ref))))))))

(0011 my-eval-body
  (0010 (body env-ref)
    (my-result-value (my-eval-body-result body env-ref))))

(0011 my-cond-has-migration-clause?
  (0010 (clauses)
    (110
      
      ((010 clauses)  (001 ()))
      ((0100 (010 (100 clauses))) (my-cond-has-migration-clause? (011 clauses)))
      ((010 (100 clauses))  (my-cond-has-migration-clause? (011 clauses)))
      ((101 (000000 (100 clauses)) 2)  t)
      ((101 (000000 (100 clauses)) 2) 
       (my-cond-has-migration-clause? (011 clauses))))))

(0011 my-eval-cond-result-mode
  (0010 (clauses env-ref migration-compatibility?)
    (110
      ((0100 (010 clauses)) (110
         (migration-compatibility? (my-result-ok (001 ())))
         ((010 ())
          (my-result-fail
            (my-error (001 unsatisfied-conditional) (001 cond))))))
      ((010 clauses)  (110
         (migration-compatibility? (my-result-ok (001 ())))
         ((010 ())
          (my-result-fail
            (my-error (001 unsatisfied-conditional) (001 cond))))))
      ((010 ())
       (001000 ((clause (100 clauses)))
         (110
           ; #217 canonical path: evaluate only the query. The expected result
           ; is already Lisp data in the interpreted program and must never be
           ; executed as code. Match it structurally, then evaluate the branch.
           ((101 (000000 clause) 3) 
            (001000 ((test-result (my-eval-result (100 clause) env-ref)))
              (110
                ((my-result-fail? test-result) test-result)
                ((11110111 (my-result-value test-result) (1001 clause))
                 
                 (my-eval-result (10011 clause) env-ref))
                ((0100 (11110111 (my-result-value test-result) (1001 clause)))
                 (my-eval-cond-result-mode
                   (011 clauses) env-ref migration-compatibility?)))))
           ; Historical two-part clauses remain migration-only, mirroring the
           ; native evaluator until their callers are moved to explicit result
           ; matching. This path intentionally retains old truthiness.
           ((101 (000000 clause) 2) 
            (001000 ((test-result (my-eval-result (100 clause) env-ref)))
              (110
                ((my-result-fail? test-result) test-result)
                ((my-result-value test-result)
                 (my-eval-result (1001 clause) env-ref))
                ((010 ())
                 (my-eval-cond-result-mode
                   (011 clauses) env-ref migration-compatibility?)))))
           ((010 ())
            (my-result-fail
              (my-error
                (001 invalid-form)
                (1110 (001 cond-clause) clause))))))))))

(0011 my-eval-cond-result
  (0010 (clauses env-ref)
    (my-eval-cond-result-mode
      clauses env-ref (my-cond-has-migration-clause? clauses))))

(0011 my-eval-cond
  (0010 (clauses env-ref)
    (my-result-value (my-eval-cond-result clauses env-ref))))

(0011 my-take-lambda-def-group
  (0010 (forms)
    (110
      
      ((010 forms)  (001 ()))
      ((my-lambda-def-form? (100 forms))
       (111 (100 forms)
             (my-take-lambda-def-group (011 forms))))
      )))

(0011 my-drop-lambda-def-group
  (0010 (forms)
    (110
      
      ((010 forms)  (001 ()))
      ((my-lambda-def-form? (100 forms))
       (my-drop-lambda-def-group (011 forms)))
      ((010 ()) forms))))

(0011 my-group-closure-from-def
  (0010 (form group captured-env)
    (001000 ((lambda-form (10011 form)))
      (1110 (001 recursive-group-closure)
            (1001 form)
            (1001 lambda-form)
            (011 (011 lambda-form))
            group
            captured-env))))

; Application-time reconstruction keeps SCC members as lexical bindings around
; the refreshed shared frame. This retains finite group recursion.
(0011 my-build-group-env-onto
  (0010 (forms group captured-env out)
    (110
      
      ((010 forms)  out)
      ((010 ())
       (001000 ((form (100 forms)))
         (my-build-group-env-onto
           (011 forms)
           group
           captured-env
           (111
             (111 (1001 form)
                   (my-group-closure-from-def form group captured-env))
             out)))))))

(0011 my-build-group-env
  (0010 (group captured-env)
    (my-build-group-env-onto group group captured-env captured-env)))

; Program-time installation is different: SCC members are top-level definitions
; and therefore belong to the shared definition frame rather than to a lexical
; prefix that could become a stale snapshot for later closures.
(0011 my-install-group-env-onto
  (0010 (forms group captured-env out)
    (110
      
      ((010 forms)  out)
      ((010 ())
       (001000 ((form (100 forms)))
         (my-install-group-env-onto
           (011 forms)
           group
           captured-env
           (my-env-define
             (1001 form)
             (my-group-closure-from-def form group captured-env)
             out)))))))

(0011 my-install-group-env
  (0010 (group captured-env)
    (my-install-group-env-onto group group captured-env captured-env)))

; caller-env is optional only for compatibility with the old experimental
; meta-eval-mutual wrapper. Main my-eval always passes it. When present it is
; used solely to refresh the shared top-level marker in a captured environment.
; Internal application returns an outcome envelope. This keeps evaluator
; failures distinct from ordinary Lisp data whose printed shape happens to be
; `(error ...)`.
(0011 my-apply-result
  (0010 (fn args caller-env)
    (110
      ((0100 (010 fn)) (my-result-fail (my-error (001 not-callable) fn)))
      ((010 fn)  (my-result-fail (my-error (001 not-callable) fn)))
      ((my-primitive? fn)
       (my-result-ok (my-apply-primitive (1001 fn) args)))
      ((my-closure? fn)
       (110
         ((my-arity-ok? (1001 fn) args)
          (my-eval-body-result
            (10011 fn)
            (bind-params
              (1001 fn)
              args
              (my-refresh-shared-frame
                (my-fourth fn)
                caller-env))))
         ((010 ())
          (my-result-fail (my-arity-error (1001 fn) args)))))
      ((my-recursive-closure? fn)
       (110
         ((my-arity-ok? (10011 fn) args)
          (001000 ((captured
                  (my-refresh-shared-frame
                    (my-fifth fn)
                    caller-env)))
            (001000 ((self-env
                    (111 (111 (1001 fn) fn)
                          captured)))
              (my-eval-body-result
                (my-fourth fn)
                (bind-params
                  (10011 fn)
                  args
                  self-env)))))
         ((010 ())
          (my-result-fail (my-arity-error (10011 fn) args)))))
      ((my-group-closure? fn)
       (110
         ((my-arity-ok? (10011 fn) args)
          (001000 ((captured
                  (my-refresh-shared-frame
                    (my-sixth fn)
                    caller-env)))
            (001000 ((group-env
                    (my-build-group-env (my-fifth fn) captured)))
              (my-eval-body-result
                (my-fourth fn)
                (bind-params
                  (10011 fn)
                  args
                  group-env)))))
         ((010 ())
          (my-result-fail (my-arity-error (10011 fn) args)))))
      ((my-macro? fn)
       (110
         ((my-arity-ok? (1001 fn) args)
          (my-eval-body-result
            (10011 fn)
            (bind-params
              (1001 fn)
              args
              (my-refresh-shared-frame
                (my-fourth fn)
                caller-env))))
         ((010 ())
          (my-result-fail (my-arity-error (1001 fn) args)))))
      ((010 ())
       (my-result-fail (my-error (001 not-callable) fn))))))

(0011 my-apply
  (0010 (fn args . caller-env-rest)
    (001000 ((caller-env
            (110
              
              ((010 caller-env-rest)  (001 ()))
              ((010 ()) (100 caller-env-rest)))))
      (my-result-value (my-apply-result fn args caller-env)))))

; Evaluate one ordinary application with explicit operator-first and
; left-to-right argument sequencing. Recursive evaluation stays inside the
; outcome channel until this application has produced a value or its first
; failure.
(0011 my-eval-application-result
  (0010 (expr env-ref)
    (001000 ((fn-result (my-eval-result (100 expr) env-ref)))
      (110
        ((my-result-fail? fn-result) fn-result)
        ((010 ())
         (001000 ((fn (my-result-value fn-result)))
           (110
             ((my-macro? fn)
              (110
                ((my-arity-ok? (1001 fn) (011 expr))
                 (001000 ((expansion-result
                         (my-apply-result fn (011 expr) env-ref)))
                   (110
                     ((my-result-fail? expansion-result) expansion-result)
                     ((010 ())
                      (my-eval-result
                        (my-result-value expansion-result)
                        env-ref)))))
                ((010 ())
                 (my-result-fail
                   (my-arity-error (1001 fn) (011 expr))))))
             ((010 ())
              (001000 ((args-result
                      (my-eval-list-result (011 expr) env-ref)))
                (110
                  ((my-result-fail? args-result) args-result)
                  ((010 ())
                   (my-apply-result
                     fn
                     (my-result-value args-result)
                     env-ref))))))))))))

(0011 my-eval-result
  (0010 (expr env-ref)
    (110
      ((0100 (010 expr)) (110
         ((my-unresolved-name? expr env-ref)
          (my-result-fail
            (my-error (001 unbound-symbol) expr)))
         ((010 ())
          (my-result-ok (env-lookup expr env-ref)))))
      ((010 expr)  (110
         ((my-unresolved-name? expr env-ref)
          (my-result-fail
            (my-error (001 unbound-symbol) expr)))
         ((010 ())
          (my-result-ok (env-lookup expr env-ref)))))
      ((0100 (010 (100 expr))) (110
         ((my-canon-quote-name? (100 expr))
          (my-result-ok (1001 expr)))
         ((my-canon-cond-name? (100 expr))
          (my-eval-cond-result (011 expr) env-ref))
         ((my-lambda-name? (100 expr))
          (001000 ((problem (my-lambda-list-error (1001 expr))))
            (110
              ((0100 (010 problem)) (my-result-ok
                 (my-make-closure
                   (1001 expr)
                   (011 (011 expr))
                   env-ref)))
              ((010 problem)  (my-result-ok
                 (my-make-closure
                   (1001 expr)
                   (011 (011 expr))
                   env-ref)))
              ((010 ())
               (my-result-fail
                 (my-lambda-invalid-form problem))))))
         ((010 ())
          (my-eval-application-result expr env-ref))))
      ((010 (100 expr))  (110
         ((my-canon-quote-name? (100 expr))
          (my-result-ok (1001 expr)))
         ((my-canon-cond-name? (100 expr))
          (my-eval-cond-result (011 expr) env-ref))
         ((my-lambda-name? (100 expr))
          (001000 ((problem (my-lambda-list-error (1001 expr))))
            (110
              ((0100 (010 problem)) (my-result-ok
                 (my-make-closure
                   (1001 expr)
                   (011 (011 expr))
                   env-ref)))
              ((010 problem)  (my-result-ok
                 (my-make-closure
                   (1001 expr)
                   (011 (011 expr))
                   env-ref)))
              ((010 ())
               (my-result-fail
                 (my-lambda-invalid-form problem))))))
         ((010 ())
          (my-eval-application-result expr env-ref))))
      ((010 ())
       (my-eval-application-result expr env-ref)))))

(0011 my-eval
  (0010 (expr env-ref)
    (my-result-value (my-eval-result expr env-ref))))

; Top-level sequencing. `def` and `defmacro` return `(new-env . value)` so
; the environment can be threaded explicitly to the next form. Under
; my-eval-program, my-env-define updates the ADR-009 shared definition frame;
; direct calls without a marker retain the historical plain-alist behavior.
;
; Contract 6 rejects Canon definition names before value construction.
(0011 my-eval-top-form
  (0010 (form env-ref)
    (110
      ((0100 (010 form)) (111 env-ref (my-eval form env-ref)))
      ((010 form)  (111 env-ref (my-eval form env-ref)))
      ((my-definition-name? (100 form))
       (110
         ((my-canon-name? (1001 form))
          (111 env-ref (my-canon-binding-error (1001 form))))
         ((010 ())
          (001000 ((value-form (10011 form)))
            (110
              ((my-lambda-form? value-form)
               (001000 ((problem (my-lambda-list-error (1001 value-form))))
                 (110
                   ((0100 (010 problem)) (001000 ((value
                            (1110 (001 recursive-closure)
                                  (1001 form)
                                  (1001 value-form)
                                  (011 (011 value-form))
                                  env-ref)))
                      (111
                        (my-env-define (1001 form) value env-ref)
                        value)))
                   ((010 problem)  (001000 ((value
                            (1110 (001 recursive-closure)
                                  (1001 form)
                                  (1001 value-form)
                                  (011 (011 value-form))
                                  env-ref)))
                      (111
                        (my-env-define (1001 form) value env-ref)
                        value)))
                   ((010 ()) (111 env-ref (my-lambda-invalid-form problem))))))
              ((010 ())
               (001000 ((value (my-eval value-form env-ref)))
                 (111
                   (my-env-define (1001 form) value env-ref)
                   value))))))))
      ((my-defmacro-name? (100 form))
       (110
         ((my-canon-name? (1001 form))
          (111 env-ref (my-canon-binding-error (1001 form))))
         ((010 ())
          (001000 ((macro-val
                  (1110 (001 macro)
                        (10011 form)
                        (011 (011 (011 form)))
                        env-ref)))
            (111
              (my-env-define (1001 form) macro-val env-ref)
              macro-val)))))
      ((010 ()) (111 env-ref (my-eval form env-ref))))))

; Dependency analysis for top-level lambda definitions stays in Lisp data.
; A graph entry is `(name dependencies)`, where dependencies are only free
; references to names from the same contiguous lambda-definition block.
(0011 my-params-bind-name?
  (0010 (name params)
    (110
      ((0100 (010 params)) (110
         ((101 params (001 ())) (001 ()))
         ((101 params name) t)
         ))
      ((010 params)  (110
         ((101 params (001 ())) (001 ()))
         ((101 params name) t)
         ))
      ((101 (100 params) name) t)
      ((010 ()) (my-params-bind-name? name (011 params))))))

(0011 my-forms-reference-name?
  (0010 (forms name)
    (110
      
      ((010 forms)  (001 ()))
      ((my-form-references-name? (100 forms) name) t)
      ((010 ()) (my-forms-reference-name? (011 forms) name)))))

(0011 my-form-references-name?
  (0010 (form name)
    (110
      ((0100 (010 form)) (110
         ((110101100 form) (101 form name))
         ))
      ((010 form)  (110
         ((110101100 form) (101 form name))
         ))
      ((0100 (010 (100 form))) (110
         ; Quoted data is not a lexical dependency.
         ((my-canon-quote-name? (100 form)) (001 ()))
         ; A nested lambda can shadow a candidate top-level name.
         ((my-lambda-name? (100 form))
          (110
            ((my-params-bind-name? name (1001 form)) (001 ()))
            ((010 ()) (my-forms-reference-name? (011 (011 form)) name))))
         ((010 ()) (my-forms-reference-name? form name))))
      ((010 (100 form))  (110
         ; Quoted data is not a lexical dependency.
         ((my-canon-quote-name? (100 form)) (001 ()))
         ; A nested lambda can shadow a candidate top-level name.
         ((my-lambda-name? (100 form))
          (110
            ((my-params-bind-name? name (1001 form)) (001 ()))
            ((010 ()) (my-forms-reference-name? (011 (011 form)) name))))
         ((010 ()) (my-forms-reference-name? form name))))
      ((010 ()) (my-forms-reference-name? form name)))))

(0011 my-lambda-def-references-name?
  (0010 (form name)
    (001000 ((lambda-form (10011 form)))
      (110
        ((my-params-bind-name? name (1001 lambda-form)) (001 ()))
        ((010 ()) (my-forms-reference-name? (011 (011 lambda-form)) name))))))

(0011 my-lambda-def-names
  (0010 (forms)
    (110
      
      ((010 forms)  (001 ()))
      ((010 ()) (111 (1001 (100 forms))
               (my-lambda-def-names (011 forms)))))))

(0011 my-def-dependencies
  (0010 (form candidates)
    (110
      
      ((010 candidates)  (001 ()))
      ((my-lambda-def-references-name? form (100 candidates))
       (111 (100 candidates)
             (my-def-dependencies form (011 candidates))))
      ((010 ()) (my-def-dependencies form (011 candidates))))))

(0011 my-build-dependency-graph-with-names
  (0010 (forms names)
    (110
      
      ((010 forms)  (001 ()))
      ((010 ())
       (111
         (1110
           (1001 (100 forms))
           (my-def-dependencies (100 forms) names))
         (my-build-dependency-graph-with-names (011 forms) names))))))

(0011 my-build-dependency-graph
  (0010 (forms)
    (001000 ((names (my-lambda-def-names forms)))
      (my-build-dependency-graph-with-names forms names))))

(0011 my-graph-dependencies
  (0010 (name graph)
    (110
      
      ((010 graph)  (001 ()))
      ((101 name (100 (100 graph))) (1001 (100 graph)))
      ((010 ()) (my-graph-dependencies name (011 graph))))))

(0011 my-graph-dependencies-reach?
  (0010 (dependencies target graph visited)
    (110
      
      ((010 dependencies)  (001 ()))
      ((101 (100 dependencies) target) t)
      ((my-symbol-member? (100 dependencies) visited)
       (my-graph-dependencies-reach?
         (011 dependencies) target graph visited))
      ((my-graph-reaches?
         (100 dependencies)
         target
         graph
         (111 (100 dependencies) visited))
       t)
      ((010 ())
       (my-graph-dependencies-reach?
         (011 dependencies) target graph visited)))))

(0011 my-graph-reaches?
  (0010 (from target graph visited)
    (my-graph-dependencies-reach?
      (my-graph-dependencies from graph)
      target
      graph
      (111 from visited))))

; The SCC containing `name` is the set of block names mutually reachable
; with it. `name` itself is always retained so an acyclic node is a singleton
; component; only components with 2+ members use recursive-group-closure.
(0011 my-scc-names
  (0010 (name candidates graph)
    (110
      
      ((010 candidates)  (001 ()))
      ((101 name (100 candidates))
       (111 (100 candidates)
             (my-scc-names name (011 candidates) graph)))
      ((my-graph-reaches? name (100 candidates) graph (001 ()))
       (110
         ((my-graph-reaches? (100 candidates) name graph (001 ()))
          (111 (100 candidates)
                (my-scc-names name (011 candidates) graph)))
         ((010 ()) (my-scc-names name (011 candidates) graph))))
      ((010 ()) (my-scc-names name (011 candidates) graph)))))

(0011 my-select-defs-by-names
  (0010 (forms names)
    (110
      
      ((010 forms)  (001 ()))
      ((my-symbol-member? (1001 (100 forms)) names)
       (111 (100 forms)
             (my-select-defs-by-names (011 forms) names)))
      ((010 ()) (my-select-defs-by-names (011 forms) names)))))

(0011 my-remove-defs-by-names
  (0010 (forms names)
    (110
      
      ((010 forms)  (001 ()))
      ((my-symbol-member? (1001 (100 forms)) names)
       (my-remove-defs-by-names (011 forms) names))
      ((010 ())
       (111 (100 forms)
             (my-remove-defs-by-names (011 forms) names))))))

(0011 my-last-lambda-def-name
  (0010 (forms)
    (110
      ((0100 (010 (011 forms))) (1001 (100 forms)))
      ((010 (011 forms))  (1001 (100 forms)))
      ((010 ()) (my-last-lambda-def-name (011 forms))))))

(0011 my-eval-lambda-components
  (0010 (forms graph env-ref final-name)
    (110
      ((0100 (010 forms)) (111 env-ref (env-lookup final-name env-ref)))
      ((010 forms)  (111 env-ref (env-lookup final-name env-ref)))
      ((010 ())
       (001000 ((name (1001 (100 forms))))
         (001000 ((component-names
                 (my-scc-names
                   name
                   (my-lambda-def-names forms)
                   graph)))
           (110
             ; A singleton stays on the ordinary top-level path. That path
             ; already gives self-recursive definitions a finite
             ; recursive-closure without falsely inventing a group.
             ((0100 (010 (011 component-names))) (001000 ((result (my-eval-top-form (100 forms) env-ref)))
                (my-eval-lambda-components
                  (011 forms)
                  graph
                  (100 result)
                  final-name)))
             ((010 (011 component-names))  (001000 ((result (my-eval-top-form (100 forms) env-ref)))
                (my-eval-lambda-components
                  (011 forms)
                  graph
                  (100 result)
                  final-name)))
             ((010 ())
              (001000 ((component
                      (my-select-defs-by-names forms component-names)))
                (001000 ((group-env (my-install-group-env component env-ref)))
                  (my-eval-lambda-components
                    (my-remove-defs-by-names forms component-names)
                    graph
                    group-env
                    final-name)))))))))))

(0011 my-eval-lambda-block
  (0010 (forms env-ref)
    (001000 ((graph (my-build-dependency-graph forms))
          (final-name (my-last-lambda-def-name forms)))
      (my-eval-lambda-components forms graph env-ref final-name))))

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
(0011 my-eval-program
  (0010 (forms env-ref)
    (110
      ((0100 (010 forms)) (111 env-ref (001 ())))
      ((010 forms)  (111 env-ref (001 ())))
      ((010 ())
       (001000 ((program-env (my-ensure-shared-frame env-ref)))
         (110
           ((my-lambda-def-form? (100 forms))
            (001000 ((block (my-take-lambda-def-group forms)))
              (001000 ((problem (my-lambda-def-group-error block)))
                (110
                  ((0100 (010 problem)) (001000 ((rest (my-drop-lambda-def-group forms)))
                     (001000 ((block-result
                             (my-eval-lambda-block block program-env)))
                       (110
                         
                         ((010 rest)  block-result)
                         ((010 ())
                          (my-eval-program
                            rest
                            (100 block-result)))))))
                  ((010 problem)  (001000 ((rest (my-drop-lambda-def-group forms)))
                     (001000 ((block-result
                             (my-eval-lambda-block block program-env)))
                       (110
                         
                         ((010 rest)  block-result)
                         ((010 ())
                          (my-eval-program
                            rest
                            (100 block-result)))))))
                  ((010 ())
                   (111
                     program-env
                     (my-lambda-invalid-form problem)))))))
           ((010 ())
            (001000 ((result (my-eval-top-form (100 forms) program-env)))
              (110
                
                ((010 (011 forms))  result)
                ((010 ())
                 (my-eval-program
                   (011 forms)
                   (100 result))))))))))))