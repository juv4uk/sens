; D8 CEILING / ASH / RSH — pure non-neg D24+
; Residency lib/domains/d8.lisp. No bare numeric call-heads.

; D8:00011111 CEILING
(0011 округлити-вгору
  (0010 (a b)
    (110
      ((нуль? (mod a b)) (quotient a b))
      ((0100 (нуль? (mod a b)))
       (додати-1 (quotient a b))))))
(0011 ceiling округлити-вгору)

; D8:01000101 ASH — non-neg shift count: left = * 2^k
(0011 арифметичний-зсув
  (0010 (n k)
    (110
      ((нуль? k) n)
      ((0100 (нуль? k))
       (помножити n (піднести-до-степеня #d24:000000000000000000000010 k))))))
(0011 ash арифметичний-зсув)

; D8:00011110 RSH — right shift = quotient by 2^k
(0011 зсунути-вправо
  (0010 (n k)
    (110
      ((нуль? k) n)
      ((0100 (нуль? k))
       (quotient n (піднести-до-степеня #d24:000000000000000000000010 k))))))
(0011 rsh зсунути-вправо)

; D8:10110101 ARITHMETIC-SHIFT — same as ASH for non-neg k
(0011 арифметично-зсунути арифметичний-зсув)
