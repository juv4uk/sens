; scripts/symbol-table.lisp — a canonical, deterministic symbol-name → numeric-id
; table for every symbol atom that appears anywhere in lib/core.lisp, requested
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
; Walks every top-level form in lib/core.lisp recursively, collecting every
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

(00001001 collect-symbols-onto
  (00001000 (expr acc)
    (00000111
      ((00100011 expr) (00000111 ((00101100 expr acc) acc) (t (00000100 expr acc))))
      ((00000010 expr) () acc)
      ((00000010 expr) (1) acc)
      (t (collect-symbols-onto (00000110 expr) (collect-symbols-onto (00000101 expr) acc))))))

(00001001 collect-all-symbols
  (00001000 (forms acc)
    (00000111
      ((00000010 forms) () acc)
      ((00000010 forms) (1) acc)
      (t (collect-all-symbols (00000110 forms) (collect-symbols-onto (00000101 forms) acc))))))

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
(00001001 insert-sorted-onto
  (00001000 (sym before after)
    (00000111
      ((00000010 after) () (reverse-onto before (00100111 sym)))
      ((00000010 after) (1) (reverse-onto before (00100111 sym)))
      ((00100101 (01000010 sym) (01000010 (00000101 after)))
       (reverse-onto before (00000100 sym after)))
      (t (insert-sorted-onto sym (00000100 (00000101 after) before) (00000110 after))))))

(00001001 insert-sorted
  (00001000 (sym sorted)
    (insert-sorted-onto sym (00000001 ()) sorted)))

(00001001 sort-symbols-onto
  (00001000 (remaining sorted)
    (00000111
      ((00000010 remaining) () sorted)
      ((00000010 remaining) (1) sorted)
      (t (sort-symbols-onto (00000110 remaining) (insert-sorted (00000101 remaining) sorted))))))

(00001001 sort-symbols
  (00001000 (symbols)
    (sort-symbols-onto symbols (00000001 ()))))

(00001001 print-table-onto
  (00001000 (symbols id)
    (00000111
      ((00000010 symbols) () (00000001 ()))
      ((00000010 symbols) (1) (00000001 ()))
      (t ((00001000 ()
            (01001000 (00000100 (01000010 (00000101 symbols)) id))
            (print-table-onto (00000110 symbols) (00001100 id 1))))))))

(00001001 core-forms (01001011 (10100110 "lib/core.lisp")))
(00001001 all-symbols (collect-all-symbols core-forms (00000001 ())))
(00001001 sorted-symbols (sort-symbols all-symbols))

(print-table-onto sorted-symbols 0)
(00000001 ())
