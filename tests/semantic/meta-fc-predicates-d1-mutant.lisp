; D1 is one bit, not the structural empty list.
; Both first-class predicates are asked about a quoted atomic datum.
; A violated law deliberately invokes non-callable D1:NO.

(110
  ((101 (my-fc-primitive? (001 sample)) #d1:0)
   (110
     ((101 (my-fc-closure? (001 sample)) #d1:1)
      #d1:1)
     (#d1:1 (#d1:0))))
  (#d1:1 (#d1:0)))
