; scripts/build-inventory.lisp — generate tests/fixtures/inventory.lisp from
; tests/fixtures/conformance.lisp (2026-09-01). Written in my-lisp itself so
; the canonical reader (read-all, write-to-string, sha256-hex) is the same
; one every conforming implementation has. The inventory is a *projection*,
; not a second source of truth — edit conformance.lisp, then rerun:
;
;   cargo run -p my-lisp-cli --bin my-lisp -- scripts/build-inventory.lisp > tests/fixtures/inventory.lisp
;
; Each inventory entry preserves the authoritative fields from conformance.lisp
; and adds stable content-addressed IDs plus mechanically observed forms.
; Never hand-edit the generated file.

(визначити fixtures (читати-всі (читати-файл "tests/fixtures/conformance.lisp")))

;; ---- Helpers ----

(визначити assoc
  (функція (key alist)
    (за-умовою ((атом? alist) ()) ((атом? (як-є ())) (за-умовою
           ((тотожне? (перше-першого alist) key) (перше alist))
           ((атом? (як-є ())) (знайти-за-ключем key (решта alist))))))))

(визначити assoc-str
  (функція (key alist)
    (за-умовою ((атом? alist) ()) ((атом? (як-є ())) (за-умовою
           ((тотожне? (перше-першого alist) key) (решта (перше alist)))
           ((атом? (як-є ())) (assoc-str key (решта alist))))))))

(визначити alist-keys
  (функція (alist)
    (за-умовою ((атом? alist) ()) ((атом? (як-є ())) (сполучити (перше-першого alist) (alist-keys (решта alist)))))))

;; Unique list (preserve order of first appearance)
(визначити uniq
  (функція (lst)
    (за-умовою ((атом? lst) ()) ((атом? (як-є ())) (за-умовою
           ((значення-у-списку? (перше lst) (решта lst)) (uniq (решта lst)))
           ((атом? (як-є ())) (сполучити (перше lst) (uniq (решта lst)))))))))

;; Structural walk to collect observed-forms
;; Rules:
;; - quote        -> record 'quote, DO NOT recurse into argument (data, not code)
;; - lambda       -> record 'lambda, recurse into body only (not params)
;; - def          -> record 'def, recurse into value expression
;; - defmacro     -> record 'defmacro, recurse into macro body
;; - cond         -> record 'cond, recurse into each clause
;; - any other list (incl. if, and, or, builtins, user calls) -> record 'application, recurse into all elements
;; - atoms (symbols, numbers, strings) -> ignored (not structural forms)

(визначити walk-observed
  (функція (v)
    (за-умовою ((атом? v) ()) ((атом? (як-є ())) (нехай ((head (перше v)))
         (за-умовою ((атом? head) (за-умовою
              ((тотожне? head (як-є quote))
               (список (як-є quote)))
              ((тотожне? head (як-є lambda))
               (сполучити (як-є lambda)
                     (за-умовою ((атом? (решта-решти v)) ()) ((атом? (як-є ())) (walk-observed (перше (решта-решти v)))))))
              ((тотожне? head (як-є def))
               (сполучити (як-є def)
                     (за-умовою ((атом? (решта-решти v)) ()) ((атом? (як-є ())) (walk-observed (перше (решта-решти v)))))))
              ((тотожне? head (як-є defmacro))
               (сполучити (як-є defmacro)
                     (за-умовою ((атом? (решта-решти v)) ())
                           ((атом? (решта (решта-решти v))) ())
                           ((атом? (як-є ())) (walk-observed (перше (решта (решта-решти v))))))))
              ((тотожне? head (як-є cond))
               (сполучити (як-є cond) (walk-cond-clauses (решта v))))
              ((атом? (як-є ()))
               (сполучити (як-є application) (walk-list v))))) ((атом? (як-є ())) (сполучити (як-є application) (walk-list v)))))))))

(визначити walk-cond-clauses
  (функція (clauses)
    (за-умовою ((атом? clauses) ()) ((атом? (як-є ())) (приєднати (walk-observed (перше-першого clauses))
                 (приєднати (за-умовою ((атом? (решта (перше clauses))) ()) ((атом? (як-є ())) (walk-observed (друге (перше clauses)))))
                         (walk-cond-clauses (решта clauses))))))))

