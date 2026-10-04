; D1-D4 human surface projection.
; Projection only: semantic authority remains exact domain + exact bits + domain law.
; Authority: language-contract.lisp, #3202 (D3), #3272 (D4), #3020 (binary-only).
; Legacy SID8/Sens8/Function8 coordinates MUST NOT be added here.
;
; Row format:
; (row DOMAIN "BITS" ROLE "EN" "UK" "SA" UK_STATUS SA_STATUS)
;
; ROLE:
;   value       -- human spelling may denote a domain value
;   display     -- descriptive label only; punctuation/structure remains reader syntax
;   form        -- special/bootstrap form surface
;   function    -- callable function surface
;   predicate   -- callable predicate surface
;   selector    -- generated selector surface
;
; Status is surface-selection status only. It does not change semantic authority.

(domain-surfaces-d1-d4
  (schema domain-surfaces-d1-d4/1)
  (status projection-only)
  (identity-law "surface -> exact (domain,bits) -> domain law")
  (languages en uk sa)

  ; D1 — PredicateBit
  (row D1 "0" value "no" "ні" "na" selected selected)
  (row D1 "1" value "yes" "так" "ām" selected selected)

  ; D2 — exact structure. These are display labels; human punctuation remains reader syntax.
  (row D2 "00" display "separator" "пропуск" "antarāla" selected candidate)
  (row D2 "01" display "close" "закрити" "samāpana" selected candidate)
  (row D2 "10" display "open" "відкрити" "udghāṭana" selected candidate)
  (row D2 "11" display "dot" "крапка" "bindu" selected selected)

  ; D3 — foundation
  (row D3 "000" display "empty" "порожнє" "śūnya" selected selected)
  (row D3 "001" form "quote" "як-є" "svarūpa" selected stable-donor)
  (row D3 "010" predicate "atom" "атом?" "aṇu?" selected stable-donor)
  (row D3 "011" function "cdr" "решта" "śeṣa" selected stable-donor)
  (row D3 "100" function "car" "перше" "ādi" selected stable-donor)
  (row D3 "101" predicate "eq" "тотожне?" "abheda?" selected stable-donor)
  (row D3 "110" form "cond" "за-умовою" "krama" selected stable-donor)
  (row D3 "111" function "cons" "сполучити" "saṃyuj" selected stable-donor)

  ; D4 — full compact bootstrap, owner-ratified #3272
  (row D4 "0000" function "apply" "застосувати" "prayoga" selected candidate)
  (row D4 "0001" function "eval" "обчислити" "vicāraṇa" selected donor-candidate)
  (row D4 "0010" form "lambda" "функція" "phalana" selected candidate)
  (row D4 "0011" form "define" "визначити" "nirvacana" selected candidate)
  (row D4 "0100" predicate "not" "не" "niṣedha" selected candidate)
  (row D4 "0101" predicate "null" "порожнє?" "śūnya?" selected candidate)
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
