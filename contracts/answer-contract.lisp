; #1804 / #3161 — minimal shared answer/control foundation.
;
; Pure Lisp data authority. Domain-specific mathematics/reasoning live in
; their own contracts and do not redefine the shared predicate/control law.
;
; Shared law:
;   D1:1      = YES
;   D1:0      = NO
;   D3:000 () = structural EMPTY / NO-WITNESS, never predicate FALSE
;   COND      = exactly (test expression)
;               D1:1 -> select
;               D1:0 -> continue as explicit NO
;               D3:000 -> continue as EMPTY/no-witness
;               exhaustion -> D3:000
;
; Critical distinction:
;   control(D1:0)   = continue
;   control(D3:000) = continue
;   but D1:0 != D3:000
;
; Human spellings remain surface projections. Canonical identity is exact
; domain + exact bits + admitted law. No rich classifier record is a predicate
; answer and no T/NIL truthiness is active authority.

(answer-contract/3

  ((identity . D3:000)
   (role . structural-empty)
   (domain-owner . D3)
   (result-form . empty-structure/no-witness)
   (predicate-answer . no)
   (false-sentinel . no)
   (list-ground . yes)
   (control-force . non-selection)
   (distinct-from-D1-zero . yes))

  ((identity . D3:001)
   (role . quote)
   (domain-owner . D3)
   (result-form . data))

  ((identity . D3:111)
   (role . cons)
   (domain-owner . D3)
   (result-form . pair))

  ((identity . D3:100)
   (role . car)
   (domain-owner . D3)
   (input-domain . pair)
   (result-form . value))

  ((identity . D3:011)
   (role . cdr)
   (domain-owner . D3)
   (input-domain . pair)
   (result-form . value))

  ((identity . D3:010)
   (role . atom)
   (domain-owner . D3)
   (result-domain . D1)
   (result-form . predicate-one-bit)
   (yes . one)
   (no . zero)
   (empty-structure-result . one)
   (pair-result . zero)
   (non-pair-result . one)
   (rich-result . forbidden)
   (host-bool-authority . forbidden))

  ((identity . D3:101)
   (role . eq)
   (domain-owner . D3)
   (input-domain . (admitted-atom admitted-atom))
   (result-domain . (D1 D3:000))
   (result-form . partial-predicate)
   (yes . one)
   (no . zero)
   (same-atom-result . one)
   (distinct-atom-result . zero)
   (outside-domain . D3:000)
   (outside-domain-meaning . no-witness)
   (rich-result . forbidden)
   (host-bool-authority . forbidden))

  ((identity . D3:110)
   (role . cond)
   (domain-owner . D3)
   (clause-shape . (test expression))
   (test-domain . (D1:1 D1:0 D3:000))
   (select-on . D1:1)
   (skip-explicit-no . D1:0)
   (skip-no-witness . D3:000)
   (zero-equals-empty . forbidden)
   (exhaustion-result . D3:000)
   (three-part-clause . forbidden)
   (explicit-result-match . forbidden)
   (generic-truthiness . forbidden)
   (host-bool-authority . forbidden)))
