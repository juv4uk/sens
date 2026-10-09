; #432 research-only RED probe.
; The lower-basis search must not pretend EQ can inspect pair contents.
; Current Canon contract: EQ accepts atoms only; pair operands must fail Type.

(eq
  (cons (quote left-a) (quote right-a))
  (cons (quote left-b) (quote right-b)))
