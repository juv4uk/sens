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
(0011 core-special-forms
  (001 (quote lambda def defmacro cond print princ write-to-string read
          eval string-append string<? read-all string? symbol->string
          string->symbol string-first string-rest sha256-hex json-parse)))

; crates/my-lisp/src/eval/builtins.rs environment.define registrations.
; Derived time operations such as mono-ms, utc-now, internet-time-sync, and
; timezone-detect intentionally do not appear here: they are defined by
; lib/time.lisp. The retained host-facing time operations expose observations
; only: mono-ns, unix-time-now, ntp-query-raw, timezone-declarations-raw.
(0011 core-builtins
  (001 (* + - / < = > abs atom car cdr cons env eq f32 f32-buffer i32
          i32-buffer make-vector max max-list min min-list mono-ns
          ntp-query-raw numeric-buffer-length numeric-buffer-map
          numeric-buffer-ref numeric-buffer-type numeric-buffer? string-slice
          timezone-declarations-raw unix-time-now vector vector-length vector-ref
          vector-set!)))

; crates/my-lisp-host/src/lib.rs register_capability calls
(0011 host-capabilities
  (001 (load process-run read-dir read-file read-file-bytes tcp-accept
          tcp-close tcp-connect tcp-listen tcp-read tcp-write write-file
          write-file-bytes)))

; the string/reader-flavored subset of the two tables above, called out
; as its own bucket per the task description ("strings/reader")
(0011 strings-reader-subset
  (001 (write-to-string read read-all string-append string<? string?
          symbol->string string->symbol string-first string-rest
          string-slice string-contains? string-empty? string-length
          string-prefix? digit->string number->string number->string-onto)))

; ---------------------------------------------------------------------
; Generated tables: read the real library sources, don't hand-copy them
; ---------------------------------------------------------------------

(0011 top-level-def-names
  (0010 (forms)
    (110
      ((010 forms) () (001 ()))
      ((010 forms) (1) (001 ()))
      (t (001001 ((form (100 forms))
                (rest (top-level-def-names (011 forms))))
           (110
             ((010 form) () rest)
             ((010 form) (1) rest)
             ((101 (100 form) (001 def)) (111 (100 (011 form)) rest))
             ((101 (100 form) (001 defmacro)) (111 (100 (011 form)) rest))
             (t rest)))))))

(0011 symbol-names-from-file
  (0010 (path)
    (top-level-def-names (110101001 (110110111 path)))))

(0011 core-my-symbols
  (symbol-names-from-file "lib/core.lisp"))

