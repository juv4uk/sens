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

(0011 fixtures (110101001 (110110111 "tests/fixtures/conformance.lisp")))

;; ---- Helpers ----

(0011 assoc
  (0010 (key alist)
    (110 ((010 alist) ()) ((010 (001 ())) (110
           ((101 (1000 alist) key) (100 alist))
           (t (assoc key (011 alist))))))))

(0011 assoc-str
  (0010 (key alist)
    (110 ((010 alist) ()) ((010 (001 ())) (110
           ((101 (1000 alist) key) (011 (100 alist)))
           (t (assoc-str key (011 alist))))))))

(0011 alist-keys
  (0010 (alist)
    (110 ((010 alist) ()) ((010 (001 ())) (111 (1000 alist) (alist-keys (011 alist)))))))

;; Unique list (preserve order of first appearance)
(0011 uniq
  (0010 (lst)
    (110 ((010 lst) ()) ((010 (001 ())) (110
           ((11101 (100 lst) (011 lst)) (uniq (011 lst)))
           (t (111 (100 lst) (uniq (011 lst)))))))))

;; Structural walk to collect observed-forms
;; Rules:
;; - quote        -> record 'quote, DO NOT recurse into argument (data, not code)
;; - lambda       -> record 'lambda, recurse into body only (not params)
;; - def          -> record 'def, recurse into value expression
;; - defmacro     -> record 'defmacro, recurse into macro body
;; - cond         -> record 'cond, recurse into each clause
;; - any other list (incl. if, and, or, builtins, user calls) -> record 'application, recurse into all elements
;; - atoms (symbols, numbers, strings) -> ignored (not structural forms)

(0011 walk-observed
  (0010 (v)
    (110 ((010 v) ()) ((010 (001 ())) (001000 ((head (100 v)))
         (110 ((010 head) (110
              ((101 head (001 quote))
               (1110 (001 quote)))
              ((101 head (001 lambda))
               (111 (001 lambda)
                     (110 ((010 (0111 v)) ()) ((010 (001 ())) (walk-observed (100 (0111 v)))))))
              ((101 head (001 def))
               (111 (001 def)
                     (110 ((010 (0111 v)) ()) ((010 (001 ())) (walk-observed (100 (0111 v)))))))
              ((101 head (001 defmacro))
               (111 (001 defmacro)
                     (110 ((010 (0111 v)) () ())
                           ((010 (0111 v)) (1) ())
                           ((010 (011 (0111 v))) () ())
                           ((010 (011 (0111 v))) (1) ())
                           (t (walk-observed (100 (011 (0111 v))))))))
              ((101 head (001 cond))
               (111 (001 cond) (walk-cond-clauses (011 v))))
              (t
               (111 (001 application) (walk-list v))))) ((010 (001 ())) (111 (001 application) (walk-list v)))))))))

(0011 walk-cond-clauses
  (0010 (clauses)
    (110 ((010 clauses) ()) ((010 (001 ())) (1111 (walk-observed (1000 clauses))
                 (1111 (110 ((010 (011 (100 clauses))) ()) ((010 (001 ())) (walk-observed (1001 (100 clauses)))))
                         (walk-cond-clauses (011 clauses))))))))

(0011 walk-list
  (0010 (lst)
    (110 ((010 lst) ()) ((010 (001 ())) (1111 (walk-observed (100 lst))
                 (walk-list (011 lst)))))))

;; Parse expr using read-all (canonical), then walk for observed-forms.
;; For NumericOverflow fixtures, the parser rejects the literal, so we skip
;; reading and return empty observed-forms (honest: no structural forms observed).
(0011 get-observed-forms
  (0010 (expr-str error-kind)
    (110
      ((101 error-kind "NumericOverflow")
       ())
      (t
       (001000 ((forms (110101001 expr-str)))
         (110 ((010 forms) ()) ((010 (001 ())) (uniq (walk-observed (100 forms))))))))))

;; Build identity record and compute ID
;; Identity includes axioms, not just expr+outcome: two fixtures can share the
;; exact same expr and expected outcome while being distinct constitutive
;; claims justified by different axioms (e.g. "(eq 3 3)" is asserted once
;; under G1's general equality and again under S1's numeric exactness) —
;; collapsing those into one ID would silently erase which axiom a fixture
;; is actually evidence for.
(0011 compute-id
  (0010 (expr axioms outcome-kind outcome-value)
    (001001 ((identity-record (1110 (111 (001 expr) expr)
                          (111 (001 axioms) axioms)
                          (111 outcome-kind outcome-value)))
          (encoded (11110100 identity-record))
          (hash (110011000 encoded)))
      (110011110 "F-" (110100011 hash 0 16)))))

;; Process one fixture -> emit inventory record
(0011 emit-fixture
  (0010 (fixture)
    (001001 ((expr (assoc-str (001 expr) fixture))
          (expected (assoc-str (001 expected) fixture))
          (error-kind (assoc-str (001 error) fixture))
          (tier (assoc-str (001 tier) fixture))
          (axioms (assoc-str (001 axioms) fixture))
          (requires (assoc-str (001 requires) fixture))
          (role (assoc-str (001 role) fixture))
          (note (assoc-str (001 note) fixture))
          (outcome-kind (110 (expected (001 expected)) (t (001 error))))
          (outcome-value (110 (expected expected) (t error-kind)))
          (id (compute-id expr axioms outcome-kind outcome-value))
          (observed-forms (get-observed-forms expr error-kind)))
      (11011011 (1110 (001 fixture)
                   (111 (001 id) id)
                   (111 (001 tier) tier)
                   (111 (001 axioms) axioms)
                   (111 (001 declared-requires) (110 (requires requires) (t ())))
                   (111 (001 observed-forms) observed-forms)
                   (111 (001 outcome-kind) outcome-kind)
                   (111 (001 outcome-value) outcome-value)
                   (111 (001 role) (110 (role role) (t ())))
                   (111 (001 note) (110 (note note) (t ()))))))))

;; Emit all fixtures
(0011 emit-all
  (0010 (remaining)
    (110 ((010 remaining) (001 ())) ((010 (001 ())) (001000 ((printed (emit-fixture (100 remaining))))
         (emit-all (011 remaining)))))))

;; Header
(11011011 (111 (001 about) "tests/fixtures/inventory.lisp — deterministic index over tests/fixtures/conformance.lisp. Each entry carries a stable content-addressed ID (F-<16hex>), the authoritative tier/axioms/declared-requires, mechanically observed forms from canonical reader walk, and the expected outcome. Generated — do not hand-edit. Run: cargo run -p my-lisp-cli --bin my-lisp -- scripts/build-inventory.lisp > tests/fixtures/inventory.lisp"))
(11011011 (111 (001 generated) "This file is GENERATED — do not hand-edit. It is a projection over tests/fixtures/conformance.lisp plus this script's canonical logic."))
(11011011 (111 (001 source) "tests/fixtures/conformance.lisp"))

(emit-all fixtures)

(001 ())