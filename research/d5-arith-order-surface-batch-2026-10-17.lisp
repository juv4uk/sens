; Exact SENS surface DEFINE batch: D5 DIFFERENCE/TIMES/LESSP/GREATERP + D6 ADD1/SUB1 aliases

; D5 surface DEFINE over exact admitted call heads (lib/domains/d5.lisp).
; Not new laws: residency already holds; body is domain coordinate call.
; D5:01011 DIFFERENCE / відняти
(0011 відняти
  (0010 (a b) (01011 a b)))
(0011 difference відняти)
; D5:10110 TIMES / помножити
(0011 помножити
  (0010 (a b) (10110 a b)))
(0011 times помножити)
; D5:11010 LESSP / менше?
(0011 менше?
  (0010 (a b) (11010 a b)))
(0011 lessp? менше?)
; D5:11011 GREATERP / більше?
(0011 більше?
  (0010 (a b) (11011 a b)))
(0011 greaterp? більше?)
; D6:001110 ADD1 / D6:001111 SUB1 domain-surface aliases
(0011 додати-1 збільшити-на-один)
(0011 відняти-1 зменшити-на-один)
(0011 add1 збільшити-на-один)
(0011 sub1 зменшити-на-один)
