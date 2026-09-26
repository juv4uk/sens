; scripts/build-dependency-classification.lisp — classify every constitutional
; fixture (tests/fixtures/conformance.lisp, keyed via tests/fixtures/inventory.lisp,
; same 1:1 positional pairing established in scripts/oracle-batch.lisp) by
; which language layers it needs in order to execute at all: the bare
; kernel (core special forms + Rust builtins), closure creation/application,
; exact-number machinery, strings/reader operations, lib/core.lisp (the one
; core library loaded in the standard bootstrap), or any OTHER lib/*.lisp
; library / host capability (tcp-*, file I/O, load, process-run) — the
; combined "reasoning/World or host capability" bucket named in
; WSM-CONSTITUTION-DEPENDENCY-CLASSIFICATION's own description.
;
; Method: read each fixture's source text with the real reader (not a
; hand-rolled tokenizer — that class of bug is exactly what R1 found and
; fixed earlier in this same investigation), walk the parsed form
; collecting every symbol that appears in HEAD (operator) position of an
; unquoted, executed sub-form, and classify each such symbol against
; tables of known names. A symbol bound locally by an enclosing lambda,
; let, let*, or defmacro parameter list is excluded — it is a user
; variable, not an external dependency. A symbol matching none of the
; known tables is left explicit as UNKNOWN rather than guessed into a
; bucket, per the task's own requirement.
;
; The core-special-form / core-builtin / host-capability tables are
; hardcoded because they live in Rust (crates/my-lisp/src/eval/mod.rs's
; evaluate_list dispatch, crates/my-lisp/src/eval/builtins.rs,
; crates/my-lisp-host/src/lib.rs's register_capability calls) — there is
; no self-hosted source to read them from. The lib/core.lisp table and the
; "every other lib/*.lisp file" table ARE generated at run time, by reading
; those files with read-dir/read-file/read-all and collecting every
; top-level (def NAME ...) / (defmacro NAME ...) name — so this stays
; correct as those libraries grow, instead of silently rotting like a
; hand-copied list would.
;
; "exact numbers" is the one bucket without a runtime type predicate to
; check against (my-lisp exposes no rational?/exact? primitive, and
; hand-rolling a source-text scanner for rational-literal syntax would
; repeat exactly the class of bug R1 found and fixed earlier in this
; investigation: guessing at tokenizer classification from outside the
; real reader). Instead this bucket is source-confirmed from ground
; truth that already exists: each fixture's own conformance.lisp record
; names its axioms, and S1 IS the constitution's "never silently
; approximate exact->inexact" axiom — a fixture tagged S1 is, by the
; constitution's own classification, exercising exact-number semantics.
; This is honestly a coarser signal than a real type check would be
; (reported as axiom-tagged-s1, not silently presented as equivalent to
; the other buckets' direct symbol-table matches) but it is not guessed.
;
; Run: my-lisp scripts/build-dependency-classification.lisp > tests/fixtures/dependency-classification.lisp

; ---------------------------------------------------------------------
; Hardcoded Rust-side tables (no self-hosted source to generate these from)
; ---------------------------------------------------------------------

; crates/my-lisp/src/eval/mod.rs evaluate_list's own match arms
(def core-special-forms
  (quote (quote lambda def defmacro cond print princ write-to-string read
          eval string-append string<? read-all string? symbol->string
          string->symbol string-first string-rest sha256-hex json-parse)))

; crates/my-lisp/src/eval/builtins.rs environment.define registrations.
; Derived time operations such as mono-ms, utc-now, internet-time-sync, and
; timezone-detect intentionally do not appear here: they are defined by
; lib/time.lisp. The retained host-facing time operations expose observations
; only: mono-ns, unix-time-now, ntp-query-raw, timezone-declarations-raw.
(def core-builtins
  (quote (* + - / < = > abs atom car cdr cons env eq f32 f32-buffer i32
          i32-buffer make-vector max max-list min min-list mono-ns
          ntp-query-raw numeric-buffer-length numeric-buffer-map
          numeric-buffer-ref numeric-buffer-type numeric-buffer? string-slice
          timezone-declarations-raw unix-time-now vector vector-length vector-ref
          vector-set!)))

; crates/my-lisp-host/src/lib.rs register_capability calls
(def host-capabilities
  (quote (load process-run read-dir read-file read-file-bytes tcp-accept
          tcp-close tcp-connect tcp-listen tcp-read tcp-write write-file
          write-file-bytes)))

; the string/reader-flavored subset of the two tables above, called out
; as its own bucket per the task description ("strings/reader")
(def strings-reader-subset
  (quote (write-to-string read read-all string-append string<? string?
          symbol->string string->symbol string-first string-rest
          string-slice string-contains? string-empty? string-length
          string-prefix? digit->string number->string number->string-onto)))

; ---------------------------------------------------------------------
; Generated tables: read the real library sources, don't hand-copy them
; ---------------------------------------------------------------------

(def top-level-def-names
  (lambda (forms)
    (cond
      ((atom? forms) () (quote ()))
      ((atom? forms) (1) (quote ()))
      (t (let* ((form (car forms))
                (rest (top-level-def-names (cdr forms))))
           (cond
             ((atom? form) () rest)
             ((atom? form) (1) rest)
             ((eq? (car form) (quote def)) (cons (car (cdr form)) rest))
             ((eq? (car form) (quote defmacro)) (cons (car (cdr form)) rest))
             (t rest)))))))

(def symbol-names-from-file
  (lambda (path)
    (top-level-def-names (read-all (read-file path)))))

(def core-my-symbols
  (symbol-names-from-file "lib/core.lisp"))

; every file under lib/ except core.lisp (and its .fasl cache), paired with
; the symbol names it defines -- an alist of (filename . (symbols...))
(def other-lib-tables
  (lambda ()
    (let* ((entries (read-dir "lib"))
           (relevant (filter
                       (lambda (name)
                         (and (string-prefix? ".lisp" (string-slice name (- (string-length name) 3) (string-length name)))
                              (not? (equal? name "core.lisp"))))
                       entries)))
      (map (lambda (name)
             (cons name (symbol-names-from-file (string-append "lib/" name))))
           relevant))))

; ---------------------------------------------------------------------
; The walker: collect every symbol used in executed head position,
; excluding locally-bound names, tagging %uses-lambda / %uses-let-family
; as it goes past lambda/let/let*/defmacro.
; ---------------------------------------------------------------------

