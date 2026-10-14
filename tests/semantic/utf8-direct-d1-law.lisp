; Self-verdicts belong to binary SENS. Numeric operands are UTF-8 byte
; data in this pinned UTF-8 reader, not implicit D1 or domain identities.
; A wrong answer selects the impossible CAR(QUOTE EMPTY) branch.

(110
  ((101 (utf8-in-range? 256 0 255) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (utf8-in-range? 255 0 255) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (utf8-continuation-byte? 128) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (utf8-continuation-byte? 192) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (utf8-byte? 255) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (utf8-byte? 256) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (utf8-all-bytes? (001 ())) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (utf8-two-continuations? 128 192) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))
