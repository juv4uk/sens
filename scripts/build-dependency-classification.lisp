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
(визначити core-special-forms
  (як-є (quote lambda def defmacro cond print princ write-to-string read
          eval string-append string<? read-all string? symbol->string
          string->symbol string-first string-rest sha256-hex json-parse)))

; crates/my-lisp/src/eval/builtins.rs environment.define registrations.
; Derived time operations such as mono-ms, utc-now, internet-time-sync, and
; timezone-detect intentionally do not appear here: they are defined by
; lib/time.lisp. The retained host-facing time operations expose observations
; only: mono-ns, unix-time-now, ntp-query-raw, timezone-declarations-raw.
(визначити core-builtins
  (як-є (* + - / < = > abs atom car cdr cons env eq f32 f32-buffer i32
          i32-buffer make-vector max max-list min min-list mono-ns
          ntp-query-raw numeric-buffer-length numeric-buffer-map
          numeric-buffer-ref numeric-buffer-type numeric-buffer? string-slice
          timezone-declarations-raw unix-time-now vector vector-length vector-ref
          vector-set!)))

; crates/my-lisp-host/src/lib.rs register_capability calls
(визначити host-capabilities
  (як-є (load process-run read-dir read-file read-file-bytes tcp-accept
          tcp-close tcp-connect tcp-listen tcp-read tcp-write write-file
          write-file-bytes)))

; the string/reader-flavored subset of the two tables above, called out
; as its own bucket per the task description ("strings/reader")
(визначити strings-reader-subset
  (як-є (write-to-string read read-all string-append string<? string?
          symbol->string string->symbol string-first string-rest
          string-slice string-contains? string-empty? string-length
          string-prefix? digit->string number->string number->string-onto)))

; ---------------------------------------------------------------------
; Generated tables: read the real library sources, don't hand-copy them
; ---------------------------------------------------------------------

(визначити top-level-def-names
  (функція (forms)
    (110 ((010 forms) (001 ())) ((010 (001 ())) (001001 ((form (100 forms))
                (rest (top-level-def-names (решта forms))))
           (за-умовою
             ((атом? form) rest)
             
             ((тотожне? (перше form) (як-є def)) (сполучити (перше (решта form)) rest))
             ((тотожне? (перше form) (як-є defmacro)) (сполучити (перше (решта form)) rest))
             ((атом? (як-є ())) rest)))))))

(визначити symbol-names-from-file
  (функція (path)
    (top-level-def-names (читати-всі (читати-файл path)))))

(визначити core-my-symbols
  (symbol-names-from-file "lib/core.lisp"))

