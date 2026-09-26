; #217 — Lisp-owned explicit control-dispatch contract.
;
; Canonical control does not coerce arbitrary values to truth. A clause names
; both the query to evaluate and the exact domain result that selects it.
;
; Conceptual clause shape:
;   (query expected-result expression)
;
; Dispatch law:
;   actual = eval(query)
;   actual structurally equals expected-result -> select expression
;   otherwise -> continue
;   no matching clause -> ()
;
; This first contract ratifies shape only. Historical two-part T/NIL cond is
; compatibility debt until migrated; it is not canonical semantic authority.

(control-dispatch-contract/1
  ((identity . "0007")
   (domain-owner . control-consumer)
   (canonical-clause-shape . (query expected-result expression))
   (selection-rule . explicit-result-equality)
   (generic-truth-coercion . forbidden)
   (host-bool-coercion . forbidden)
   (empty-list-as-false . forbidden)
   (arbitrary-nonempty-as-true . forbidden)
   (no-match . ()))

  ((result-domain . exact-q-decision)
   (admitted-results . (0/1 1/1))
   (dispatch . explicit-result-equality))

  ((result-domain . structural-kind)
   (admitted-results . (()
                        (0)
                        (1)))
   (dispatch . explicit-result-equality))

  ((result-domain . identity-relation)
   (admitted-results . ((1)
                        (0)))
   (dispatch . explicit-result-equality))

  ((compatibility . historical-two-part-cond)
   (status . migration-only)
   (semantic-authority . forbidden)
   (uses-generic-truthiness . yes)
   (retire-after . library-migration)))
