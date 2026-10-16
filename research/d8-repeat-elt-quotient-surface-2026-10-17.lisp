; D8:00001010 REPEAT + D8:00000101 ELT + D5:10111 QUOTIENT uk surface
; Pure composition / alias. Residency: lib/domains/d{5,8}.lisp

; D8:00000101 ELT
(0011 елемент-за-індексом
  (0010 (lst n)
    (110
      ((нуль? n) (100 lst))
      ((0101 lst) (001 ()))
      ((0100 (0101 lst))
       (елемент-за-індексом (011 lst) (зменшити-на-один n))))))
(0011 elt елемент-за-індексом)

; D8:00001010 REPEAT
(0011 повторити
  (0010 (n x)
    (110
      ((нуль? n) (001 ()))
      ((0100 (нуль? n))
       (111 x (повторити (зменшити-на-один n) x))))))
(0011 repeat повторити)

; D5:10111 QUOTIENT — domain surface uk (body already as quotient)
(0011 частка quotient)
