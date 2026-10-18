; D10 empty-queue? / sortcar / sort* / map-into / vector↔list
; Pure composition over existing Core4. Residency lib/domains/d10.lisp.

; D10:0011000010 EMPTY-QUEUE?
(0011 черга-порожня?
  (0010 (q) (порожній? q)))
(0011 empty-queue? черга-порожня?)

; D10:0001110011 SORTCAR — sort by CAR via stable list sort
(0011 сортувати-за-першим
  (0010 (елементи)
    (сортувати-список-за
      (0010 (a b) (менше? (перше a) (перше b)))
      елементи)))
(0011 sortcar сортувати-за-першим)

; D10:0011001011 SORT* — alias to stable list sort with caller predicate
(0011 сортувати-зірочка сортувати-список-за)
(0011 sort* сортувати-зірочка)

; D10:0011001001 MAP-INTO — pure: map fn over src (dest ignored)
(0011 відобразити-у
  (0010 (fn dest src)
    (відобразити fn src)))
(0011 map-into відобразити-у)

; D10:0000101100 VECTOR->LIST / D10:0000101111 LIST->VECTOR
(0011 вектор->список
  (0010 (v) v))
(0011 vector->list вектор->список)
(0011 список->вектор
  (0010 (xs) xs))
(0011 list->vector список->вектор)
