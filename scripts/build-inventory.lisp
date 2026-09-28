; scripts/build-inventory.lisp — generate tests/fixtures/inventory.lisp from
; tests/fixtures/conformance.lisp (2026-09-01). Written in my-lisp itself so
; the canonical reader (read-all, write-to-string, sha256-hex) is the same
; one every conforming implementation has. The inventory is a *projection*,
; not a second source of truth — edit conformance.lisp, then rerun:
;
;   cargo run -p sens-cli --bin my-lisp -- scripts/build-inventory.lisp > tests/fixtures/inventory.lisp
;
; Each inventory entry preserves the authoritative fields from conformance.lisp
; and adds stable content-addressed IDs plus mechanically observed forms.
; Never hand-edit the generated file.

(00001001 fixtures (01001011 (10100110 "tests/fixtures/conformance.lisp")))

;; ---- Helpers ----

(00001001 assoc
  (00001000 (key alist)
    (00000111
      ((00000010 alist) () ())
      ((00000010 alist) (1) ())
      (t (00000111
           ((00000011 (00110011 alist) key) (00000101 alist))
           (t (assoc key (00000110 alist))))))))

(00001001 assoc-str
  (00001000 (key alist)
    (00000111
      ((00000010 alist) () ())
      ((00000010 alist) (1) ())
      (t (00000111
           ((00000011 (00110011 alist) key) (00000110 (00000101 alist)))
           (t (assoc-str key (00000110 alist))))))))

(00001001 alist-keys
  (00001000 (alist)
    (00000111
      ((00000010 alist) () ())
      ((00000010 alist) (1) ())
      (t (00000100 (00110011 alist) (alist-keys (00000110 alist)))))))

;; Unique list (preserve order of first appearance)
(00001001 uniq
  (00001000 (lst)
    (00000111
      ((00000010 lst) () ())
      ((00000010 lst) (1) ())
      (t (00000111
           ((00101100 (00000101 lst) (00000110 lst)) (uniq (00000110 lst)))
           (t (00000100 (00000101 lst) (uniq (00000110 lst)))))))))

;; Structural walk to collect observed-forms
;; Rules:
;; - quote        -> record 'quote, DO NOT recurse into argument (data, not code)
;; - lambda       -> record 'lambda, recurse into body only (not params)
;; - def          -> record 'def, recurse into value expression
;; - defmacro     -> record 'defmacro, recurse into macro body
;; - cond         -> record 'cond, recurse into each clause
;; - any other list (incl. if, and, or, builtins, user calls) -> record 'application, recurse into all elements
;; - atoms (symbols, numbers, strings) -> ignored (not structural forms)

(00001001 walk-observed
  (00001000 (v)
    (00000111
      ((00000010 v) () ())
      ((00000010 v) (1) ())
      (t
       (10011100 ((head (00000101 v)))
         (00000111
           ((00000010 head) () (00000111
              ((00000011 head (00000001 quote))
               (00100111 (00000001 quote)))
              ((00000011 head (00000001 lambda))
               (00000100 (00000001 lambda)
                     (00000111 ((00000010 (00110101 v)) () ())
                           ((00000010 (00110101 v)) (1) ())
                           (t (walk-observed (00000101 (00110101 v)))))))
              ((00000011 head (00000001 def))
               (00000100 (00000001 def)
                     (00000111 ((00000010 (00110101 v)) () ())
                           ((00000010 (00110101 v)) (1) ())
                           (t (walk-observed (00000101 (00110101 v)))))))
              ((00000011 head (00000001 defmacro))
               (00000100 (00000001 defmacro)
                     (00000111 ((00000010 (00110101 v)) () ())
                           ((00000010 (00110101 v)) (1) ())
                           ((00000010 (00000110 (00110101 v))) () ())
                           ((00000010 (00000110 (00110101 v))) (1) ())
                           (t (walk-observed (00000101 (00000110 (00110101 v))))))))
              ((00000011 head (00000001 cond))
               (00000100 (00000001 cond) (walk-cond-clauses (00000110 v))))
              (t
               (00000100 (00000001 application) (walk-list v)))))
           ((00000010 head) (1) (00000111
              ((00000011 head (00000001 quote))
               (00100111 (00000001 quote)))
              ((00000011 head (00000001 lambda))
               (00000100 (00000001 lambda)
                     (00000111 ((00000010 (00110101 v)) () ())
                           ((00000010 (00110101 v)) (1) ())
                           (t (walk-observed (00000101 (00110101 v)))))))
              ((00000011 head (00000001 def))
               (00000100 (00000001 def)
                     (00000111 ((00000010 (00110101 v)) () ())
                           ((00000010 (00110101 v)) (1) ())
                           (t (walk-observed (00000101 (00110101 v)))))))
              ((00000011 head (00000001 defmacro))
               (00000100 (00000001 defmacro)
                     (00000111 ((00000010 (00110101 v)) () ())
                           ((00000010 (00110101 v)) (1) ())
                           ((00000010 (00000110 (00110101 v))) () ())
                           ((00000010 (00000110 (00110101 v))) (1) ())
                           (t (walk-observed (00000101 (00000110 (00110101 v))))))))
              ((00000011 head (00000001 cond))
               (00000100 (00000001 cond) (walk-cond-clauses (00000110 v))))
              (t
               (00000100 (00000001 application) (walk-list v)))))
           (t
            (00000100 (00000001 application) (walk-list v)))))))))

