; #1810 — minimal shared COND control law.
;
; COND does not understand arbitrary answer algebras.
; It consumes exactly the contextual one-bit predicate result:
;
;   1 -> select/evaluate expression
;   0 -> continue
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
   (no-match . structural-empty)
   (zero-empty-distinct . required)
   (three-part-clause . forbidden)
   (expected-result-field . forbidden)
   (explicit-result-equality . forbidden)
   (generic-truth-coercion . forbidden)
   (host-bool-coercion . forbidden)
   (empty-list-as-false . forbidden)
   (arbitrary-nonempty-as-true . forbidden)))