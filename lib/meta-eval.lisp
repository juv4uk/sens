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

(визначити my-primitive
  (функція (name)
    (список (як-є primitive) name)))

(визначити my-error
  (функція (kind detail)
    (список (як-є error) kind detail)))

; Internal evaluator outcomes carry provenance that interpreted Lisp data cannot
; forge. The tag is a native closure identity, not a symbol or list shape that
; a program could reproduce with quote/cons. Public my-eval/my-apply unwrap the
; envelope, so the observable interface stays unchanged.
(визначити my-result-ok-token
  (функція (value) value))

(визначити my-result-fail-token
  (функція (value) value))

(визначити my-result-ok
  (функція (value)
    (сполучити my-result-ok-token value)))

(визначити my-result-fail
  (функція (error)
    (сполучити my-result-fail-token error)))

(визначити my-result-fail?
  (функція (result)
    (за-умовою
      
      ((атом? result)  ні)
      ((атом? ()) (тотожне? (перше result) my-result-fail-token)))))

(визначити my-result-value
  (функція (result)
    (решта result)))

; Surface spellings are not owned here. The generated projection loaded before
; this evaluator maps every admitted runtime spelling to the numeric semantic ID
; from lib/surface/semantic-registry.lisp. This file owns only the mapping from
; those opaque IDs to evaluator mechanisms.
; Canon and semantic IDs are atoms: D3:101 EQ compares their exact
; identity. D8:11110111 EQUAL has no admitted mechanism here.
(визначити my-semantic-id?
  (функція (name semantic-id)
    (за-умовою
      ; D3 EQ is defined only on atoms. A source list is never a name.
      ((хибне? (атом? name)) ні)
      ((тотожне? name semantic-id) так)
      (так (тотожне? (my-semantic-id-for-surface name) semantic-id)))))

; The D6 LET binding list is data for the pinned mixed reader.
; Evaluate D3:110 outside that binding position so its head retains 3 bits.
; This SENS function owns the existing seven semantic-ID branches.
(визначити my-canon-semantic-id
  (функція (name)
    (за-умовою
      ; Lists are data, not callable Canon names or D3-EQ operands.
      ((хибне? (атом? name)) (як-є ()))
      ((тотожне? name 001) 001)
      ((тотожне? name 010) 010)
      ((тотожне? name 101) 101)
      ((тотожне? name 111) 111)
      ((тотожне? name 100) 100)
      ((тотожне? name 011) 011)
      ((тотожне? name 110) 110)
      (так (my-semantic-id-for-surface name)))))

(визначити my-canon-identity
  (функція (name)
    (нехай ((semantic-id (my-canon-semantic-id name)))
      (за-умовою
        ((тотожне? semantic-id 001) (як-є quote))
        ((тотожне? semantic-id 010) (як-є atom))
        ((тотожне? semantic-id 101) (як-є eq))
        ((тотожне? semantic-id 111) (як-є cons))
        ((тотожне? semantic-id 100) (як-є car))
        ((тотожне? semantic-id 011) (як-є cdr))
        ((тотожне? semantic-id 110) (як-є cond))
        ))))

(визначити my-lambda-name?
  (функція (name)
    (my-semantic-id? name 0010)))

(визначити my-define-name?
  (функція (name)
    (my-semantic-id? name 0011)))

(визначити my-defmacro-name?
  (функція (name)
    (my-semantic-id? name 00011)))

(визначити my-def-compat-name?
  (функція (name)
    (my-semantic-id? name 0011)))

(визначити my-definition-name?
  (функція (name)
    (за-умовою
      ((my-define-name? name) так)
      ((my-def-compat-name? name) так)
      (так ні))))

; Canon identity is an atom or (). D4 NULL/NOT project that
; structural distinction to an exact one-bit D1 predicate for D3 COND.
(визначити my-canon-name?
  (функція (name)
    (хибне? (порожній? (my-canon-identity name)))))

; Canon callable names remain the five currently admitted primitives.
; The last branch explicitly rejects all other identities as D1:NO.
(визначити my-canon-callable-identity?
  (функція (identity-ref)
    (за-умовою
      ((тотожне? identity-ref (як-є atom)) так)
      ((тотожне? identity-ref (як-є eq)) так)
      ((тотожне? identity-ref (як-є cons)) так)
      ((тотожне? identity-ref (як-є car)) так)
      ((тотожне? identity-ref (як-є cdr)) так)
      (так ні))))

(визначити my-canon-quote-name?
  (функція (name)
    (тотожне? (my-canon-identity name) (як-є quote))))

(визначити my-canon-cond-name?
  (функція (name)
    (тотожне? (my-canon-identity name) (як-є cond))))

(визначити my-canon-binding-error
  (функція (name)
    (створити-структуровану-помилку
      (як-є invalid-form)
      (список (як-є canonical-name-immutable) name))))

; Root primitive meanings are represented as values. Canon is handled first.
; Ordinary non-Canon boundary spellings are resolved to exact SENS identities
; here; the primitive value carried by the evaluator never uses the human
; spelling as its identity.
(визначити my-default-binding
  (функція (name)
    (нехай ((identity-ref (my-canon-identity name)))
      (за-умовою
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
        ((атом? ()) name)))))

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
(визначити my-shared-frame-binding?
  (функція (binding)
    (за-умовою
      
      ((атом? binding)  ні)
      ((атом? ()) (тотожне? (перше binding) 0)))))

(визначити my-frame-bound?
  (функція (name frame)
    (за-умовою
      
      ((атом? frame)  ні)
      ((тотожне? (перше (перше frame)) name) так)
      ((атом? ()) (ім'я-зв'язане-в-кадрі? name (решта frame))))))

(визначити my-frame-lookup
  (функція (name frame)
    (за-умовою
      ((тотожне? (перше (перше frame)) name) (решта (перше frame)))
      ((атом? ()) (знайти-значення-імені-в-рамці name (решта frame))))))

(визначити my-env-has-shared-frame?
  (функція (env-ref)
    (за-умовою
      
      ((атом? env-ref)  ні)
      ((my-shared-frame-binding? (перше env-ref)) так)
      ((атом? ()) (my-env-has-shared-frame? (решта env-ref))))))

