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
(00001001 core-special-forms
  (00000001 (quote lambda def defmacro cond print princ write-to-string read
          eval string-append string<? read-all string? symbol->string
          string->symbol string-first string-rest sha256-hex json-parse)))

; crates/my-lisp/src/eval/builtins.rs environment.define registrations.
; Derived time operations such as mono-ms, utc-now, internet-time-sync, and
; timezone-detect intentionally do not appear here: they are defined by
; lib/time.lisp. The retained host-facing time operations expose observations
; only: mono-ns, unix-time-now, ntp-query-raw, timezone-declarations-raw.
(00001001 core-builtins
  (00000001 (* + - / < = > abs atom car cdr cons env eq f32 f32-buffer i32
          i32-buffer make-vector max max-list min min-list mono-ns
          ntp-query-raw numeric-buffer-length numeric-buffer-map
          numeric-buffer-ref numeric-buffer-type numeric-buffer? string-slice
          timezone-declarations-raw unix-time-now vector vector-length vector-ref
          vector-set!)))

; crates/my-lisp-host/src/lib.rs register_capability calls
(00001001 host-capabilities
  (00000001 (load process-run read-dir read-file read-file-bytes tcp-accept
          tcp-close tcp-connect tcp-listen tcp-read tcp-write write-file
          write-file-bytes)))

; the string/reader-flavored subset of the two tables above, called out
; as its own bucket per the task description ("strings/reader")
(00001001 strings-reader-subset
  (00000001 (write-to-string read read-all string-append string<? string?
          symbol->string string->symbol string-first string-rest
          string-slice string-contains? string-empty? string-length
          string-prefix? digit->string number->string number->string-onto)))

; ---------------------------------------------------------------------
; Generated tables: read the real library sources, don't hand-copy them
; ---------------------------------------------------------------------

(00001001 top-level-def-names
  (00001000 (forms)
    (00000111
      ((00000010 forms) (00000001 ()))
      (t (let* ((form (00000101 forms))
                (rest (top-level-def-names (00000110 forms))))
           (00000111
             ((00000010 form) rest)
             ((00000011 (00000101 form) (00000001 def)) (00000100 (00000101 (00000110 form)) rest))
             ((00000011 (00000101 form) (00000001 defmacro)) (00000100 (00000101 (00000110 form)) rest))
             (t rest)))))))

(00001001 symbol-names-from-file
  (00001000 (path)
    (top-level-def-names (read-all (read-file path)))))

(00001001 core-my-symbols
  (symbol-names-from-file "lib/core.lisp"))