; the constitutional fixture set deliberately includes malformed special
; forms (a lambda missing its body, a defmacro missing its parameter
; list, a let-binding missing its value expression) to test the real
; evaluator's own Arity errors -- crates/my-lisp/tests exercises the
; same class at conformance.lisp:113/134 (lambda/defmacro arity fixtures).
; The real evaluator rejects these at eval time; this classifier only
; needs to not crash while walking them, so every destructuring step
; below that assumes a minimum shape uses these instead of raw car/cdr,
; degrading a missing piece to () rather than erroring.
(def safe-car
  (lambda (lst) (cond ((atom? lst) () (quote ()))
                      ((atom? lst) (1) (quote ())) (t (car lst)))))
(def safe-cdr
  (lambda (lst) (cond ((atom? lst) () (quote ()))
                      ((atom? lst) (1) (quote ())) (t (cdr lst)))))

(def collect-symbols-leaf
  (lambda (form)
    (cond
      ((symbol? form) (list form))
      ((atom? form) () (quote ()))
      ((atom? form) (1) (quote ()))
      (t (append (collect-symbols-leaf (car form)) (collect-symbols-leaf (cdr form)))))))

(def collect-heads-each
  (lambda (forms bound)
    (cond
      ((atom? forms) () (quote ()))
      ((atom? forms) (1) (quote ()))
      (t (append (collect-heads (car forms) bound)
                 (collect-heads-each (cdr forms) bound))))))

(def collect-heads-cond-clauses
  (lambda (clauses bound)
    (cond
      ((atom? clauses) () (quote ()))
      ((atom? clauses) (1) (quote ()))
      (t (let* ((clause (car clauses))
                (test-form (safe-car clause))
                (body-form (safe-car (safe-cdr clause)))
                (test-deps (collect-heads test-form bound))
                (body-deps (collect-heads body-form bound))
                (rest-deps (collect-heads-cond-clauses (cdr clauses) bound)))
           (append test-deps (append body-deps rest-deps)))))))

