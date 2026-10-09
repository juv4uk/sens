; RED research witness for #419.
; Hypothesis under test: PRIM_QUOTE could be removed by defining quote as an ordinary eager Lisp function.
; This fixture is intentionally not wired into steady-state CI and must not merge to main as semantic authority.
;
; Falsification criterion:
; In an eager evaluator, an ordinary function receives evaluated arguments. Therefore a plain function cannot implement
; (quote SYMBOL) when SYMBOL is unbound, because suppressing that evaluation is the behavior being explained.
;
; A future GREEN is valid only if it names an explicitly lower evaluation-control mechanism. Renaming quote, routing
; through a surface alias, registry lookup, macro expander that itself requires quote-equivalent control, or host AST access
; does not count.

(def quote-as-ordinary-function
  (lambda (x) x))

; If ordinary eager function application were sufficient, this would yield canon-sculpt-unbound-symbol as data.
; Expected RED on the current evaluator: the argument is evaluated before the function body and the symbol is unbound.
(quote-as-ordinary-function canon-sculpt-unbound-symbol)
