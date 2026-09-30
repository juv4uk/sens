; #1826 — exact-ℚ admissibility for numeric comparison predicates.
;
; Exactness answers only one question here: may this numeric predicate produce
; an exact language answer without approximation?
;
; If admitted, the result is the ordinary SENS PredicateBit:
;   0 = NO
;   1 = YES
;
; PredicateBit is not Number. Exact rational values 0/1 and 1/1 remain ordinary
; Numbers and must not be used as predicate identity.
;
; Outside the admitted exact-ℚ domain the predicate must fail with a named
; domain/type failure. Structural () is not a third predicate result.

(exact-q-predicate-contract/2
  ((domain-owner . exact-q-comparison-predicate)
   (admissibility . all-required-values-exact-rational)
   (result-form . predicate-one-bit)
   (yes . one)
   (no . zero)
   (outside-domain . named-domain-error)
   (approximation-policy . forbidden)
   (number-as-predicate-result . forbidden)
   (generic-truth-coercion . forbidden)
   (host-bool-authority . forbidden))

  ((identity . 00011010)
   (relation . strictly-increasing)
   (operand-domain . exact-rational-sequence))

  ((identity . 00011011)
   (relation . strictly-decreasing)
   (operand-domain . exact-rational-sequence))

  ((identity . 00011100)
   (relation . numeric-equality)
   (operand-domain . exact-rational-sequence))

  ((identity . 00011101)
   (relation . nondecreasing)
   (operand-domain . exact-rational-sequence))

  ((identity . 00011110)
   (relation . nonincreasing)
   (operand-domain . exact-rational-sequence)))