(def collect-heads-let*-seq
  (lambda (bindings body bound)
    (cond
      ((atom? bindings) () (collect-heads body bound))
      ((atom? bindings) (1) (collect-heads body bound))
      (t (let* ((binding (car bindings))
                (name (safe-car binding))
                (value-form (safe-car (safe-cdr binding)))
                (value-deps (collect-heads value-form bound))
                (new-bound (cons name bound))
                (rest-deps (collect-heads-let*-seq (cdr bindings) body new-bound)))
           (append value-deps rest-deps))))))

(def collect-heads
  (lambda (form bound)
    (cond
      ((atom? form) () (quote ()))
      ((atom? form) (1) (quote ()))
      (t (let ((head (car form)))
           (cond
             ((and (symbol? head) (eq? head (quote quote)))
              (quote ()))
             ((and (symbol? head) (eq? head (quote lambda)))
              (let* ((params (safe-car (safe-cdr form)))
                     (body (safe-cdr (safe-cdr form)))
                     (param-names (collect-symbols-leaf params))
                     (new-bound (append param-names bound)))
                (cons (quote %uses-lambda) (collect-heads-each body new-bound))))
             ((and (symbol? head) (eq? head (quote let)))
              (let* ((bindings (safe-car (safe-cdr form)))
                     (body (safe-car (safe-cdr (safe-cdr form))))
                     (names (map (lambda (b) (safe-car b)) bindings))
                     (value-forms (map (lambda (b) (safe-car (safe-cdr b))) bindings))
                     (value-deps (collect-heads-each value-forms bound))
                     (new-bound (append names bound))
                     (body-deps (collect-heads body new-bound)))
                (cons (quote %uses-lambda)
                      (cons (quote %uses-let-family) (append value-deps body-deps)))))
             ((and (symbol? head) (eq? head (quote let*)))
              (let* ((bindings (safe-car (safe-cdr form)))
                     (body (safe-car (safe-cdr (safe-cdr form)))))
                (cons (quote %uses-lambda)
                      (cons (quote %uses-let-family)
                            (collect-heads-let*-seq bindings body bound)))))
             ((and (symbol? head) (eq? head (quote def)))
              (let* ((name (safe-car (safe-cdr form)))
                     (value-form (safe-car (safe-cdr (safe-cdr form))))
                     ; def's own name is visible inside its own value-expr:
                     ; the evaluator shares one lexical frame between a def
                     ; and the closure it defines, so a self-referential
                     ; (def f (lambda (x) ... (f ...))) genuinely resolves
                     ; at call time even though f isn't bound yet when the
                     ; closure is created (crates/my-lisp/src/eval/special_forms/core.rs
                     ; evaluate_definition's own comment documents this).
                     (new-bound (cons name bound)))
                (collect-heads value-form new-bound)))
             ((and (symbol? head) (eq? head (quote defmacro)))
              (let* ((params (safe-car (safe-cdr (safe-cdr form))))
                     (body (safe-cdr (safe-cdr (safe-cdr form))))
                     (param-names (collect-symbols-leaf params))
                     (new-bound (append param-names bound)))
                (cons (quote %uses-lambda) (collect-heads-each body new-bound))))
             ((and (symbol? head) (eq? head (quote cond)))
              (collect-heads-cond-clauses (cdr form) bound))
             (t
              (let* ((head-dep (cond
                                  ((not? (symbol? head)) (quote ()))
                                  ((member? head bound) (quote ()))
                                  (t (list head))))
                     (head-recurse (cond ((atom? head) () (quote ()))
                                         ((atom? head) (1) (quote ())) (t (collect-heads head bound))))
                     (args-deps (collect-heads-each (cdr form) bound)))
                (append head-dep (append head-recurse args-deps))))))))))

(def collect-deps-one
  (lambda (form bound)
    (cond
      ((symbol? form) (cond ((member? form bound) (quote ())) (t (list form))))
      (t (collect-heads form bound)))))

; a fixture's expr text can hold MORE than one top-level form (e.g.
; "(def count-down (lambda ...)) (count-down 100000)" -- a def followed
; by a call, exactly like a real script). read-all captures every form;
; a top-level def/defmacro extends the bound-set for the forms that
; follow it in the SAME fixture, matching how they'd actually be
; evaluated in one shared environment.
(def collect-deps-top-seq
  (lambda (forms bound)
    (cond
      ((atom? forms) () (quote ()))
      ((atom? forms) (1) (quote ()))
      (t (let* ((form (car forms))
                (deps (collect-deps-one form bound))
                (new-bound (cond
                             ((atom? form) () bound)
                             ((atom? form) (1) bound)
                             ((and (symbol? (car form)) (eq? (car form) (quote def)))
                              (cons (car (cdr form)) bound))
                             ((and (symbol? (car form)) (eq? (car form) (quote defmacro)))
                              (cons (car (cdr form)) bound))
                             (t bound))))
           (append deps (collect-deps-top-seq (cdr forms) new-bound)))))))