; every file under lib/ except core.lisp (and its .fasl cache), paired with
; the symbol names it defines -- an alist of (filename . (symbols...))
(0011 other-lib-tables
  (0010 ()
    (001001 ((entries (read-dir "lib"))
           (relevant (101001
                       (0010 (name)
                         (11110101 (110101010 ".lisp" (110100011 name (01011 (110100010 name) 3) (110100010 name)))
                              (0100 (11110111 name "core.lisp"))))
                       entries)))
      (101000 (0010 (name)
             (111 name (symbol-names-from-file (110011110 "lib/" name))))
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
(0011 safe-car
  (0010 (lst) (110 ((010 lst) () (001 ()))
                      ((010 lst) (1) (001 ())) (t (100 lst)))))
(0011 safe-cdr
  (0010 (lst) (110 ((010 lst) () (001 ()))
                      ((010 lst) (1) (001 ())) (t (011 lst)))))

(0011 collect-symbols-leaf
  (0010 (form)
    (110
      ((110101100 form) (1110 form))
      ((010 form) () (001 ()))
      ((010 form) (1) (001 ()))
      (t (1111 (collect-symbols-leaf (100 form)) (collect-symbols-leaf (011 form)))))))

(0011 collect-heads-each
  (0010 (forms bound)
    (110
      ((010 forms) () (001 ()))
      ((010 forms) (1) (001 ()))
      (t (1111 (collect-heads (100 forms) bound)
                 (collect-heads-each (011 forms) bound))))))

(0011 collect-heads-cond-clauses
  (0010 (clauses bound)
    (110
      ((010 clauses) () (001 ()))
      ((010 clauses) (1) (001 ()))
      (t (001001 ((clause (100 clauses))
                (test-form (safe-car clause))
                (body-form (safe-car (safe-cdr clause)))
                (test-deps (collect-heads test-form bound))
                (body-deps (collect-heads body-form bound))
                (rest-deps (collect-heads-cond-clauses (011 clauses) bound)))
           (1111 test-deps (1111 body-deps rest-deps)))))))

(0011 collect-heads-let*-seq
  (0010 (bindings body bound)
    (110
      ((010 bindings) () (collect-heads body bound))
      ((010 bindings) (1) (collect-heads body bound))
      (t (001001 ((binding (100 bindings))
                (name (safe-car binding))
                (value-form (safe-car (safe-cdr binding)))
                (value-deps (collect-heads value-form bound))
                (new-bound (111 name bound))
                (rest-deps (collect-heads-let*-seq (011 bindings) body new-bound)))
           (1111 value-deps rest-deps))))))

(0011 collect-heads
  (0010 (form bound)
    (110
      ((010 form) () (001 ()))
      ((010 form) (1) (001 ()))
      (t (001000 ((head (100 form)))
           (110
             ((11110101 (110101100 head) (101 head (001 quote)))
              (001 ()))
             ((11110101 (110101100 head) (101 head (001 lambda)))
              (001001 ((params (safe-car (safe-cdr form)))
                     (body (safe-cdr (safe-cdr form)))
                     (param-names (collect-symbols-leaf params))
                     (new-bound (1111 param-names bound)))
                (111 (001 %uses-lambda) (collect-heads-each body new-bound))))
             ((11110101 (110101100 head) (101 head (001 let)))
              (001001 ((bindings (safe-car (safe-cdr form)))
                     (body (safe-car (safe-cdr (safe-cdr form))))
                     (names (101000 (0010 (b) (safe-car b)) bindings))
                     (value-forms (101000 (0010 (b) (safe-car (safe-cdr b))) bindings))
                     (value-deps (collect-heads-each value-forms bound))
                     (new-bound (1111 names bound))
                     (body-deps (collect-heads body new-bound)))
                (111 (001 %uses-lambda)
                      (111 (001 %uses-let-family) (1111 value-deps body-deps)))))
             ((11110101 (110101100 head) (101 head (001 let*)))
              (001001 ((bindings (safe-car (safe-cdr form)))
                     (body (safe-car (safe-cdr (safe-cdr form)))))
                (111 (001 %uses-lambda)
                      (111 (001 %uses-let-family)
                            (collect-heads-let*-seq bindings body bound)))))
             ((11110101 (110101100 head) (101 head (001 def)))
              (001001 ((name (safe-car (safe-cdr form)))
                     (value-form (safe-car (safe-cdr (safe-cdr form))))
                     ; def's own name is visible inside its own value-expr:
                     ; the evaluator shares one lexical frame between a def
                     ; and the closure it defines, so a self-referential
                     ; (def f (lambda (x) ... (f ...))) genuinely resolves
                     ; at call time even though f isn't bound yet when the
                     ; closure is created (crates/my-lisp/src/eval/special_forms/core.rs
                     ; evaluate_definition's own comment documents this).
                     (new-bound (111 name bound)))
                (collect-heads value-form new-bound)))
             ((11110101 (110101100 head) (101 head (001 defmacro)))
              (001001 ((params (safe-car (safe-cdr (safe-cdr form))))
                     (body (safe-cdr (safe-cdr (safe-cdr form))))
                     (param-names (collect-symbols-leaf params))
                     (new-bound (1111 param-names bound)))
                (111 (001 %uses-lambda) (collect-heads-each body new-bound))))
             ((11110101 (110101100 head) (101 head (001 cond)))
              (collect-heads-cond-clauses (011 form) bound))
             (t
              (001001 ((head-dep (110
                                  ((0100 (110101100 head)) (001 ()))
                                  ((11101 head bound) (001 ()))
                                  (t (1110 head))))
                     (head-recurse (110 ((010 head) () (001 ()))
                                         ((010 head) (1) (001 ())) (t (collect-heads head bound))))
                     (args-deps (collect-heads-each (011 form) bound)))
                (1111 head-dep (1111 head-recurse args-deps))))))))))

(0011 collect-deps-one
  (0010 (form bound)
    (110
      ((110101100 form) (110 ((11101 form bound) (001 ())) (t (1110 form))))
      (t (collect-heads form bound)))))

; a fixture's expr text can hold MORE than one top-level form (e.g.
; "(def count-down (lambda ...)) (count-down 100000)" -- a def followed
; by a call, exactly like a real script). read-all captures every form;
; a top-level def/defmacro extends the bound-set for the forms that
; follow it in the SAME fixture, matching how they'd actually be
; evaluated in one shared environment.
(0011 collect-deps-top-seq
  (0010 (forms bound)
    (110
      ((010 forms) () (001 ()))
      ((010 forms) (1) (001 ()))
      (t (001001 ((form (100 forms))
                (deps (collect-deps-one form bound))
                (new-bound (110
                             ((010 form) () bound)
                             ((010 form) (1) bound)
                             ((11110101 (110101100 (100 form)) (101 (100 form) (001 def)))
                              (111 (100 (011 form)) bound))
                             ((11110101 (110101100 (100 form)) (101 (100 form) (001 defmacro)))
                              (111 (100 (011 form)) bound))
                             (t bound))))
           (1111 deps (collect-deps-top-seq (011 forms) new-bound)))))))

(0011 collect-deps-top
  (0010 (forms)
    (collect-deps-top-seq forms (001 ()))))

; ---------------------------------------------------------------------
; Classification of one fixture's collected raw head-symbol list against
; the known tables.
; ---------------------------------------------------------------------

(0011 is-marker?
  (0010 (s)
    (11111100 (101 s (001 %uses-lambda)) (101 s (001 %uses-let-family)))))

(0011 unique-onto
  (0010 (items acc)
    (110
      ((010 items) () acc)
      ((010 items) (1) acc)
      ((11101 (100 items) acc) (unique-onto (011 items) acc))
      (t (unique-onto (011 items) (111 (100 items) acc))))))

(0011 uniq (0010 (items) (unique-onto items (001 ()))))

(0011 owning-library
  (0010 (sym tables)
    (110
      ((010 tables) () (001 ()))
      ((010 tables) (1) (001 ()))
      ((11101 sym (011 (100 tables))) (100 (100 tables)))
      (t (owning-library sym (011 tables))))))

; classify one real (non-marker) symbol; returns (bucket-tag . library-or-())
(0011 classify-symbol
  (0010 (sym other-tables)
    (110
      ((11101 sym core-special-forms) (111 (001 core) (001 ())))
      ((11101 sym core-builtins) (111 (001 core) (001 ())))
      ((11101 sym host-capabilities) (111 (001 reasoning-world-or-host) sym))
      ((11101 sym core-my-symbols) (111 (001 macro-expanded-core) (001 ())))
      (t (001000 ((lib (owning-library sym other-tables)))
           (110
             ((11110111 lib (001 ())) (111 (001 unknown) (001 ())))
             (t (111 (001 reasoning-world-or-host) lib))))))))

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
(0011 known-unreadable-oversized-exponent?
  (0010 (expr-str)
    (11111100 (110101000 "e100001" expr-str)
        (110101000 "e-100001" expr-str))))

(0011 classify-fixture
  (0010 (id expr-str axioms-list other-tables)
    (110
      ((known-unreadable-oversized-exponent? expr-str)
       (1110 (001 dependency-classification)
             (111 (001 id) id)
             (111 (001 buckets) (001 (core)))
             (111 (001 unknown-symbols) (001 ()))
             (111 (001 world-host-libraries) (001 ()))
             (111 (001 axiom-tagged-s1) (11101 (001 S1) axioms-list))
             (111 (001 note) "source text exceeds the reader's own decimal-literal exponent resource bound; not locally re-parsed, classified as core (the reader itself) by inspection")))
      (t (classify-readable-fixture id expr-str axioms-list other-tables)))))

(0011 classify-readable-fixture
  (0010 (id expr-str axioms-list other-tables)
    (001001 ((parsed-forms (110101001 expr-str))
           (raw (collect-deps-top parsed-forms))
           (markers (101001 is-marker? raw))
           (real-syms (uniq (101001 (0010 (s) (0100 (is-marker? s))) raw)))
           (classified (101000 (0010 (s) (111 s (classify-symbol s other-tables))) real-syms))
           (bucket-of (0010 (tag) (101000 (0010 (c) (100 c)) (101001 (0010 (c) (101 (100 (011 c)) tag)) classified))))
           (unknowns (bucket-of (001 unknown)))
           (uses-core (11111100 (11101 (001 core) (101000 (0010 (c) (100 (011 c))) classified))
                          (0100 (110111011 (010 real-syms)))))
           (uses-macro-core (11101 (001 macro-expanded-core) (101000 (0010 (c) (100 (011 c))) classified)))
           (uses-world-host (11101 (001 reasoning-world-or-host) (101000 (0010 (c) (100 (011 c))) classified)))
           (uses-lambda (11101 (001 %uses-lambda) markers))
           (uses-let-family (11101 (001 %uses-let-family) markers))
           (uses-strings-reader (101001 (0010 (s) (11101 s strings-reader-subset)) real-syms))
           (world-host-libraries (uniq (101001 (0010 (x) (0100 (11110111 x (001 ()))))
                                                (101000 (0010 (c) (011 (011 c))) classified))))
           (buckets (101001 (0010 (x) (0100 (11110111 x (001 ()))))
                      (1110
                        (110 (uses-core (001 core)) (t (001 ())))
                        (110 ((11111100 uses-lambda uses-let-family) (001 closure-application)) (t (001 ())))
                        (110 ((11101 (001 S1) axioms-list) (001 exact-numbers)) (t (001 ())))
                        (110 ((110111011 (010 uses-strings-reader)) (001 strings-reader)) (t (001 ())))
                        (110 ((11111100 uses-macro-core uses-let-family) (001 macro-expanded-core)) (t (001 ())))
                        (110 (uses-world-host (001 reasoning-world-or-host)) (t (001 ())))))))
      (1110 (001 dependency-classification)
            (111 (001 id) id)
            (111 (001 buckets) buckets)
            (111 (001 unknown-symbols) unknowns)
            (111 (001 world-host-libraries) world-host-libraries)
            (111 (001 axiom-tagged-s1) (11101 (001 S1) axioms-list))))))

; ---------------------------------------------------------------------
; Fixture pairing (same technique as scripts/oracle-batch.lisp)
; ---------------------------------------------------------------------

(0011 fixtures-only
  (0010 (entries)
    (110
      ((010 entries) () (001 ()))
      ((010 entries) (1) (001 ()))
      ((010 (100 entries)) () (fixtures-only (011 entries)))
      ((010 (100 entries)) (1) (fixtures-only (011 entries)))
      (t (110
           ((101 (100 (100 entries)) (001 fixture))
            (111 (100 entries) (fixtures-only (011 entries))))
           (t (fixtures-only (011 entries))))))))

(0011 process-pair
  (0010 (inventory-remaining conformance-remaining other-tables)
    (110
      ((010 inventory-remaining) () (001 ()))
      ((010 inventory-remaining) (1) (001 ()))
      ((010 conformance-remaining) () (001 ()))
      ((010 conformance-remaining) (1) (001 ()))
      (t (001001 ((invf (100 inventory-remaining))
                (id (011 (11100 (001 id) (011 invf))))
                (conff (100 conformance-remaining))
                (expr-str (011 (11100 (001 expr) conff)))
                (axioms-entry (11100 (001 axioms) conff))
                (axioms-list (110 ((010 axioms-entry) () (001 ()))
                                   ((010 axioms-entry) (1) (001 ())) (t (011 axioms-entry))))
                (record (classify-fixture id expr-str axioms-list other-tables))
                (emitted (11011011 record)))
           (process-pair (011 inventory-remaining) (011 conformance-remaining) other-tables))))))

(11011011 (111 (001 about) "dependency-classification.lisp — WSM-CONSTITUTION-DEPENDENCY-CLASSIFICATION: every tests/fixtures/inventory.lisp fixture, classified by executable dependency (core / closure-application / exact-numbers / strings-reader / macro-expanded-core / reasoning-world-or-host), generated from the live source tables, not hand-copied."))
(11011011 (111 (001 generated) "Run: my-lisp scripts/build-dependency-classification.lisp > tests/fixtures/dependency-classification.lisp"))

(process-pair
  (fixtures-only (110101001 (110110111 "tests/fixtures/inventory.lisp")))
  (110101001 (110110111 "tests/fixtures/conformance.lisp"))
  (other-lib-tables))

(001 ())