(00001001 walk-cond-clauses
  (00001000 (clauses)
    (00000111
      ((00000010 clauses) () ())
      ((00000010 clauses) (1) ())
      (t (00101001 (walk-observed (00110011 clauses))
                 (00101001 (00000111 ((00000010 (00000110 (00000101 clauses))) () ())
                               ((00000010 (00000110 (00000101 clauses))) (1) ())
                               (t (walk-observed (00110100 (00000101 clauses)))))
                         (walk-cond-clauses (00000110 clauses))))))))

(00001001 walk-list
  (00001000 (lst)
    (00000111
      ((00000010 lst) () ())
      ((00000010 lst) (1) ())
      (t (00101001 (walk-observed (00000101 lst))
                 (walk-list (00000110 lst)))))))

;; Parse expr using read-all (canonical), then walk for observed-forms.
;; For NumericOverflow fixtures, the parser rejects the literal, so we skip
;; reading and return empty observed-forms (honest: no structural forms observed).
(00001001 get-observed-forms
  (00001000 (expr-str error-kind)
    (00000111
      ((00000011 error-kind "NumericOverflow")
       ())
      (t
       (10011100 ((forms (01001011 expr-str)))
         (00000111
           ((00000010 forms) () ())
           ((00000010 forms) (1) ())
           (t (uniq (walk-observed (00000101 forms))))))))))

;; Build identity record and compute ID
;; Identity includes axioms, not just expr+outcome: two fixtures can share the
;; exact same expr and expected outcome while being distinct constitutive
;; claims justified by different axioms (e.g. "(eq 3 3)" is asserted once
;; under G1's general equality and again under S1's numeric exactness) —
;; collapsing those into one ID would silently erase which axiom a fixture
;; is actually evidence for.
(00001001 compute-id
  (00001000 (expr axioms outcome-kind outcome-value)
    (10011101 ((identity (00100111 (00000100 (00000001 expr) expr)
                          (00000100 (00000001 axioms) axioms)
                          (00000100 outcome-kind outcome-value)))
          (encoded (01001100 identity))
          (hash (10100001 encoded)))
      (00111010 "F-" (01000001 hash 0 16)))))

;; Process one fixture -> emit inventory record
(00001001 emit-fixture
  (00001000 (fixture)
    (10011101 ((expr (assoc-str (00000001 expr) fixture))
          (expected (assoc-str (00000001 expected) fixture))
          (error-kind (assoc-str (00000001 error) fixture))
          (tier (assoc-str (00000001 tier) fixture))
          (axioms (assoc-str (00000001 axioms) fixture))
          (requires (assoc-str (00000001 requires) fixture))
          (role (assoc-str (00000001 role) fixture))
          (note (assoc-str (00000001 note) fixture))
          (outcome-kind (00000111 (expected (00000001 expected)) (t (00000001 error))))
          (outcome-value (00000111 (expected expected) (t error-kind)))
          (id (compute-id expr axioms outcome-kind outcome-value))
          (observed-forms (get-observed-forms expr error-kind)))
      (01001000 (00100111 (00000001 fixture)
                   (00000100 (00000001 id) id)
                   (00000100 (00000001 tier) tier)
                   (00000100 (00000001 axioms) axioms)
                   (00000100 (00000001 declared-requires) (00000111 (requires requires) (t ())))
                   (00000100 (00000001 observed-forms) observed-forms)
                   (00000100 (00000001 outcome-kind) outcome-kind)
                   (00000100 (00000001 outcome-value) outcome-value)
                   (00000100 (00000001 role) (00000111 (role role) (t ())))
                   (00000100 (00000001 note) (00000111 (note note) (t ()))))))))

;; Emit all fixtures
(00001001 emit-all
  (00001000 (remaining)
    (00000111
      ((00000010 remaining) () (00000001 ()))
      ((00000010 remaining) (1) (00000001 ()))
      (t
       (10011100 ((printed (emit-fixture (00000101 remaining))))
         (emit-all (00000110 remaining)))))))

;; Header
(01001000 (00000100 (00000001 about) "tests/fixtures/inventory.lisp — deterministic index over tests/fixtures/conformance.lisp. Each entry carries a stable content-addressed ID (F-<16hex>), the authoritative tier/axioms/declared-requires, mechanically observed forms from canonical reader walk, and the expected outcome. Generated — do not hand-edit. Run: cargo run -p sens-cli --bin my-lisp -- scripts/build-inventory.lisp > tests/fixtures/inventory.lisp"))
(01001000 (00000100 (00000001 generated) "This file is GENERATED — do not hand-edit. It is a projection over tests/fixtures/conformance.lisp plus this script's canonical logic."))
(01001000 (00000100 (00000001 source) "tests/fixtures/conformance.lisp"))

(emit-all fixtures)

(00000001 ())