; D5 arithmetic surfaces from lib/domains/d5.lisp — not new laws.
; Bodies call exact domain heads already admitted (PLUS/DIFFERENCE/TIMES/LESSP/GREATERP).
; D5:01000 ZEROP: x = x+x iff x=0 on qualified D24+ (PLUS rejects foreign domains).

(0011 нуль?
  (0010 (значення)
    (101 значення (01010 значення значення))))
(0011 нуль-д24? нуль?)
(0011 zerop нуль?)

(0011 додати
  (0010 (a b) (01010 a b)))
(0011 plus додати)

(0011 відняти
  (0010 (a b) (01011 a b)))
(0011 difference відняти)

(0011 помножити
  (0010 (a b) (10110 a b)))
(0011 times помножити)

(0011 менше?
  (0010 (a b) (11010 a b)))
(0011 lessp менше?)

(0011 більше?
  (0010 (a b) (11011 a b)))
(0011 greaterp більше?)
