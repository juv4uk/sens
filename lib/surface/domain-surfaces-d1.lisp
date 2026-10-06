; D1 human surface projection.
; One domain per file. Projection only; exact bits + D1 law remain semantic authority.
; Row format: (row D1 "BITS" ROLE "EN" "UK" "SA" UK_STATUS SA_STATUS)

(domain-surfaces-d1
  (schema domain-surfaces-d1/1)
  (status projection-only)
  (identity-law "surface -> exact (D1,bits) -> D1 law")
  (languages en uk sa)

  (row D1 "0" value "no" "ні" "na" selected selected)
  (row D1 "1" value "yes" "так" "ām" selected selected)
)
