; D10 empty-queue? / sortcar / sort* / map-into / vector↔list
; Pure composition over existing Core4. Residency lib/domains/d10.lisp.

; D10:0011000010 EMPTY-QUEUE?
(визначити черга-порожня?
  (функція (q) (порожній? q)))
(визначити empty-queue? черга-порожня?)

; D10:0001110011 SORTCAR — sort by CAR via stable list sort
(визначити сортувати-за-першим
  (функція (елементи)
    (сортувати-список-за
      (функція (a b) (менше? (перше a) (перше b)))
      елементи)))
(визначити sortcar сортувати-за-першим)

; D10:0011001011 SORT* — alias to stable list sort with caller predicate
(визначити сортувати-зірочка сортувати-список-за)
(визначити sort* сортувати-зірочка)

; D10:0011001001 MAP-INTO — pure: map fn over src (dest ignored)
(визначити відобразити-у
  (функція (fn dest src)
    (відобразити fn src)))
(визначити map-into відобразити-у)

; D10:0000101100 VECTOR->LIST / D10:0000101111 LIST->VECTOR
(визначити вектор->список
  (функція (v) v))
(визначити vector->list вектор->список)
(визначити список->вектор
  (функція (xs) xs))
(визначити list->vector список->вектор)
