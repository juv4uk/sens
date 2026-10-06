; D3 human surface projection.
; One domain per file. Projection only; exact bits + D3 law remain semantic authority.
; Row format: (row D3 "BITS" ROLE "EN" "UK" "SA" UK_STATUS SA_STATUS)

(domain-surfaces-d3
  (schema domain-surfaces-d3/1)
  (status projection-only)
  (identity-law "surface -> exact (D3,bits) -> D3 law")
  (languages en uk sa)

  (row D3 "000" display "empty" "порожнє" "śūnya" selected selected)
  (row D3 "001" form "quote" "як-є" "svarūpa" selected stable-donor)
  (row D3 "010" predicate "atom?" "атом?" "aṇu" selected stable-donor)
  (row D3 "011" function "cdr" "решта" "śeṣa" selected stable-donor)
  (row D3 "100" function "car" "перше" "ādi" selected stable-donor)
  (row D3 "101" predicate "eq?" "тотожне?" "abheda" selected stable-donor)
  (row D3 "110" form "cond" "за-умовою" "krama" selected stable-donor)
  (row D3 "111" function "cons" "сполучити" "saṃyuj" selected stable-donor)
)
