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

(def fixtures (read-all (read-file "tests/fixtures/conformance.lisp")))

;; ---- Helpers ----

(def assoc
  (lambda (key alist)
    (cond
      ((atom? alist) () ())
      ((atom? alist) (1) ())
      (t (cond
           ((eq? (caar alist) key) (car alist))
           (t (assoc key (cdr alist))))))))

(def assoc-str
  (lambda (key alist)
    (cond
      ((atom? alist) () ())
      ((atom? alist) (1) ())
      (t (cond
           ((eq? (caar alist) key) (cdr (car alist)))
           (t (assoc-str key (cdr alist))))))))

(def alist-keys
  (lambda (alist)
    (cond
      ((atom? alist) () ())
      ((atom? alist) (1) ())
      (t (cons (caar alist) (alist-keys (cdr alist)))))))

;; Unique list (preserve order of first appearance)
(def uniq
  (lambda (lst)
    (cond
      ((atom? lst) () ())
      ((atom? lst) (1) ())
      (t (cond
           ((member? (car lst) (cdr lst)) (uniq (cdr lst)))
           (t (cons (car lst) (uniq (cdr lst)))))))))

;; Structural walk to collect observed-forms
;; Rules:
;; - quote        -> record 'quote, DO NOT recurse into argument (data, not code)
;; - lambda       -> record 'lambda, recurse into body only (not params)
;; - def          -> record 'def, recurse into value expression
;; - defmacro     -> record 'defmacro, recurse into macro body
;; - cond         -> record 'cond, recurse into each clause
;; - any other list (incl. if, and, or, builtins, user calls) -> record 'application, recurse into all elements
;; - atoms (symbols, numbers, strings) -> ignored (not structural forms)

(def walk-observed
  (lambda (v)
    (cond
      ((atom? v) () ())
      ((atom? v) (1) ())
      (t
       (let ((head (car v)))
         (cond
           ((atom? head) () (cond
              ((eq? head (quote quote))
               (list (quote quote)))
              ((eq? head (quote lambda))
               (cons (quote lambda)
                     (cond ((atom? (cddr v)) () ())
                           ((atom? (cddr v)) (1) ())
                           (t (walk-observed (car (cddr v)))))))
              ((eq? head (quote def))
               (cons (quote def)
                     (cond ((atom? (cddr v)) () ())
                           ((atom? (cddr v)) (1) ())
                           (t (walk-observed (car (cddr v)))))))
              ((eq? head (quote defmacro))
               (cons (quote defmacro)
                     (cond ((atom? (cddr v)) () ())
                           ((atom? (cddr v)) (1) ())
                           ((atom? (cdr (cddr v))) () ())
                           ((atom? (cdr (cddr v))) (1) ())
                           (t (walk-observed (car (cdr (cddr v))))))))
              ((eq? head (quote cond))
               (cons (quote cond) (walk-cond-clauses (cdr v))))
              (t
               (cons (quote application) (walk-list v)))))
           ((atom? head) (1) (cond
              ((eq? head (quote quote))
               (list (quote quote)))
              ((eq? head (quote lambda))
               (cons (quote lambda)
                     (cond ((atom? (cddr v)) () ())
                           ((atom? (cddr v)) (1) ())
                           (t (walk-observed (car (cddr v)))))))
              ((eq? head (quote def))
               (cons (quote def)
                     (cond ((atom? (cddr v)) () ())
                           ((atom? (cddr v)) (1) ())
                           (t (walk-observed (car (cddr v)))))))
              ((eq? head (quote defmacro))
               (cons (quote defmacro)
                     (cond ((atom? (cddr v)) () ())
                           ((atom? (cddr v)) (1) ())
                           ((atom? (cdr (cddr v))) () ())
                           ((atom? (cdr (cddr v))) (1) ())
                           (t (walk-observed (car (cdr (cddr v))))))))
              ((eq? head (quote cond))
               (cons (quote cond) (walk-cond-clauses (cdr v))))
              (t
               (cons (quote application) (walk-list v)))))
           (t
            (cons (quote application) (walk-list v)))))))))

