; Machine-readable inventory of the English-facing public surface.
; Машинно-читаний інвентар англомовної публічної поверхні.
; This file classifies names; it does not choose Ukrainian words.

(uk-surface-inventory
  (schema uk-surface-inventory/1)
  (eligibility-rules
    ((public (user-program-name documented-or-exercised-as-api))
     (internal (implementation-helper accumulator-worker bootstrap-mechanism))
     (compatibility (supported-historical-user-name))
     (predicate (returns-only-t-or-empty-for-its-valid-domain))
     (symbolic-sugar (compact-notation-over-word-first-public-name))))
  (public
    ((canon (quote atom eq cons car cdr cond))
     (necessary-forms (define lambda))
     (language-macros (defmacro))
     (compatibility-forms (def))
     (root-builtins
       (+ - * / < = > atom car cdr cons env eq
        eval f32-buffer i32-buffer json-parse make-vector
        mono-ns ntp-query-raw numeric-buffer-length numeric-buffer-map
        numeric-buffer-ref numeric-buffer-type numeric-buffer? princ print read
        read-all sha256-hex string->codepoint string->symbol string-append
        string-first string-rest string-slice string<? string? symbol->string
        timezone-declarations-raw unix-time-now vector vector-length vector-ref
        vector-set! write-to-string codepoint->string))
     ; abs/max/max-list/min/min-list moved here 2026-09-11 (from
     ; root-builtins): migrated from Rust builtins.rs to lib/core.lisp, see
     ; docs/VERTICAL-SLICE-1-ABS-MIN-MAX-2026-09-11.md. This inventory
     ; had gone stale relative to the actual implementation until
     ; corrected.
     (core-library
       (abs identity list not and or gensym pair second third fourth cadddr fifth
        caar cadr cddr length reverse append map filter reduce let equal? max
        max-list member? min min-list assoc let* nth string-empty? string-length
        string-prefix? string-contains? symbol? quotient mod <= >= number->string
        -> ->> isqrt sqrt))))
  ; Ukrainian words carry the readable surface. Mathematical marks remain
  ; optional compact notation over the same existing operations.
  (symbolic-sugar (+ - * / < = > <= >=))
  (internal
    ((bootstrap (make-macro))
     (core-library
       (length-onto reverse-onto map-onto filter-onto largest-chunk binary-fold
        nondecreasing-from? nonincreasing-from? digit->string
        number->string-onto sqrt-iter isqrt-step))))
  ; Every future Ukrainian spelling for these public predicates ends in ?.
  (public-predicates
    (atom eq < = > numeric-buffer? string<? string? not equal? member?
     string-empty? string-prefix? string-contains? symbol? <= >=)))
