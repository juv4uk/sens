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

(0011 collect-symbols-onto
  (0010 (expr acc)
    (110
      ((SYMBOL? expr) (110 ((MEMBER expr acc) acc) ((010 (001 ())) (111 expr acc))))
      ((010 expr) acc)
      ((010 (001 ())) (collect-symbols-onto (011 expr) (collect-symbols-onto (100 expr) acc))))))

(0011 collect-all-symbols
  (0010 (forms acc)
    (110 ((010 forms) acc) ((010 (001 ())) (collect-all-symbols (011 forms) (collect-symbols-onto (100 forms) acc))))))

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
(0011 insert-sorted-onto
  (0010 (sym before after)
    (110
      ((010 after) (reverse-onto before (LIST sym)))
      ((STRING< (SYMBOL->STRING sym) (SYMBOL->STRING (100 after)))
       (reverse-onto before (111 sym after)))
      ((010 (001 ())) (insert-sorted-onto sym (111 (100 after) before) (011 after))))))

(0011 insert-sorted
  (0010 (sym sorted)
    (insert-sorted-onto sym (001 ()) sorted)))

(0011 sort-symbols-onto
  (0010 (remaining sorted)
    (110 ((010 remaining) sorted) ((010 (001 ())) (sort-symbols-onto (011 remaining) (insert-sorted (100 remaining) sorted))))))

(0011 sort-symbols
  (0010 (symbols)
    (sort-symbols-onto symbols (001 ()))))

(0011 print-table-onto
  (0010 (symbols id)
    (110 ((010 symbols) (001 ())) ((010 (001 ())) ((0010 ()
            (PRINT (LIST (SYMBOL->STRING (100 symbols)) id))
            (print-table-onto (011 symbols) (01010 id 1))))))))

(0011 core-forms (READ-ALL (READ-FILE "lib/core4.lisp")))
(0011 all-symbols (collect-all-symbols core-forms (001 ())))
(0011 sorted-symbols (sort-symbols all-symbols))

(print-table-onto sorted-symbols 0)
(001 ())