(визначити my-shared-frame-value
  (функція (env-ref)
    (за-умовою
      
      ((атом? env-ref)  (як-є ()))
      ((my-shared-frame-binding? (перше env-ref)) (решта (перше env-ref)))
      ((атом? ()) (my-shared-frame-value (решта env-ref))))))

(визначити my-ensure-shared-frame
  (функція (env-ref)
    (за-умовою
      ((my-env-has-shared-frame? env-ref) env-ref)
      ((атом? ()) (сполучити (сполучити 0 (як-є ())) env-ref)))))

(визначити my-replace-shared-frame
  (функція (env-ref frame)
    (за-умовою
      
      ((атом? env-ref)  env-ref)
      ((my-shared-frame-binding? (перше env-ref))
       (сполучити (сполучити 0 frame) (решта env-ref)))
      ((атом? ())
       (сполучити (перше env-ref)
             (my-replace-shared-frame (решта env-ref) frame))))))

(визначити my-refresh-shared-frame
  (функція (captured-env caller-env)
    (за-умовою
      ((my-env-has-shared-frame? captured-env)
       (за-умовою
         ((my-env-has-shared-frame? caller-env)
          (my-replace-shared-frame
            captured-env
            (my-shared-frame-value caller-env)))
         ((атом? ()) captured-env)))
      ((атом? ()) captured-env))))

; Definitions update the shared marker when one is active. Outside
; my-eval-program this falls back to the historical plain-alist extension, so
; direct my-eval-top-form use remains compatible.
(визначити my-env-define
  (функція (name value env-ref)
    (за-умовою
      
      ((атом? env-ref)  (сполучити (сполучити name value) env-ref))
      ((my-shared-frame-binding? (перше env-ref))
       (сполучити
         (сполучити 0
               (сполучити (сполучити name value)
                     (решта (перше env-ref))))
         (решта env-ref)))
      ((атом? ())
       (сполучити (перше env-ref)
             (додати-визначення-до-оточення name value (решта env-ref)))))))

; Contract 6.0: Canon outranks the lexical alist even if a hostile/pre-existing
; environment contains the same text. Non-Canon names retain ordinary lookup.
(визначити env-lookup
  (функція (name env-ref)
    (нехай ((identity-ref (my-canon-identity name)))
      (за-умовою
        ((my-canon-callable-identity? identity-ref) (my-primitive identity-ref))
        ((my-canon-name? name) (my-canon-binding-error name))
        
        ((атом? env-ref)  (my-default-binding name))
        ((my-shared-frame-binding? (перше env-ref))
         (за-умовою
           ((ім'я-зв'язане-в-кадрі? name (решта (перше env-ref)))
            (знайти-значення-імені-в-рамці name (решта (перше env-ref))))
           ((атом? ()) (знайти-значення-імені-в-лексичному-середовищі name (решта env-ref)))))
        ((тотожне? (перше (перше env-ref)) name) (решта (перше env-ref)))
        ((атом? ()) (знайти-значення-імені-в-лексичному-середовищі name (решта env-ref)))))))

