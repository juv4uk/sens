; #1711/#1703 — current Lisp-owned foundation answer contract.
;
; This document owns language-level result roles. It intentionally keeps the
; foundation small while the binary-only migration proceeds.
;
; Canonical predicate result:
;   one bit only: 0 NO / 1 YES
;
; Canonical control:
;   COND consumes only that one-bit predicate result.
;
; Structural empty () is data/exhaustion, never a third truth value.

(answer-contract/2

  ((identity . structural-empty)
   (domain-owner . structure)
   (result-form . empty-structure)
   (predicate-answer . no)
   (false-sentinel . no))

  ((identity . 00000001)
   (domain-owner . structure)
   (role . quote)
   (result-form . data))

  ((identity . 00000100)
   (domain-owner . structure)
   (role . cons)
   (input-domain . (value value))
   (result-form . pair))

  ((identity . 00000101)
   (domain-owner . structure)
   (role . car)
   (input-domain . pair)
   (result-form . value))

  ((identity . 00000110)
   (domain-owner . structure)
   (role . cdr)
   (input-domain . pair)
   (result-form . value))

  ((identity . 00000010)
   (domain-owner . predicate)
   (role . atom)
   (question . atomic-or-non-pair)
   (result-form . predicate-one-bit)
   (yes . one)
   (no . zero)
   (empty-structure-result . one)
   (pair-result . zero)
   (non-pair-result . one)
   (structural-kind-result . forbidden)
   (host-bool-authority . forbidden))

  ((identity . 00000011)
   (domain-owner . predicate)
   (role . eq)
   (input-domain . (admitted-atom admitted-atom))
   (result-form . predicate-one-bit)
   (yes . one)
   (no . zero)
   (same-atom-result . one)
   (distinct-atom-result . zero)
   (outside-domain . type-error)
   (identity-relation-result . forbidden)
   (deep-equality . separate-operation)
   (host-bool-authority . forbidden))

  ((identity . 00000111)
   (domain-owner . control)
   (role . cond)
   (clause-shape . (test expression))
   (test-domain . predicate-one-bit)
   (select-on . one)
   (skip-on . zero)
   (exhaustion-result . structural-empty)
   (three-part-clause . forbidden)
   (expected-result-field . forbidden)
   (generic-truthiness . forbidden)
   (graded-answer-match . forbidden))

  ((identity . binary-only-boundary)
   (predicate-width . one-bit)
   (control-width . two-bit-default)
   (text-width . seven-bit-upc7)
   (function-width . eight-bit)
   (number-width . variable-binary)
   (cross-domain-bit-coercion . forbidden)))