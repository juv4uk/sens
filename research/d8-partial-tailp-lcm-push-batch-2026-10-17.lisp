; D8 PARTIAL / TAILP / LCM / PUSH + MOD uk alias — pure composition
; Residency lib/domains/d8.lisp. No new opcodes. No bare numeric call-heads.

; D8:00011010 PARTIAL — same law as D6 CURRY
(0011 застосувати-префікс частково-застосувати)
(0011 partial застосувати-префікс)

; D8:00101100 MOD uk surface (body already mod / остача)
(0011 модульна-остача mod)
(0011 остача-модульна модульна-остача)

; D8:00100110 LCM — |a*b|/gcd for non-negative D24+
(0011 нск
  (0010 (a b)
    (110
      ((or (нуль? a) (нуль? b)) #d24:000000000000000000000000)
      ((0100 (or (нуль? a) (нуль? b)))
       (quotient (помножити a b) (нсд a b))))))
(0011 lcm нск)

; D8:01000110 PUSH — functional cons to front
(0011 додати-на-початок
  (0010 (елемент список)
    (сполучити елемент список)))
(0011 push додати-на-початок)

; D8:01010110 TAILP — structural: sub is some cdr-chain of lst
(0011 спільний-хвіст?
  (0010 (sub lst)
    (110
      ((equal? sub lst) (001 (1)))
      ((0101 lst) (001 (0)))
      ((0100 (0101 lst))
       (спільний-хвіст? sub (решта lst))))))
(0011 tailp? спільний-хвіст?)