(def walk-cond-clauses
  (lambda (clauses)
    (cond
      ((atom? clauses) () ())
      ((atom? clauses) (1) ())
      (t (append (walk-observed (caar clauses))
                 (append (cond ((atom? (cdr (car clauses))) () ())
                               ((atom? (cdr (car clauses))) (1) ())
                               (t (walk-observed (cadr (car clauses)))))
                         (walk-cond-clauses (cdr clauses))))))))

(def walk-list
  (lambda (lst)
    (cond
      ((atom? lst) () ())
      ((atom? lst) (1) ())
      (t (append (walk-observed (car lst))
                 (walk-list (cdr lst)))))))

;; Parse expr using read-all (canonical), then walk for observed-forms.
;; For NumericOverflow fixtures, the parser rejects the literal, so we skip
;; reading and return empty observed-forms (honest: no structural forms observed).
(def get-observed-forms
  (lambda (expr-str error-kind)
    (cond
      ((eq? error-kind "NumericOverflow")
       ())
      (t
       (let ((forms (read-all expr-str)))
         (cond
           ((atom? forms) () ())
           ((atom? forms) (1) ())
           (t (uniq (walk-observed (car forms))))))))))

;; Build identity record and compute ID
;; Identity includes axioms, not just expr+outcome: two fixtures can share the
;; exact same expr and expected outcome while being distinct constitutive
;; claims justified by different axioms (e.g. "(eq 3 3)" is asserted once
;; under G1's general equality and again under S1's numeric exactness) —
;; collapsing those into one ID would silently erase which axiom a fixture
;; is actually evidence for.
(def compute-id
  (lambda (expr axioms outcome-kind outcome-value)
    (let* ((identity (list (cons (quote expr) expr)
                          (cons (quote axioms) axioms)
                          (cons outcome-kind outcome-value)))
          (encoded (write-to-string identity))
          (hash (sha256-hex encoded)))
      (string-append "F-" (string-slice hash 0 16)))))

;; Process one fixture -> emit inventory record
(def emit-fixture
  (lambda (fixture)
    (let* ((expr (assoc-str (quote expr) fixture))
          (expected (assoc-str (quote expected) fixture))
          (error-kind (assoc-str (quote error) fixture))
          (tier (assoc-str (quote tier) fixture))
          (axioms (assoc-str (quote axioms) fixture))
          (requires (assoc-str (quote requires) fixture))
          (role (assoc-str (quote role) fixture))
          (note (assoc-str (quote note) fixture))
          (outcome-kind (cond (expected (quote expected)) (t (quote error))))
          (outcome-value (cond (expected expected) (t error-kind)))
          (id (compute-id expr axioms outcome-kind outcome-value))
          (observed-forms (get-observed-forms expr error-kind)))
      (print (list (quote fixture)
                   (cons (quote id) id)
                   (cons (quote tier) tier)
                   (cons (quote axioms) axioms)
                   (cons (quote declared-requires) (cond (requires requires) (t ())))
                   (cons (quote observed-forms) observed-forms)
                   (cons (quote outcome-kind) outcome-kind)
                   (cons (quote outcome-value) outcome-value)
                   (cons (quote role) (cond (role role) (t ())))
                   (cons (quote note) (cond (note note) (t ()))))))))

;; Emit all fixtures
(def emit-all
  (lambda (remaining)
    (cond
      ((atom? remaining) () (quote ()))
      ((atom? remaining) (1) (quote ()))
      (t
       (let ((printed (emit-fixture (car remaining))))
         (emit-all (cdr remaining)))))))

;; Header
(print (cons (quote about) "tests/fixtures/inventory.lisp — deterministic index over tests/fixtures/conformance.lisp. Each entry carries a stable content-addressed ID (F-<16hex>), the authoritative tier/axioms/declared-requires, mechanically observed forms from canonical reader walk, and the expected outcome. Generated — do not hand-edit. Run: cargo run -p my-lisp-cli --bin my-lisp -- scripts/build-inventory.lisp > tests/fixtures/inventory.lisp"))
(print (cons (quote generated) "This file is GENERATED — do not hand-edit. It is a projection over tests/fixtures/conformance.lisp plus this script's canonical logic."))
(print (cons (quote source) "tests/fixtures/conformance.lisp"))

(emit-all fixtures)

(quote ())