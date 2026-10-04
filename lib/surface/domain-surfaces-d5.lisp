; D5 v2 human surface projection.
; Projection only: semantic authority remains exact D5 bits + Contract 11.3 law.
; Authority: #3305 / contracts/d5-ratification.lisp.
; Historical flat-byte coordinates are not valid keys here.
;
; Row format:
; (row D5 "BITS" ROLE "EN" "UK" "SA" UK_STATUS SA_STATUS)

(domain-surfaces-d5
  (schema domain-surfaces-d5/1)
  (status projection-only)
  (identity-law "surface -> exact (D5,bits) -> D5 law")
  (languages en uk sa)

  (row D5 "00000" function  "evalquote"    "обчислити-як-є"                 "svarūpa-vicāraṇa"   selected candidate)
  (row D5 "00001" form      "function"     "функція-значення"                "phalana-rūpa"        selected candidate)
  (row D5 "00010" form      "fexpr"        "необчислений-вираз"              "avicārita-rūpa"      selected candidate)
  (row D5 "00011" form      "macro"        "макрос"                          "vistāra-rūpa"        selected candidate)
  (row D5 "00100" form      "label"        "мітка"                           "cihna"               stable-donor candidate)
  (row D5 "00101" form      "prog"         "програма"                        "kāryakrama"          selected candidate)
  (row D5 "00110" function  "set"          "встановити"                      "sthāpana"            selected candidate)
  (row D5 "00111" form      "setq"         "встановити-ім'я"                 "nāma-sthāpana"       selected candidate)
  (row D5 "01000" predicate "zerop"        "нуль?"                           "saṅkhyā-śūnya?"      selected candidate)
  (row D5 "01001" predicate "numberp"      "число?"                          "saṅkhyā?"            selected candidate)
  (row D5 "01010" function  "plus"         "додати"                          "yoga"                stable-donor stable-donor)
  (row D5 "01011" function  "difference"   "відняти"                         "viyoga"              stable-donor stable-donor)

  ; Selector spellings are generated compositionally from D3/D4 surface words.
  (row D5 "01100" selector  "cdaar"        "решта-від-першого-від-першого"  "śeṣa-ādi-ādi"        generated generated)
  (row D5 "01101" selector  "cdadr"        "решта-від-першого-від-решти"    "śeṣa-ādi-śeṣa"      generated generated)
  (row D5 "01110" selector  "cddar"        "решта-від-решти-від-першого"    "śeṣa-śeṣa-ādi"      generated generated)
  (row D5 "01111" selector  "cdddr"        "решта-від-решти-від-решти"      "śeṣa-śeṣa-śeṣa"    generated generated)
  (row D5 "10000" selector  "caaar"        "перше-від-першого-від-першого"  "ādi-ādi-ādi"        generated generated)
  (row D5 "10001" selector  "caadr"        "перше-від-першого-від-решти"    "ādi-ādi-śeṣa"      generated generated)
  (row D5 "10010" selector  "cadar"        "перше-від-решти-від-першого"    "ādi-śeṣa-ādi"      generated generated)
  (row D5 "10011" selector  "caddr"        "перше-від-решти-від-решти"      "ādi-śeṣa-śeṣa"    generated generated)

  (row D5 "10100" function  "reverse"      "зворот"                          "viloma"              stable-donor stable-donor)
  (row D5 "10101" function  "reverse-onto" "зворот-до"                       "viloma-saṅkalana"    selected candidate)
  (row D5 "10110" function  "times"        "помножити"                       "guṇana"              stable-donor stable-donor)
  (row D5 "10111" function  "quotient"     "частка"                          "bhāga"               stable-donor stable-donor)
  (row D5 "11000" form      "go"           "перейти"                         "gamana"              selected candidate)
  (row D5 "11001" form      "return"       "повернути"                       "nivartana"           selected candidate)
  (row D5 "11010" predicate "lessp"        "менше?"                          "hīna?"               stable-donor stable-donor)
  (row D5 "11011" predicate "greaterp"     "більше?"                         "adhika?"             stable-donor stable-donor)
  (row D5 "11100" function  "assoc"        "знайти-за-ключем"                "saṃbandha"           stable-donor stable-donor)
  (row D5 "11101" predicate "member"       "значення-у-списку?"              "sambaddha?"          stable-donor stable-donor)
  (row D5 "11110" function  "pairlis"      "спарувати"                       "yugma-bandha"        selected candidate)
  (row D5 "11111" function  "subst"        "замінити"                        "ādeśa"               stable-donor candidate)
)