(визначити walk-list
  (функція (lst)
    (за-умовою ((атом? lst) ()) ((атом? (як-є ())) (приєднати (walk-observed (перше lst))
                 (walk-list (решта lst)))))))

;; Parse expr using read-all (canonical), then walk for observed-forms.
;; For NumericOverflow fixtures, the parser rejects the literal, so we skip
;; reading and return empty observed-forms (honest: no structural forms observed).
(визначити get-observed-forms
  (функція (expr-str error-kind)
    (за-умовою
      ((тотожне? error-kind "NumericOverflow")
       ())
      ((атом? (як-є ()))
       (нехай ((forms (читати-всі expr-str)))
         (за-умовою ((атом? forms) ()) ((атом? (як-є ())) (uniq (walk-observed (перше forms))))))))))

;; Build identity record and compute ID
;; Identity includes axioms, not just expr+outcome: two fixtures can share the
;; exact same expr and expected outcome while being distinct constitutive
;; claims justified by different axioms (e.g. "(eq 3 3)" is asserted once
;; under G1's general equality and again under S1's numeric exactness) —
;; collapsing those into one ID would silently erase which axiom a fixture
;; is actually evidence for.
(визначити compute-id
  (функція (expr axioms outcome-kind outcome-value)
    (нехай-послідовно ((identity-record (список (сполучити (як-є expr) expr)
                          (сполучити (як-є axioms) axioms)
                          (сполучити outcome-kind outcome-value)))
          (encoded (значення-у-текст identity-record))
          (hash (геш-256-шістнадцятковий encoded)))
      (рядок-додати "F-" (рядок-зріз hash 0 16)))))

;; Process one fixture -> emit inventory record
(визначити emit-fixture
  (функція (fixture)
    (нехай-послідовно ((expr (assoc-str (як-є expr) fixture))
          (expected (assoc-str (як-є expected) fixture))
          (error-kind (assoc-str (як-є error) fixture))
          (tier (assoc-str (як-є tier) fixture))
          (axioms (assoc-str (як-є axioms) fixture))
          (requires (assoc-str (як-є requires) fixture))
          (role (assoc-str (як-є role) fixture))
          (note (assoc-str (як-є note) fixture))
          (outcome-kind (за-умовою (expected (як-є expected)) ((атом? (як-є ())) (як-є error))))
          (outcome-value (за-умовою (expected expected) ((атом? (як-є ())) error-kind)))
          (id (compute-id expr axioms outcome-kind outcome-value))
          (observed-forms (get-observed-forms expr error-kind)))
      (друкувати (список (як-є fixture)
                   (сполучити (як-є id) id)
                   (сполучити (як-є tier) tier)
                   (сполучити (як-є axioms) axioms)
                   (сполучити (як-є declared-requires) (за-умовою (requires requires) ((атом? (як-є ())) ())))
                   (сполучити (як-є observed-forms) observed-forms)
                   (сполучити (як-є outcome-kind) outcome-kind)
                   (сполучити (як-є outcome-value) outcome-value)
                   (сполучити (як-є role) (за-умовою (role role) ((атом? (як-є ())) ())))
                   (сполучити (як-є note) (за-умовою (note note) ((атом? (як-є ())) ()))))))))

;; Emit all fixtures
(визначити emit-all
  (функція (remaining)
    (за-умовою ((атом? remaining) (як-є ())) ((атом? (як-є ())) (нехай ((printed (emit-fixture (перше remaining))))
         (emit-all (решта remaining)))))))

;; Header
(друкувати (сполучити (як-є about) "tests/fixtures/inventory.lisp — deterministic index over tests/fixtures/conformance.lisp. Each entry carries a stable content-addressed ID (F-<16hex>), the authoritative tier/axioms/declared-requires, mechanically observed forms from canonical reader walk, and the expected outcome. Generated — do not hand-edit. Run: cargo run -p my-lisp-cli --bin my-lisp -- scripts/build-inventory.lisp > tests/fixtures/inventory.lisp"))
(друкувати (сполучити (як-є generated) "This file is GENERATED — do not hand-edit. It is a projection over tests/fixtures/conformance.lisp plus this script's canonical logic."))
(друкувати (сполучити (як-є source) "tests/fixtures/conformance.lisp"))

(emit-all fixtures)

(як-є ())

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити знайти-за-ключем assoc)
