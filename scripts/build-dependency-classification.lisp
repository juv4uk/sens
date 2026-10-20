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
(визначити особливі-форми-ядра
  (як-є (quote lambda def defmacro cond print princ write-to-string read
          eval string-append string<? read-all string? symbol->string
          string->symbol string-first string-rest sha256-hex json-parse)))

; crates/my-lisp/src/eval/builtins.rs environment.define registrations.
; Derived time operations such as mono-ms, utc-now, internet-time-sync, and
; timezone-detect intentionally do not appear here: they are defined by
; lib/time.lisp. The retained host-facing time operations expose observations
; only: mono-ns, unix-time-now, ntp-query-raw, timezone-declarations-raw.
(визначити вбудовані-функції-ядра
  (як-є (* + - / < = > abs atom car cdr cons env eq f32 f32-buffer i32
          i32-buffer make-vector max max-list min min-list mono-ns
          ntp-query-raw numeric-buffer-length numeric-buffer-map
          numeric-buffer-ref numeric-buffer-type numeric-buffer? string-slice
          timezone-declarations-raw unix-time-now vector vector-length vector-ref
          vector-set!)))

; crates/my-lisp-host/src/lib.rs register_capability calls
(визначити можливості-зовнішнього-виконавця
  (як-є (load process-run read-dir read-file read-file-bytes tcp-accept
          tcp-close tcp-connect tcp-listen tcp-read tcp-write write-file
          записати-байти-файла)))

; the string/reader-flavored subset of the two tables above, called out
; as its own bucket per the task description ("strings/reader")
(визначити засоби-рядків-і-читача
  (як-є (write-to-string read read-all string-append string<? string?
          symbol->string string->symbol string-first string-rest
          string-slice string-contains? string-empty? string-length
          string-prefix? взяти-десятковий-символ number->string number->string-onto)))

; ---------------------------------------------------------------------
; Generated tables: read the real library sources, don't hand-copy them
; ---------------------------------------------------------------------

(визначити назви-визначень-верхнього-рівня
  (функція (форми)
    (110 ((010 форми) (001 ())) ((010 (001 ())) (001001 ((форма (100 форми))
                (решта-визначень (назви-визначень-верхнього-рівня (решта форми))))
           (за-умовою
             ((атом? форма) решта-визначень)
             
             ((тотожне? (перше форма) (як-є def)) (сполучити (перше (решта форма)) решта-визначень))
             ((тотожне? (перше форма) (як-є defmacro)) (сполучити (перше (решта форма)) решта-визначень))
             ((атом? (як-є ())) решта-визначень)))))))

(визначити назви-символів-з-файла
  (функція (шлях)
    (назви-визначень-верхнього-рівня (читати-всі (читати-файл шлях)))))

(визначити символи-основної-бібліотеки
  (назви-символів-з-файла "lib/core.lisp"))

; every file under lib/ except core.lisp (and its .fasl cache), paired with
; the symbol names it defines -- an alist of (filename . (symbols...))
(визначити таблиці-інших-бібліотек
  (функція ()
    (001001 ((записи (read-dir "lib"))
           (відповідні (101001
                       (функція (назва)
                         (11110101 (110101010 ".lisp" (110100011 назва (01011 (110100010 назва) 3) (110100010 назва)))
                              (0100 (11110111 назва "core.lisp"))))
                       записи)))
      (відобразити (функція (назва)
             (111 назва (назви-символів-з-файла (110011110 "lib/" назва))))
           відповідні))))

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
(визначити безпечне-перше
  (функція (список-значень) (за-умовою ((атом? список-значень) (як-є ())) ((атом? (як-є ())) (перше список-значень)))))
(визначити безпечна-решта
  (функція (список-значень) (за-умовою ((атом? список-значень) (як-є ())) ((атом? (як-є ())) (решта список-значень)))))

(визначити зібрати-символи-з-листків
  (функція (форма)
    (за-умовою
      ((символ? форма) (список форма))
      ((атом? форма) (як-є ()))
      
      ((атом? (як-є ())) (приєднати (зібрати-символи-з-листків (перше форма)) (зібрати-символи-з-листків (решта форма)))))))