; every file under lib/ except core.lisp (and its .fasl cache), paired with
; the symbol names it defines -- an alist of (filename . (symbols...))
(00001001 other-lib-tables
  (00001000 ()
    (let* ((entries (read-dir "lib"))
           (relevant (filter
                       (00001000 (name)
                         (and (string-prefix? ".lisp" (string-slice name (00001101 (string-length name) 3) (string-length name)))
                              (not? (equal? name "core.lisp"))))
                       entries)))
      (map (00001000 (name)
             (00000100 name (symbol-names-from-file (string-append "lib/" name))))
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
(00001001 safe-car
  (00001000 (lst) (00000111 ((00000010 lst) (00000001 ())) (t (00000101 lst)))))
(00001001 safe-cdr
  (00001000 (lst) (00000111 ((00000010 lst) (00000001 ())) (t (00000110 lst)))))

(00001001 collect-symbols-leaf
  (00001000 (form)
    (00000111
      ((symbol? form) (list form))
      ((00000010 form) (00000001 ()))
      (t (append (collect-symbols-leaf (00000101 form)) (collect-symbols-leaf (00000110 form)))))))

(00001001 collect-heads-each
  (00001000 (forms bound)
    (00000111
      ((00000010 forms) (00000001 ()))
      (t (append (collect-heads (00000101 forms) bound)
                 (collect-heads-each (00000110 forms) bound))))))

(00001001 collect-heads-cond-clauses
  (00001000 (clauses bound)
    (00000111
      ((00000010 clauses) (00000001 ()))
      (t (let* ((clause (00000101 clauses))
                (test-form (safe-car clause))
                (body-form (safe-car (safe-cdr clause)))
                (test-deps (collect-heads test-form bound))
                (body-deps (collect-heads body-form bound))
                (rest-deps (collect-heads-cond-clauses (00000110 clauses) bound)))
           (append test-deps (append body-deps rest-deps)))))))

(00001001 collect-heads-let*-seq
  (00001000 (bindings body bound)
    (00000111
      ((00000010 bindings) (collect-heads body bound))
      (t (let* ((binding (00000101 bindings))
                (name (safe-car binding))
                (value-form (safe-car (safe-cdr binding)))
                (value-deps (collect-heads value-form bound))
                (new-bound (00000100 name bound))
                (rest-deps (collect-heads-let*-seq (00000110 bindings) body new-bound)))
           (append value-deps rest-deps))))))

(00001001 collect-heads
  (00001000 (form bound)
    (00000111
      ((00000010 form) (00000001 ()))
      (t (let ((head (00000101 form)))
           (00000111
             ((and (symbol? head) (00000011 head (00000001 quote)))
              (00000001 ()))
             ((and (symbol? head) (00000011 head (00000001 lambda)))
              (let* ((params (safe-car (safe-cdr form)))
                     (body (safe-cdr (safe-cdr form)))
                     (param-names (collect-symbols-leaf params))
                     (new-bound (append param-names bound)))
                (00000100 (00000001 %uses-lambda) (collect-heads-each body new-bound))))
             ((and (symbol? head) (00000011 head (00000001 let)))
              (let* ((bindings (safe-car (safe-cdr form)))
                     (body (safe-car (safe-cdr (safe-cdr form))))
                     (names (map (00001000 (b) (safe-car b)) bindings))
                     (value-forms (map (00001000 (b) (safe-car (safe-cdr b))) bindings))
                     (value-deps (collect-heads-each value-forms bound))
                     (new-bound (append names bound))
                     (body-deps (collect-heads body new-bound)))
                (00000100 (00000001 %uses-lambda)
                      (00000100 (00000001 %uses-let-family) (append value-deps body-deps)))))
             ((and (symbol? head) (00000011 head (00000001 let*)))
              (let* ((bindings (safe-car (safe-cdr form)))
                     (body (safe-car (safe-cdr (safe-cdr form)))))
                (00000100 (00000001 %uses-lambda)
                      (00000100 (00000001 %uses-let-family)
                            (collect-heads-let*-seq bindings body bound)))))
             ((and (symbol? head) (00000011 head (00000001 def)))
              (let* ((name (safe-car (safe-cdr form)))
                     (value-form (safe-car (safe-cdr (safe-cdr form))))
                     ; def's own name is visible inside its own value-expr:
                     ; the evaluator shares one lexical frame between a def
                     ; and the closure it defines, so a self-referential
                     ; (def f (lambda (x) ... (f ...))) genuinely resolves
                     ; at call time even though f isn't bound yet when the
                     ; closure is created (crates/my-lisp/src/eval/special_forms/core.rs
                     ; evaluate_definition's own comment documents this).
                     (new-bound (00000100 name bound)))
                (collect-heads value-form new-bound)))
             ((and (symbol? head) (00000011 head (00000001 defmacro)))
              (let* ((params (safe-car (safe-cdr (safe-cdr form))))
                     (body (safe-cdr (safe-cdr (safe-cdr form))))
                     (param-names (collect-symbols-leaf params))
                     (new-bound (append param-names bound)))
                (00000100 (00000001 %uses-lambda) (collect-heads-each body new-bound))))
             ((and (symbol? head) (00000011 head (00000001 cond)))
              (collect-heads-cond-clauses (00000110 form) bound))
             (t
              (let* ((head-dep (00000111
                                  ((not? (symbol? head)) (00000001 ()))
                                  ((member? head bound) (00000001 ()))
                                  (t (list head))))
                     (head-recurse (00000111 ((00000010 head) (00000001 ())) (t (collect-heads head bound))))
                     (args-deps (collect-heads-each (00000110 form) bound)))
                (append head-dep (append head-recurse args-deps))))))))))

(00001001 collect-deps-one
  (00001000 (form bound)
    (00000111
      ((symbol? form) (00000111 ((member? form bound) (00000001 ())) (t (list form))))
      (t (collect-heads form bound)))))

; a fixture's expr text can hold MORE than one top-level form (e.g.
; "(def count-down (lambda ...)) (count-down 100000)" -- a def followed
; by a call, exactly like a real script). read-all captures every form;
; a top-level def/defmacro extends the bound-set for the forms that
; follow it in the SAME fixture, matching how they'd actually be
; evaluated in one shared environment.
(00001001 collect-deps-top-seq
  (00001000 (forms bound)
    (00000111
      ((00000010 forms) (00000001 ()))
      (t (let* ((form (00000101 forms))
                (deps (collect-deps-one form bound))
                (new-bound (00000111
                             ((00000010 form) bound)
                             ((and (symbol? (00000101 form)) (00000011 (00000101 form) (00000001 def)))
                              (00000100 (00000101 (00000110 form)) bound))
                             ((and (symbol? (00000101 form)) (00000011 (00000101 form) (00000001 defmacro)))
                              (00000100 (00000101 (00000110 form)) bound))
                             (t bound))))
           (append deps (collect-deps-top-seq (00000110 forms) new-bound)))))))

(00001001 collect-deps-top
  (00001000 (forms)
    (collect-deps-top-seq forms (00000001 ()))))

; ---------------------------------------------------------------------
; Classification of one fixture's collected raw head-symbol list against
; the known tables.
; ---------------------------------------------------------------------

(00001001 is-marker?
  (00001000 (s)
    (or (00000011 s (00000001 %uses-lambda)) (00000011 s (00000001 %uses-let-family)))))

(00001001 unique-onto
  (00001000 (items acc)
    (00000111
      ((00000010 items) acc)
      ((member? (00000101 items) acc) (unique-onto (00000110 items) acc))
      (t (unique-onto (00000110 items) (00000100 (00000101 items) acc))))))

(00001001 uniq (00001000 (items) (unique-onto items (00000001 ()))))

(00001001 owning-library
  (00001000 (sym tables)
    (00000111
      ((00000010 tables) (00000001 ()))
      ((member? sym (00000110 (00000101 tables))) (00000101 (00000101 tables)))
      (t (owning-library sym (00000110 tables))))))

; classify one real (non-marker) symbol; returns (bucket-tag . library-or-())
(00001001 classify-symbol
  (00001000 (sym other-tables)
    (00000111
      ((member? sym core-special-forms) (00000100 (00000001 core) (00000001 ())))
      ((member? sym core-builtins) (00000100 (00000001 core) (00000001 ())))
      ((member? sym host-capabilities) (00000100 (00000001 reasoning-world-or-host) sym))
      ((member? sym core-my-symbols) (00000100 (00000001 macro-expanded-core) (00000001 ())))
      (t (let ((lib (owning-library sym other-tables)))
           (00000111
             ((equal? lib (00000001 ())) (00000100 (00000001 unknown) (00000001 ())))
             (t (00000100 (00000001 reasoning-world-or-host) lib))))))))

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
(00001001 known-unreadable-oversized-exponent?
  (00001000 (expr-str)
    (or (string-contains? "e100001" expr-str)
        (string-contains? "e-100001" expr-str))))

(00001001 classify-fixture
  (00001000 (id expr-str axioms-list other-tables)
    (00000111
      ((known-unreadable-oversized-exponent? expr-str)
       (list (00000001 dependency-classification)
             (00000100 (00000001 id) id)
             (00000100 (00000001 buckets) (00000001 (core)))
             (00000100 (00000001 unknown-symbols) (00000001 ()))
             (00000100 (00000001 world-host-libraries) (00000001 ()))
             (00000100 (00000001 axiom-tagged-s1) (member? (00000001 S1) axioms-list))
             (00000100 (00000001 note) "source text exceeds the reader's own decimal-literal exponent resource bound; not locally re-parsed, classified as core (the reader itself) by inspection")))
      (t (classify-readable-fixture id expr-str axioms-list other-tables)))))

(00001001 classify-readable-fixture
  (00001000 (id expr-str axioms-list other-tables)
    (let* ((parsed-forms (read-all expr-str))
           (raw (collect-deps-top parsed-forms))
           (markers (filter is-marker? raw))
           (real-syms (uniq (filter (00001000 (s) (not? (is-marker? s))) raw)))
           (classified (map (00001000 (s) (00000100 s (classify-symbol s other-tables))) real-syms))
           (bucket-of (00001000 (tag) (map (00001000 (c) (00000101 c)) (filter (00001000 (c) (00000011 (00000101 (00000110 c)) tag)) classified))))
           (unknowns (bucket-of (00000001 unknown)))
           (uses-core (or (member? (00000001 core) (map (00001000 (c) (00000101 (00000110 c))) classified))
                          (00000010 real-syms)))
           (uses-macro-core (member? (00000001 macro-expanded-core) (map (00001000 (c) (00000101 (00000110 c))) classified)))
           (uses-world-host (member? (00000001 reasoning-world-or-host) (map (00001000 (c) (00000101 (00000110 c))) classified)))
           (uses-lambda (member? (00000001 %uses-lambda) markers))
           (uses-let-family (member? (00000001 %uses-let-family) markers))
           (uses-strings-reader (filter (00001000 (s) (member? s strings-reader-subset)) real-syms))
           (world-host-libraries (uniq (filter (00001000 (x) (not? (equal? x (00000001 ()))))
                                                (map (00001000 (c) (00000110 (00000110 c))) classified))))
           (buckets (filter (00001000 (x) (not? (equal? x (00000001 ()))))
                      (list
                        (00000111 (uses-core (00000001 core)) (t (00000001 ())))
                        (00000111 ((or uses-lambda uses-let-family) (00000001 closure-application)) (t (00000001 ())))
                        (00000111 ((member? (00000001 S1) axioms-list) (00000001 exact-numbers)) (t (00000001 ())))
                        (00000111 ((not? (00000010 uses-strings-reader)) (00000001 strings-reader)) (t (00000001 ())))
                        (00000111 ((or uses-macro-core uses-let-family) (00000001 macro-expanded-core)) (t (00000001 ())))
                        (00000111 (uses-world-host (00000001 reasoning-world-or-host)) (t (00000001 ())))))))
      (list (00000001 dependency-classification)
            (00000100 (00000001 id) id)
            (00000100 (00000001 buckets) buckets)
            (00000100 (00000001 unknown-symbols) unknowns)
            (00000100 (00000001 world-host-libraries) world-host-libraries)
            (00000100 (00000001 axiom-tagged-s1) (member? (00000001 S1) axioms-list))))))

; ---------------------------------------------------------------------
; Fixture pairing (same technique as scripts/oracle-batch.lisp)
; ---------------------------------------------------------------------

(00001001 fixtures-only
  (00001000 (entries)
    (00000111
      ((00000010 entries) (00000001 ()))
      ((00000010 (00000101 entries)) (fixtures-only (00000110 entries)))
      (t (00000111
           ((00000011 (00000101 (00000101 entries)) (00000001 fixture))
            (00000100 (00000101 entries) (fixtures-only (00000110 entries))))
           (t (fixtures-only (00000110 entries))))))))

(00001001 process-pair
  (00001000 (inventory-remaining conformance-remaining other-tables)
    (00000111
      ((00000010 inventory-remaining) (00000001 ()))
      ((00000010 conformance-remaining) (00000001 ()))
      (t (let* ((invf (00000101 inventory-remaining))
                (id (00000110 (assoc (00000001 id) (00000110 invf))))
                (conff (00000101 conformance-remaining))
                (expr-str (00000110 (assoc (00000001 expr) conff)))
                (axioms-entry (assoc (00000001 axioms) conff))
                (axioms-list (00000111 ((00000010 axioms-entry) (00000001 ())) (t (00000110 axioms-entry))))
                (record (classify-fixture id expr-str axioms-list other-tables))
                (emitted (print record)))
           (process-pair (00000110 inventory-remaining) (00000110 conformance-remaining) other-tables))))))

(print (00000100 (00000001 about) "dependency-classification.lisp — WSM-CONSTITUTION-DEPENDENCY-CLASSIFICATION: every tests/fixtures/inventory.lisp fixture, classified by executable dependency (core / closure-application / exact-numbers / strings-reader / macro-expanded-core / reasoning-world-or-host), generated from the live source tables, not hand-copied."))
(print (00000100 (00000001 generated) "Run: my-lisp scripts/build-dependency-classification.lisp > tests/fixtures/dependency-classification.lisp"))

(process-pair
  (fixtures-only (read-all (read-file "tests/fixtures/inventory.lisp")))
  (read-all (read-file "tests/fixtures/conformance.lisp"))
  (other-lib-tables))

(00000001 ())