(def collect-deps-top
  (lambda (forms)
    (collect-deps-top-seq forms (quote ()))))

; ---------------------------------------------------------------------
; Classification of one fixture's collected raw head-symbol list against
; the known tables.
; ---------------------------------------------------------------------

(def is-marker?
  (lambda (s)
    (or (eq? s (quote %uses-lambda)) (eq? s (quote %uses-let-family)))))

(def unique-onto
  (lambda (items acc)
    (cond
      ((atom? items) () acc)
      ((atom? items) (1) acc)
      ((member? (car items) acc) (unique-onto (cdr items) acc))
      (t (unique-onto (cdr items) (cons (car items) acc))))))

(def uniq (lambda (items) (unique-onto items (quote ()))))

(def owning-library
  (lambda (sym tables)
    (cond
      ((atom? tables) () (quote ()))
      ((atom? tables) (1) (quote ()))
      ((member? sym (cdr (car tables))) (car (car tables)))
      (t (owning-library sym (cdr tables))))))

; classify one real (non-marker) symbol; returns (bucket-tag . library-or-())
(def classify-symbol
  (lambda (sym other-tables)
    (cond
      ((member? sym core-special-forms) (cons (quote core) (quote ())))
      ((member? sym core-builtins) (cons (quote core) (quote ())))
      ((member? sym host-capabilities) (cons (quote reasoning-world-or-host) sym))
      ((member? sym core-my-symbols) (cons (quote macro-expanded-core) (quote ())))
      (t (let ((lib (owning-library sym other-tables)))
           (cond
             ((equal? lib (quote ())) (cons (quote unknown) (quote ())))
             (t (cons (quote reasoning-world-or-host) lib))))))))

; my-lisp has no try/catch: a fixture whose own point is that its source
; text exceeds the reader's decimal-literal exponent resource bound
; (crates/my-lisp/src/value.rs's MAX_DECIMAL_LITERAL_EXPONENT_MAGNITUDE,
; 10000 as of commit 3a90df3) makes read-all itself throw a hard parse
; error, aborting the whole batch -- exactly the same shape of problem
; scripts/oracle-batch.lisp hit and fixed by not locally re-parsing at
; all. This classifier DOES need a local parse to walk the AST, so it
; cannot avoid reading altogether; instead it special-cases the exact,
; currently-known set of such fixtures (verified via
; `grep -n 'e100001\|e-100001' tests/fixtures/conformance.lisp`: exactly
; three, all S3 axiom-tagged, all with error . "NumericOverflow" already
; recorded) rather than guessing at a general-purpose exponent scanner --
; the R1 lesson earlier in this investigation was specifically about the
; risk of hand-rolling number classification outside the real reader. If
; a future fixture adds a different oversized-exponent literal, this
; check needs re-verification against the live corpus, not silent trust.
(def known-unreadable-oversized-exponent?
  (lambda (expr-str)
    (or (string-contains? "e100001" expr-str)
        (string-contains? "e-100001" expr-str))))

(def classify-fixture
  (lambda (id expr-str axioms-list other-tables)
    (cond
      ((known-unreadable-oversized-exponent? expr-str)
       (list (quote dependency-classification)
             (cons (quote id) id)
             (cons (quote buckets) (quote (core)))
             (cons (quote unknown-symbols) (quote ()))
             (cons (quote world-host-libraries) (quote ()))
             (cons (quote axiom-tagged-s1) (member? (quote S1) axioms-list))
             (cons (quote note) "source text exceeds the reader's own decimal-literal exponent resource bound; not locally re-parsed, classified as core (the reader itself) by inspection")))
      (t (classify-readable-fixture id expr-str axioms-list other-tables)))))