(визначити зібрати-голови-кожного
  (функція (форми зв'язані)
    (за-умовою ((атом? форми) (як-є ())) ((атом? (як-є ())) (приєднати (зібрати-викличні-голови (перше форми) зв'язані)
                 (зібрати-голови-кожного (решта форми) зв'язані))))))

(визначити зібрати-голови-клауз-умови
  (функція (клаузи зв'язані)
    (110 ((010 клаузи) (001 ())) ((010 (001 ())) (001001 ((клауза (100 клаузи))
                (форма-умови (безпечне-перше клауза))
                (форма-тіла (безпечне-перше (безпечна-решта клауза)))
                (залежності-умови (зібрати-викличні-голови форма-умови зв'язані))
                (залежності-тіла (зібрати-викличні-голови форма-тіла зв'язані))
                (залежності-решти (зібрати-голови-клауз-умови (решта клаузи) зв'язані)))
           (приєднати залежності-умови (приєднати залежності-тіла залежності-решти)))))))

(визначити зібрати-голови-послідовного-зв'язування
  (функція (зв'язування тіло зв'язані)
    (110 ((010 зв'язування) (зібрати-викличні-голови тіло зв'язані)) ((010 (001 ())) (001001 ((зв'язок (100 зв'язування))
                (назва (безпечне-перше зв'язок))
                (форма-значення (безпечне-перше (безпечна-решта зв'язок)))
                (залежності-значення (зібрати-викличні-голови форма-значення зв'язані))
                (нові-зв'язані (сполучити назва зв'язані))
                (залежності-решти (зібрати-голови-послідовного-зв'язування (решта зв'язування) тіло нові-зв'язані)))
           (приєднати залежності-значення залежності-решти))))))

(визначити зібрати-викличні-голови
  (функція (форма зв'язані)
    (за-умовою
      ((атом? форма) (як-є ()))
      
      ((010 (001 ())) (001000 ((голова (100 форма)))
           (за-умовою
             ((11110101 (110101100 голова) (101 голова (001 quote)))
              (як-є ()))
             ((11110101 (110101100 голова) (101 голова (001 lambda)))
              (нехай-послідовно ((параметри (безпечне-перше (безпечна-решта форма)))
                     (тіло (безпечна-решта (безпечна-решта форма)))
                     (назви-параметрів (зібрати-символи-з-листків параметри))
                     (нові-зв'язані (приєднати назви-параметрів зв'язані)))
                (сполучити (як-є %uses-lambda) (зібрати-голови-кожного тіло нові-зв'язані))))
             ((11110101 (110101100 голова) (101 голова (001 let)))
              (нехай-послідовно ((зв'язування (безпечне-перше (безпечна-решта форма)))
                     (тіло (безпечне-перше (безпечна-решта (безпечна-решта форма))))
                     (назви (відобразити (функція (зв'язок-пара) (безпечне-перше зв'язок-пара)) зв'язування))
                     (форми-значень (відобразити (функція (зв'язок-пара) (безпечне-перше (безпечна-решта зв'язок-пара))) зв'язування))
                     (залежності-значення (зібрати-голови-кожного форми-значень зв'язані))
                     (нові-зв'язані (приєднати назви зв'язані))
                     (залежності-тіла (зібрати-викличні-голови тіло нові-зв'язані)))
                (сполучити (як-є %uses-lambda)
                      (сполучити (як-є %uses-let-family) (приєднати залежності-значення залежності-тіла)))))
             ((11110101 (110101100 голова) (101 голова (001 let*)))
              (нехай-послідовно ((зв'язування (безпечне-перше (безпечна-решта форма)))
                     (тіло (безпечне-перше (безпечна-решта (безпечна-решта форма)))))
                (сполучити (як-є %uses-lambda)
                      (сполучити (як-є %uses-let-family)
                            (зібрати-голови-послідовного-зв'язування зв'язування тіло зв'язані)))))
             ((11110101 (110101100 голова) (101 голова (001 def)))
              (нехай-послідовно ((назва (безпечне-перше (безпечна-решта форма)))
                     (форма-значення (безпечне-перше (безпечна-решта (безпечна-решта форма))))
                     ; def's own name is visible inside its own value-expr:
                     ; the evaluator shares one lexical frame between a def
                     ; and the closure it defines, so a self-referential
                     ; (def f (lambda (x) ... (f ...))) genuinely resolves
                     ; at call time even though f isn't bound yet when the
                     ; closure is created (crates/my-lisp/src/eval/special_forms/core.rs
                     ; evaluate_definition's own comment documents this).
                     (нові-зв'язані (сполучити назва зв'язані)))
                (зібрати-викличні-голови форма-значення нові-зв'язані)))
             ((11110101 (110101100 голова) (101 голова (001 defmacro)))
              (нехай-послідовно ((параметри (безпечне-перше (безпечна-решта (безпечна-решта форма))))
                     (тіло (безпечна-решта (безпечна-решта (безпечна-решта форма))))
                     (назви-параметрів (зібрати-символи-з-листків параметри))
                     (нові-зв'язані (приєднати назви-параметрів зв'язані)))
                (сполучити (як-є %uses-lambda) (зібрати-голови-кожного тіло нові-зв'язані))))
             ((11110101 (110101100 голова) (101 голова (001 cond)))
              (зібрати-голови-клауз-умови (решта форма) зв'язані))
             ((атом? (як-є ()))
              (001001 ((залежність-голови (110
                                  ((0100 (110101100 голова)) (001 ()))
                                  ((значення-у-списку? голова зв'язані) (як-є ()))
                                  ((атом? (як-є ())) (список голова))))
                     (обхід-голови (за-умовою ((атом? голова) (як-є ())) ((атом? (як-є ())) (зібрати-викличні-голови голова зв'язані))))
                     (залежності-аргументів (зібрати-голови-кожного (решта форма) зв'язані)))
                (приєднати залежність-голови (приєднати обхід-голови залежності-аргументів))))))))))

(визначити зібрати-залежності-однієї-форми
  (функція (форма зв'язані)
    (за-умовою
      ((110101100 форма) (110 ((11101 форма зв'язані) (001 ())) ((010 (001 ())) (1110 форма))))
      ((атом? (як-є ())) (зібрати-викличні-голови форма зв'язані)))))

; a fixture's expr text can hold MORE than one top-level form (e.g.
; "(def count-down (lambda ...)) (count-down 100000)" -- a def followed
; by a call, exactly like a real script). read-all captures every form;
; a top-level def/defmacro extends the bound-set for the forms that
; follow it in the SAME fixture, matching how they'd actually be
; evaluated in one shared environment.
(визначити зібрати-залежності-верхнього-рівня-послідовно
  (функція (форми зв'язані)
    (110 ((010 форми) (001 ())) ((010 (001 ())) (001001 ((форма (100 форми))
                (залежності (зібрати-залежності-однієї-форми форма зв'язані))
                (нові-зв'язані (за-умовою
                             ((атом? форма) зв'язані)
                             
                             ((11110101 (110101100 (100 форма)) (101 (100 форма) (001 def)))
                              (сполучити (перше (решта форма)) зв'язані))
                             ((11110101 (110101100 (100 форма)) (101 (100 форма) (001 defmacro)))
                              (сполучити (перше (решта форма)) зв'язані))
                             ((атом? (як-є ())) зв'язані))))
           (приєднати залежності (зібрати-залежності-верхнього-рівня-послідовно (решта форми) нові-зв'язані)))))))

(визначити зібрати-залежності-верхнього-рівня
  (функція (форми)
    (зібрати-залежності-верхнього-рівня-послідовно форми (як-є ()))))

; ---------------------------------------------------------------------
; Classification of one fixture's collected raw head-symbol list against
; the known tables.
; ---------------------------------------------------------------------

(визначити маркер-залежності?
  (функція (символ-значення)
    (11111100 (101 символ-значення (001 %uses-lambda)) (101 символ-значення (001 %uses-let-family)))))

(визначити унікальні-до
  (функція (елементи накопичувач)
    (за-умовою
      ((атом? елементи) накопичувач)
      
      ((значення-у-списку? (перше елементи) накопичувач) (унікальні-до (решта елементи) накопичувач))
      ((атом? (як-є ())) (унікальні-до (решта елементи) (сполучити (перше елементи) накопичувач))))))

(визначити унікальні (функція (елементи) (унікальні-до елементи (як-є ()))))

(визначити бібліотека-власник
  (функція (символ таблиці)
    (за-умовою
      ((атом? таблиці) (як-є ()))
      
      ((значення-у-списку? символ (решта (перше таблиці))) (перше (перше таблиці)))
      ((атом? (як-є ())) (бібліотека-власник символ (решта таблиці))))))

; classify one real (non-marker) symbol; returns (bucket-tag . library-or-())
(визначити класифікувати-символ
  (функція (символ інші-таблиці)
    (за-умовою
      ((значення-у-списку? символ особливі-форми-ядра) (сполучити (як-є core) (як-є ())))
      ((значення-у-списку? символ вбудовані-функції-ядра) (сполучити (як-є core) (як-є ())))
      ((значення-у-списку? символ можливості-зовнішнього-виконавця) (сполучити (як-є reasoning-world-or-host) символ))
      ((значення-у-списку? символ символи-основної-бібліотеки) (сполучити (як-є macro-expanded-core) (як-є ())))
      ((010 (001 ())) (001000 ((бібліотека (бібліотека-власник символ інші-таблиці)))
           (за-умовою
             ((11110111 бібліотека (001 ())) (111 (001 unknown) (001 ())))
             ((атом? (як-є ())) (сполучити (як-є reasoning-world-or-host) бібліотека))))))))

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
(визначити відомий-нечитаний-великий-показник?
  (функція (текст-виразу)
    (11111100 (110101000 "e100001" текст-виразу)
        (110101000 "e-100001" текст-виразу))))

(визначити класифікувати-приклад
  (функція (ідентифікатор текст-виразу перелік-аксіом інші-таблиці)
    (за-умовою
      ((відомий-нечитаний-великий-показник? текст-виразу)
       (список (як-є dependency-classification)
             (сполучити (як-є id) ідентифікатор)
             (сполучити (як-є buckets) (як-є (core)))
             (сполучити (як-є unknown-symbols) (як-є ()))
             (сполучити (як-є world-host-libraries) (як-є ()))
             (сполучити (як-є axiom-tagged-s1) (значення-у-списку? (як-є S1) перелік-аксіом))
             (сполучити (як-є note) "source text exceeds the reader's own decimal-literal exponent resource bound; not locally re-parsed, classified as core (the reader itself) by inspection")))
      ((атом? (як-є ())) (класифікувати-читаний-приклад ідентифікатор текст-виразу перелік-аксіом інші-таблиці)))))

(визначити класифікувати-читаний-приклад
  (функція (ідентифікатор текст-виразу перелік-аксіом інші-таблиці)
    (нехай-послідовно ((прочитані-форми (читати-всі текст-виразу))
           (сирі-залежності (зібрати-залежності-верхнього-рівня прочитані-форми))
           (маркери (відсіяти маркер-залежності? сирі-залежності))
           (справжні-символи (унікальні (відсіяти (функція (символ-значення) (хибне? (маркер-залежності? символ-значення))) сирі-залежності)))
           (класифіковані (відобразити (функція (символ-значення) (сполучити символ-значення (класифікувати-символ символ-значення інші-таблиці))) справжні-символи))
           (отримати-категорію (функція (позначка) (відобразити (функція (елемент) (перше елемент)) (відсіяти (функція (елемент) (тотожне? (перше (решта елемент)) позначка)) класифіковані))))
           (невідомі-символи (отримати-категорію (як-є unknown)))
           (використовує-ядро (11111100 (11101 (001 core) (101000 (0010 (елемент) (100 (011 елемент))) класифіковані))
                          (хибне? (відповідь-не (атом? справжні-символи)))))
           (використовує-макросне-ядро (значення-у-списку? (як-є macro-expanded-core) (відобразити (функція (елемент) (перше (решта елемент))) класифіковані)))
           (використовує-зовнішній-світ (значення-у-списку? (як-є reasoning-world-or-host) (відобразити (функція (елемент) (перше (решта елемент))) класифіковані)))
           (використовує-функцію (значення-у-списку? (як-є %uses-lambda) маркери))
           (використовує-зв'язування (значення-у-списку? (як-є %uses-let-family) маркери))
           (використовує-рядки-читач (відсіяти (функція (символ-значення) (значення-у-списку? символ-значення засоби-рядків-і-читача)) справжні-символи))
           (бібліотеки-зовнішнього-світу (унікальні (101001 (0010 (значення) (0100 (11110111 значення (001 ()))))
                                                (відобразити (функція (елемент) (решта (решта елемент))) класифіковані))))
           (категорії (101001 (0010 (значення) (0100 (11110111 значення (001 ()))))
                      (список
                        (за-умовою (використовує-ядро (як-є core)) ((атом? (як-є ())) (як-є ())))
                        (110 ((11111100 використовує-функцію використовує-зв'язування) (001 closure-application)) ((010 (001 ())) (001 ())))
                        (110 ((11101 (001 S1) перелік-аксіом) (001 exact-numbers)) ((010 (001 ())) (001 ())))
                        (110 ((110111011 (010 використовує-рядки-читач)) (001 strings-reader)) ((010 (001 ())) (001 ())))
                        (110 ((11111100 використовує-макросне-ядро використовує-зв'язування) (001 macro-expanded-core)) ((010 (001 ())) (001 ())))
                        (за-умовою (використовує-зовнішній-світ (як-є reasoning-world-or-host)) ((атом? (як-є ())) (як-є ())))))))
      (список (як-є dependency-classification)
            (сполучити (як-є id) ідентифікатор)
            (сполучити (як-є buckets) категорії)
            (сполучити (як-є unknown-symbols) невідомі-символи)
            (сполучити (як-є world-host-libraries) бібліотеки-зовнішнього-світу)
            (сполучити (як-є axiom-tagged-s1) (значення-у-списку? (як-є S1) перелік-аксіом))))))

; ---------------------------------------------------------------------
; Fixture pairing (same technique as scripts/oracle-batch.lisp)
; ---------------------------------------------------------------------

(визначити тільки-приклади
  (функція (записи)
    (за-умовою
      ((атом? записи) (як-є ()))
      
      ((атом? (перше записи)) (тільки-приклади (решта записи)))
      
      ((атом? (як-є ())) (за-умовою
           ((тотожне? (перше (перше записи)) (як-є fixture))
            (сполучити (перше записи) (тільки-приклади (решта записи))))
           ((атом? (як-є ())) (тільки-приклади (решта записи))))))))

(визначити обробити-пару-прикладів
  (функція (залишок-інвентарю залишок-прикладів інші-таблиці)
    (за-умовою
      ((атом? залишок-інвентарю) (як-є ()))
      
      ((атом? залишок-прикладів) (як-є ()))
      
      ((010 (001 ())) (001001 ((запис-інвентарю (100 залишок-інвентарю))
                (ідентифікатор (решта (знайти-за-ключем (як-є id) (решта запис-інвентарю))))
                (приклад-відповідності (перше залишок-прикладів))
                (текст-виразу (решта (знайти-за-ключем (як-є expr) приклад-відповідності)))
                (запис-аксіом (знайти-за-ключем (як-є axioms) приклад-відповідності))
                (перелік-аксіом (за-умовою ((атом? запис-аксіом) (як-є ())) ((атом? (як-є ())) (решта запис-аксіом))))
                (запис-результату (класифікувати-приклад ідентифікатор текст-виразу перелік-аксіом інші-таблиці))
                (виведене (11011011 запис-результату)))
           (обробити-пару-прикладів (решта залишок-інвентарю) (решта залишок-прикладів) інші-таблиці))))))

(11011011 (111 (001 about) "dependency-classification.lisp — WSM-CONSTITUTION-DEPENDENCY-CLASSIFICATION: every tests/fixtures/inventory.lisp fixture, classified by executable dependency (core / closure-application / exact-numbers / strings-reader / macro-expanded-core / reasoning-world-or-host), generated from the live source tables, not hand-copied."))
(11011011 (111 (001 generated) "Run: my-lisp scripts/build-dependency-classification.lisp > tests/fixtures/dependency-classification.lisp"))

(обробити-пару-прикладів
  (тільки-приклади (110101001 (110110111 "tests/fixtures/inventory.lisp")))
  (110101001 (110110111 "tests/fixtures/conformance.lisp"))
  (таблиці-інших-бібліотек))

(як-є ())