; every file under lib/ except core.lisp (and its .fasl cache), paired with
; the symbol names it defines -- an alist of (filename . (symbols...))
(визначити other-lib-tables
  (функція ()
    (001001 ((entries (read-dir "lib"))
           (relevant (101001
                       (функція (name)
                         (11110101 (110101010 ".lisp" (110100011 name (01011 (110100010 name) 3) (110100010 name)))
                              (0100 (11110111 name "core.lisp"))))
                       entries)))
      (відобразити (функція (name)
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
(визначити safe-car
  (функція (lst) (за-умовою ((атом? lst) (як-є ())) ((атом? (як-є ())) (перше lst)))))
(визначити safe-cdr
  (функція (lst) (за-умовою ((атом? lst) (як-є ())) ((атом? (як-є ())) (решта lst)))))

(визначити collect-symbols-leaf
  (функція (form)
    (за-умовою
      ((символ? form) (список form))
      ((атом? form) (як-є ()))
      
      ((атом? (як-є ())) (приєднати (collect-symbols-leaf (перше form)) (collect-symbols-leaf (решта form)))))))

(визначити collect-heads-each
  (функція (forms bound)
    (за-умовою ((атом? forms) (як-є ())) ((атом? (як-є ())) (приєднати (collect-heads (перше forms) bound)
                 (collect-heads-each (решта forms) bound))))))

(визначити collect-heads-cond-clauses
  (функція (clauses bound)
    (110 ((010 clauses) (001 ())) ((010 (001 ())) (001001 ((clause (100 clauses))
                (test-form (safe-car clause))
                (body-form (safe-car (safe-cdr clause)))
                (test-deps (collect-heads test-form bound))
                (body-deps (collect-heads body-form bound))
                (rest-deps (collect-heads-cond-clauses (решта clauses) bound)))
           (приєднати test-deps (приєднати body-deps rest-deps)))))))

(визначити collect-heads-let*-seq
  (функція (bindings body bound)
    (110 ((010 bindings) (collect-heads body bound)) ((010 (001 ())) (001001 ((binding (100 bindings))
                (name (safe-car binding))
                (value-form (safe-car (safe-cdr binding)))
                (value-deps (collect-heads value-form bound))
                (new-bound (сполучити name bound))
                (rest-deps (collect-heads-let*-seq (решта bindings) body new-bound)))
           (приєднати value-deps rest-deps))))))

(визначити collect-heads
  (функція (form bound)
    (за-умовою
      ((атом? form) (як-є ()))
      
      ((010 (001 ())) (001000 ((head (100 form)))
           (за-умовою
             ((11110101 (110101100 head) (101 head (001 quote)))
              (як-є ()))
             ((11110101 (110101100 head) (101 head (001 lambda)))
              (нехай-послідовно ((params (safe-car (safe-cdr form)))
                     (body (safe-cdr (safe-cdr form)))
                     (param-names (collect-symbols-leaf params))
                     (new-bound (приєднати param-names bound)))
                (сполучити (як-є %uses-lambda) (collect-heads-each body new-bound))))
             ((11110101 (110101100 head) (101 head (001 let)))
              (нехай-послідовно ((bindings (safe-car (safe-cdr form)))
                     (body (safe-car (safe-cdr (safe-cdr form))))
                     (names (відобразити (функція (b) (safe-car b)) bindings))
                     (value-forms (відобразити (функція (b) (safe-car (safe-cdr b))) bindings))
                     (value-deps (collect-heads-each value-forms bound))
                     (new-bound (приєднати names bound))
                     (body-deps (collect-heads body new-bound)))
                (сполучити (як-є %uses-lambda)
                      (сполучити (як-є %uses-let-family) (приєднати value-deps body-deps)))))
             ((11110101 (110101100 head) (101 head (001 let*)))
              (нехай-послідовно ((bindings (safe-car (safe-cdr form)))
                     (body (safe-car (safe-cdr (safe-cdr form)))))
                (сполучити (як-є %uses-lambda)
                      (сполучити (як-є %uses-let-family)
                            (collect-heads-let*-seq bindings body bound)))))
             ((11110101 (110101100 head) (101 head (001 def)))
              (нехай-послідовно ((name (safe-car (safe-cdr form)))
                     (value-form (safe-car (safe-cdr (safe-cdr form))))
                     ; def's own name is visible inside its own value-expr:
                     ; the evaluator shares one lexical frame between a def
                     ; and the closure it defines, so a self-referential
                     ; (def f (lambda (x) ... (f ...))) genuinely resolves
                     ; at call time even though f isn't bound yet when the
                     ; closure is created (crates/my-lisp/src/eval/special_forms/core.rs
                     ; evaluate_definition's own comment documents this).
                     (new-bound (сполучити name bound)))
                (collect-heads value-form new-bound)))
             ((11110101 (110101100 head) (101 head (001 defmacro)))
              (нехай-послідовно ((params (safe-car (safe-cdr (safe-cdr form))))
                     (body (safe-cdr (safe-cdr (safe-cdr form))))
                     (param-names (collect-symbols-leaf params))
                     (new-bound (приєднати param-names bound)))
                (сполучити (як-є %uses-lambda) (collect-heads-each body new-bound))))
             ((11110101 (110101100 head) (101 head (001 cond)))
              (collect-heads-cond-clauses (решта form) bound))
             ((атом? (як-є ()))
              (001001 ((head-dep (110
                                  ((0100 (110101100 head)) (001 ()))
                                  ((значення-у-списку? head bound) (як-є ()))
                                  ((атом? (як-є ())) (список head))))
                     (head-recurse (за-умовою ((атом? head) (як-є ())) ((атом? (як-є ())) (collect-heads head bound))))
                     (args-deps (collect-heads-each (решта form) bound)))
                (приєднати head-dep (приєднати head-recurse args-deps))))))))))

(визначити collect-deps-one
  (функція (form bound)
    (за-умовою
      ((110101100 form) (110 ((11101 form bound) (001 ())) ((010 (001 ())) (1110 form))))
      ((атом? (як-є ())) (collect-heads form bound)))))

; a fixture's expr text can hold MORE than one top-level form (e.g.
; "(def count-down (lambda ...)) (count-down 100000)" -- a def followed
; by a call, exactly like a real script). read-all captures every form;
; a top-level def/defmacro extends the bound-set for the forms that
; follow it in the SAME fixture, matching how they'd actually be
; evaluated in one shared environment.
(визначити collect-deps-top-seq
  (функція (forms bound)
    (110 ((010 forms) (001 ())) ((010 (001 ())) (001001 ((form (100 forms))
                (deps (collect-deps-one form bound))
                (new-bound (за-умовою
                             ((атом? form) bound)
                             
                             ((11110101 (110101100 (100 form)) (101 (100 form) (001 def)))
                              (сполучити (перше (решта form)) bound))
                             ((11110101 (110101100 (100 form)) (101 (100 form) (001 defmacro)))
                              (сполучити (перше (решта form)) bound))
                             ((атом? (як-є ())) bound))))
           (приєднати deps (collect-deps-top-seq (решта forms) new-bound)))))))

(визначити collect-deps-top
  (функція (forms)
    (collect-deps-top-seq forms (як-є ()))))

; ---------------------------------------------------------------------
; Classification of one fixture's collected raw head-symbol list against
; the known tables.
; ---------------------------------------------------------------------

(визначити is-marker?
  (функція (s)
    (11111100 (101 s (001 %uses-lambda)) (101 s (001 %uses-let-family)))))

(визначити unique-onto
  (функція (items acc)
    (за-умовою
      ((атом? items) acc)
      
      ((значення-у-списку? (перше items) acc) (unique-onto (решта items) acc))
      ((атом? (як-є ())) (unique-onto (решта items) (сполучити (перше items) acc))))))

(визначити uniq (функція (items) (unique-onto items (як-є ()))))

(визначити owning-library
  (функція (sym tables)
    (за-умовою
      ((атом? tables) (як-є ()))
      
      ((значення-у-списку? sym (решта (перше tables))) (перше (перше tables)))
      ((атом? (як-є ())) (owning-library sym (решта tables))))))

; classify one real (non-marker) symbol; returns (bucket-tag . library-or-())
(визначити classify-symbol
  (функція (sym other-tables)
    (за-умовою
      ((значення-у-списку? sym core-special-forms) (сполучити (як-є core) (як-є ())))
      ((значення-у-списку? sym core-builtins) (сполучити (як-є core) (як-є ())))
      ((значення-у-списку? sym host-capabilities) (сполучити (як-є reasoning-world-or-host) sym))
      ((значення-у-списку? sym core-my-symbols) (сполучити (як-є macro-expanded-core) (як-є ())))
      ((010 (001 ())) (001000 ((lib (owning-library sym other-tables)))
           (за-умовою
             ((11110111 lib (001 ())) (111 (001 unknown) (001 ())))
             ((атом? (як-є ())) (сполучити (як-є reasoning-world-or-host) lib))))))))

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
(визначити known-unreadable-oversized-exponent?
  (функція (expr-str)
    (11111100 (110101000 "e100001" expr-str)
        (110101000 "e-100001" expr-str))))

(визначити classify-fixture
  (функція (id expr-str axioms-list other-tables)
    (за-умовою
      ((known-unreadable-oversized-exponent? expr-str)
       (список (як-є dependency-classification)
             (сполучити (як-є id) id)
             (сполучити (як-є buckets) (як-є (core)))
             (сполучити (як-є unknown-symbols) (як-є ()))
             (сполучити (як-є world-host-libraries) (як-є ()))
             (сполучити (як-є axiom-tagged-s1) (значення-у-списку? (як-є S1) axioms-list))
             (сполучити (як-є note) "source text exceeds the reader's own decimal-literal exponent resource bound; not locally re-parsed, classified as core (the reader itself) by inspection")))
      ((атом? (як-є ())) (classify-readable-fixture id expr-str axioms-list other-tables)))))

(визначити classify-readable-fixture
  (функція (id expr-str axioms-list other-tables)
    (нехай-послідовно ((parsed-forms (читати-всі expr-str))
           (raw (collect-deps-top parsed-forms))
           (markers (відсіяти is-marker? raw))
           (real-syms (uniq (відсіяти (функція (s) (хибне? (is-marker? s))) raw)))
           (classified (відобразити (функція (s) (сполучити s (classify-symbol s other-tables))) real-syms))
           (bucket-of (функція (tag) (відобразити (функція (c) (перше c)) (відсіяти (функція (c) (тотожне? (перше (решта c)) tag)) classified))))
           (unknowns (bucket-of (як-є unknown)))
           (uses-core (11111100 (11101 (001 core) (101000 (0010 (c) (100 (011 c))) classified))
                          (хибне? (відповідь-не (атом? real-syms)))))
           (uses-macro-core (значення-у-списку? (як-є macro-expanded-core) (відобразити (функція (c) (перше (решта c))) classified)))
           (uses-world-host (значення-у-списку? (як-є reasoning-world-or-host) (відобразити (функція (c) (перше (решта c))) classified)))
           (uses-lambda (значення-у-списку? (як-є %uses-lambda) markers))
           (uses-let-family (значення-у-списку? (як-є %uses-let-family) markers))
           (uses-strings-reader (відсіяти (функція (s) (значення-у-списку? s strings-reader-subset)) real-syms))
           (world-host-libraries (uniq (101001 (0010 (x) (0100 (11110111 x (001 ()))))
                                                (відобразити (функція (c) (решта (решта c))) classified))))
           (buckets (101001 (0010 (x) (0100 (11110111 x (001 ()))))
                      (список
                        (за-умовою (uses-core (як-є core)) ((атом? (як-є ())) (як-є ())))
                        (110 ((11111100 uses-lambda uses-let-family) (001 closure-application)) ((010 (001 ())) (001 ())))
                        (110 ((11101 (001 S1) axioms-list) (001 exact-numbers)) ((010 (001 ())) (001 ())))
                        (110 ((110111011 (010 uses-strings-reader)) (001 strings-reader)) ((010 (001 ())) (001 ())))
                        (110 ((11111100 uses-macro-core uses-let-family) (001 macro-expanded-core)) ((010 (001 ())) (001 ())))
                        (за-умовою (uses-world-host (як-є reasoning-world-or-host)) ((атом? (як-є ())) (як-є ())))))))
      (список (як-є dependency-classification)
            (сполучити (як-є id) id)
            (сполучити (як-є buckets) buckets)
            (сполучити (як-є unknown-symbols) unknowns)
            (сполучити (як-є world-host-libraries) world-host-libraries)
            (сполучити (як-є axiom-tagged-s1) (значення-у-списку? (як-є S1) axioms-list))))))

; ---------------------------------------------------------------------
; Fixture pairing (same technique as scripts/oracle-batch.lisp)
; ---------------------------------------------------------------------

(визначити fixtures-only
  (функція (entries)
    (за-умовою
      ((атом? entries) (як-є ()))
      
      ((атом? (перше entries)) (fixtures-only (решта entries)))
      
      ((атом? (як-є ())) (за-умовою
           ((тотожне? (перше (перше entries)) (як-є fixture))
            (сполучити (перше entries) (fixtures-only (решта entries))))
           ((атом? (як-є ())) (fixtures-only (решта entries))))))))

(визначити process-pair
  (функція (inventory-remaining conformance-remaining other-tables)
    (за-умовою
      ((атом? inventory-remaining) (як-є ()))
      
      ((атом? conformance-remaining) (як-є ()))
      
      ((010 (001 ())) (001001 ((invf (100 inventory-remaining))
                (id (решта (знайти-за-ключем (як-є id) (решта invf))))
                (conff (перше conformance-remaining))
                (expr-str (решта (знайти-за-ключем (як-є expr) conff)))
                (axioms-entry (знайти-за-ключем (як-є axioms) conff))
                (axioms-list (за-умовою ((атом? axioms-entry) (як-є ())) ((атом? (як-є ())) (решта axioms-entry))))
                (record (classify-fixture id expr-str axioms-list other-tables))
                (emitted (11011011 record)))
           (process-pair (решта inventory-remaining) (решта conformance-remaining) other-tables))))))

(11011011 (111 (001 about) "dependency-classification.lisp — WSM-CONSTITUTION-DEPENDENCY-CLASSIFICATION: every tests/fixtures/inventory.lisp fixture, classified by executable dependency (core / closure-application / exact-numbers / strings-reader / macro-expanded-core / reasoning-world-or-host), generated from the live source tables, not hand-copied."))
(11011011 (111 (001 generated) "Run: my-lisp scripts/build-dependency-classification.lisp > tests/fixtures/dependency-classification.lisp"))

(process-pair
  (fixtures-only (110101001 (110110111 "tests/fixtures/inventory.lisp")))
  (110101001 (110110111 "tests/fixtures/conformance.lisp"))
  (other-lib-tables))

(як-є ())