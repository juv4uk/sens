; #1711/#1663 — current Lisp-owned control dispatch contract.
;
; Canonical COND is binary predicate control, not explicit-result matching.
; A clause is exactly (test expression). The test must produce the exact
; one-bit predicate result owned by SENS.
;
;   1 -> select/evaluate expression
;   0 -> continue
;
; Exhaustion returns structural (), which is data and not a predicate answer.

(control-dispatch-contract/2
  ((identity . 00000111)
   (domain-owner . control)
   (canonical-clause-shape . (test expression))
   (predicate-domain . exact-one-bit)
   (select-on . one)
   (skip-on . zero)
   (no-match . ())
   (empty-list-as-false . forbidden)
   (arbitrary-nonempty-as-true . forbidden)
   (host-bool-coercion . forbidden)
   (explicit-result-equality-dispatch . forbidden)
   (three-part-clause . forbidden)
   (graded-answer-dispatch . forbidden)))

  ((migration . current)
   (shared-core1-core4-law . required)
   (semantic-witness . issue-1709)
   (old-explicit-result-control . historical-only)))