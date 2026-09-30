; #1717 executable witness: variadic predicate combinators after Predicate1 reset.
; Every operand is itself a predicate expression; there are no source predicate literals.
;
; OR: NO, NO, YES -> YES
(01001000
  (10011011
    (00000010 (00000001 (00000000)))
    (00000010 (00000001 (00000000)))
    (00000010 (00000001 ()))))

; AND: YES, YES, YES -> YES
(01001000
  (10011010
    (00000010 (00000001 ()))
    (00000010 (00000001 ()))
    (00000010 (00000001 ()))))
