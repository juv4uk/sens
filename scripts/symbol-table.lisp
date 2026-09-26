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

(def collect-symbols-onto
  (lambda (expr acc)
    (cond
      ((symbol? expr) (cond ((member? expr acc) acc) (t (cons expr acc))))
      ((atom? expr) () acc)
      ((atom? expr) (1) acc)
      (t (collect-symbols-onto (cdr expr) (collect-symbols-onto (car expr) acc))))))

(def collect-all-symbols
  (lambda (forms acc)
    (cond
      ((atom? forms) () acc)
      ((atom? forms) (1) acc)
      (t (collect-all-symbols (cdr forms) (collect-symbols-onto (car forms) acc))))))

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
(def insert-sorted-onto
  (lambda (sym before after)
    (cond
      ((atom? after) () (reverse-onto before (list sym)))
      ((atom? after) (1) (reverse-onto before (list sym)))
      ((string<? (symbol->string sym) (symbol->string (car after)))
       (reverse-onto before (cons sym after)))
      (t (insert-sorted-onto sym (cons (car after) before) (cdr after))))))

(def insert-sorted
  (lambda (sym sorted)
    (insert-sorted-onto sym (quote ()) sorted)))

(def sort-symbols-onto
  (lambda (remaining sorted)
    (cond
      ((atom? remaining) () sorted)
      ((atom? remaining) (1) sorted)
      (t (sort-symbols-onto (cdr remaining) (insert-sorted (car remaining) sorted))))))

(def sort-symbols
  (lambda (symbols)
    (sort-symbols-onto symbols (quote ()))))

(def print-table-onto
  (lambda (symbols id)
    (cond
      ((atom? symbols) () (quote ()))
      ((atom? symbols) (1) (quote ()))
      (t ((lambda ()
            (print (cons (symbol->string (car symbols)) id))
            (print-table-onto (cdr symbols) (+ id 1))))))))

(def core-forms (read-all (read-file "lib/core4.lisp")))
(def all-symbols (collect-all-symbols core-forms (quote ())))
(def sorted-symbols (sort-symbols all-symbols))

(print-table-onto sorted-symbols 0)
(quote ())
