; D8:00010001 NTH-right, structural law #3744.
; Expected exact D1 PredicateBit vector (1 1 0); third is wrong-side mutant.
; Exact D24 index, no bare numeric code standing in for a domain.
(список
  (equal?
    (елемент-справа #d24:000000000000000000000000
      (список (як-є а) (як-є б) (як-є в)))
    (як-є в))
  (equal?
    (елемент-справа #d24:000000000000000000000001
      (список (як-є а) (як-є б) (як-є в)))
    (як-є б))
  (equal?
    (елемент-справа #d24:000000000000000000000000
      (список (як-є а) (як-є б) (як-є в)))
    (як-є а)))
