; D8:00010001 NTH-right, structural law #3744.
; Expected exact D1 PredicateBit vector (1 1 0); third is wrong-side mutant.
; Exact D24 index, no bare numeric code standing in for a domain.
(list
  (equal?
    (елемент-справа #d24:000000000000000000000000
      (list (quote а) (quote б) (quote в)))
    (quote в))
  (equal?
    (елемент-справа #d24:000000000000000000000001
      (list (quote а) (quote б) (quote в)))
    (quote б))
  (equal?
    (елемент-справа #d24:000000000000000000000000
      (list (quote а) (quote б) (quote в)))
    (quote а)))
