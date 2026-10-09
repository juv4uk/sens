; #419 research RED probe — executable research, not semantic authority.
;
; Hypothesis: PRIM_QUOTE can be replaced by an ordinary eager Lisp function.
; Falsification: an ordinary function receives evaluated arguments, so an
; unbound symbol cannot arrive at the body as source data. That suppression
; of evaluation is exactly the behavior under explanation.
;
; This experiment falsifies only the ordinary-function route. It does NOT
; prove quote irreducible; a smaller explicitly declared evaluation-control
; mechanism remains a valid research question.

(def quote-as-ordinary-function
  (lambda (x) x))

; Predicted observation on the current eager evaluator: RED / UnknownSymbol
; before the body can return the symbol as data.
(quote-as-ordinary-function canon-sculpt-unbound-symbol)
