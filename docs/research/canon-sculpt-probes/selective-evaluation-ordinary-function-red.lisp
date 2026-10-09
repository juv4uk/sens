; #419 research RED probe — executable research, not semantic authority.
;
; Hypothesis: runtime branch selection can be reduced to ordinary eager
; function application without any special selective-evaluation mechanism.
;
; The function body deliberately ignores its second parameter. If ordinary
; eager application were enough to model selective evaluation, the second
; source expression would remain unevaluated. On the current evaluator it is
; evaluated before the call, so the unbound symbol prevents the body from
; returning `selected`.
;
; This falsifies only ordinary-function branching. A macro can suppress or
; rearrange source expressions, but a macro that must choose using a runtime
; query still needs some lower runtime selection mechanism; otherwise it has
; merely renamed the same semantic power.

(def choose-first-eager
  (lambda (selected unselected)
    selected))

(choose-first-eager
  (quote selected)
  canon-sculpt-unbound-branch)
