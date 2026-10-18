; scripts/symbol-table.lisp — a canonical, deterministic symbol-name → numeric-id
; table for every symbol atom that appears anywhere in lib/core4.lisp, requested
; by the fpga-lisp session (2026-08-10).
;
; Problem this solves: each hand-written bootstrap .asm file (M19-M26) invents
; its own numeric symbol IDs from memory (900-913 for third, 1000-1031 for
; pair, 2000-2032 for triple, ...) with no single source of truth — already
; caused one real bug (M22, a reversed-order list) from the same class of
; error: manual bookkeeping, never checked against anything. The risk grows
; with every new bootstrap file.
;
; This is not the reader's own interning order — my-lisp makes no promise
; anywhere about what order symbols get interned in, and enforcing one just
; for this would be a new, unjustified constraint on the reader. Any stable,
; deterministic numbering solves the actual problem (a single source of
; truth to pull from instead of reinventing per file); alphabetical order is
; simplest to audit by eye and re-derive by hand if this script's output is
; ever unavailable.
;
; Walks every top-level form in lib/core4.lisp recursively, collecting every
; symbol atom encountered — function names (def targets), parameter names in
; lambda-lists, special-form keywords (quote/cond/lambda/def/...), and any
; symbol referenced in a body — not just the ~36 top-level `def` names.
; Numbers, strings, and structural nil/pairs are excluded via `symbol?`.
;
; Usage:
;   cargo run -p my-lisp-cli -- scripts/symbol-table.lisp > symbol-table.txt
; Output: one `(name . id)` pair per line, e.g. `("second" . 47)`, sorted by
; name, ids starting at 0. Convert to `.define` lines in fpga/asm/constants.inc
; is this file's own tooling's job, not this script's — the format here is
; deliberately plain data, not pre-formatted assembly.

(визначити collect-symbols-onto
  (функція (expr acc)
    (за-умовою
      ((символ? expr) (за-умовою ((значення-у-списку? expr acc) acc) ((атом? (як-є ())) (сполучити expr acc))))
      ((атом? expr) acc)
      ((атом? (як-є ())) (collect-symbols-onto (решта expr) (collect-symbols-onto (перше expr) acc))))))

(визначити collect-all-symbols
  (функція (forms acc)
    (за-умовою ((атом? forms) acc) ((атом? (як-є ())) (collect-all-symbols (решта forms) (collect-symbols-onto (перше forms) acc))))))

; Tail-recursive on purpose, not the more obvious `(cons (car sorted)
; (insert-sorted sym (cdr sorted)))`: that shape's real Rust-stack depth
; grows with list length, and blew the (debug-build) stack outright at
; 83 elements while writing this — the exact class of bug this
; project's own -onto accumulator convention (length-onto, reverse-onto,
; map-onto...) exists to avoid. Splits the list into `before`/`after`
; around the insertion point instead of building up a nested `cons`.
; Навмисно хвостово-рекурсивна, не очевидніша форма `(cons (car sorted)
; (insert-sorted sym (cdr sorted)))`: та форма росте вглиб Rust-стеку з
; довжиною списку і переповнила (debug-збірку) стеку саме на 83
; елементах під час написання цього файлу — той самий клас багу, від
; якого захищає власна -onto-конвенція проєкту. Розбиває список на
; before/after навколо точки вставки замість вкладеного cons.
(визначити insert-sorted-onto
  (функція (sym before after)
    (за-умовою
      ((атом? after) (зворот-до before (список sym)))
      ((текст-передує? (символ-у-текст sym) (символ-у-текст (перше after)))
       (зворот-до before (сполучити sym after)))
      ((атом? (як-є ())) (insert-sorted-onto sym (сполучити (перше after) before) (решта after))))))

(визначити insert-sorted
  (функція (sym sorted)
    (insert-sorted-onto sym (як-є ()) sorted)))

(визначити sort-symbols-onto
  (функція (remaining sorted)
    (за-умовою ((атом? remaining) sorted) ((атом? (як-є ())) (sort-symbols-onto (решта remaining) (insert-sorted (перше remaining) sorted))))))

(визначити sort-symbols
  (функція (symbols)
    (sort-symbols-onto symbols (як-є ()))))

(визначити print-table-onto
  (функція (symbols id)
    (за-умовою ((атом? symbols) (як-є ())) ((атом? (як-є ())) ((функція ()
            (друкувати (список (символ-у-текст (перше symbols)) id))
            (print-table-onto (решта symbols) (додати id 1))))))))

(визначити core-forms (читати-всі (читати-файл "lib/core4.lisp")))
(визначити all-symbols (collect-all-symbols core-forms (як-є ())))
(визначити sorted-symbols (sort-symbols all-symbols))

(print-table-onto sorted-symbols 0)
(як-є ())

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список LIST)
(визначити значення-у-списку? MEMBER)
(визначити читати-всі READ-ALL)
(визначити текст-передує? STRING<)
(визначити символ-у-текст SYMBOL->STRING)
(визначити символ? SYMBOL?)
(визначити зворот-до reverse-onto)
