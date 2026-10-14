; Native SENS D1 self-verdict: two structural and three explicit-D24 facts.
; Mathematical admission is D24+ only; no Number or D8 promotion.
; Wrong results select the impossible CAR(QUOTE EMPTY) branch.

(110
  ((101 (utf8-all-bytes? (001 не-список)) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (utf8-all-bytes? (001 ())) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

; First and last unsigned D24 natural-byte laws, plus a non-integer rejection.
(110
  ((101 (utf8-in-range? #d24:000000000000000000000000 #d24:000000000000000000000000 #d24:000000000000000011111111) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))
(110
  ((101 (utf8-byte? #d24:000000000000000011111111) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))
(110
  ((101 (utf8-byte? (10111 #d24:000000000000000000000001 #d24:000000000000000000000010)) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))