(визначити env-bound?
  (функція (name env-ref)
    (за-умовою
      ((my-canon-name? name) так)
      
      ((атом? env-ref)  ні)
      ((my-shared-frame-binding? (перше env-ref))
       (за-умовою
         ((ім'я-зв'язане-в-кадрі? name (решта (перше env-ref))) так)
         ((атом? ()) (ім'я-визначене-в-оточенні? name (решта env-ref)))))
      ((тотожне? (перше (перше env-ref)) name) так)
      ((атом? ()) (ім'я-визначене-в-оточенні? name (решта env-ref))))))

(визначити my-primitive?
  (функція (value)
    (за-умовою
      
      ((атом? value)  ні)
      ((атом? ()) (тотожне? (перше value) (як-є primitive))))))

; UnknownSymbol belongs to name resolution, not application. A symbol produced
; as a value (for example by quote) is not an unresolved lookup and therefore
; must later fail as not-callable/Type if placed in operator position.
;
; `symbol?` itself is language-owned in core.lisp, derived without a Rust builtin,
; so this distinction adds no primitive to the closed Canon.
; This predicate crosses a D3:110 COND boundary: always yield the
; exact one-bit D1 result. () is data, never an implicit false predicate.
(визначити my-unresolved-name?
  (функція (name env-ref)
    (за-умовою
      ((символ? name)
       (за-умовою
         ((тотожне? name так) ні)
         ((my-canon-name? name) ні)
         ((ім'я-визначене-в-оточенні? name env-ref) ні)
         ((my-primitive? (my-default-binding name)) ні)
         (так так)))
      (так ні))))

(визначити my-macro?
  (функція (value)
    (за-умовою
      
      ((атом? value) ні)
      (так (тотожне? (перше value) (як-є macro))))))

(визначити my-closure?
  (функція (value)
    (за-умовою
      
      ((атом? value) ні)
      (так (тотожне? (перше value) (як-є closure))))))

; A recursive closure is finite Lisp data. It does not require a cyclic host
; Environment. At call time my-apply reconstructs the one self-binding that
; the function needs. Contract 6 guarantees that this name is never Canon.
;
; Shape:
;   (recursive-closure name params body captured-env)
(визначити my-recursive-closure?
  (функція (value)
    (за-умовою
      
      ((атом? value) ні)
      (так (тотожне? (перше value) (як-є recursive-closure))))))

; A mutually-recursive group is also finite Lisp data. Every member stores the
; same raw group and captured outer environment; my-apply reconstructs the
; group's bindings at call time rather than relying on a cyclic host object.
;
; Shape:
;   (recursive-group-closure name params body group captured-env)
(визначити my-group-closure?
  (функція (value)
    (за-умовою
      ((атом? value) ні)
      ((атом? ()) (тотожне? (перше value) (як-є recursive-group-closure))))))

(визначити my-lambda-form?
  (функція (form)
    (за-умовою
      ((атом? form)  ні)
      ((атом? (перше form))  (my-lambda-name? (перше form)))
      (так ні))))

(визначити my-lambda-def-form?
  (функція (form)
    (за-умовою
      ((атом? form)  ні)
      ((my-definition-name? (перше form))
       (за-умовою
         ((my-canon-name? (друге form)) ні)
         ((атом? ()) (перевірити-форму-лямбда? (третє form)))))
      (так ні))))

(визначити my-fourth
  (функція (values)
    (перше (решта (решта (решта values))))))

(визначити my-fifth
  (функція (values)
    (перше (решта (решта (решта (решта values)))))))

(визначити my-sixth
  (функція (values)
    (перше (решта (решта (решта (решта (решта values))))))))

(визначити my-compare-two
  (функція (operator left right)
    (за-умовою
      ((тотожне? operator 11010) (менше? left right))
      ((тотожне? operator 11110111) (однакові? left right))
      ((тотожне? operator 11011) (більше? left right))
      )))

; Chained comparison semantics are Lisp-owned: values arrive already
; evaluated, adjacent pairs are compared left-to-right, and evaluation stops
; at the first false pair.
; NOTE: my-compare-two returns exact-Q 1/0, not t/(). Since 0 is truthy
; in my-lisp (only Nil and Bool(false) are falsy), we MUST use a 3-part
; clause matching the exact-Q YES result (1) — not a 2-part clause.
(визначити my-compare-chain
  (функція (operator values)
    (за-умовою
      
      ((атом? (решта values))  так)
      ((тотожне? (my-compare-two operator (перше values) (друге values)) 1)
       (усі-сусідні-значення-задовольняють-порівняння? operator (решта values)))
      )))

; Primitive *identity* is a Lisp value. This function is the narrow bridge
; from that identity to the admitted native operation mechanism.
(визначити my-apply-primitive
  (функція (name args)
    (за-умовою
      ((тотожне? name (як-є atom)) (атом? (перше args)))
      ((тотожне? name (як-є eq))   (тотожне? (перше args) (друге args)))
      ((тотожне? name (як-є car))  (перше (перше args)))
      ((тотожне? name (як-є cdr))  (решта (перше args)))
      ((тотожне? name (як-є cons)) (сполучити (перше args) (друге args)))
      ((тотожне? name 01010) (додати (перше args) (друге args)))
      ((тотожне? name 01011) (відняти (перше args) (друге args)))
      ((тотожне? name 10110) (помножити (перше args) (друге args)))
      ((тотожне? name 11010) (усі-сусідні-значення-задовольняють-порівняння? 11010 args))
      ((тотожне? name 11110111) (усі-сусідні-значення-задовольняють-порівняння? 11110111 args))
      ((тотожне? name 11011) (усі-сусідні-значення-задовольняють-порівняння? 11011 args))
      ((тотожне? name 11110100)
       (значення-у-текст (перше args)))
      ((тотожне? name 11101101)
       (текст-у-символ (перше args)))
      ((атом? ()) (список (як-є unknown-primitive) name)))))

; Lambda-list arity is derivable from Lisp list structure itself:
;   (x y)        -> exact 2
;   (x y . rest) -> at least 2
;   args         -> at least 0
; No host metadata is required.
; An arity is D24 mathematics, not an implicitly promoted reader Number.
; One derived structural counter supplies BOTH fixed and received counts.
(визначити my-fixed-param-count
  (функція (params)
    (за-умовою
      ((атом? params) 0)
      ((атом? ()) (додати 1
                       (порахувати-обов'язкові-параметри-лямбди (решта params)))))))

(визначити my-rest-param?
  (функція (params)
    (за-умовою
      
      ((атом? params)  (за-умовою
         ((тотожне? params (як-є ())) ні)
         (так так)))
      (так (лямбда-має-параметр-залишку? (решта params))))))

(визначити my-arity-ok?
  (функція (params args)
    (нехай ((fixed (порахувати-обов'язкові-параметри-лямбди params))
             (received (порахувати-обов'язкові-параметри-лямбди args)))
      (за-умовою
        ((лямбда-має-параметр-залишку? params)
         (за-умовою
           ((менше? received fixed) ні)
           ((хибне? (менше? received fixed)) так)
           (так ні)))
        (так
         (за-умовою
           ((тотожне? received fixed) так)
           (так ні)))))))

(визначити my-arity-detail
  (функція (params args)
    (нехай ((fixed (порахувати-обов'язкові-параметри-лямбди params))
          (received (порахувати-обов'язкові-параметри-лямбди args)))
      (список
        (як-є expected)
        (за-умовою
          ((лямбда-має-параметр-залишку? params) (список (як-є at-least) fixed))
          ((атом? ()) (список (як-є exact) fixed)))
        (як-є received)
        received))))

(визначити my-arity-error
  (функція (params args)
    (створити-структуровану-помилку (як-є arity) (опис-очікуваної-та-одержаної-арності params args))))

; Lambda-list validation is syntax semantics, not application semantics.
; Contract 6 adds reserved-Canon rejection to the existing structural checks.
(визначити my-symbol-member?
  (функція (name names)
    (за-умовою
      ((атом? names)  ні)
      ((тотожне? name (перше names)) так)
      ((атом? ()) (my-symbol-member? name (решта names))))))

(визначити my-lambda-list-error-pairs
  (функція (params seen)
    (за-умовою
      
      ((атом? params)  (за-умовою
         ((тотожне? params (як-є ())) (як-є ()))
         ((символ? params)
          (за-умовою
            ((my-canon-name? params)
             (список (як-є canonical-parameter) params))
            ((my-symbol-member? params seen)
             (список (як-є duplicate-parameter) params))
            ))
         ((атом? ()) (список (як-є invalid-rest) params))))
      ((символ? (перше params))
       (за-умовою
         ((my-canon-name? (перше params))
          (список (як-є canonical-parameter) (перше params)))
         ((my-symbol-member? (перше params) seen)
          (список (як-є duplicate-parameter) (перше params)))
         ((атом? ())
          (my-lambda-list-error-pairs
            (решта params)
            (сполучити (перше params) seen)))))
      ((атом? ()) (список (як-є non-symbol-parameter) (перше params))))))

(визначити перевірити-параметри-лямбди
  (функція (params)
    (за-умовою
      
      ((атом? params)  (за-умовою
         ((тотожне? params (як-є ())) (як-є ()))
         ((символ? params)
          (за-умовою
            ((my-canon-name? params)
             (список (як-є canonical-parameter) params))
            ))
         ((атом? ()) (список (як-є invalid-parameters) params))))
      ((атом? ()) (my-lambda-list-error-pairs params (як-є ()))))))

(визначити my-lambda-invalid-form
  (функція (problem)
    (створити-структуровану-помилку
      (як-є invalid-form)
      (сполучити (як-є lambda-parameters) problem))))

(визначити my-make-closure
  (функція (params body env-ref)
    (нехай ((problem (перевірити-параметри-лямбди params)))
      (за-умовою
        
        ((атом? problem)  (список (як-є closure) params body env-ref))
        ((атом? ()) (my-lambda-invalid-form problem))))))

; Return the first malformed lambda-list in a top-level recursive group.
; Canon-named definitions never enter a recursive group; my-lambda-def-form?
; routes them to the ordinary top-form rejection path first.
(визначити my-lambda-def-group-error
  (функція (forms)
    (за-умовою
      
      ((атом? forms)  (як-є ()))
      ((атом? ())
       (нехай ((problem
               (перевірити-параметри-лямбди (друге (третє (перше forms))))))
         (за-умовою
           
           ((атом? problem)  (my-lambda-def-group-error (решта forms)))
           ((атом? ()) problem)))))))

; Parameter binding owns only the successful path. Arity and Canon-name
; validity are checked before this function is entered.
(визначити bind-params
  (функція (params args env-ref)
    (за-умовою
      
      ((атом? params)  (за-умовою
         ((тотожне? params (як-є ())) env-ref)
         ((атом? ()) (сполучити (сполучити params args) env-ref))))
      ((атом? ()) (сполучити (сполучити (перше params) (перше args))
               (зв'язати-аргументи-з-лямбда-параметрами (решта params) (решта args) env-ref))))))

(визначити my-eval-list-result
  (функція (exprs env-ref)
    (за-умовою
      
      ((атом? exprs)  (власний-результат-успіх (як-є ())))
      ((атом? ())
       (нехай ((head-result (обчислити-вираз-з-наслідком (перше exprs) env-ref)))
         (за-умовою
           ((це-результат-невдалого-обчислення? head-result) head-result)
           ((атом? ())
            (нехай ((tail-result (обчислити-аргументи-з-явним-успіхом-або-помилкою (решта exprs) env-ref)))
              (за-умовою
                ((це-результат-невдалого-обчислення? tail-result) tail-result)
                ((атом? ())
                 (власний-результат-успіх
                   (сполучити
                     (my-result-value head-result)
                     (my-result-value tail-result)))))))))))))

(визначити my-eval-list
  (функція (exprs env-ref)
    (my-result-value (обчислити-аргументи-з-явним-успіхом-або-помилкою exprs env-ref))))

(визначити my-eval-body-result
  (функція (body env-ref)
    (за-умовою
      ((хибне? (атом? (решта body))) (обчислити-вираз-з-наслідком (перше body) env-ref))
      ((атом? (решта body))  (обчислити-вираз-з-наслідком (перше body) env-ref))
      ((атом? ())
       (нехай ((first-result (обчислити-вираз-з-наслідком (перше body) env-ref)))
         (за-умовою
           ((це-результат-невдалого-обчислення? first-result) first-result)
           ((атом? ()) (обчислити-послідовне-тіло-з-раннім-збоєм (решта body) env-ref))))))))

(визначити my-eval-body
  (функція (body env-ref)
    (my-result-value (обчислити-послідовне-тіло-з-раннім-збоєм body env-ref))))

(визначити my-cond-has-migration-clause?
  (функція (clauses)
    (за-умовою
      
      ((атом? clauses) ні)
      ((хибне? (атом? (перше clauses))) (my-cond-has-migration-clause? (решта clauses)))
      ((атом? (перше clauses))  (my-cond-has-migration-clause? (решта clauses)))
      ((тотожне? (довжина (перше clauses)) 2)  так)
      (так (my-cond-has-migration-clause? (решта clauses))))))

(визначити my-eval-cond-result-mode
  (функція (clauses env-ref migration-compatibility?)
    (за-умовою
      
      ((атом? clauses)  (за-умовою
         (migration-compatibility? (власний-результат-успіх (як-є ())))
         ((атом? ())
          (власний-результат-невдача
            (створити-структуровану-помилку (як-є unsatisfied-conditional) (як-є cond))))))
      ((атом? ())
       (нехай ((clause (перше clauses)))
         (за-умовою
           ; #217 canonical path: evaluate only the query. The expected result
           ; is already Lisp data in the interpreted program and must never be
           ; executed as code. Match it structurally, then evaluate the branch.
           ((тотожне? (довжина clause) 3) 
            (нехай ((test-result (обчислити-вираз-з-наслідком (перше clause) env-ref)))
              (за-умовою
                ((це-результат-невдалого-обчислення? test-result) test-result)
                ((однакові? (my-result-value test-result) (друге clause))
                 
                 (обчислити-вираз-з-наслідком (третє clause) env-ref))
                ((хибне? (однакові? (my-result-value test-result) (друге clause)))
                 (my-eval-cond-result-mode
                   (решта clauses) env-ref migration-compatibility?)))))
           ; Historical two-part clauses remain migration-only, mirroring the
           ; native evaluator until their callers are moved to explicit result
           ; matching. This path intentionally retains old truthiness.
           ((тотожне? (довжина clause) 2) 
            (нехай ((test-result (обчислити-вираз-з-наслідком (перше clause) env-ref)))
              (за-умовою
                ((це-результат-невдалого-обчислення? test-result) test-result)
                ((my-result-value test-result)
                 (обчислити-вираз-з-наслідком (друге clause) env-ref))
                ((атом? ())
                 (my-eval-cond-result-mode
                   (решта clauses) env-ref migration-compatibility?)))))
           ((атом? ())
            (власний-результат-невдача
              (створити-структуровану-помилку
                (як-є invalid-form)
                (список (як-є cond-clause) clause))))))))))

(визначити my-eval-cond-result
  (функція (clauses env-ref)
    (my-eval-cond-result-mode
      clauses env-ref (my-cond-has-migration-clause? clauses))))

(визначити my-eval-cond
  (функція (clauses env-ref)
    (my-result-value (my-eval-cond-result clauses env-ref))))

(визначити my-take-lambda-def-group
  (функція (forms)
    (за-умовою
      
      ((атом? forms)  (як-є ()))
      ((визначення-лямбди-на-верхньому-рівні? (перше forms))
       (сполучити (перше forms)
             (my-take-lambda-def-group (решта forms))))
      )))

(визначити my-drop-lambda-def-group
  (функція (forms)
    (за-умовою
      
      ((атом? forms)  (як-є ()))
      ((визначення-лямбди-на-верхньому-рівні? (перше forms))
       (my-drop-lambda-def-group (решта forms)))
      ((атом? ()) forms))))

(визначити my-group-closure-from-def
  (функція (form group captured-env)
    (нехай ((lambda-form (третє form)))
      (список (як-є recursive-group-closure)
            (друге form)
            (друге lambda-form)
            (решта (решта lambda-form))
            group
            captured-env))))

; Application-time reconstruction keeps SCC members as lexical bindings around
; the refreshed shared frame. This retains finite group recursion.
(визначити my-build-group-env-onto
  (функція (forms group captured-env out)
    (за-умовою
      
      ((атом? forms)  out)
      ((атом? ())
       (нехай ((form (перше forms)))
         (my-build-group-env-onto
           (решта forms)
           group
           captured-env
           (сполучити
             (сполучити (друге form)
                   (створити-замикання-взаєморекурсивної-групи form group captured-env))
             out)))))))

(визначити побудувати-лексичні-зв'язки-рекурсивної-групи
  (функція (group captured-env)
    (my-build-group-env-onto group group captured-env captured-env)))

; Program-time installation is different: SCC members are top-level definitions
; and therefore belong to the shared definition frame rather than to a lexical
; prefix that could become a stale snapshot for later closures.
(визначити my-install-group-env-onto
  (функція (forms group captured-env out)
    (за-умовою
      
      ((атом? forms)  out)
      ((атом? ())
       (нехай ((form (перше forms)))
         (my-install-group-env-onto
           (решта forms)
           group
           captured-env
           (додати-визначення-до-оточення
             (друге form)
             (створити-замикання-взаєморекурсивної-групи form group captured-env)
             out)))))))

(визначити встановити-взаєморекурсивні-замикання
  (функція (group captured-env)
    (my-install-group-env-onto group group captured-env captured-env)))

; caller-env is optional only for compatibility with the old experimental
; meta-eval-mutual wrapper. Main my-eval always passes it. When present it is
; used solely to refresh the shared top-level marker in a captured environment.
; Internal application returns an outcome envelope. This keeps evaluator
; failures distinct from ordinary Lisp data whose printed shape happens to be
; `(error ...)`.
(визначити my-apply-result
  (функція (fn args caller-env)
    (за-умовою
      
      ((атом? fn)  (власний-результат-невдача (створити-структуровану-помилку (як-є not-callable) fn)))
      ((my-primitive? fn)
       (власний-результат-успіх (my-apply-primitive (друге fn) args)))
      ((це-замикання? fn)
       (за-умовою
         ((арність-відповідає-аргументам? (друге fn) args)
          (обчислити-послідовне-тіло-з-раннім-збоєм
            (третє fn)
            (зв'язати-аргументи-з-лямбда-параметрами
              (друге fn)
              args
              (оновити-спільний-кадр-замикання
                (my-fourth fn)
                caller-env))))
         ((атом? ())
          (власний-результат-невдача (my-arity-error (друге fn) args)))))
      ((це-рекурсивне-замикання? fn)
       (за-умовою
         ((арність-відповідає-аргументам? (третє fn) args)
          (нехай ((captured
                  (оновити-спільний-кадр-замикання
                    (my-fifth fn)
                    caller-env)))
            (нехай ((self-env
                    (сполучити (сполучити (друге fn) fn)
                          captured)))
              (обчислити-послідовне-тіло-з-раннім-збоєм
                (my-fourth fn)
                (зв'язати-аргументи-з-лямбда-параметрами
                  (третє fn)
                  args
                  self-env)))))
         ((атом? ())
          (власний-результат-невдача (my-arity-error (третє fn) args)))))
      ((це-замикання-рекурсивної-групи? fn)
       (за-умовою
         ((арність-відповідає-аргументам? (третє fn) args)
          (нехай ((captured
                  (оновити-спільний-кадр-замикання
                    (my-sixth fn)
                    caller-env)))
            (нехай ((group-env
                    (побудувати-лексичні-зв'язки-рекурсивної-групи (my-fifth fn) captured)))
              (обчислити-послідовне-тіло-з-раннім-збоєм
                (my-fourth fn)
                (зв'язати-аргументи-з-лямбда-параметрами
                  (третє fn)
                  args
                  group-env)))))
         ((атом? ())
          (власний-результат-невдача (my-arity-error (третє fn) args)))))
      ((my-macro? fn)
       (за-умовою
         ((арність-відповідає-аргументам? (друге fn) args)
          (обчислити-послідовне-тіло-з-раннім-збоєм
            (третє fn)
            (зв'язати-аргументи-з-лямбда-параметрами
              (друге fn)
              args
              (оновити-спільний-кадр-замикання
                (my-fourth fn)
                caller-env))))
         ((атом? ())
          (власний-результат-невдача (my-arity-error (друге fn) args)))))
      ((атом? ())
       (власний-результат-невдача (створити-структуровану-помилку (як-є not-callable) fn))))))

(визначити my-apply
  (функція (fn args . caller-env-rest)
    (нехай ((caller-env
            (за-умовою
              
              ((атом? caller-env-rest)  (як-є ()))
              ((атом? ()) (перше caller-env-rest)))))
      (my-result-value (застосувати-функцію-з-наслідком fn args caller-env)))))

; Evaluate one ordinary application with explicit operator-first and
; left-to-right argument sequencing. Recursive evaluation stays inside the
; outcome channel until this application has produced a value or its first
; failure.
(визначити my-eval-application-result
  (функція (expr env-ref)
    (нехай ((fn-result (обчислити-вираз-з-наслідком (перше expr) env-ref)))
      (за-умовою
        ((це-результат-невдалого-обчислення? fn-result) fn-result)
        ((атом? ())
         (нехай ((fn (my-result-value fn-result)))
           (за-умовою
             ((my-macro? fn)
              (за-умовою
                ((арність-відповідає-аргументам? (друге fn) (решта expr))
                 (нехай ((expansion-result
                         (застосувати-функцію-з-наслідком fn (решта expr) env-ref)))
                   (за-умовою
                     ((це-результат-невдалого-обчислення? expansion-result) expansion-result)
                     ((атом? ())
                      (обчислити-вираз-з-наслідком
                        (my-result-value expansion-result)
                        env-ref)))))
                ((атом? ())
                 (власний-результат-невдача
                   (my-arity-error (друге fn) (решта expr))))))
             ((атом? ())
              (нехай ((args-result
                      (обчислити-аргументи-з-явним-успіхом-або-помилкою (решта expr) env-ref)))
                (за-умовою
                  ((це-результат-невдалого-обчислення? args-result) args-result)
                  ((атом? ())
                   (застосувати-функцію-з-наслідком
                     fn
                     (my-result-value args-result)
                     env-ref))))))))))))

(визначити my-eval-result
  (функція (expr env-ref)
    (за-умовою
      ((атом? expr)  (за-умовою
         ((визначити-невирішене-ім'я-в-оточенні? expr env-ref)
          (власний-результат-невдача
            (створити-структуровану-помилку (як-є unbound-symbol) expr)))
         ((атом? ())
          (власний-результат-успіх (знайти-значення-імені-в-лексичному-середовищі expr env-ref)))))
      ((хибне? (атом? (перше expr))) (за-умовою
         ((my-canon-quote-name? (перше expr))
          (власний-результат-успіх (друге expr)))
         ((my-canon-cond-name? (перше expr))
          (my-eval-cond-result (решта expr) env-ref))
         ((my-lambda-name? (перше expr))
          (нехай ((problem (перевірити-параметри-лямбди (друге expr))))
            (за-умовою
              
              ((атом? problem)  (власний-результат-успіх
                 (створити-лексичне-замикання-або-повернути-структуровану-помилку
                   (друге expr)
                   (решта (решта expr))
                   env-ref)))
              ((атом? ())
               (власний-результат-невдача
                 (my-lambda-invalid-form problem))))))
         ((атом? ())
          (my-eval-application-result expr env-ref))))
      ((атом? (перше expr))  (за-умовою
         ((my-canon-quote-name? (перше expr))
          (власний-результат-успіх (друге expr)))
         ((my-canon-cond-name? (перше expr))
          (my-eval-cond-result (решта expr) env-ref))
         ((my-lambda-name? (перше expr))
          (нехай ((problem (перевірити-параметри-лямбди (друге expr))))
            (за-умовою
              
              ((атом? problem)  (власний-результат-успіх
                 (створити-лексичне-замикання-або-повернути-структуровану-помилку
                   (друге expr)
                   (решта (решта expr))
                   env-ref)))
              ((атом? ())
               (власний-результат-невдача
                 (my-lambda-invalid-form problem))))))
         ((атом? ())
          (my-eval-application-result expr env-ref))))
      ((атом? ())
       (my-eval-application-result expr env-ref)))))

(визначити my-eval
  (функція (expr env-ref)
    (my-result-value (обчислити-вираз-з-наслідком expr env-ref))))

; Top-level sequencing. `def` and `defmacro` return `(new-env . value)` so
; the environment can be threaded explicitly to the next form. Under
; my-eval-program, my-env-define updates the ADR-009 shared definition frame;
; direct calls without a marker retain the historical plain-alist behavior.
;
; Contract 6 rejects Canon definition names before value construction.
(визначити обчислити-форму-та-оновити-оточення
  (функція (form env-ref)
    (за-умовою
      ((атом? form)  (сполучити env-ref (my-eval form env-ref)))
      ((my-definition-name? (перше form))
       (за-умовою
         ((my-canon-name? (друге form))
          (сполучити env-ref (my-canon-binding-error (друге form))))
         ((атом? ())
          (нехай ((value-form (третє form)))
            (за-умовою
              ((перевірити-форму-лямбда? value-form)
               (нехай ((problem (перевірити-параметри-лямбди (друге value-form))))
                 (за-умовою
                   
                   ((атом? problem)  (нехай ((value
                            (список (як-є recursive-closure)
                                  (друге form)
                                  (друге value-form)
                                  (решта (решта value-form))
                                  env-ref)))
                      (сполучити
                        (додати-визначення-до-оточення (друге form) value env-ref)
                        value)))
                   ((атом? ()) (сполучити env-ref (my-lambda-invalid-form problem))))))
              ((атом? ())
               (нехай ((value (my-eval value-form env-ref)))
                 (сполучити
                   (додати-визначення-до-оточення (друге form) value env-ref)
                   value))))))))
      ((my-defmacro-name? (перше form))
       (за-умовою
         ((my-canon-name? (друге form))
          (сполучити env-ref (my-canon-binding-error (друге form))))
         ((атом? ())
          (нехай ((macro-val
                  (список (як-є macro)
                        (третє form)
                        (решта (решта (решта form)))
                        env-ref)))
            (сполучити
              (додати-визначення-до-оточення (друге form) macro-val env-ref)
              macro-val)))))
      ((атом? ()) (сполучити env-ref (my-eval form env-ref))))))

; Dependency analysis for top-level lambda definitions stays in Lisp data.
; A graph entry is `(name dependencies)`, where dependencies are only free
; references to names from the same contiguous lambda-definition block.
(визначити my-params-bind-name?
  (функція (name params)
    (за-умовою
      
      ((атом? params)  (за-умовою
         ((тотожне? params (як-є ())) ні)
         ((тотожне? params name) так)
         (так ні)))
      ((тотожне? (перше params) name) так)
      ((атом? ()) (ім'я-зв'язане-формальними-параметрами? name (решта params))))))

(визначити my-forms-reference-name?
  (функція (forms name)
    (за-умовою
      
      ((атом? forms) ні)
      ((вільне-посилання-у-формі-з-урахуванням-цитат-та-затінення? (перше forms) name) так)
      ((атом? ()) (my-forms-reference-name? (решта forms) name)))))

(визначити my-form-references-name?
  (функція (form name)
    (за-умовою
      
      ((атом? form)  (за-умовою
         ((символ? form) (тотожне? form name))
         (так ні)))
      ((хибне? (атом? (перше form))) (за-умовою
         ; Quoted data is not a lexical dependency.
         ((my-canon-quote-name? (перше form)) ні)
         ; A nested lambda can shadow a candidate top-level name.
         ((my-lambda-name? (перше form))
          (за-умовою
            ((ім'я-зв'язане-формальними-параметрами? name (друге form)) ні)
            ((атом? ()) (my-forms-reference-name? (решта (решта form)) name))))
         ((атом? ()) (my-forms-reference-name? form name))))
      ((атом? (перше form))  (за-умовою
         ; Quoted data is not a lexical dependency.
         ((my-canon-quote-name? (перше form)) ні)
         ; A nested lambda can shadow a candidate top-level name.
         ((my-lambda-name? (перше form))
          (за-умовою
            ((ім'я-зв'язане-формальними-параметрами? name (друге form)) ні)
            ((атом? ()) (my-forms-reference-name? (решта (решта form)) name))))
         ((атом? ()) (my-forms-reference-name? form name))))
      ((атом? ()) (my-forms-reference-name? form name)))))

(визначити my-lambda-def-references-name?
  (функція (form name)
    (нехай ((lambda-form (третє form)))
      (за-умовою
        ((ім'я-зв'язане-формальними-параметрами? name (друге lambda-form)) ні)
        ((атом? ()) (my-forms-reference-name? (решта (решта lambda-form)) name))))))

(визначити my-lambda-def-names
  (функція (forms)
    (за-умовою
      
      ((атом? forms)  (як-є ()))
      ((атом? ()) (сполучити (друге (перше forms))
               (my-lambda-def-names (решта forms)))))))

(визначити my-def-dependencies
  (функція (form candidates)
    (за-умовою
      
      ((атом? candidates)  (як-є ()))
      ((визначення-посилається-на-ім'я? form (перше candidates))
       (сполучити (перше candidates)
             (залежності-визначення-серед-кандидатів form (решта candidates))))
      ((атом? ()) (залежності-визначення-серед-кандидатів form (решта candidates))))))

(визначити my-build-dependency-graph-with-names
  (функція (forms names)
    (за-умовою
      
      ((атом? forms)  (як-є ()))
      ((атом? ())
       (сполучити
         (список
           (друге (перше forms))
           (залежності-визначення-серед-кандидатів (перше forms) names))
         (my-build-dependency-graph-with-names (решта forms) names))))))

(визначити побудувати-граф-залежностей-визначень
  (функція (forms)
    (нехай ((names (my-lambda-def-names forms)))
      (my-build-dependency-graph-with-names forms names))))

(визначити my-graph-dependencies
  (функція (name graph)
    (за-умовою
      
      ((атом? graph)  (як-є ()))
      ((тотожне? name (перше (перше graph))) (друге (перше graph)))
      ((атом? ()) (my-graph-dependencies name (решта graph))))))

(визначити my-graph-dependencies-reach?
  (функція (dependencies target graph visited)
    (за-умовою
      
      ((атом? dependencies) ні)
      ((тотожне? (перше dependencies) target) так)
      ((my-symbol-member? (перше dependencies) visited)
       (my-graph-dependencies-reach?
         (решта dependencies) target graph visited))
      ((вузол-графа-досяжний?
         (перше dependencies)
         target
         graph
         (сполучити (перше dependencies) visited))
       так)
      ((атом? ())
       (my-graph-dependencies-reach?
         (решта dependencies) target graph visited)))))

(визначити my-graph-reaches?
  (функція (from target graph visited)
    (my-graph-dependencies-reach?
      (my-graph-dependencies from graph)
      target
      graph
      (сполучити from visited))))

; The SCC containing `name` is the set of block names mutually reachable
; with it. `name` itself is always retained so an acyclic node is a singleton
; component; only components with 2+ members use recursive-group-closure.
(визначити my-scc-names
  (функція (name candidates graph)
    (за-умовою
      
      ((атом? candidates)  (як-є ()))
      ((тотожне? name (перше candidates))
       (сполучити (перше candidates)
             (імена-сильно-зв'язаної-компоненти name (решта candidates) graph)))
      ((вузол-графа-досяжний? name (перше candidates) graph (як-є ()))
       (за-умовою
         ((вузол-графа-досяжний? (перше candidates) name graph (як-є ()))
          (сполучити (перше candidates)
                (імена-сильно-зв'язаної-компоненти name (решта candidates) graph)))
         ((атом? ()) (імена-сильно-зв'язаної-компоненти name (решта candidates) graph))))
      ((атом? ()) (імена-сильно-зв'язаної-компоненти name (решта candidates) graph)))))

(визначити my-select-defs-by-names
  (функція (forms names)
    (за-умовою
      
      ((атом? forms)  (як-є ()))
      ((my-symbol-member? (друге (перше forms)) names)
       (сполучити (перше forms)
             (відібрати-визначення-іменованої-групи (решта forms) names)))
      ((атом? ()) (відібрати-визначення-іменованої-групи (решта forms) names)))))

(визначити my-remove-defs-by-names
  (функція (forms names)
    (за-умовою
      
      ((атом? forms)  (як-є ()))
      ((my-symbol-member? (друге (перше forms)) names)
       (вилучити-з-блоку-визначення-заданих-імен (решта forms) names))
      ((атом? ())
       (сполучити (перше forms)
             (вилучити-з-блоку-визначення-заданих-імен (решта forms) names))))))

(визначити my-last-lambda-def-name
  (функція (forms)
    (за-умовою
      ((хибне? (атом? (решта forms))) (друге (перше forms)))
      ((атом? (решта forms))  (друге (перше forms)))
      ((атом? ()) (my-last-lambda-def-name (решта forms))))))

(визначити my-eval-lambda-components
  (функція (forms graph env-ref final-name)
    (за-умовою
      
      ((атом? forms)  (сполучити env-ref (знайти-значення-імені-в-лексичному-середовищі final-name env-ref)))
      ((атом? ())
       (нехай ((name (друге (перше forms))))
         (нехай ((component-names
                 (імена-сильно-зв'язаної-компоненти
                   name
                   (my-lambda-def-names forms)
                   graph)))
           (за-умовою
             ; A singleton stays on the ordinary top-level path. That path
             ; already gives self-recursive definitions a finite
             ; recursive-closure without falsely inventing a group.
             ((хибне? (атом? (решта component-names))) (нехай ((result (обчислити-форму-та-оновити-оточення (перше forms) env-ref)))
                (my-eval-lambda-components
                  (решта forms)
                  graph
                  (перше result)
                  final-name)))
             ((атом? (решта component-names))  (нехай ((result (обчислити-форму-та-оновити-оточення (перше forms) env-ref)))
                (my-eval-lambda-components
                  (решта forms)
                  graph
                  (перше result)
                  final-name)))
             ((атом? ())
              (нехай ((component
                      (відібрати-визначення-іменованої-групи forms component-names)))
                (нехай ((group-env (встановити-взаєморекурсивні-замикання component env-ref)))
                  (my-eval-lambda-components
                    (вилучити-з-блоку-визначення-заданих-імен forms component-names)
                    graph
                    group-env
                    final-name)))))))))))

(визначити обчислити-блок-взаємних-визначень
  (функція (forms env-ref)
    (нехай ((graph (побудувати-граф-залежностей-визначень forms))
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
(визначити my-eval-program
  (функція (forms env-ref)
    (за-умовою
      ((атом? forms)  (сполучити env-ref (як-є ())))
      ((атом? ())
       (нехай ((program-env (my-ensure-shared-frame env-ref)))
         (за-умовою
           ((визначення-лямбди-на-верхньому-рівні? (перше forms))
            (нехай ((block (my-take-lambda-def-group forms)))
              (нехай ((problem (my-lambda-def-group-error block)))
                (за-умовою
                  
                  ((атом? problem)  (нехай ((rest (my-drop-lambda-def-group forms)))
                     (нехай ((block-result
                             (обчислити-блок-взаємних-визначень block program-env)))
                       (за-умовою
                         
                         ((атом? rest)  block-result)
                         ((атом? ())
                          (обчислити-послідовність-форм
                            rest
                            (перше block-result)))))))
                  ((атом? ())
                   (сполучити
                     program-env
                     (my-lambda-invalid-form problem)))))))
           ((атом? ())
            (нехай ((result (обчислити-форму-та-оновити-оточення (перше forms) program-env)))
              (за-умовою
                
                ((атом? (решта forms))  result)
                ((атом? ())
                 (обчислити-послідовність-форм
                   (решта forms)
                   (перше result))))))))))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити зв'язати-аргументи-з-лямбда-параметрами bind-params)
(визначити ім'я-визначене-в-оточенні? env-bound?)
(визначити знайти-значення-імені-в-лексичному-середовищі env-lookup)
(визначити застосувати-функцію-з-наслідком my-apply-result)
(визначити опис-очікуваної-та-одержаної-арності my-arity-detail)
(визначити арність-відповідає-аргументам? my-arity-ok?)
(визначити це-замикання? my-closure?)
(визначити усі-сусідні-значення-задовольняють-порівняння? my-compare-chain)
(визначити залежності-визначення-серед-кандидатів my-def-dependencies)
(визначити додати-визначення-до-оточення my-env-define)
(визначити створити-структуровану-помилку my-error)
(визначити обчислити-послідовне-тіло-з-раннім-збоєм my-eval-body-result)
(визначити обчислити-аргументи-з-явним-успіхом-або-помилкою my-eval-list-result)
(визначити обчислити-послідовність-форм my-eval-program)
(визначити обчислити-вираз-з-наслідком my-eval-result)
(визначити порахувати-обов'язкові-параметри-лямбди my-fixed-param-count)
(визначити вільне-посилання-у-формі-з-урахуванням-цитат-та-затінення? my-form-references-name?)
(визначити ім'я-зв'язане-в-кадрі? my-frame-bound?)
(визначити знайти-значення-імені-в-рамці my-frame-lookup)
(визначити вузол-графа-досяжний? my-graph-reaches?)
(визначити створити-замикання-взаєморекурсивної-групи my-group-closure-from-def)
(визначити це-замикання-рекурсивної-групи? my-group-closure?)
(визначити визначення-лямбди-на-верхньому-рівні? my-lambda-def-form?)
(визначити визначення-посилається-на-ім'я? my-lambda-def-references-name?)
(визначити перевірити-форму-лямбда? my-lambda-form?)
(визначити створити-лексичне-замикання-або-повернути-структуровану-помилку my-make-closure)
(визначити ім'я-зв'язане-формальними-параметрами? my-params-bind-name?)
(визначити це-рекурсивне-замикання? my-recursive-closure?)
(визначити оновити-спільний-кадр-замикання my-refresh-shared-frame)
(визначити вилучити-з-блоку-визначення-заданих-імен my-remove-defs-by-names)
(визначити лямбда-має-параметр-залишку? my-rest-param?)
(визначити власний-результат-невдача my-result-fail)
(визначити це-результат-невдалого-обчислення? my-result-fail?)
(визначити власний-результат-успіх my-result-ok)
(визначити імена-сильно-зв'язаної-компоненти my-scc-names)
(визначити відібрати-визначення-іменованої-групи my-select-defs-by-names)
(визначити визначити-невирішене-ім'я-в-оточенні? my-unresolved-name?)

; Сумісні назви попередніх викликачів. Це посилання на чинні Lisp-замикання D10/укр,
; не нові коди, функції, механізми чи окремий спосіб виконання.
(визначити my-lambda-list-error перевірити-параметри-лямбди)
(визначити my-build-group-env побудувати-лексичні-зв'язки-рекурсивної-групи)
(визначити my-eval-top-form обчислити-форму-та-оновити-оточення)
(визначити my-install-group-env встановити-взаєморекурсивні-замикання)
(визначити my-build-dependency-graph побудувати-граф-залежностей-визначень)
(визначити my-eval-lambda-block обчислити-блок-взаємних-визначень)
