; D8 FLOOR / DIVIDE / REM + LOGBITP — pure for non-negative D24+
; Residency lib/domains/d8.lisp. No bare numeric call-heads.

; D8:10110111 FLOOR — non-neg integers: same as quotient
(0011 округлити-вниз
  (0010 (a b) (quotient a b)))
(0011 floor округлити-вниз)

; D8:11110110 DIVIDE
(0011 поділити
  (0010 (a b) (quotient a b)))
(0011 divide поділити)

; D8:01000000 REM — same as mod for non-neg
(0011 остача-зі-знаком mod)
(0011 rem остача-зі-знаком)

; D8:01001110 LOGBITP — bit index of n is 1?
(0011 біт-встановлений?
  (0010 (index n)
    (equal?
      (mod
        (quotient n (піднести-до-степеня #d24:000000000000000000000010 index))
        #d24:000000000000000000000010)
      #d24:000000000000000000000001)))
(0011 logbitp? біт-встановлений?)
