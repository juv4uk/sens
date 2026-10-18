; D10 numeric-not-equal / vector-list / slice + D9 dependents/lint-size
; Pure composition. Residency lib/domains/d9.lisp + d10.lisp.

; D10:0000000111 NUMERIC-NOT-EQUAL?
(0011 числа-нерівні?
  (0010 (a b) (хибне? (equal? a b))))
(0011 numeric-not-equal? числа-нерівні?)

; D10:0000101100 VECTOR->LIST / D10:0000101111 LIST->VECTOR
(0011 вектор->список
  (0010 (v) v))
(0011 vector->list вектор->список)
(0011 список->вектор
  (0010 (xs) xs))
(0011 list->vector список->вектор)

; D10:0000110110 VECTOR-SLICE — same as string-slice on lists
(0011 зріз-вектора
  (0010 (v start end)
    (взяти (відняти end start) (відкинути start v))))
(0011 vector-slice зріз-вектора)

; D10:0000011000 MULTIPLE-VALUE-LIST
(0011 список-усіх-значень
  (0010 (xs) xs))
(0011 multiple-value-list список-усіх-значень)

; D9:001011100 DEPENDENTS-OF → map-get
(0011 залежні-від мапа-отримати)
(0011 dependents-of залежні-від)

; D9:001100001 LINT-SIZE → length
(0011 аналіз-розмір довжина)
(0011 lint-size аналіз-розмір)
