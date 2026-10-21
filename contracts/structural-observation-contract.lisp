; Контракт структурних спостережень — залишкові неядерні
; різновиди структурованих результатів.
;
; ATOM (00000010) та EQ (00000011) більше не визначаються тут:
; їхні чинні точні однобітні предикатні закони належать спільним
; семантичним свідченням Lisp у #1709.
; Цей документ збережено лише для структурних і текстових
; спостережень, які ще не перенесено.

(structural-observation-contract-1
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
