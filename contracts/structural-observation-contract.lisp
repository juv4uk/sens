; structural-observation-contract.lisp — Lisp-owned result algebra for #218.
;
; This contract is derived from the structure the language actually has:
; Canon 0 `()` is a distinct ground value, pairs are the one decomposable
; cons-cell shape, and every remaining runtime value is non-pair/atomic for
; PRIM_ATOM's structural jurisdiction.
;
; The contract therefore does not ask a generic TRUE/FALSE question. It reports
; the observed structural class. PRIM_EQ likewise reports its own atom-identity
; relation instead of borrowing a universal truth sentinel.
;
; These result records are ordinary Lisp data, not new primitive identities.
; They are intentionally non-coercible to generic truth. #217 now supplies the
; canonical explicit-result-equality dispatch that can consume them without
; Value -> bool coercion. Historical two-part cond remains migration-only.

(structural-observation-contract/1
  ((identity . "0002")
   (surface . atom)
   (domain-owner . structural-observation)
   (input-domain . value)
   (result-form . structural-kind)
   (cases .
     (((when . canon-zero)
       (result . (structural-kind empty-list)))
      ((when . pair)
       (result . (structural-kind pair)))
      ((when . non-pair-nonempty)
       (result . (structural-kind atom)))))
   (generic-truth-coercion . forbidden)
   (control-dispatch . explicit-result-equality))

  ((identity . "0003")
   (surface . eq)
   (domain-owner . structural-observation)
   (input-domain . (atom? atom))
   (result-form . identity-relation)
   (cases .
     (((when . same-atom)
       (result . (identity-relation same)))
      ((when . distinct-atoms)
       (result . (identity-relation distinct)))))
   (outside-domain . type-error)
   (generic-truth-coercion . forbidden)
   (control-dispatch . explicit-result-equality))

  ((identity . "1023")
   (surface . symbol?)
   (domain-owner . structural-observation)
   (input-domain . value)
   (result-form . class-membership)
   (target-class . symbol)
   (cases .
     (((when . symbol)
       (result . (class-membership symbol member)))
      ((when . non-symbol)
       (result . (class-membership symbol nonmember)))))
   (generic-truth-coercion . forbidden)
   (control-dispatch . explicit-result-equality))

  ((identity . "1024")
   (surface . string?)
   (domain-owner . structural-observation)
   (input-domain . value)
   (result-form . class-membership)
   (target-class . string)
   (cases .
     (((when . string)
       (result . (class-membership string member)))
      ((when . non-string)
       (result . (class-membership string nonmember)))))
   (generic-truth-coercion . forbidden)
   (control-dispatch . explicit-result-equality))

  ((identity . "1025")
   (surface . string<?)
   (domain-owner . structural-observation)
   (input-domain . (string string))
   (result-form . text-order)
   (cases .
     (((when . left-before-right)
       (result . (text-order before)))
      ((when . same-text)
       (result . (text-order same)))
      ((when . left-after-right)
       (result . (text-order after)))))
   (outside-domain . type-error)
   (generic-truth-coercion . forbidden)
   (control-dispatch . explicit-result-equality))

  ((identity . "1026")
   (surface . numeric-buffer?)
   (domain-owner . structural-observation)
   (input-domain . value)
   (result-form . class-membership)
   (target-class . numeric-buffer)
   (cases .
     (((when . numeric-buffer)
       (result . (class-membership numeric-buffer member)))
      ((when . non-numeric-buffer)
       (result . (class-membership numeric-buffer nonmember)))))
   (generic-truth-coercion . forbidden)
   (control-dispatch . explicit-result-equality)))
