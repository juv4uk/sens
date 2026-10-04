; #1810 — minimal shared COND control law.
;
; COND does not understand arbitrary answer algebras.
; Canonical D3:011 consumes exactly:
;
;   D1:1   -> select/evaluate expression
;   D1:0   -> continue with explicit NO
;   D3:000 -> continue with EMPTY/no-witness
;
; 0 and () project to the same control action but remain distinct values.
;
; A clause is exactly:
;   (test expression)
;
; Exhaustion returns structural (), which is data and never predicate FALSE.

(control-dispatch-contract/2
  ((identity . 00000111)
   (domain-owner . control)
   (canonical-clause-shape . (test expression))
   (test-domain . (predicate-one-bit structural-empty-no-witness))
   (select-on . one)
   (skip-on . (zero structural-empty))
   (zero-equals-empty . forbidden)
   (partial-predicate-empty-witness . admitted)
   (no-match . structural-empty)
   (three-part-clause . forbidden)
   (expected-result-field . forbidden)
   (explicit-result-equality . forbidden)
   (generic-truth-coercion . forbidden)
   (host-bool-coercion . forbidden)
   (empty-list-as-false . forbidden)
   (structural-empty-as-no-witness . admitted)
   (arbitrary-nonempty-as-true . forbidden)))