; D8 POP / PAIR / EQUAL / AND / OR surfaces + INTEGER-LENGTH
; Residency lib/domains/d8.lisp. Aliases to existing Core4 / pure bit-length.

; D8:10111100 POP
(0011 зняти-з-початку
  (0010 (список) (решта список)))
(0011 pop зняти-з-початку)

; D8:11111101 PAIR — already Core4 `pair`
(0011 пара pair)

; D8:11110111 EQUAL — already Core4 `equal?`
(0011 однакові? equal?)

; D8:11110101 AND / D8:11111100 OR — Core4 short-circuit macros
(0011 та and)
(0011 або or)

; D8:10111111 INTEGER-LENGTH — successive quotient by 2
(0011 бітова-довжина-з
  (0010 (n acc)
    (110
      ((нуль? n) acc)
      ((0100 (нуль? n))
       (бітова-довжина-з
         (quotient n #d24:000000000000000000000010)
         (додати-1 acc))))))
(0011 бітова-довжина-цілого
  (0010 (n)
    (110
      ((нуль? n) #d24:000000000000000000000000)
      ((0100 (нуль? n))
       (бітова-довжина-з n #d24:000000000000000000000000)))))
(0011 integer-length бітова-довжина-цілого)