(def classify-readable-fixture
  (lambda (id expr-str axioms-list other-tables)
    (let* ((parsed-forms (read-all expr-str))
           (raw (collect-deps-top parsed-forms))
           (markers (filter is-marker? raw))
           (real-syms (uniq (filter (lambda (s) (not? (is-marker? s))) raw)))
           (classified (map (lambda (s) (cons s (classify-symbol s other-tables))) real-syms))
           (bucket-of (lambda (tag) (map (lambda (c) (car c)) (filter (lambda (c) (eq? (car (cdr c)) tag)) classified))))
           (unknowns (bucket-of (quote unknown)))
           (uses-core (or (member? (quote core) (map (lambda (c) (car (cdr c))) classified))
                          (atom? real-syms)))
           (uses-macro-core (member? (quote macro-expanded-core) (map (lambda (c) (car (cdr c))) classified)))
           (uses-world-host (member? (quote reasoning-world-or-host) (map (lambda (c) (car (cdr c))) classified)))
           (uses-lambda (member? (quote %uses-lambda) markers))
           (uses-let-family (member? (quote %uses-let-family) markers))
           (uses-strings-reader (filter (lambda (s) (member? s strings-reader-subset)) real-syms))
           (world-host-libraries (uniq (filter (lambda (x) (not? (equal? x (quote ()))))
                                                (map (lambda (c) (cdr (cdr c))) classified))))
           (buckets (filter (lambda (x) (not? (equal? x (quote ()))))
                      (list
                        (cond (uses-core (quote core)) (t (quote ())))
                        (cond ((or uses-lambda uses-let-family) (quote closure-application)) (t (quote ())))
                        (cond ((member? (quote S1) axioms-list) (quote exact-numbers)) (t (quote ())))
                        (cond ((not? (atom? uses-strings-reader)) (quote strings-reader)) (t (quote ())))
                        (cond ((or uses-macro-core uses-let-family) (quote macro-expanded-core)) (t (quote ())))
                        (cond (uses-world-host (quote reasoning-world-or-host)) (t (quote ())))))))
      (list (quote dependency-classification)
            (cons (quote id) id)
            (cons (quote buckets) buckets)
            (cons (quote unknown-symbols) unknowns)
            (cons (quote world-host-libraries) world-host-libraries)
            (cons (quote axiom-tagged-s1) (member? (quote S1) axioms-list))))))

; ---------------------------------------------------------------------
; Fixture pairing (same technique as scripts/oracle-batch.lisp)
; ---------------------------------------------------------------------

(def fixtures-only
  (lambda (entries)
    (cond
      ((atom? entries) () (quote ()))
      ((atom? entries) (1) (quote ()))
      ((atom? (car entries)) () (fixtures-only (cdr entries)))
      ((atom? (car entries)) (1) (fixtures-only (cdr entries)))
      (t (cond
           ((eq? (car (car entries)) (quote fixture))
            (cons (car entries) (fixtures-only (cdr entries))))
           (t (fixtures-only (cdr entries))))))))

(def process-pair
  (lambda (inventory-remaining conformance-remaining other-tables)
    (cond
      ((atom? inventory-remaining) () (quote ()))
      ((atom? inventory-remaining) (1) (quote ()))
      ((atom? conformance-remaining) () (quote ()))
      ((atom? conformance-remaining) (1) (quote ()))
      (t (let* ((invf (car inventory-remaining))
                (id (cdr (assoc (quote id) (cdr invf))))
                (conff (car conformance-remaining))
                (expr-str (cdr (assoc (quote expr) conff)))
                (axioms-entry (assoc (quote axioms) conff))
                (axioms-list (cond ((atom? axioms-entry) () (quote ()))
                                   ((atom? axioms-entry) (1) (quote ())) (t (cdr axioms-entry))))
                (record (classify-fixture id expr-str axioms-list other-tables))
                (emitted (print record)))
           (process-pair (cdr inventory-remaining) (cdr conformance-remaining) other-tables))))))

(print (cons (quote about) "dependency-classification.lisp — WSM-CONSTITUTION-DEPENDENCY-CLASSIFICATION: every tests/fixtures/inventory.lisp fixture, classified by executable dependency (core / closure-application / exact-numbers / strings-reader / macro-expanded-core / reasoning-world-or-host), generated from the live source tables, not hand-copied."))
(print (cons (quote generated) "Run: my-lisp scripts/build-dependency-classification.lisp > tests/fixtures/dependency-classification.lisp"))

(process-pair
  (fixtures-only (read-all (read-file "tests/fixtures/inventory.lisp")))
  (read-all (read-file "tests/fixtures/conformance.lisp"))
  (other-lib-tables))

(quote ())