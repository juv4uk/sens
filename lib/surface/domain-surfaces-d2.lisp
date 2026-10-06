; D2 human surface projection.
; One domain per file. Projection only; exact bits + D2 law remain semantic authority.
; Row format: (row D2 "BITS" ROLE "EN" "UK" "SA" UK_STATUS SA_STATUS)

(domain-surfaces-d2
  (schema domain-surfaces-d2/1)
  (status projection-only)
  (identity-law "surface -> exact (D2,bits) -> D2 law")
  (languages en uk sa)

  (row D2 "00" display "separator" "пропуск" "antarāla" selected candidate)
  (row D2 "01" display "close" "закрити" "samāpana" selected candidate)
  (row D2 "10" display "open" "відкрити" "udghāṭana" selected candidate)
  (row D2 "11" display "dot" "крапка" "bindu" selected selected)
)
