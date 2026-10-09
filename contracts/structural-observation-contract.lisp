; structural-observation-contract.lisp — remaining non-core structural result algebras.
;
; ATOM (00000010) and EQ (00000011) no longer live here: their current exact
; one-bit predicate laws are owned by the shared Lisp semantic witnesses under #1709.
; This document remains only for still-unmigrated structural/text observations.

(structural-observation-contract/1
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
