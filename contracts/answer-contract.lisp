; #1804 — minimal shared answer/control foundation.
;
; Pure Lisp data authority. Domain-specific mathematics/reasoning live in
; their own contracts and do not redefine the shared predicate/control law.
;
; Shared law:
;   ()        = structural empty, never predicate FALSE
;   predicate = exact one contextual bit: 0 NO / 1 YES
;   COND      = exactly (test expression), consuming PredicateBit only
;
; Human spellings remain surface projections. Function identity remains exact
; Function8. No rich classifier record is a predicate answer.

(answer-contract/2

  ((identity . structural-empty)
   (domain-owner . structure)
   (result-form . empty-structure)
   (predicate-answer . no)
   (false-sentinel . no))

  ((identity . 00000001)
   (domain-owner . structure)
   (result-form . data))

  ((identity . 00000100)
   (domain-owner . structure)
   (result-form . pair))

  ((identity . 00000101)
   (domain-owner . structure)
   (input-domain . pair)
   (result-form . value))

  ((identity . 00000110)
   (domain-owner . structure)
   (input-domain . pair)
   (result-form . value))

  ((identity . 00000010)
   (domain-owner . predicate)
   (result-form . predicate-one-bit)
   (yes . one)
   (no . zero)
   (empty-structure-result . one)
   (pair-result . zero)
   (non-pair-result . one)
   (rich-result . forbidden)
   (host-bool-authority . forbidden))

  ((identity . 00000011)
   (domain-owner . predicate)
   (input-domain . (admitted-atom admitted-atom))
   (result-form . (predicate-one-bit structural-empty-no-witness))
   (yes . one)
   (no . zero)
   (same-atom-result . one)
   (distinct-atom-result . zero)
   (outside-domain . structural-empty-no-witness)
   (rich-result . forbidden)
   (host-bool-authority . forbidden))

  ((identity . 00000111)
   (domain-owner . control)
   (clause-shape . (test expression))
   (test-domain . (predicate-one-bit structural-empty-no-witness))
   (select-on . one)
   (skip-on . (zero structural-empty))
   (exhaustion-result . structural-empty)
   (zero-empty-distinct . required)
   (three-part-clause . forbidden)
   (explicit-result-match . forbidden)
   (generic-truthiness . forbidden)
   (host-bool-authority . forbidden)))