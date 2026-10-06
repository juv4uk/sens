; D4 human surface projection.
; One domain per file. Projection only; exact bits + D4 law remain semantic authority.
; Row format: (row D4 "BITS" ROLE "EN" "UK" "SA" UK_STATUS SA_STATUS)

(domain-surfaces-d4
  (schema domain-surfaces-d4/1)
  (status projection-only)
  (identity-law "surface -> exact (D4,bits) -> D4 law")
  (languages en uk sa)

  (row D4 "0000" function "apply" "застосувати" "prayoga" selected candidate)
  (row D4 "0001" function "eval" "обчислити" "vicāraṇa" selected donor-candidate)
  (row D4 "0010" form "lambda" "функція" "phalana" selected candidate)
  (row D4 "0011" form "define" "визначити" "nirvacana" selected candidate)
  (row D4 "0100" predicate "not?" "хибне?" "niṣedha" selected candidate)
  (row D4 "0101" predicate "null?" "порожнє?" "śūnya-parīkṣā" selected candidate)
  (row D4 "0110" selector "cdar" "решта-від-першого" "śeṣa-ādi" selected generated)
  (row D4 "0111" selector "cddr" "решта-від-решти" "śeṣa-śeṣa" selected generated)
  (row D4 "1000" selector "caar" "перше-від-першого" "ādi-ādi" selected generated)
  (row D4 "1001" selector "cadr" "перше-від-решти" "ādi-śeṣa" selected generated)
  (row D4 "1010" function "lookup" "знайти" "anveṣaṇa" selected candidate)
  (row D4 "1011" function "bind" "зв'язати" "bandha" selected candidate)
  (row D4 "1100" function "evcon" "обчислити-умови" "krama-vicāraṇa" selected candidate)
  (row D4 "1101" function "evlis" "обчислити-список" "śreṇī-vicāraṇa" selected candidate)
  (row D4 "1110" function "list" "список" "śreṇī" selected stable-donor)
  (row D4 "1111" function "append" "приєднати" "saṅkalana" selected stable-donor)
)
